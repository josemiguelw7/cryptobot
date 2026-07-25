"""
ENTRANCE EXAM runner — the formal gate into the Strategy League.

Spec: docs/entrance_exam.md (pre-registered pass bar; stricter-only).
Rolling 183-day windows stepping 91 days over daily candles, per pair.
Signals close -> next open, 0.6% fee + 0.05% slip per side (engine.py).
One exam per candidate name, ever — enforced via results/exam_ledger.csv.

Usage:
    python backtest/exam.py --selftest
    python backtest/exam.py --candidate trend_200
"""
import argparse, csv, os, sys
from datetime import date
import numpy as np
import pandas as pd
import engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "candles_daily")
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "results")
LEDGER = os.path.join(RESULTS, "exam_ledger.csv")

WIN, STEP = 183, 91
FEE, SLIP = 0.006, 0.0005
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


# ---------------------------------------------------------------- candidates
# Each candidate: (warmup_bars, builder). Builder takes a daily df and
# returns a full-history position array (0/1). Indicators only look
# backward, so computing on full history then slicing leaks nothing.

def _trend(n):
    def build(df):
        sma = df["close"].rolling(n).mean()
        sig = (df["close"] > sma).astype(int)
        return sig.shift(1).fillna(0).astype(int).to_numpy()
    return build

def _cross(fast, slow):
    def build(df):
        d = engine.add_signals(df.copy(), fast, slow)
        return d["position"].to_numpy()
    return build

CANDIDATES = {
    "hold":       (1,   lambda df: np.ones(len(df), dtype=int)),
    "sma_20_50":  (50,  _cross(20, 50)),      # selftest control
    "trend_150":  (150, _trend(150)),
    "trend_200":  (200, _trend(200)),
    "trend_250":  (250, _trend(250)),
}


# ---------------------------------------------------------------- windows

def hold_max_dd(closes):
    eq = closes / closes[0]
    run_max = np.maximum.accumulate(eq)
    return float((eq / run_max - 1.0).min())


def exam_pair(pair, warmup, build, fee, slip):
    path = os.path.join(DAILY, f"{pair}_86400s.csv")
    if not os.path.exists(path):
        return []
    df = engine.load_candles(path)
    if len(df) < warmup + WIN + 1:
        return []
    pos = build(df)
    closes = df["close"].to_numpy(float)
    rows, start = [], warmup
    while start + WIN <= len(df):
        sl = df.iloc[start:start + WIN].copy()
        sl["position"] = pos[start:start + WIN]
        r = engine.run_backtest(sl, fee_rate=fee, slip_rate=slip)
        rows.append({
            "pair": pair, "start": str(sl["datetime"].iloc[0].date()),
            "ret": r["total_return"], "bh": r["buy_hold_return"],
            "dd": r["max_drawdown"],
            "bh_dd": hold_max_dd(closes[start:start + WIN]),
            "trades": r["n_trades"]})
        start += STEP
    return rows


# ---------------------------------------------------------------- verdict

def grade(rows):
    n = len(rows)
    pairs = len({r["pair"] for r in rows})
    stitched = float(np.prod([1 + r["ret"] for r in rows]) - 1)
    stitched_bh = float(np.prod([1 + r["bh"] for r in rows]) - 1)
    shallower = sum(1 for r in rows if r["dd"] > r["bh_dd"])
    trades = sum(r["trades"] for r in rows)
    worst_dd = min((r["dd"] for r in rows), default=0.0)
    checks = {
        "1_sample  (>=8 windows, >=2 pairs)":
            n >= 8 and pairs >= 2,
        "2_safety  (no window DD <= -20%)":
            worst_dd > -0.20,
        "3_riskedge(shallower DD >=60% win.)":
            n > 0 and shallower / n >= 0.60,
        "4_return  (stitched >= buy-hold)":
            stitched >= stitched_bh,
        "5_activity(>=4 trades total)":
            trades >= 4,
    }
    summary = {"windows": n, "pairs": pairs, "stitched": stitched,
               "stitched_bh": stitched_bh, "worst_dd": worst_dd,
               "shallower_pct": shallower / n if n else 0.0,
               "trades": trades}
    return all(checks.values()), checks, summary


# ---------------------------------------------------------------- ledger

def ledger_names():
    if not os.path.exists(LEDGER):
        return set()
    with open(LEDGER) as f:
        return {row["candidate"] for row in csv.DictReader(f)}


def ledger_record(name, verdict, summary):
    os.makedirs(RESULTS, exist_ok=True)
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["candidate", "date", "verdict", "windows",
                        "pairs", "stitched", "stitched_bh", "trades"])
        w.writerow([name, date.today().isoformat(),
                    "PASS" if verdict else "FAIL",
                    summary["windows"], summary["pairs"],
                    f"{summary['stitched']:.4f}",
                    f"{summary['stitched_bh']:.4f}", summary["trades"]])


def save_windows(name, rows):
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, f"exam_{name}_{date.today()}.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


# ---------------------------------------------------------------- run

def run_exam(name, fee, slip, record):
    warmup, build = CANDIDATES[name]
    rows = []
    for pair in PAIRS:
        rows += exam_pair(pair, warmup, build, fee, slip)
    verdict, checks, summary = grade(rows)
    print(f"\n=== ENTRANCE EXAM: {name} ===")
    print(f"windows {summary['windows']} | pairs {summary['pairs']} | "
          f"trades {summary['trades']}")
    print(f"stitched {summary['stitched']:+.1%} vs "
          f"buy-hold {summary['stitched_bh']:+.1%} | "
          f"worst window DD {summary['worst_dd']:.1%} | "
          f"shallower-DD windows {summary['shallower_pct']:.0%}")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"VERDICT: {'PASS - eligible for league' if verdict else 'FAIL'}")
    if record:
        out = save_windows(name, rows)
        ledger_record(name, verdict, summary)
        print(f"windows saved -> {out}\nrecorded in ledger -> {LEDGER}")
    else:
        print("(selftest: nothing recorded)")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fee", type=float, default=FEE)
    ap.add_argument("--slip", type=float, default=SLIP)
    args = ap.parse_args()

    if args.selftest:
        print("SELFTEST: harness validation only, ledger untouched.")
        run_exam("hold", args.fee, args.slip, record=False)
        run_exam("sma_20_50", args.fee, args.slip, record=False)
        return

    if not args.candidate:
        sys.exit("Provide --candidate NAME or --selftest. "
                 f"Known: {sorted(CANDIDATES)}")
    if args.candidate not in CANDIDATES:
        sys.exit(f"Unknown candidate {args.candidate!r}. "
                 f"Known: {sorted(CANDIDATES)}")
    if args.candidate in ledger_names():
        sys.exit(f"REFUSED: {args.candidate!r} already examined. "
                 "One exam per candidate, ever (docs/entrance_exam.md). "
                 "A tweak is a NEW candidate with a NEW name.")
    run_exam(args.candidate, args.fee, args.slip, record=True)


if __name__ == "__main__":
    main()
