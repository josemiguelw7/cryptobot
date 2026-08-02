"""
STOCK adapter over the hourly exam (docs/stocks_standard.md).

Deliberately does NOT edit exam_1h.py: the crypto batch may be running
that file, and instrument versions never mix mid-generation. This
module imports exam_1h and overrides its configuration at the module
level; every function keeps resolving names through exam_1h's global
namespace, so the patched values apply uniformly (including inside the
permutation test).

Overrides, each pre-registered in docs/stocks_standard.md:
  data      data/stocks/{TICKER}_1h.csv  (730d RTH bars, adjusted)
  universe  seeds_stocks.PAIRS (frozen 10)
  windows   WIN=630 (~90 sessions), STEP=315
  gaps      overnight/weekend/holiday gaps are NORMAL: a gap is fatal
            only if >96h, or >2h NOT landing on a session-open bar
  costs     FEE=0.0, SLIP=0.0005 flat both legs (stricter than the
            2bps the standard allows ETFs - ratchet-safe)
  sharpe    session aggregation (7 RTH bars) and sqrt(252); using
            crypto's sqrt(365) would inflate stock Sharpe ~20%
  ledger    timeframe tag "1h-stk"; SAME global ledger and K counter
"""
import csv, os, sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))

import numpy as np
import exam_1h as X
import exam
import seeds_stocks as SS

STOCKS = os.path.join(ROOT, "data", "stocks")
ET = ZoneInfo("America/New_York")

# --- 1..4: universe, seeds, windows, costs ---------------------------
X.SEEDS = SS
X.PAIRS = SS.PAIRS
X.WIN, X.STEP = 630, 315
X.FEE, X.SLIP = 0.0, 0.0005


# --- 5: data loader --------------------------------------------------
def load_hourly_stk(tk):
    path = os.path.join(STOCKS, f"{tk}_1h.csv")
    if not os.path.exists(path):
        return [], []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    closes = [float(r["close"]) for r in rows]
    ts = [int(float(r["timestamp"])) for r in rows]
    return closes, ts

X.load_hourly = load_hourly_stk


# --- 6: session-aware gap policy -------------------------------------
def window_has_gap_stk(ts, a, b):
    for i in range(a + 1, b):
        d = ts[i] - ts[i - 1]
        if d <= 2 * 3600:
            continue
        if d > 96 * 3600:              # data hole across sessions
            return True
        h = datetime.fromtimestamp(ts[i], tz=ET)
        if h.hour != 9:                # legit gaps land on the 9:30 bar
            return True
    return False

X.window_has_gap = window_has_gap_stk


# --- 7: Sharpe by sessions, sqrt(252) --------------------------------
def sharpe_stk(rows):
    hourly = []
    for r in rows:
        c = r["curve"]
        hourly += [c[0] - 1] + [c[i] / c[i - 1] - 1
                                for i in range(1, len(c))]
    sess = [float(np.prod([1 + x for x in hourly[i:i + 7]]) - 1)
            for i in range(0, len(hourly) - 6, 7)]
    if len(sess) < 30:
        return 0.0
    mu, sd = float(np.mean(sess)), float(np.std(sess, ddof=1))
    return (mu / sd) * (252 ** 0.5) if sd > 0 else 0.0

X.sharpe_annualized_from_rows = sharpe_stk


# --- 8: fingerprint over the stock store -----------------------------
def fingerprint_stk():
    import hashlib
    parts = []
    for t in SS.PAIRS:
        p = os.path.join(STOCKS, f"{t}_1h.csv")
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:8] \
            if os.path.exists(p) else "missing"
        parts.append(f"{t}:{h}")
    return ";".join(parts)

X.fingerprint_1h = fingerprint_stk


# --- 9: ledger tag ---------------------------------------------------
def ledger_record_stk(name, verdict, sm):
    os.makedirs(X.RESULTS, exist_ok=True)
    n_examined = len(exam.ledger_names()) + 1
    with open(X.LEDGER, "a", newline="") as f:
        csv.writer(f).writerow(
            [name, date.today().isoformat(),
             "PASS" if verdict else "FAIL", sm["windows"], sm["pairs"],
             f"{sm['stitched']:.4f}", f"{sm['stitched_bh']:.4f}",
             sm["trades"], exam.git_hash(), n_examined,
             fingerprint_stk(), "1h-stk"])

X.ledger_record_1h = ledger_record_stk


def dryrun():
    """Window/gap accounting only - touches nothing, records nothing."""
    print("DRYRUN stock exam windows (no ledger writes)")
    total = 0
    for t in SS.PAIRS:
        closes, ts = load_hourly_stk(t)
        if not closes:
            print(f"  {t}: NO DATA"); continue
        cutoff = ts[-1] - X.HOLDOUT_DAYS * 86400
        hi = next((i for i, x in enumerate(ts) if x >= cutoff), len(ts))
        n_ok = n_gap = 0
        start = 0
        while start + X.WIN <= hi:
            if window_has_gap_stk(ts, start, start + X.WIN):
                n_gap += 1
            else:
                n_ok += 1
            start += X.STEP
        total += n_ok
        print(f"  {t}: {len(ts)} bars, {n_ok} main windows, "
              f"{n_gap} gap-dropped")
    print(f"total main windows: {total} "
          f"(need >=24 across >=4 tickers per criterion 1)")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate")
    ap.add_argument("--dryrun", action="store_true")
    ap.add_argument("--iters", type=int, default=200)
    a = ap.parse_args()
    if a.dryrun:
        dryrun(); return
    if not a.candidate:
        sys.exit(f"--candidate NAME or --dryrun. Seeds: {SS.SEEDS}")
    if a.candidate in exam.ledger_names():
        sys.exit(f"REFUSED: {a.candidate!r} already examined. One exam "
                 f"per name, ever.")
    X.run(a.candidate, record=True, n_iter=a.iters)


if __name__ == "__main__":
    main()
