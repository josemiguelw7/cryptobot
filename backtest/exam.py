"""
ENTRANCE EXAM runner — the formal gate into the Strategy League.

Spec: docs/entrance_exam.md (pre-registered pass bar; stricter-only).
Rolling 183-day windows stepping 91 days over daily candles, per pair.
Strategies come from bot/strategies.py (shared with the live league).
One exam per candidate name, ever — enforced via results/exam_ledger.csv.

Simulation (W1.2): each window is driven bar-by-bar through the
strategy's step(); fractional target weights and path-dependent logic
(stop-losses) are supported. Fees+slippage charged on every weight
change, per side. Signals use COMPLETED candles only (W1.3): the data
loader drops today's still-forming bar.

Usage:
    python backtest/exam.py --selftest
    python backtest/exam.py --candidate t200s10
"""
import argparse, csv, hashlib, os, subprocess, sys
from datetime import date, datetime, timezone
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot"))
import strategies as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
import lint_candles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "candles_daily")
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
LEDGER = os.path.join(RESULTS, "exam_ledger.csv")

WIN, STEP = 183, 91
FEE, SLIP = 0.006, 0.0005
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


# ---------------------------------------------------------------- data

def load_closes(pair):
    """Completed daily closes, oldest..newest. Drops today's partial
    bar (W1.3) so exam and live signals see identical data."""
    path = os.path.join(DAILY, f"{pair}_86400s.csv")
    if not os.path.exists(path):
        return [], []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = [r for r in rows if r["datetime"] < today]
    closes = [float(r["close"]) for r in rows]
    dates = [r["datetime"] for r in rows]
    return closes, dates


# ---------------------------------------------------------------- simulate

def simulate_window(strat, closes, a, b, fee, slip):
    """Drive strat bar-by-bar over the window [a, b). CRUCIAL: step()
    sees FULL history closes[:i+1] (so a 200-day SMA has its lookback
    even when the window is 183 days), but equity is measured only
    across the window. Fresh position at window open; costs charged on
    every weight change, per side, on turned-over notional. Stateful:
    ctx carries weight + entry_price so stop-losses work.
    Returns (equity_curve, n_trades)."""
    eq = 1.0
    ctx = {"weight": 0.0, "entry_price": None}
    curve, trades = [], 0

    def apply_target(tgt, px):
        nonlocal eq, trades
        tgt = max(0.0, min(1.0, float(tgt)))
        turn = abs(tgt - ctx["weight"])
        if turn > 1e-9:
            eq *= (1 - (fee + slip) * turn)
            trades += 1
            if ctx["weight"] == 0 and tgt > 0:
                ctx["entry_price"] = px
            elif tgt == 0:
                ctx["entry_price"] = None
            ctx["weight"] = tgt

    # establish opening position from history available at bar a
    apply_target(strat.step(closes[:a + 1], ctx), closes[a])
    for i in range(a + 1, b):
        r = closes[i] / closes[i - 1] - 1
        eq *= (1 + ctx["weight"] * r)
        apply_target(strat.step(closes[:i + 1], ctx), closes[i])
        curve.append(eq)
    return curve, trades


def _dd(curve):
    peak, mdd = curve[0], 0.0
    for v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return mdd


def exam_pair(pair, strat, fee, slip):
    closes, dates = load_closes(pair)
    # need warmup history before the first window can open
    start = strat.warmup
    if len(closes) < start + WIN:
        return []
    rows = []
    while start + WIN <= len(closes):
        curve, trades = simulate_window(strat, closes, start,
                                        start + WIN, fee, slip)
        if not curve:
            start += STEP; continue
        w = closes[start:start + WIN]
        bh = [c / w[0] for c in w]
        rows.append({
            "pair": pair, "start": dates[start],
            "ret": curve[-1] - 1, "bh": w[-1] / w[0] - 1,
            "dd": _dd(curve), "bh_dd": _dd(bh), "trades": trades})
        start += STEP
    return rows


# ---------------------------------------------------------------- grade

def grade(rows):
    n = len(rows)
    pairs = len({r["pair"] for r in rows})
    stitched = float(np.prod([1 + r["ret"] for r in rows]) - 1)
    stitched_bh = float(np.prod([1 + r["bh"] for r in rows]) - 1)
    shallower = sum(1 for r in rows if r["dd"] > r["bh_dd"])
    trades = sum(r["trades"] for r in rows)
    worst_dd = min((r["dd"] for r in rows), default=0.0)
    # non-overlapping subset (W3.2): every other window ~ step 183
    nonov = rows[::2]
    st_no = float(np.prod([1 + r["ret"] for r in nonov]) - 1)
    st_no_bh = float(np.prod([1 + r["bh"] for r in nonov]) - 1)
    checks = {
        "1_sample  (>=8 windows, >=2 pairs)": n >= 8 and pairs >= 2,
        "2_safety  (no window DD <= -20%)":   worst_dd > -0.20,
        "3_riskedge(shallower DD >=60% win.)": n > 0 and shallower / n >= 0.60,
        "4_return  (stitched >= buy-hold)":   stitched >= stitched_bh,
        "5_activity(>=4 trades total)":       trades >= 4,
    }
    summary = {"windows": n, "pairs": pairs, "stitched": stitched,
               "stitched_bh": stitched_bh, "worst_dd": worst_dd,
               "shallower_pct": shallower / n if n else 0.0,
               "trades": trades, "nonov_windows": len(nonov),
               "nonov_stitched": st_no, "nonov_bh": st_no_bh}
    return all(checks.values()), checks, summary


