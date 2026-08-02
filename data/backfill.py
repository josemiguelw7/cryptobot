"""
data/backfill.py - fetch hourly candles for every pair in the point-in-time
universe that the intraday store is missing or holds too little of.

This is the script that closes the survivorship hole. Without it the intraday
exam runs on today's 25 winners; with it, on the 63 pairs a bot would actually
have been able to trade. Resumable: already-covered pairs are skipped, so an
interrupted run can simply be re-run.

Usage:
    python data/backfill.py                # fetch everything missing
    python data/backfill.py --dry-run
    python data/backfill.py --limit 5      # first N only, for a smoke test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FETCH = os.path.join(HERE, "fetch_candles.py")

sys.path.insert(0, HERE)
import pit_universe as pu


def stale_pairs(granularity, max_stale_hours):
    """Pairs whose newest bar is older than tolerance. Refreshing these is a
    separate job from backfilling missing pairs: the file exists and is
    correct as far as it goes, it just stopped being updated."""
    import csv as _csv
    import glob as _glob
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).timestamp()
    out = []
    for path in _glob.glob(os.path.join(HERE, "candles", f"*_{granularity}s.csv")):
        pair = os.path.basename(path).split("_")[0]
        try:
            ts = [int(r["timestamp"]) for r in _csv.DictReader(open(path))]
        except Exception:
            continue
        if ts and (now - max(ts)) / 3600 > max_stale_hours:
            out.append(pair)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--granularity", type=int, default=3600)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh-stale", type=float, default=None, metavar="HOURS",
                    help="refresh pairs staler than HOURS instead of backfilling")
    a = ap.parse_args()

    if a.refresh_stale is not None:
        todo = stale_pairs(a.granularity, a.refresh_stale)
        rep = {"ever": todo, "have_hourly": []}
        print(f"refresh mode @ {a.granularity}s: {len(todo)} pairs staler "
              f"than {a.refresh_stale}h")
    else:
        rep = pu.coverage_report(a.days)
        todo = sorted(rep["missing"])
        print(f"universe: {len(rep['ever'])} pairs · covered: "
              f"{len(rep['have_hourly'])} · to fetch: {len(todo)}")
    if a.limit:
        todo = todo[:a.limit]

    if a.dry_run or not todo:
        for p in todo:
            print(f"  would fetch {p}")
        return 0

    ok, gapped, failed = [], [], []
    t0 = time.time()
    for i, pair in enumerate(todo, 1):
        print(f"\n[{i}/{len(todo)}] {pair}", flush=True)
        r = subprocess.run(
            [sys.executable, FETCH, pair, str(a.granularity), str(a.days), "--quiet"],
            capture_output=True, text=True)
        tail = (r.stdout or "").strip().splitlines()
        for line in tail[-8:]:
            print("   " + line, flush=True)
        if r.returncode == 0:
            ok.append(pair)
        elif r.returncode == 1:
            gapped.append(pair)
        else:
            failed.append(pair)
            print(f"   FAILED rc={r.returncode}: {(r.stderr or '').strip()[:200]}",
                  flush=True)

    mins = (time.time() - t0) / 60
    print(f"\n{'='*58}")
    print(f"complete in {mins:.1f} min · clean {len(ok)} · with gaps "
          f"{len(gapped)} · failed {len(failed)}")
    if gapped:
        print(f"  gaps (expected for illiquid/new pairs): {', '.join(gapped)}")
    if failed:
        print(f"  FAILED, re-run to retry: {', '.join(failed)}")
    print("\nNow re-run:  python data/pit_universe.py  and  python data/audit.py --intraday")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
