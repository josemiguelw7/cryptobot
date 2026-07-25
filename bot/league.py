"""
STRATEGY LEAGUE - multiple paper strategies, side by side, ZERO real money.

Forward paper trading only. Each strategy has its own cash, holdings,
peak and circuit breaker. Results append to logs/league_equity.csv and
logs/league_trades.csv for the portal and (later) the public site.

Members:
  BTC-HOLD   benchmark: buy BTC once, hold. The bar every candidate
             must beat (docs/success_criteria.md). No circuit breaker.
  BTC-TREND  exam graduate: hold BTC while price > 200-day SMA, else
             cash. Backtest exam: return ~= hold, drawdown robustly
             smaller across the whole MA grid.
  MOM-ROT    control (FAILED its point-in-time exam): top-3 momentum
             rotation, weekly. Inherits the original paper book.

Usage: python bot/league.py     # one decision cycle for all members
"""
import csv, json, os, time
from datetime import datetime, timezone
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
import sys as _sys
_sys.path.insert(0, HERE)
import strategies as S   # shared logic: exam graduate == live member (W1.1)
STATE = os.path.join(HERE, "league_state.json")
LEGACY = os.path.join(HERE, "state.json")
UNIVERSE = os.path.join(ROOT, "data", "universe.json")
EQLOG = os.path.join(ROOT, "logs", "league_equity.csv")
TRLOG = os.path.join(ROOT, "logs", "league_trades.csv")
BASE = "https://api.exchange.coinbase.com"
FEE, SLIP = 0.006, 0.0005
START = 10_000.0
MAXDD = 0.20

STRATS = {
    "BTC-HOLD":  {"kind": "hold",   "pair": "BTC-USD", "benchmark": True},
    "BTC-TREND": {"kind": "trend",  "pair": "BTC-USD", "ma": 200},
    "MOM-ROT":   {"kind": "momrot", "top_n": 3, "lookback": 30,
                  "rebal_days": 7, "note": "control (failed exam)"},
}

_cache = {}

def _raw(pair):
    """Cached (close, date) rows, oldest..newest, from Coinbase."""
    if pair not in _cache:
        r = requests.get(f"{BASE}/products/{pair}/candles",
                         params={"granularity": 86400}, timeout=30)
        r.raise_for_status()
        rows = sorted(r.json())  # each: [time, low, high, open, close, vol]
        _cache[pair] = [(row[4],
                         datetime.fromtimestamp(row[0], timezone.utc)
                         .strftime("%Y-%m-%d")) for row in rows]
        time.sleep(0.12)
    return _cache[pair]

def daily_closes(pair):
    """ALL closes incl. today's forming bar — used for live valuation."""
    return [c for c, _ in _raw(pair)]

