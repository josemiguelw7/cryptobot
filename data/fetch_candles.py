"""
Download historical OHLCV candles from Coinbase's public market-data API.
No API keys required - this endpoint is public, read-only.

HARDENED 2026-08-01. The previous version had four failure modes, all of
which had already fired silently on the live store:

  1. `if not chunk: break` - one empty response ended the whole backfill and
     whatever had been collected was saved as if complete. Truncation with
     no error, no exit code, no log line.
  2. No continuity check. Missing bars inside the fetched range were written
     without comment; the store carried two 6h holes for months unnoticed.
  3. Unclosed bars were written. Coinbase returns the in-progress bar, so
     every fetch put a partial, still-moving bar on disk. Charter section
     4.5(b) forbids strategy code from seeing those - 8 daily files were
     found holding bars dated in the future.
  4. Wholesale overwrite. A partial fetch replaced good history with less.

Not every gap is a bug: the two 6h holes above were verified on 2026-08-01
to be permanent upstream gaps - Coinbase still returns nothing for those
windows. This script reports gaps; it does not interpolate them, ever.

Exit code 0 = complete, 1 = fetched with gaps, 2 = refused to write.

Usage:
    python data/fetch_candles.py BTC-USD 3600 365
    python data/fetch_candles.py BTC-USD 3600 365 --force   # allow shrink
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.exchange.coinbase.com"
MAX_CANDLES = 300
OUT_DIR = os.path.join(os.path.dirname(__file__), "candles")
GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}

RETRIES = 4
BACKOFF = 1.8
PACE = 0.35


def fetch_chunk(product, granularity, start, end):
    """One request, with retries. Raises if every attempt fails."""
    url = f"{BASE}/products/{product}/candles"
    params = {"granularity": granularity,
              "start": start.isoformat(), "end": end.isoformat()}
    last_err = None
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(BACKOFF ** (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(BACKOFF ** attempt)
    raise RuntimeError(f"{product} {start:%Y-%m-%d %H:%M} failed after "
                       f"{RETRIES} attempts: {last_err}")


def fetch_history(product, granularity, days_back, verbose=True):
    """Returns (rows, report). Never truncates silently: an empty chunk is
    recorded and the walk continues, because an empty window may be a real
    upstream gap rather than a failure, and only continuing reveals which."""
    if granularity not in GRANULARITIES:
        raise ValueError(f"granularity must be one of {sorted(GRANULARITIES)}")

    now = datetime.now(timezone.utc)
    start_limit = now - timedelta(days=days_back)
    span = timedelta(seconds=granularity * MAX_CANDLES)

    rows, empty_windows, failed_windows = [], [], []
    cursor_end = now
    while cursor_end > start_limit:
        cursor_start = max(cursor_end - span, start_limit)
        try:
            chunk = fetch_chunk(product, granularity, cursor_start, cursor_end)
        except RuntimeError as e:
            failed_windows.append((cursor_start, cursor_end, str(e)))
            chunk = []
        if not chunk:
            empty_windows.append((cursor_start, cursor_end))
        rows.extend(chunk)
        cursor_end = cursor_start
        time.sleep(PACE)
        if verbose:
            print(f"  ...{len(rows)} candles (back to {cursor_start:%Y-%m-%d})")

    seen = {row[0]: row for row in rows}

    # --- drop unclosed bars. Charter 4.5(b): a bar that has not closed must
    # never reach strategy code. Coinbase returns the in-progress bar, so this
    # is not hypothetical - it is every single fetch.
    now_ts = now.timestamp()
    unclosed = [t for t in seen if t + granularity > now_ts]
    for t in unclosed:
        del seen[t]

    ordered = [seen[k] for k in sorted(seen)]

    # --- continuity check over what remains
    ts = sorted(seen)
    gaps = [(a, b - a) for a, b in zip(ts, ts[1:]) if b - a > granularity]
    expected = int((ts[-1] - ts[0]) / granularity) + 1 if len(ts) > 1 else len(ts)

    report = {
        "product": product, "granularity": granularity,
        "bars": len(ordered), "expected": expected,
        "missing": max(0, expected - len(ordered)),
        "unclosed_dropped": len(unclosed),
        "gaps": gaps, "empty_windows": empty_windows,
        "failed_windows": failed_windows,
        "first": ts[0] if ts else None, "last": ts[-1] if ts else None,
    }
    return ordered, report


def read_existing(path):
    """-> {timestamp: row} of what is already on disk."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                t = int(r["timestamp"])
            except (KeyError, TypeError, ValueError):
                continue
            out[t] = [t, r["low"], r["high"], r["open"], r["close"], r["volume"]]
    return out


