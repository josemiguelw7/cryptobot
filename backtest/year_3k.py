"""
"If I'd invested $3,000 a year ago with the current bot settings,
 what would I have today?" — answered TWO ways:

  (A) NAIVE  : momentum rotation using TODAY's top-25 universe.json.
               This peeks at the future (we only know today's top coins
               because they survived). It is the mirage. Shown so you
               can SEE the bias, not to trust it.
  (B) HONEST : same strategy, but the tradable universe at each weekly
               decision is chosen from TRAILING dollar-volume only —
               no knowledge of the future. This is the real answer.

Benchmarks: BTC-HOLD and ETH-HOLD over the same year.
Current bot settings: top-3 by 30d momentum, weekly rebalance,
0.6% fee + 0.05% slip per side. Start $3,000.
"""
import csv, glob, json, os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DD = os.path.join(ROOT, "data", "candles_daily")
START, TOP_N, LOOK, REBAL = 3000.0, 3, 30, 7
FEE, SLIP = 0.006, 0.0005

def load(pair):
    p = os.path.join(DD, f"{pair}_86400s.csv")
    out = {}
    with open(p) as f:
        for r in csv.DictReader(f):
            out[r["datetime"]] = (float(r["close"]), float(r["volume"]))
    return out

# load everything once
files = glob.glob(os.path.join(DD, "*_86400s.csv"))
allpairs = [os.path.basename(f).replace("_86400s.csv", "") for f in files]
data = {p: load(p) for p in allpairs}
# common calendar (BTC has full history)
dates = sorted(data["BTC-USD"].keys())
# last 366 calendar days present in data
year_dates = dates[-366:]
d0, d1 = year_dates[0], year_dates[-1]

def close(pair, d):
    row = data.get(pair, {}).get(d)
    return row[0] if row else None

def hold_return(pair):
    p0, p1 = close(pair, d0), close(pair, d1)
    # one entry fee, one exit fee
    return START * (p1 / p0) * (1 - FEE - SLIP) * (1 - FEE - SLIP)

def momentum_rotation(universe_fn):
    """universe_fn(d, idx) -> list of tradable pairs known at date d."""
    cash, units, last_rebal = START, {}, -10**9
    for idx, d in enumerate(year_dates):
        # mark to market
        equity = cash + sum(u * (close(p, d) or 0) for p, u in units.items())
        if idx - last_rebal < REBAL:
            continue
        univ = universe_fn(d, idx)
        mom = {}
        for p in univ:
            c_now = close(p, d)
            # 30 trading days back
            j = idx - LOOK
            if j < 0:
                continue
            c_then = close(p, year_dates[j])
            if c_now and c_then:
                mom[p] = c_now / c_then - 1
        ranked = sorted(mom.items(), key=lambda kv: kv[1], reverse=True)
        target = [p for p, m in ranked[:TOP_N] if m > 0]
        # sell what's not in target
        for p in [p for p in list(units) if p not in target]:
            px = close(p, d)
            if px:
                gross = units.pop(p) * px * (1 - SLIP)
                cash += gross * (1 - FEE)
        # buy new
        new = [p for p in target if p not in units]
        if new and cash > 1:
            per = cash / len(new)
            for p in new:
                px = close(p, d)
                if px:
                    units[p] = (per * (1 - FEE)) / (px * (1 + SLIP))
            cash = 0.0
        last_rebal = idx
    final = cash + sum(u * (close(p, d1) or 0) for p, u in units.items())
    return final

# (A) naive: today's universe.json, fixed, all year
with open(os.path.join(ROOT, "data", "universe.json")) as f:
    today_univ = json.load(f)
naive = momentum_rotation(lambda d, idx: today_univ)

# (B) honest: point-in-time top-25 by trailing 30d dollar-volume
def pit_universe(d, idx):
    if idx < LOOK:
        return []
    window = year_dates[idx - LOOK:idx]
    dv = {}
    for p in allpairs:
        vals = []
        for wd in window:
            row = data.get(p, {}).get(wd)
            if row:
                vals.append(row[0] * row[1])   # close * volume = $volume
        if len(vals) >= LOOK * 0.8:
            dv[p] = sum(vals) / len(vals)
    top = sorted(dv.items(), key=lambda kv: kv[1], reverse=True)[:25]
    return [p for p, _ in top]
honest = momentum_rotation(pit_universe)

btc = hold_return("BTC-USD")
eth = hold_return("ETH-USD")

def line(label, v):
    pct = v / START - 1
    print(f"  {label:34} ${v:>9,.2f}   {pct:+7.1%}")

print(f"\n$3,000 invested {d0} -> {d1}\n")
print("  ── the mirage (do not trust) ──")
line("Momentum rotation, TODAY's coins", naive)
print("\n  ── the honest answer ──")
line("Momentum rotation, point-in-time", honest)
print("\n  ── benchmarks (just hold) ──")
line("BTC-HOLD", btc)
line("ETH-HOLD", eth)
print()
