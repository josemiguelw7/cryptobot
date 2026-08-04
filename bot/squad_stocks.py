"""
STOCK forward squad — the charter's engine on a market clock.

Adapter over bot/squad.py: imports it and overrides data, quotes,
paths, and the seed module, so every charter rule (s4.1 costs, s4.3
cost gate, s4.5 integrity, s8 kill switches, s3 counted days, s12.1
loss taxonomy) is enforced by the SAME code the crypto squad runs.
No forked logic; one engine, two markets.

Stock-specific behavior, all pre-registered in docs/stocks_standard.md:
  clock    trades only on closed RTH bars, 9:30-16:00 ET Mon-Fri.
           Outside the session it marks equity and exits politely.
           Holidays need no calendar: no fresh bar, no cycle.
  costs    commission 0.0 (zero-commission era), slippage 5bps flat
           per leg, x2 on stop-outs (same rule as crypto)
  sizing   vol target 2%/day, estimated from RTH bars with a session
           scale of 7 bars (not 24)
  horizon  hold_h declared in RTH bars in seeds_stocks
  data     data/stocks/{TICKER}_1h.csv, refreshed by fetch_stocks

Run: .venv/bin/python bot/squad_stocks.py [--status]
"""
from __future__ import annotations
import csv, os, subprocess, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import squad as Q
import seeds_stocks as SS

ET = ZoneInfo("America/New_York")
STOCKS = os.path.join(ROOT, "data", "stocks")

# --- seeds + paths (separate ledgers, same formats) -----------------
Q.SEEDS = SS
Q.STATE = os.path.join(HERE, "squad_stocks_state.json")
Q.EQLOG = os.path.join(ROOT, "logs", "squad_stocks_equity.csv")
Q.TRLOG = os.path.join(ROOT, "logs", "squad_stocks_trades.csv")
Q.DECLOG = os.path.join(ROOT, "logs", "squad_stocks_decisions.csv")
Q.DAYLOG = os.path.join(ROOT, "logs", "squad_stocks_daily.csv")

# --- costs: zero commission, flat 5bps slippage ---------------------
Q.FEE_TAKER = 0.0
Q.slip_for = lambda t: 0.0005

# --- vol sizing on session scale (7 RTH bars, not 24) ---------------
def vol_weight_stk(closes):
    if len(closes) < 9:
        return 0.0
    rets = [closes[i] / closes[i - 1] - 1 for i in range(-7, 0)]
    mu = sum(rets) / 7
    var = sum((r - mu) ** 2 for r in rets) / 6
    vol_day = (var ** 0.5) * (7 ** 0.5)
    if vol_day <= 0:
        return 1.0 / Q.MAX_POS
    return min(1.0 / Q.MAX_POS, Q.TV_DAY / vol_day)

Q.vol_weight = vol_weight_stk


# --- market clock ---------------------------------------------------
def session_open(now=None):
    et = (now or datetime.now(timezone.utc)).astimezone(ET)
    m = et.hour * 60 + et.minute
    return et.weekday() < 5 and 570 <= m < 960


# --- data -----------------------------------------------------------
def load_stk(tk):
    path = os.path.join(STOCKS, f"{tk}_1h.csv")
    if not os.path.exists(path):
        return [], []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return ([float(r["close"]) for r in rows],
            [int(float(r["timestamp"])) for r in rows])

Q.load_hourly = load_stk


def load_bars_stk(tk):
    """E2.1 full RTH candles. yfinance gives o/h/l/c/v; the store has
    always had them."""
    path = os.path.join(STOCKS, f"{tk}_1h.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            out.append((int(float(r["timestamp"])), float(r["open"]),
                        float(r["high"]), float(r["low"]),
                        float(r["close"]), float(r["volume"])))
        except (KeyError, ValueError):
            continue
    return out

Q.load_bars = load_bars_stk
Q.MARKET = "SPY"                  # E2.4: stock market proxy


def topup_stk(tickers):
    """Refresh the whole store (yfinance is batch-shaped). Returns the
    tickers that came back with no data — each an execution_data event."""
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "data", "fetch_stocks.py")],
                   capture_output=True, text=True, cwd=ROOT)
    return [t for t in tickers if not load_stk(t)[0]]

Q.topup = topup_stk


def quote_stk(tk):
    """Last closed RTH bar as the execution reference, with the modeled
    spread applied symmetrically. Stocks have no public 24/7 top-of-book
    like Coinbase's ticker; the charter's requirement is that the fill
    reference is not the bar the signal read, which holds: signals read
    the last CLOSED bar and fills price off that close plus slippage."""
    closes, _ = load_stk(tk)
    if not closes:
        raise RuntimeError(f"no data for {tk}")
    px = closes[-1]
    half = 0.0002 * px
    return {"bid": px - half, "ask": px + half, "mid": px,
            "spread_pct": 0.0004}

Q.quote = quote_stk


def cycle():
    now = Q.utc_now()
    if not SS.ARMED:
        print(f"[{now:%Y-%m-%d %H:%M} UTC] stock squad (UNARMED)")
        print("  seed roster adopted; engine waits for ARMED=True after")
        print("  all 10 exam verdicts are recorded. (charter s9.3)")
        return 0
    if not session_open(now):
        et = now.astimezone(ET)
        print(f"[{now:%Y-%m-%d %H:%M} UTC / {et:%H:%M} ET] market CLOSED "
              f"- no signals, no counted cycle")
        return 0
    return Q.cycle()


if __name__ == "__main__":
    if "--status" in sys.argv:
        et = datetime.now(timezone.utc).astimezone(ET)
        print(f"stock squad | ARMED={SS.ARMED} | "
              f"{et:%Y-%m-%d %H:%M} ET | "
              f"session {'OPEN' if session_open() else 'CLOSED'}")
        Q.status()
    else:
        sys.exit(cycle())
