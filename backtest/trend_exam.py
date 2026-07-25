"""
ENTRANCE EXAM (one-time): long-MA trend following on BTC / ETH.
Rule: hold the coin while close > SMA(N), else cash. Signal on close,
executed at NEXT day's close (no lookahead). Taker fee + slip per side.
Grid over N to check for a plateau (edge) vs isolated spikes (noise).
"""
import csv, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEE, SLIP = 0.006, 0.0005
COST = FEE + SLIP                       # per side

def closes(pair):
    p = os.path.join(ROOT, "data", "candles_daily", f"{pair}_86400s.csv")
    with open(p) as f:
        rows = list(csv.DictReader(f))
    return [float(r["close"]) for r in rows]     # oldest -> newest

def sma(xs, n, i):
    return sum(xs[i - n + 1:i + 1]) / n

def run(cl, n):
    eq, pos, trades = 1.0, 0, 0
    curve = []
    for i in range(n, len(cl) - 1):
        sig = 1 if cl[i] > sma(cl, n, i) else 0
        r = cl[i + 1] / cl[i] - 1                # next-day return
        if sig != pos:                           # trade at next close
            eq *= (1 - COST)
            trades += 1
            pos = sig
        if pos:
            eq *= (1 + r)
        curve.append(eq)
    return curve, trades

def stats(curve, days):
    yrs = days / 365
    cagr = curve[-1] ** (1 / yrs) - 1
    peak, mdd = curve[0], 0
    rets = []
    prev = curve[0]
    for v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
        rets.append(v / prev - 1)
        prev = v
    mu = sum(rets) / len(rets)
    sd = (sum((r - mu) ** 2 for r in rets) / len(rets)) ** 0.5
    sharpe = (mu / sd * math.sqrt(365)) if sd else 0
    return curve[-1], cagr, mdd, sharpe

print(f"{'pair':8} {'MA':>4} {'final':>8} {'CAGR':>8} {'maxDD':>8} "
      f"{'Sharpe':>7} {'trades':>7}")
for pair in ["BTC-USD", "ETH-USD"]:
    cl = closes(pair)
    # buy & hold benchmark over same window as longest MA for fairness
    for n in [100, 150, 200, 250, 300]:
        curve, tr = run(cl, n)
        fin, cagr, mdd, sh = stats(curve, len(curve))
        print(f"{pair:8} {n:>4} {fin:>8.2f} {cagr:>8.1%} {mdd:>8.1%} "
              f"{sh:>7.2f} {tr:>7}")
    hold = [c / cl[300] for c in cl[300:]]
    fin, cagr, mdd, sh = stats(hold, len(hold))
    print(f"{pair:8} HOLD {fin:>8.2f} {cagr:>8.1%} {mdd:>8.1%} "
          f"{sh:>7.2f} {'0':>7}")
    print()
