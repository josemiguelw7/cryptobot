"""
data/refresh_intraday.py - keep the intraday stores current, then gate.

WHY THIS EXISTS, AND WHY IT IS NOT OPTIONAL

Coinbase serves roughly 60 days of 5-minute granularity and nothing older.
fetch_candles.py merges rather than overwrites, so history accumulates
locally - but only for days on which this actually runs. A day missed is a
day of 5m data that can never be recovered from any source. As of
2026-08-01 the 5m store began 2026-06-03: exactly at the edge. There is no
slack in this window.

The hourly store has the same property with a longer fuse (~300 days).

ORDER OF OPERATIONS

Refresh first, audit second, and retry once before declaring failure. On
2026-08-01 a bare audit reported NOM-USD as 3.5h stale and returned exit 2;
a single refetch of that one pair produced the missing 02:00 bar and the
audit went clean. The bar existed upstream - the sliding-window refresh had
simply run before it was emitted. Auditing before refreshing, or auditing
without a retry, converts that ordinary race into a false execution_data
halt. The tolerance is not the problem and must not be widened: over the
trailing 180 days, at least one PIT universe pair is >3h stale in only 19
of 4318 hours (0.4%).

EXIT CODES
    0  stores current, audit clean of blocking findings
    1  refreshed with gaps, or audit warnings only (normal: the two
       permanent Coinbase holes are WARNING findings on nearly every pair,
       so 0 is unreachable for the hourly store)
    2  audit blocking after retry -> charter section 8 execution_data.
       Do not start a counted intraday cycle.

Note that 2 is a statement about the INTRADAY squad only. The daily league
trades a different store and is not gated by this script.

Usage:
    python data/refresh_intraday.py
    python data/refresh_intraday.py --skip-5m      # hourly + audit only
    python data/refresh_intraday.py --limit 3      # smoke test
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FETCH = os.path.join(HERE, "fetch_candles.py")
AUDIT = os.path.join(HERE, "audit.py")
CANDLES = os.path.join(HERE, "candles")

DAYS_5M = 60          # the whole window Coinbase will give at 300s
DAYS_1H = 365
STALE_1H = 3.0        # matches audit.py; see docstring before changing


def pairs_in_store(granularity):
    """Whatever the store already tracks at this granularity. Deliberately
    not a hardcoded list: when the 5m store is expanded from 25 pairs to the
    full PIT universe, this picks the new pairs up with no edit here."""
    pat = os.path.join(CANDLES, f"*_{granularity}s.csv")
    return sorted({os.path.basename(p).split("_")[0] for p in glob.glob(pat)})


def newest_bar_age_hours(pair, granularity):
    """Hours since the newest bar on disk, or None if unreadable."""
    import csv
    path = os.path.join(CANDLES, f"{pair}_{granularity}s.csv")
    try:
        ts = [int(r["timestamp"]) for r in csv.DictReader(open(path))]
    except Exception:
        return None
    if not ts:
        return None
    now = datetime.now(timezone.utc).timestamp()
    return (now - max(ts)) / 3600.0


def fetch(pair, granularity, days):
    """-> returncode. 0 complete, 1 gaps, 2 refused/failed."""
    r = subprocess.run(
        [sys.executable, FETCH, pair, str(granularity), str(days), "--quiet"],
        capture_output=True, text=True, cwd=ROOT)
    for line in (r.stdout or "").strip().splitlines()[-6:]:
        print("   " + line, flush=True)
    if r.returncode == 2:
        print(f"   FAILED rc=2: {(r.stderr or '').strip()[:200]}", flush=True)
    return r.returncode


def refresh(granularity, days, limit=None):
    todo = pairs_in_store(granularity)
    if limit:
        todo = todo[:limit]
    if not todo:
        print(f"no {granularity}s pairs in store; nothing to refresh")
        return [], []
    print(f"\n{'='*58}\nrefreshing {len(todo)} pairs @ {granularity}s "
          f"({days}d window, merge)\n{'='*58}", flush=True)
    gapped, failed = [], []
    t0 = time.time()
    for i, pair in enumerate(todo, 1):
        print(f"\n[{i}/{len(todo)}] {pair}", flush=True)
        rc = fetch(pair, granularity, days)
        if rc == 1:
            gapped.append(pair)
        elif rc != 0:
            failed.append(pair)
    print(f"\n{granularity}s done in {(time.time()-t0)/60:.1f} min · "
          f"clean {len(todo)-len(gapped)-len(failed)} · gaps {len(gapped)} · "
          f"failed {len(failed)}", flush=True)
    return gapped, failed


def run_audit():
    """-> (returncode, stdout). 2 == blocking == execution_data."""
    r = subprocess.run([sys.executable, AUDIT, "--intraday"],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def stale_now(granularity, tolerance):
    return [p for p in pairs_in_store(granularity)
            if (lambda a: a is not None and a > tolerance)(
                newest_bar_age_hours(p, granularity))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-5m", action="store_true")
    ap.add_argument("--skip-1h", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    print(f"intraday refresh · {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
          flush=True)

    gapped, failed = [], []
    if not a.skip_5m:
        g, f = refresh(300, DAYS_5M, a.limit)
        gapped += g
        failed += f
    if not a.skip_1h:
        # hourly only needs the pairs that actually drifted; refetching 65
        # pairs x 365 days daily is ~40 min of API calls for nothing.
        todo = stale_now(3600, STALE_1H)
        print(f"\n{'='*58}\nhourly: {len(todo)} pairs staler than {STALE_1H}h"
              f"\n{'='*58}", flush=True)
        for i, pair in enumerate(todo, 1):
            print(f"\n[{i}/{len(todo)}] {pair}", flush=True)
            rc = fetch(pair, 3600, DAYS_1H)
            if rc == 1:
                gapped.append(pair)
            elif rc != 0:
                failed.append(pair)

    print(f"\n{'='*58}\nAUDIT\n{'='*58}", flush=True)
    rc, out = run_audit()
    print(out.strip()[-2000:], flush=True)

    if rc == 2:
        # One retry, targeted. See the docstring: on 2026-08-01 this exact
        # path turned a false execution_data halt into a clean audit. If the
        # bar genuinely does not exist upstream the retry adds nothing and
        # the halt stands, which is the correct outcome.
        retry = sorted(set(stale_now(300, STALE_1H) + stale_now(3600, STALE_1H)))
        if retry:
            print(f"\nBLOCKING. Retrying {len(retry)} stale pair(s) once "
                  f"before declaring execution_data: {', '.join(retry)}",
                  flush=True)
            for pair in retry:
                print(f"\n  retry {pair}", flush=True)
                g = 300 if os.path.exists(
                    os.path.join(CANDLES, f"{pair}_300s.csv")) else 3600
                fetch(pair, g, DAYS_5M if g == 300 else DAYS_1H)
                if g == 300 and os.path.exists(
                        os.path.join(CANDLES, f"{pair}_3600s.csv")):
                    fetch(pair, 3600, DAYS_1H)
            print(f"\n{'='*58}\nAUDIT (after retry)\n{'='*58}", flush=True)
            rc, out = run_audit()
            print(out.strip()[-2000:], flush=True)

    # Persist the verdict. When the intraday seeds exist they must be able
    # to ask "was today a counted day?" without re-deriving it, and charter
    # 43 makes that answer load-bearing for the return series.
    try:
        import json
        marker = os.path.join(ROOT, "logs", "intraday_gate.json")
        prior = []
        if os.path.exists(marker):
            prior = json.load(open(marker)).get("history", [])[-364:]
        entry = {"utc": f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
                 "audit_exit": rc,
                 "execution_data": rc == 2,
                 "fetch_failures": failed,
                 "gapped": len(gapped)}
        json.dump({"latest": entry, "history": prior + [entry]},
                  open(marker, "w"), indent=2)
    except Exception as e:
        print(f"WARNING: could not write intraday_gate.json: {e}")

    print(f"\n{'='*58}")
    if failed:
        print(f"fetch failures: {', '.join(failed)}")
    if rc == 2:
        print("RESULT: execution_data condition stands after retry.")
        print("Charter section 8: do not start a counted intraday cycle.")
        print("This does NOT gate the daily league, which uses a different store.")
    elif rc == 1:
        print("RESULT: warnings only. Intraday stores are current and usable.")
        print("(exit 0 is unreachable while the two permanent Coinbase holes")
        print(" of 2025-10-25 and 2026-05-08 remain WARNING-level findings.)")
    else:
        print("RESULT: clean.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
