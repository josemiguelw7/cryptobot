"""
Candle data linter (build plan W1.5). Everything downstream trusts
these CSVs, so validate before any exam runs. Hard errors abort the
exam; warnings are printed.

Usage:
    python data/lint_candles.py                # lint the 8 exam pairs
    python data/lint_candles.py BTC-USD ETH-USD
"""
import csv, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DAILY = os.path.join(HERE, "candles_daily")
EXAM_PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
              "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


def lint_pair(pair):
    """Return (errors, warnings) lists for one pair."""
    path = os.path.join(DAILY, f"{pair}_86400s.csv")
    errs, warns = [], []
    if not os.path.exists(path):
        return [f"{pair}: file missing"], []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 2:
        return [f"{pair}: too few rows ({len(rows)})"], []
    return _check_rows(pair, rows, errs, warns)


def _check_rows(pair, rows, errs, warns):
    prev_ts = prev_close = None
    seen = set()
    for r in rows:
        try:
            ts = int(r["timestamp"]); close = float(r["close"])
            hi = float(r["high"]); lo = float(r["low"])
            op = float(r["open"])
        except (ValueError, KeyError) as e:
            errs.append(f"{pair}: unparseable row ({e})")
            continue
        if ts in seen:
            errs.append(f"{pair}: duplicate timestamp {r['datetime']}")
        seen.add(ts)
        for label, v in (("close", close), ("open", op),
                         ("high", hi), ("low", lo)):
            if v <= 0:
                errs.append(f"{pair}: {label}<=0 at {r['datetime']}")
        if hi < lo:
            errs.append(f"{pair}: high<low at {r['datetime']}")
        if prev_ts is not None:
            gap = (ts - prev_ts) / 86400
            if gap > 1.5:
                warns.append(f"{pair}: {int(gap)}-day gap before "
                             f"{r['datetime']}")
            if prev_close and prev_close > 0:
                move = abs(close / prev_close - 1)
                if move > 0.60:
                    warns.append(f"{pair}: {move:.0%} single-bar move "
                                 f"at {r['datetime']} (bad data?)")
        prev_ts, prev_close = ts, close
    return errs, warns


def lint(pairs):
    """Lint all pairs. Returns (all_errors, all_warnings)."""
    all_e, all_w = [], []
    for p in pairs:
        e, w = lint_pair(p)
        all_e += e; all_w += w
    return all_e, all_w


def main():
    pairs = sys.argv[1:] or EXAM_PAIRS
    errs, warns = lint(pairs)
    for w in warns:
        print(f"  WARN  {w}")
    for e in errs:
        print(f"  ERROR {e}")
    print(f"\n{len(pairs)} pairs: {len(errs)} errors, {len(warns)} warnings")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