def save_csv(product, granularity, rows, force=False, replace=False):
    """MERGES with whatever is on disk. Atomic write.

    Merge, not overwrite, because a rolling fetch window slides at both ends:
    refetching 365 days a week later adds 7 days at the tail and drops 7 at
    the head. Overwriting would quietly discard the oldest week every single
    refresh, and the charter's 180-day Path B window needs history to
    accumulate, not tread water. Fetched bars win on any timestamp collision -
    the exchange may revise a bar, and the newer read is the better one.

    --replace restores overwrite semantics; --force allows the result to be
    smaller than what it replaces. Both are deliberately awkward to reach."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{product}_{granularity}s.csv")

    prior = read_existing(path)
    if replace:
        merged = {r[0]: r for r in rows}
    else:
        merged = dict(prior)
        merged.update({r[0]: r for r in rows})

    if prior and len(merged) < len(prior) and not force:
        print(
            f"REFUSING TO WRITE: {path} holds {len(prior)} bars, the result "
            f"would hold {len(merged)}. That would destroy "
            f"{len(prior) - len(merged)} bars of history.\n"
            f"If the shrink is intended, re-run with --force.", file=sys.stderr)
        raise SystemExit(2)

    ordered = [merged[k] for k in sorted(merged)]
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "datetime", "low", "high", "open", "close", "volume"])
        for t, low, high, op, close, vol in ordered:
            dt = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([t, dt, low, high, op, close, vol])
    os.replace(tmp, path)
    return path, len(prior), len(ordered)


def print_report(rep):
    g = rep["granularity"]
    print(f"\n  bars written .......... {rep['bars']}")
    print(f"  expected in range ..... {rep['expected']}")
    print(f"  missing ............... {rep['missing']}")
    print(f"  unclosed bars dropped . {rep['unclosed_dropped']}")
    if rep["failed_windows"]:
        print(f"  REQUEST FAILURES ...... {len(rep['failed_windows'])}")
        for s, e, msg in rep["failed_windows"][:3]:
            print(f"      {s:%Y-%m-%d %H:%M} -> {e:%Y-%m-%d %H:%M}")
    if rep["empty_windows"]:
        print(f"  empty windows ......... {len(rep['empty_windows'])}")
    if rep["gaps"]:
        worst_at, worst = max(rep["gaps"], key=lambda x: x[1])
        when = datetime.fromtimestamp(worst_at, timezone.utc)
        print(f"  gaps .................. {len(rep['gaps'])}, worst "
              f"{worst/3600:.1f}h at {when:%Y-%m-%d %H:%M} UTC")
        print(f"      Gaps are reported, never filled. Re-request the window "
              f"to tell an upstream hole from a fetch failure.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product", nargs="?", default="BTC-USD")
    ap.add_argument("granularity", nargs="?", type=int, default=3600)
    ap.add_argument("days", nargs="?", type=int, default=365)
    ap.add_argument("--force", action="store_true",
                    help="allow the merged result to be smaller than what exists")
    ap.add_argument("--replace", action="store_true",
                    help="overwrite instead of merging with existing history")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    print(f"Fetching {a.product} @ {a.granularity}s for the last {a.days} days...")
    rows, rep = fetch_history(a.product, a.granularity, a.days, verbose=not a.quiet)
    if not rows:
        print("No candles returned. Nothing written.")
        return 2

    path, prior, total = save_csv(a.product, a.granularity, rows,
                                  force=a.force, replace=a.replace)
    print_report(rep)
    first = datetime.fromtimestamp(rep["first"], timezone.utc)
    last = datetime.fromtimestamp(rep["last"], timezone.utc)
    print(f"  merged into store ..... {prior} -> {total} bars (+{total - prior})")
    print(f"\nSaved -> {path}")
    print(f"Fetched range: {first:%Y-%m-%d %H:%M} to {last:%Y-%m-%d %H:%M} UTC")

    if rep["failed_windows"]:
        return 2
    return 1 if rep["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
