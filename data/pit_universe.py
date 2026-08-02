"""
data/pit_universe.py - point-in-time universe membership.

The bias this exists to kill, restated because it already cost this project
once: data/build_universe.py ranks TODAY's Coinbase pairs by TODAY's volume.
Any pair that was liquid last year and has since died is absent. A backtest
over that universe is a backtest over winners. On the daily league the same
mistake turned an honest -90% into a fictional +354%.

This module answers a different question: which pairs would a bot have been
ABLE to trade on each date, using only information available then. Membership
is trailing-30-day median dollar volume as of that date, from the daily
panel, which is far broader (423 pairs) than the intraday store.

Residual bias, disclosed rather than hidden: pairs fully delisted from
Coinbase cannot be fetched at all, so they are invisible here too. This
narrows the bias; it does not eliminate it. Any writeup says so.

Usage:
    python data/pit_universe.py                 # summary
    python data/pit_universe.py --fetch-list    # pairs needing hourly data
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DAILY_DIR = os.path.join(HERE, "candles_daily")
INTRADAY_DIR = os.path.join(HERE, "candles")

LOOKBACK_DAYS = 30
TOP_K = 25


def dollar_volume_panel():
    cols = {}
    for path in sorted(glob.glob(os.path.join(DAILY_DIR, "*_86400s.csv"))):
        pair = os.path.basename(path).replace("_86400s.csv", "")
        try:
            df = pd.read_csv(path, usecols=["datetime", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            s = df.set_index("datetime").resample("1D").last()
            cols[pair] = s["close"] * s["volume"]
        except Exception:
            continue
    return pd.DataFrame(cols).sort_index()


def membership(window_days=365, lookback=LOOKBACK_DAYS, top_k=TOP_K):
    """-> (per_date {date: set(pairs)}, ever set). Uses only trailing data."""
    V = dollar_volume_panel()
    med = V.rolling(lookback, min_periods=lookback).median().tail(window_days)
    per_date, ever = {}, set()
    for d, row in med.iterrows():
        r = row.dropna()
        if r.empty:
            continue
        top = set(r.nlargest(top_k).index)
        per_date[d] = top
        ever |= top
    return per_date, ever


def have_hourly(window_days=365, tolerance_days=10):
    """Pairs whose hourly data reaches as far back as the pair itself does.

    Two symmetric mistakes to avoid, both made and caught on 2026-08-01:

      - Presence is not coverage. A 7-day file for a pair needing a year
        satisfies a naive existence check, then silently shortens whatever
        window the exam runs over. (Found via a PEPE-USD test fetch: 167 bars
        counted as covered against an 8,750-bar need.)
      - Youth is not absence. A flat 300-day minimum flagged TON, HYPE, MON
        and five others as missing when their hourly data was complete - they
        simply had not existed for 300 days. Refetching would change nothing.

    So the target is not a fixed length: it is the pair's own start, taken
    from the daily panel, floored at the window. Returns (covered, young)
    where `young` are complete but shorter than the window - usable, but an
    exam must know it is not comparing equal histories."""
    daily_start = {}
    for path in glob.glob(os.path.join(DAILY_DIR, "*_86400s.csv")):
        pair = os.path.basename(path).replace("_86400s.csv", "")
        try:
            ts = pd.read_csv(path, usecols=["timestamp"])["timestamp"]
            if len(ts):
                daily_start[pair] = ts.min()
        except Exception:
            continue

    now = pd.Timestamp.now("UTC").timestamp()
    window_start = now - window_days * 86400
    tol = tolerance_days * 86400

    covered, young = set(), set()
    for path in glob.glob(os.path.join(INTRADAY_DIR, "*_3600s.csv")):
        pair = os.path.basename(path).split("_")[0]
        try:
            ts = pd.read_csv(path, usecols=["timestamp"])["timestamp"]
            if len(ts) < 2:
                continue
            first = ts.min()
        except Exception:
            continue
        target = max(window_start, daily_start.get(pair, window_start))
        if first <= target + tol:
            covered.add(pair)
            if first > window_start + tol:
                young.add(pair)
    return covered, young


def coverage_report(window_days=365):
    per_date, ever = membership(window_days)
    have, young = have_hourly(window_days)
    today_universe = set()
    up = os.path.join(HERE, "universe.json")
    if os.path.exists(up):
        today_universe = set(json.load(open(up)))
    return {
        "dates": len(per_date),
        "ever": ever,
        "have_hourly": have,
        "young": young & ever,
        "today_universe": today_universe,
        "missing": ever - have,
        "dropped_out": ever - today_universe,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=365)
    ap.add_argument("--fetch-list", action="store_true",
                    help="print only the pairs needing hourly data, one per line")
    a = ap.parse_args()

    rep = coverage_report(a.window)
    if a.fetch_list:
        for p in sorted(rep["missing"]):
            print(p)
        return 0

    ever, have = rep["ever"], rep["have_hourly"]
    print(f"\nPOINT-IN-TIME UNIVERSE  (trailing {LOOKBACK_DAYS}d median $vol, "
          f"top {TOP_K}, {a.window}d window)")
    print(f"  rebalance dates evaluated ...... {rep['dates']}")
    print(f"  pairs EVER in the universe ..... {len(ever)}")
    print(f"  pairs in today's universe.json . {len(rep['today_universe'])}")
    print(f"  pairs with hourly data ......... {len(have)}")
    print()
    missing = sorted(rep["missing"])
    print(f"  IN UNIVERSE, NO HOURLY DATA .... {len(missing)}")
    if missing:
        pct = len(missing) / len(ever) * 100
        print(f"  -> {pct:.0f}% of the real universe is absent from the "
              f"intraday store.")
        for i in range(0, len(missing), 6):
            print("       " + ", ".join(missing[i:i+6]))
    print()
    young = sorted(rep["young"])
    if young:
        print(f"  COMPLETE BUT YOUNGER THAN THE WINDOW: {len(young)}")
        print(f"  Fully fetched - these pairs simply did not exist for the whole")
        print(f"  window. Usable, but an exam must not treat their shorter")
        print(f"  history as equivalent, and must not read their absence early")
        print(f"  in the window as a signal.")
        for i in range(0, len(young), 6):
            print("       " + ", ".join(young[i:i+6]))
        print()
    dropped = sorted(rep["dropped_out"])
    print(f"  WERE in the universe, not in today's top-{TOP_K}: {len(dropped)}")
    print(f"  These are precisely the pairs whose absence creates survivorship")
    print(f"  bias. An exam that cannot see them is an exam on winners.")
    print()
    if missing:
        print("  Next: data/backfill.py  (fetches the missing pairs)")
        return 1
    print("  Intraday store covers the point-in-time universe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
