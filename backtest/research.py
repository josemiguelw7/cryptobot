"""
RESEARCH SCREEN — broad, cheap, and NEVER ledger-recording.

The graded exam uses the 8 pre-committed pairs in entrance_exam.md and
burns a candidate name permanently. Research has no such constraints:
screen anything against anything, as often as you like, because nothing
here can admit a strategy to the league.

The firewall matters. Screening 40 strategies x 30 pairs and then
examining only the winner is p-hacking with extra steps. So this tool
prints a multiple-testing warning proportional to how much you searched.

    python backtest/research.py --min-history 900
    python backtest/research.py --strategies trend_200,rsi_14 --top 15
"""
import argparse, csv, glob, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam, strategies as S

DAILY = os.path.join(ROOT, "data", "candles_daily")


def available_pairs(min_history):
    out = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*_86400s.csv"))):
        pair = os.path.basename(path).replace("_86400s.csv", "")
        try:
            with open(path) as f:
                n = sum(1 for _ in f) - 1
        except Exception:
            continue
        if n >= min_history:
            out.append((pair, n))
    return out


def screen(strat_names, pairs):
    results = {}
    for nm in strat_names:
        try:
            strat = S.get(nm)
        except KeyError:
            print(f"  skip unknown strategy {nm}"); continue
        rows = []
        for p in pairs:
            try:
                rows += exam.exam_pair(p, strat, exam.FEE, exam.SLIP)
            except Exception:
                continue
        if not rows:
            continue
        edges = np.array([r["ret"] - r["bh"] for r in rows])
        results[nm] = {
            "windows": len(rows),
            "pairs": len({r["pair"] for r in rows}),
            "mean_edge": float(edges.mean()),
            "pct_positive": float((edges > 0).mean()),
            "trades": sum(r["trades"] for r in rows),
            "worst_dd": min(r["dd"] for r in rows),
        }
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-history", type=int, default=900)
    ap.add_argument("--strategies", default="")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()

    pool = available_pairs(a.min_history)[:a.top]
    pairs = [p for p, _n in pool]
    names = ([s.strip() for s in a.strategies.split(",") if s.strip()]
             or sorted(S.REGISTRY))

    print(f"RESEARCH SCREEN  (nothing here is recorded or admissible)")
    print(f"  {len(pairs)} pairs with >= {a.min_history} daily bars")
    print(f"  {len(names)} strategies\n")

    res = screen(names, pairs)
    print(f"{'strategy':>14} {'edge/win':>10} {'win%':>7} "
          f"{'windows':>8} {'trades':>8} {'worstDD':>9}")
    for nm, r in sorted(res.items(), key=lambda kv: -kv[1]["mean_edge"]):
        print(f"{nm:>14} {r['mean_edge']:>9.2%} {r['pct_positive']:>6.0%} "
              f"{r['windows']:>8} {r['trades']:>8} {r['worst_dd']:>8.0%}")

    trials = len(names) * len(pairs)
    print(f"\n  MULTIPLE-TESTING WARNING")
    print(f"  This screen ran ~{trials} strategy-pair trials.")
    print(f"  Picking the best of {len(names)} and then examining it is")
    print(f"  selection bias. If you examine a winner from this screen,")
    print(f"  record the screen size in the research journal, and treat")
    print(f"  the exam as testing a HYPOTHESIS FORMED HERE, not a fresh")
    print(f"  idea. See backtest/validation.py deflated_check().")
    print(f"  Edge is measured vs buy-and-hold, net of {exam.FEE:.2%} fees.")


if __name__ == "__main__":
    main()