def completed_closes(pair):
    """Closes on COMPLETED days only (drops today's partial candle).
    Signals use this so the live signal == the exam signal (W1.3)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [c for c, d in _raw(pair) if d < today]

def price(pair):
    return daily_closes(pair)[-1]

def days_since(iso):
    if iso is None:
        return 10**9
    return (datetime.now(timezone.utc)
            - datetime.fromisoformat(iso)).total_seconds() / 86400

def targets(cfg):
    if cfg["kind"] == "hold":
        return [cfg["pair"]]
    if cfg["kind"] == "trend":
        # SAME code path as the exam: shared Trend strategy on COMPLETED
        # closes. If this passes the exam, this is what trades. (W1.1/W1.3)
        cl = completed_closes(cfg["pair"])
        strat = S.Trend(cfg["ma"])
        if len(cl) < strat.warmup:
            return []
        w = strat.step(cl, {"weight": 0.0, "entry_price": None})
        return [cfg["pair"]] if w > 0 else []
    if cfg["kind"] == "momrot":
        with open(UNIVERSE) as f:
            pairs = json.load(f)
        mom = {}
        for p in pairs:
            try:
                cl = daily_closes(p)
            except Exception as e:
                print(f"  fetch failed {p}: {e}")
                continue
            if len(cl) > cfg["lookback"]:
                mom[p] = cl[-1] / cl[-1 - cfg["lookback"]] - 1
        ranked = sorted(mom.items(), key=lambda kv: kv[1], reverse=True)
        return [p for p, m in ranked[:cfg["top_n"]] if m > 0]

def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    now = datetime.now(timezone.utc).isoformat()
    st = {n: {"cash": START, "units": {}, "last_rebalance": None,
              "created": now} for n in STRATS}
    if os.path.exists(LEGACY):            # continuity for MOM-ROT
        with open(LEGACY) as f:
            old = json.load(f)
        for k in ("cash", "units", "last_rebalance", "created",
                  "peak_equity", "halted"):
            if k in old:
                st["MOM-ROT"][k] = old[k]
    return st

def append(path, header, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow(row)

def log_trade(now, strat, action, pair, px, units, value, fee):
    append(TRLOG, ["time", "strategy", "action", "pair", "price",
                   "units", "value", "fee"],
           [now.isoformat(), strat, action, pair, px,
            units, f"{value:.2f}", f"{fee:.2f}"])

def sell(st, now, name, pair, px, tag="SELL"):
    gross = st["units"].pop(pair) * px * (1 - SLIP)
    fee = gross * FEE
    st["cash"] += gross - fee
    log_trade(now, name, tag, pair, px, "", gross, fee)
    print(f"  [{name}] {tag} {pair} @ {px:,.4f} (fee ${fee:.2f})")

def cycle():
    league = load()
    now = datetime.now(timezone.utc)
    print(f"[{now:%Y-%m-%d %H:%M} UTC] league cycle")
    for name, cfg in STRATS.items():
        st = league[name]
        tgt = targets(cfg) or []
        px = {p: price(p) for p in set(list(st["units"]) + tgt)}
        equity = st["cash"] + sum(u * px.get(p, 0)
                                  for p, u in st["units"].items())
        peak = max(st.get("peak_equity", equity), equity)
        st["peak_equity"] = peak
        append(EQLOG, ["time", "strategy", "equity", "cash", "holdings"],
               [now.isoformat(), name, f"{equity:.2f}",
                f"{st['cash']:.2f}", " ".join(st["units"]) or "cash"])
        print(f"  [{name}] equity ${equity:,.2f} "
              f"holding {list(st['units']) or 'cash'} -> target {tgt or 'cash'}")

        if st.get("halted"):
            print(f"  [{name}] HALTED (circuit breaker). Retired.")
            continue
        if (not cfg.get("benchmark") and st["units"]
                and equity < peak * (1 - MAXDD)):
            print(f"  [{name}] CIRCUIT BREAKER: ${equity:,.2f} is "
                  f">{MAXDD:.0%} below peak ${peak:,.2f}. Liquidating.")
            for p in list(st["units"]):
                sell(st, now, name, p, px[p], tag="HALT-SELL")
            st["halted"] = True
            continue

        gate = cfg.get("rebal_days")
        if gate and days_since(st["last_rebalance"]) < gate:
            continue
        if set(tgt) == set(st["units"]):
            if gate:
                st["last_rebalance"] = now.isoformat()
            continue

        for p in [p for p in list(st["units"]) if p not in tgt]:
            sell(st, now, name, p, px[p])
        new = [p for p in tgt if p not in st["units"]]
        if new and st["cash"] > 1:
            per = st["cash"] / len(new)
            for p in new:
                fee = per * FEE
                u = (per - fee) / (px[p] * (1 + SLIP))
                st["units"][p] = u
                log_trade(now, name, "BUY", p, px[p],
                          f"{u:.6f}", per, fee)
                print(f"  [{name}] BUY {p} @ {px[p]:,.4f} "
                      f"(${per:,.2f}, fee ${fee:.2f})")
            st["cash"] = 0.0
        st["last_rebalance"] = now.isoformat()

    # atomic write (W2.2): temp file + replace, so a crash mid-write
    # can never corrupt the forward record.
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(league, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE)
    print("league state saved.")

if __name__ == "__main__":
    cycle()