# ---------------------------------------------------------------- provenance

def git_hash():
    try:
        h = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            stderr=subprocess.DEVNULL).decode().strip()
        dirty = subprocess.call(
            ["git", "diff", "--quiet"], cwd=ROOT) != 0
        return h + ("-dirty" if dirty else "")
    except Exception:
        return "nogit"


def data_fingerprint(pairs):
    parts = []
    for p in pairs:
        path = os.path.join(DAILY, f"{p}_86400s.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()[:8]
            parts.append(f"{p}:{h}")
    return ";".join(parts)


def ledger_names():
    if not os.path.exists(LEDGER):
        return set()
    with open(LEDGER) as f:
        return {row["candidate"] for row in csv.DictReader(f)}


def ledger_record(name, verdict, summary, pairs):
    os.makedirs(RESULTS, exist_ok=True)
    new = not os.path.exists(LEDGER)
    n_examined = len(ledger_names()) + 1
    with open(LEDGER, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["candidate", "date", "verdict", "windows",
                        "pairs", "stitched", "stitched_bh", "trades",
                        "git_hash", "candidates_examined_to_date",
                        "data_fingerprint"])
        w.writerow([name, date.today().isoformat(),
                    "PASS" if verdict else "FAIL",
                    summary["windows"], summary["pairs"],
                    f"{summary['stitched']:.4f}",
                    f"{summary['stitched_bh']:.4f}", summary["trades"],
                    git_hash(), n_examined, data_fingerprint(pairs)])


def save_windows(name, rows):
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, f"exam_{name}_{date.today()}.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def run_exam(name, fee, slip, record):
    strat = S.get(name)
    rows = []
    for pair in PAIRS:
        rows += exam_pair(pair, strat, fee, slip)
    if not rows:
        print(f"{name}: no valid windows (needs more history)."); return False
    verdict, checks, sm = grade(rows)
    print(f"\n=== ENTRANCE EXAM: {name} ===")
    print(f"windows {sm['windows']} (non-overlap {sm['nonov_windows']}) | "
          f"pairs {sm['pairs']} | trades {sm['trades']}")
    print(f"stitched {sm['stitched']:+.1%} vs buy-hold {sm['stitched_bh']:+.1%}"
          f"  |  non-overlap {sm['nonov_stitched']:+.1%} vs "
          f"{sm['nonov_bh']:+.1%}")
    print(f"worst window DD {sm['worst_dd']:.1%} | "
          f"shallower-DD windows {sm['shallower_pct']:.0%}")
    # fee stress (W3.1): re-grade at 1.5x cost, report only
    srows = []
    for pair in PAIRS:
        srows += exam_pair(pair, strat, fee * 1.5, slip * 1.5)
    if srows:
        sv, _, _ = grade(srows)
        print(f"fee-stress @1.5x: would {'PASS' if sv else 'FAIL'}")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"VERDICT: {'PASS - eligible for league' if verdict else 'FAIL'}")
    if record:
        out = save_windows(name, rows)
        ledger_record(name, verdict, sm, PAIRS)
        print(f"saved -> {out}\nledger -> {LEDGER}")
    else:
        print("(selftest: nothing recorded)")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fee", type=float, default=FEE)
    ap.add_argument("--slip", type=float, default=SLIP)
    ap.add_argument("--skip-lint", action="store_true")
    args = ap.parse_args()

    if not args.skip_lint:
        errs, warns = lint_candles.lint(PAIRS)
        for w in warns[:10]:
            print(f"  data WARN: {w}")
        if errs:
            for e in errs[:10]:
                print(f"  data ERROR: {e}")
            sys.exit("Aborting: data linter found hard errors.")

    if args.selftest:
        print("SELFTEST: harness validation only, ledger untouched.")
        run_exam("hold", args.fee, args.slip, record=False)
        run_exam("trend_200", args.fee, args.slip, record=False)
        return

    if not args.candidate:
        sys.exit(f"Provide --candidate NAME or --selftest. "
                 f"Known: {sorted(S.REGISTRY)}")
    if args.candidate not in S.REGISTRY:
        sys.exit(f"Unknown candidate {args.candidate!r}. "
                 f"Known: {sorted(S.REGISTRY)}")
    if args.candidate in ledger_names():
        sys.exit(f"REFUSED: {args.candidate!r} already examined. "
                 "One exam per candidate, ever (docs/entrance_exam.md).")
    run_exam(args.candidate, args.fee, args.slip, record=True)


if __name__ == "__main__":
    main()
