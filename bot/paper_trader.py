"""
Paper trading bot - momentum rotation with ZERO real money.

Each cycle: fetch live daily closes from Coinbase's public API, mark
the paper portfolio to market, and - if 7+ days since last rebalance -
re-pick the top N coins by 30-day momentum (positive-momentum filter,
otherwise sit in cash). Simulated fills include fees + slippage.

State persists in bot/state.json; every simulated trade is appended to
logs/paper_trades.csv. No API keys. No orders. No real account.

Usage:
    python bot/paper_trader.py          # one decision cycle
    python bot/paper_trader.py --loop   # check hourly, forever
"""
import argparse, csv, json, os, time
from datetime import datetime, timezone
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE_PATH = os.path.join(HERE, "state.json")
TRADELOG = os.path.join(ROOT, "logs", "paper_trades.csv")
UNIVERSE = os.path.join(ROOT, "data", "universe.json")
BASE = "https://api.exchange.coinbase.com"

TOP_N, LOOKBACK, REBAL_DAYS = 3, 30, 7
FEE, SLIP = 0.006, 0.0005
START_CASH = 10_000.0
MAX_DRAWDOWN = 0.20   # circuit breaker: halt if equity falls 20% off peak


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"cash": START_CASH, "units": {}, "last_rebalance": None,
            "created": datetime.now(timezone.utc).isoformat()}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def fetch_daily_closes(pair):
    """Recent daily candles for one pair, closes oldest -> newest."""
    r = requests.get(f"{BASE}/products/{pair}/candles",
                     params={"granularity": 86400}, timeout=30)
    r.raise_for_status()
    rows = sorted(r.json())          # oldest first
    return [row[4] for row in rows]  # close column


def days_since(iso):
    if iso is None:
        return 10**9
    then = datetime.fromisoformat(iso)
    return (datetime.now(timezone.utc) - then).total_seconds() / 86400


def log_trade(row):
    os.makedirs(os.path.dirname(TRADELOG), exist_ok=True)
    new = not os.path.exists(TRADELOG)
    with open(TRADELOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "action", "pair", "price", "units",
                        "value", "fee"])
        w.writerow(row)


def cycle(state):
    with open(UNIVERSE) as f:
        pairs = json.load(f)

    mom, price = {}, {}
    for p in pairs:
        try:
            c = fetch_daily_closes(p)
        except Exception as e:
            print(f"  fetch failed {p}: {e}")
            continue
        if len(c) > LOOKBACK:
            price[p] = c[-1]
            mom[p] = c[-1] / c[-1 - LOOKBACK] - 1
        time.sleep(0.15)

    now = datetime.now(timezone.utc)
    equity = state["cash"] + sum(u * price.get(p, 0)
                                 for p, u in state["units"].items())
    print(f"\n[{now:%Y-%m-%d %H:%M} UTC] paper equity ${equity:,.2f} | "
          f"cash ${state['cash']:,.2f} | "
          f"holding {list(state['units']) or 'nothing'}")

    # append equity snapshot for the portal's chart
    hist = os.path.join(ROOT, "logs", "equity_history.csv")
    hnew = not os.path.exists(hist)
    os.makedirs(os.path.dirname(hist), exist_ok=True)
    with open(hist, "a", newline="") as f:
        w = csv.writer(f)
        if hnew:
            w.writerow(["time", "equity", "cash", "holdings"])
        w.writerow([now.isoformat(), f"{equity:.2f}", f"{state['cash']:.2f}",
                    " ".join(state["units"]) or "cash"])

    ranked = sorted(mom.items(), key=lambda kv: kv[1], reverse=True)
    print("Top momentum: " +
          ", ".join(f"{p} {m:+.1%}" for p, m in ranked[:5]))

    # --- circuit breaker (#12): protect against every future mistake ---
    peak = max(state.get("peak_equity", equity), equity)
    state["peak_equity"] = peak
    if state.get("halted"):
        print("HALTED by circuit breaker. To resume after reviewing what "
              "happened, remove the 'halted' key from bot/state.json.")
        return
    if state["units"] and equity < peak * (1 - MAX_DRAWDOWN):
        print(f"CIRCUIT BREAKER TRIPPED: equity ${equity:,.2f} is more than "
              f"{MAX_DRAWDOWN:.0%} below peak ${peak:,.2f}. "
              f"Liquidating to cash and halting.")
        for p in list(state["units"]):
            gross = state["units"].pop(p) * price[p] * (1 - SLIP)
            fee = gross * FEE
            state["cash"] += gross - fee
            log_trade([now.isoformat(), "HALT-SELL", p, price[p], "",
                       f"{gross:.2f}", f"{fee:.2f}"])
        state["halted"] = True
        return

    if days_since(state["last_rebalance"]) < REBAL_DAYS:
        print(f"No rebalance due "
              f"(last was {days_since(state['last_rebalance']):.1f}d ago).")
        return

    target = [p for p, m in ranked[:TOP_N] if m > 0]
    print(f"REBALANCE -> target: {target or 'ALL CASH'}")

    for p in [p for p in list(state["units"]) if p not in target]:
        gross = state["units"].pop(p) * price[p] * (1 - SLIP)
        fee = gross * FEE
        state["cash"] += gross - fee
        log_trade([now.isoformat(), "SELL", p, price[p], "",
                   f"{gross:.2f}", f"{fee:.2f}"])
        print(f"  SELL {p} @ {price[p]:,.4f} (fee ${fee:.2f})")

    new = [p for p in target if p not in state["units"]]
    if new and state["cash"] > 1:
        per = state["cash"] / len(new)
        for p in new:
            fee = per * FEE
            u = (per - fee) / (price[p] * (1 + SLIP))
            state["units"][p] = u
            log_trade([now.isoformat(), "BUY", p, price[p], f"{u:.6f}",
                       f"{per:.2f}", f"{fee:.2f}"])
            print(f"  BUY  {p} @ {price[p]:,.4f} "
                  f"(${per:,.2f}, fee ${fee:.2f})")
        state["cash"] = 0.0

    state["last_rebalance"] = now.isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()
    state = load_state()
    while True:
        cycle(state)
        save_state(state)
        if not args.loop:
            break
        time.sleep(3600)


if __name__ == "__main__":
    main()
