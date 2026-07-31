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


def screen(strat_names, pairs, fee=None, slip=None, max_bars=None):
    fee = exam.FEE if fee is None else fee
    slip = exam.SLIP if slip is None else slip
    # load each pair ONCE (not once per strategy), optionally capped to
    # the most recent max_bars so deep stock histories (XOM: 16k bars)
    # don't turn an O(history) indicator into a coffee break
    data = {}
    for p in pairs:
        try:
            cl, dt = exam.load_closes(p)
        except Exception:
            continue
        if max_bars and len(cl) > max_bars:
            cl, dt = cl[-max_bars:], dt[-max_bars:]
        if cl:
            data[p] = (cl, dt)
    results = {}
    for nm in strat_names:
        try:
            strat = S.get(nm)
        except KeyError:
            print(f"  skip unknown strategy {nm}"); continue
        rows = []
        for p, (cl, dt) in data.items():
            try:
                rows += exam.exam_pair_closes(p, strat, cl, fee, slip, dt)
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
    ap.add_argument("--pairs", default="",
                    help="comma list; overrides auto discovery")
    ap.add_argument("--fee", type=float, default=None,
                    help="per-side fee (default: exam.FEE 0.6%%)")
    ap.add_argument("--slip", type=float, default=None)
    ap.add_argument("--max-bars", type=int, default=3000,
                    help="cap history per pair (0 = unlimited)")
    ap.add_argument("--market", default="all",
                    choices=["crypto", "stocks", "all"],
                    help="filter universe by suffix (-USD vs -US)")
    a = ap.parse_args()

    if a.pairs:
        pairs = [p.strip() for p in a.pairs.split(",") if p.strip()]
    else:
        pool = available_pairs(a.min_history)
        pairs = [p for p, _n in pool]
    if a.market == "crypto":
        pairs = [p for p in pairs if p.endswith("-USD")]
    elif a.market == "stocks":
        pairs = [p for p in pairs if p.endswith("-US")]
    pairs = pairs[:a.top]
    names = ([s.strip() for s in a.strategies.split(",") if s.strip()]
             or sorted(S.REGISTRY))
    fee = exam.FEE if a.fee is None else a.fee
    slip = exam.SLIP if a.slip is None else a.slip

    print(f"RESEARCH SCREEN  (nothing here is recorded or admissible)")
    print(f"  {len(pairs)} pairs | fee {fee:.2%}/side + slip {slip:.2%}")
    print(f"  {len(names)} strategies\n")

    res = screen(names, pairs, fee, slip, a.max_bars or None)
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
    print(f"  Edge is measured vs buy-and-hold, net of {fee:.2%} fees.")


if __name__ == "__main__":
    main()
