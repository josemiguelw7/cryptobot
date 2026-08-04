"""
DIVERSITY GAUGE (E2.6) — how much are we paying twice for one opinion?

Reads a squad state file and reports how similar the bots' books are.
Pure observation: it computes no returns, changes no state, and gates
nothing. Safe to run inside a live epoch because it cannot influence a
decision -- it only makes an existing property visible.

Metrics, per squad:
  overlap      mean pairwise Jaccard over held symbols (1.00 = clones)
  distinct     number of distinct books (a book = the held symbol set)
  effective    distinct books as a share of non-cash bots
  clusters     the actual groups, so a clone set is named not implied

Motivation: on 2026-08-04, 8 of 10 stock bots held identical books and
nothing in the system said so out loud.

Run: .venv/bin/python bot/diversity.py [--log]
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SQUADS = [("crypto", os.path.join(HERE, "squad_state.json")),
          ("stocks", os.path.join(HERE, "squad_stocks_state.json"))]
OUT = os.path.join(ROOT, "logs", "diversity.csv")


def jaccard(a, b):
    if not a and not b:
        return 1.0
    u = len(a | b)
    return len(a & b) / u if u else 1.0


def analyse(path):
    try:
        st = json.load(open(path))
    except Exception:
        return None
    books = {n: frozenset(b.get("units", {}))
             for n, b in st.get("bots", {}).items()}
    if not books:
        return None
    names = sorted(books)
    invested = [n for n in names if books[n]]
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    ov = ([jaccard(books[a], books[b]) for a, b in pairs] or [0.0])
    inv_pairs = [(a, b) for i, a in enumerate(invested)
                 for b in invested[i + 1:]]
    inv_ov = ([jaccard(books[a], books[b]) for a, b in inv_pairs] or [0.0])

    clusters = {}
    for n in invested:
        clusters.setdefault(books[n], []).append(n)
    distinct = len(clusters)
    return {
        "bots": len(names),
        "invested": len(invested),
        "overlap_all": sum(ov) / len(ov),
        "overlap_invested": sum(inv_ov) / len(inv_ov),
        "distinct": distinct,
        "effective": distinct / len(invested) if invested else 0.0,
        "clusters": sorted(clusters.items(), key=lambda kv: -len(kv[1])),
    }


def main(log=False):
    now = datetime.now(timezone.utc)
    rows = []
    for label, path in SQUADS:
        r = analyse(path)
        if not r:
            print(f"{label:7s} no state")
            continue
        print(f"{label} · {r['invested']}/{r['bots']} bots invested")
        print(f"  mean pairwise overlap (invested only): "
              f"{r['overlap_invested']:.2f}   "
              f"distinct books: {r['distinct']}   "
              f"effective diversity: {r['effective']:.0%}")
        for book, members in r["clusters"]:
            flag = "  <-- CLONE SET" if len(members) > 1 else ""
            print(f"    [{len(members)}] {' '.join(sorted(book)) or 'cash'}"
                  f"  :: {', '.join(members)}{flag}")
        worst = r["clusters"][0] if r["clusters"] else None
        if worst and len(worst[1]) > 1:
            print(f"  WARNING: {len(worst[1])} bots hold an identical book. "
                  f"That is {len(worst[1])-1} slice(s) of capital buying "
                  f"an opinion already owned.")
        rows.append([now.isoformat(), label, r["bots"], r["invested"],
                     f"{r['overlap_invested']:.4f}", r["distinct"],
                     f"{r['effective']:.4f}"])
        print()
    if log and rows:
        new = not os.path.exists(OUT)
        with open(OUT, "a") as f:
            if new:
                f.write("time,squad,bots,invested,overlap,distinct,"
                        "effective\n")
            for r in rows:
                f.write(",".join(str(x) for x in r) + "\n")
        print(f"logged -> {OUT}")


if __name__ == "__main__":
    main("--log" in sys.argv)
