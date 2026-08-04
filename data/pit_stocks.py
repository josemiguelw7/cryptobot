"""
POINT-IN-TIME STOCK UNIVERSE (docs/seed_proposals_v2.md s5).

The crypto side already refuses to let a backtest know which coins
survived (data/pit_universe.py). The stock side currently does not: the
10-name menu is 3 ETFs plus 7 megacaps chosen in 2026, which is exactly
the shape of mistake that turned a +354% crypto backtest into -90% when
it was rebuilt honestly.

This module builds membership the same way as crypto: a name is in the
universe on date D if its trailing dollar volume as of D put it in the
top K. No future knowledge.

READ THIS BEFORE TRUSTING IT
---------------------------
Point-in-time RANKING does not repair a survivorship-contaminated
CANDIDATE LIST. If the candidate list is "the S&P 500 as it stands
today", every name in it survived to today, and ranking them by
historical volume launders the bias instead of removing it. The
candidate list must come from HISTORICAL INDEX MEMBERSHIP -- including
the names that were delisted, acquired, or went to zero.

So this module refuses to run on a hand-typed list of today's winners.
Supply `--candidates FILE` where FILE is a CSV of
    ticker,first_date,last_date
drawn from a historical membership source. A name with a last_date is a
name that LEFT -- those are the rows that make the exercise honest, and
a file containing none is almost certainly today's list in disguise.

Usage:
    python data/pit_stocks.py --candidates data/sp_membership.csv
    python data/pit_stocks.py --candidates FILE --fetch   (download bars)
"""
from __future__ import annotations
import argparse, csv, json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STOCKS = os.path.join(HERE, "stocks")
OUT = os.path.join(HERE, "stock_universe_pit.json")

LOOKBACK_DAYS = 30        # trailing window for the volume rank
TOP_K = 50                # universe width
MIN_DEAD = 0.05           # >=5% of rows must be names that LEFT


def load_candidates(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({"ticker": r["ticker"].strip().upper(),
                         "first": (r.get("first_date") or "").strip(),
                         "last": (r.get("last_date") or "").strip()})
    if not rows:
        raise SystemExit(f"{path}: empty candidate list")
    dead = [r for r in rows if r["last"]]
    frac = len(dead) / len(rows)
    print(f"candidates: {len(rows)} names, {len(dead)} with an exit date "
          f"({frac:.1%})")
    if frac < MIN_DEAD:
        raise SystemExit(
            f"REFUSING: only {frac:.1%} of candidates ever left the index.\n"
            f"A real membership history over years carries delistings,\n"
            f"acquisitions and failures. A list without them is today's\n"
            f"survivors wearing a timestamp. Fix the source, not this\n"
            f"threshold. (docs/seed_proposals_v2.md s5)")
    return rows


def daily_panel(tickers):
    """{ticker: {date: dollar_volume}} from data/stocks/*_1d.csv."""
    panel = {}
    for tk in tickers:
        p = os.path.join(STOCKS, f"{tk}_1d.csv")
        if not os.path.exists(p):
            continue
        d = {}
        with open(p) as f:
            for r in csv.DictReader(f):
                try:
                    d[r["datetime"][:10]] = (float(r["close"]) *
                                             float(r["volume"]))
                except (KeyError, ValueError):
                    continue
        if d:
            panel[tk] = d
    return panel


def membership(cands, top_k=TOP_K, lookback=LOOKBACK_DAYS):
    panel = daily_panel([c["ticker"] for c in cands])
    window = {c["ticker"]: (c["first"], c["last"]) for c in cands}
    dates = sorted({d for v in panel.values() for d in v})
    out = {}
    for i, day in enumerate(dates):
        if i < lookback:
            continue
        back = dates[i - lookback:i]          # STRICTLY before `day`
        scores = {}
        for tk, series in panel.items():
            first, last = window[tk]
            if first and day < first:
                continue                       # not listed yet
            if last and day > last:
                continue                       # already gone
            vals = [series[d] for d in back if d in series]
            if len(vals) >= lookback // 2:
                scores[tk] = sum(vals) / len(vals)
        out[day] = sorted(scores, key=lambda t: -scores[t])[:top_k]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--top", type=int, default=TOP_K)
    ap.add_argument("--fetch", action="store_true",
                    help="download daily bars for every candidate first")
    a = ap.parse_args()

    cands = load_candidates(a.candidates)
    if a.fetch:
        sys.path.insert(0, HERE)
        import fetch_stocks
        for c in cands:
            try:
                fetch_stocks.save(c["ticker"], "1d", "max", "1d")
            except Exception as e:
                print(f"  {c['ticker']}: {e}")

    m = membership(cands, a.top)
    if not m:
        raise SystemExit("no daily bars found; run with --fetch first")
    days = sorted(m)
    json.dump({"built": datetime.now(timezone.utc).isoformat(),
               "top_k": a.top, "lookback_days": LOOKBACK_DAYS,
               "membership": m}, open(OUT, "w"))
    latest = m[days[-1]]
    churn = len(set(m[days[0]]) ^ set(latest))
    print(f"membership built: {len(days)} dates, {days[0]} -> {days[-1]}")
    print(f"  today's top {a.top}: {' '.join(latest[:12])} ...")
    print(f"  names differing between first and last date: {churn}")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
