"""
data/audit.py - standing data-integrity gate for the candle store.

Charter section 4.5 forbids strategy code from seeing unclosed bars, and
section 8 halts a bot after 3 execution_data events in one day. Neither is
enforceable without a detector, so this is it. Run before any exam, any
squad cycle, and from bot/daily.py.

The failures this catches were all found live in the store on 2026-08-01:
  - every intraday file 198h stale, silently
  - two 6h windows absent across ~95% of pairs (2025-10-25 15:00 and
    2026-05-08 01:00 UTC). Re-requesting them from Coinbase returns nothing
    even now, and the bar before each shows collapsed volume: these are
    permanent upstream gaps, not fetch failures. They cannot be repaired and
    must never be interpolated.
  - 8 daily files carrying bars dated in the FUTURE - unclosed bars sitting
    on disk waiting to be read as if settled
  - hourly coverage for 25 pairs when the point-in-time universe over the
    same year contained 63

Exit code 0 = clean, 1 = warnings, 2 = blocking failures.

Usage:
    python data/audit.py                 # full audit
    python data/audit.py --intraday      # 300s/3600s store only
    python data/audit.py --max-stale 26  # override staleness tolerance (hours)
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INTRADAY_DIR = os.path.join(HERE, "candles")
DAILY_DIR = os.path.join(HERE, "candles_daily")

# A bar may legitimately be up to one full period old plus a fetch delay.
# Anything beyond this means the fetcher stopped and nobody noticed.
STALE_TOLERANCE_PERIODS = 3.0
STALE_FLOOR_HOURS = 2.0

# A gap this size in a liquid pair is a plumbing failure, not a quiet market.
SYSTEMATIC_GAP_PERIODS = 3

BLOCKING = "FAIL"
WARNING = "WARN"


class Finding:
    def __init__(self, level, code, subject, detail):
        self.level, self.code, self.subject, self.detail = level, code, subject, detail

    def __str__(self):
        return f"  [{self.level}] {self.code:<16} {self.subject:<22} {self.detail}"


def read_timestamps(path):
    ts = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                ts.append(int(row["timestamp"]))
            except (KeyError, TypeError, ValueError):
                continue
    return sorted(set(ts))


def audit_file(path, now_ts, max_stale_hours=None):
    """Returns (findings, stats) for one candle file."""
    name = os.path.basename(path).replace(".csv", "")
    pair, gran = name.rsplit("_", 1)
    step = int(gran.rstrip("s"))
    findings = []

    ts = read_timestamps(path)
    if len(ts) < 2:
        findings.append(Finding(BLOCKING, "empty", name, f"{len(ts)} usable bars"))
        return findings, None

    first, last = ts[0], ts[-1]

    # --- 1. FUTURE BARS. Charter 4.5(b): unclosed bars must be invisible.
    # A bar timestamped at or after now has not closed yet. If it is on disk,
    # some loader will eventually read it as settled, and that is lookahead.
    future = [t for t in ts if t + step > now_ts]
    if future:
        ahead_h = (max(future) + step - now_ts) / 3600
        findings.append(Finding(
            BLOCKING, "future_bar", name,
            f"{len(future)} unclosed bar(s); latest closes {ahead_h:.1f}h from now"))

    # --- 2. STALENESS. Silent fetcher death is the failure mode here.
    tol_h = max_stale_hours if max_stale_hours is not None else max(
        STALE_FLOOR_HOURS, (step * STALE_TOLERANCE_PERIODS) / 3600)
    stale_h = (now_ts - last) / 3600
    if stale_h > tol_h:
        findings.append(Finding(
            BLOCKING, "stale", name, f"{stale_h:.1f}h old (tolerance {tol_h:.1f}h)"))

    # --- 3. GAPS. Distinguish plumbing failure from an illiquid market.
    gaps = [(a, b - a) for a, b in zip(ts, ts[1:]) if b - a > step]
    big = [(a, g) for a, g in gaps if g >= step * SYSTEMATIC_GAP_PERIODS]
    if big:
        worst_at, worst = max(big, key=lambda x: x[1])
        when = datetime.fromtimestamp(worst_at, timezone.utc)
        findings.append(Finding(
            WARNING, "gap", name,
            f"{len(big)} gap(s) >= {SYSTEMATIC_GAP_PERIODS} bars; worst "
            f"{worst/3600:.1f}h at {when:%Y-%m-%d %H:%M} UTC"))

    expected = int((last - first) / step) + 1
    missing_pct = (expected - len(ts)) / expected * 100 if expected else 0.0
    return findings, {
        "pair": pair, "step": step, "bars": len(ts), "first": first, "last": last,
        "span_days": (last - first) / 86400, "missing_pct": missing_pct,
        "gap_starts": {a for a, _ in big},
    }


def detect_systematic_gaps(all_stats, min_fraction=0.25, floor=3):
    """A gap at the identical timestamp across many unrelated pairs is not a
    market being quiet - it is an upstream event: an exchange incident, or a
    fetch that failed and was written as if it succeeded.

    THIS DETECTOR DOES NOT DISTINGUISH THE TWO. It flags the pattern; a human
    resolves the cause by re-requesting that window from the API. Verified
    2026-08-01 for the two 6h gaps in this store (2025-10-25 15:00 and
    2026-05-08 01:00 UTC): Coinbase still returns nothing for those windows,
    and the bar immediately preceding each shows collapsed volume. They are
    permanent upstream gaps. Refetching will not repair them, and the bars
    must never be interpolated - a strategy is blind and flat across them.
    An earlier version of this docstring asserted "fetcher failure, not
    market" before that check was run. It was wrong. Do not assert a cause
    this detector cannot see.

    The threshold scales with universe size: a gap shared by 3 of 25 pairs is
    suspicious, the same 3 out of 423 is coincidence. A flat floor of 3
    produced 2,339 false positives on the daily store - a detector that cries
    wolf gets muted, and a muted detector is worse than none."""
    per_step = defaultdict(set)
    for s in all_stats:
        per_step[s["step"]].add(s["pair"])

    by_ts = defaultdict(list)
    for s in all_stats:
        for g in s["gap_starts"]:
            by_ts[(s["step"], g)].append(s["pair"])

    out = []
    for (step, g), pairs in sorted(by_ts.items(), key=lambda x: -len(x[1])):
        universe = len(per_step[step]) or 1
        threshold = max(floor, int(min_fraction * universe))
        if len(pairs) >= threshold:
            when = datetime.fromtimestamp(g, timezone.utc)
            out.append(Finding(
                WARNING, "correlated_gap", f"{step}s @ {when:%Y-%m-%d %H:%M}",
                f"absent in {len(pairs)}/{universe} pairs (threshold {threshold})"
                f" -> upstream event; re-request the window to classify"))
    return out


def audit_coverage(intraday_stats):
    """Charter 4.5: an exam can only be as honest as its universe. If the
    hourly store holds only today's winners, no backtest can undo that.

    Compares against the POINT-IN-TIME universe, not the raw daily file count.
    An earlier version compared 65 hourly pairs to 423 daily files and warned
    forever - but most of those 423 were never liquid enough to trade. The
    right denominator is what a bot could actually have picked from."""
    findings = []
    have = {s["pair"] for s in intraday_stats if s["step"] == 3600}
    if not have:
        return findings
    try:
        sys.path.insert(0, HERE)
        import pit_universe as pu
        _, ever = pu.membership()
    except Exception as e:
        findings.append(Finding(WARNING, "coverage_unknown", "hourly store",
                                f"could not compute PIT universe: {e}"))
        return findings

    missing = ever - have
    if missing:
        findings.append(Finding(
            BLOCKING, "universe_gap", "hourly store",
            f"{len(missing)}/{len(ever)} point-in-time universe pairs have no "
            f"hourly data: {', '.join(sorted(missing)[:8])}"
            f"{' ...' if len(missing) > 8 else ''}"))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intraday", action="store_true")
    ap.add_argument("--daily", action="store_true")
    ap.add_argument("--max-stale", type=float, default=None,
                    help="staleness tolerance in hours")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    dirs = []
    if args.intraday or not args.daily:
        dirs.append(INTRADAY_DIR)
    if args.daily or not args.intraday:
        dirs.append(DAILY_DIR)

    now_ts = datetime.now(timezone.utc).timestamp()
    findings, stats = [], []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.csv"))):
            f, s = audit_file(path, now_ts, args.max_stale)
            findings.extend(f)
            if s:
                stats.append(s)

    findings.extend(detect_systematic_gaps(stats))
    findings.extend(audit_coverage(stats))

    blocking = [f for f in findings if f.level == BLOCKING]
    warnings = [f for f in findings if f.level == WARNING]

    print(f"\nDATA AUDIT  {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    print(f"{len(stats)} files checked across {len(dirs)} store(s)\n")

    by_code = defaultdict(list)
    for f in findings:
        by_code[f.code].append(f)
    for code in sorted(by_code, key=lambda c: -len(by_code[c])):
        group = by_code[code]
        print(f"{code} ({len(group)}):")
        show = group if (len(group) <= 6 or not args.quiet and code
                         in ("systematic_gap", "universe_narrow")) else group[:6]
        for f in show:
            print(f)
        if len(show) < len(group):
            print(f"       ... and {len(group)-len(show)} more")
        print()

    print(f"RESULT: {len(blocking)} blocking, {len(warnings)} warnings")
    if blocking:
        print("Blocking failures present. Per charter section 8 this is an "
              "execution_data condition: do not start a counted cycle.")
    return 2 if blocking else (1 if warnings else 0)


if __name__ == "__main__":
    sys.exit(main())
