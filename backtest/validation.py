"""
VALIDATION — is a result distinguishable from luck?

The exam answers "did it clear the bar." These answer "should I believe
it." Cheap to run: the full exam sim is ~0.06s, so thousands of
resamples cost seconds. Compute is not the constraint; inference is.

  permutation_test  shuffle returns, keep the strategy -> how often does
                    chance alone reproduce this? (real p-value)
  bootstrap_ci      resample windows -> confidence interval on return
  parameter_plateau is the result a plateau or a knife-edge?
  deflated_sharpe   Bailey & Lopez de Prado: correct the significance
                    threshold for HOW MANY candidates you have tried
  breakeven_turnover  max trades/year the fee structure can support

Usage:
    python backtest/validation.py --candidate trend_200 --all
"""
import argparse, csv, math, os, random, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam, strategies as S

LEDGER = os.path.join(HERE, "results", "exam_ledger.csv")


def _stitch(rows, key="ret"):
    return float(np.prod([1 + r[key] for r in rows]) - 1)


# ------------------------------------------------------------ permutation
def permutation_test(name, n_iter=500, seed=0):
    """H0: the strategy has no edge; any result is timing luck.
    Shuffle each pair's daily RETURNS (destroying serial structure the
    strategy keys on) but keep the same distribution, then re-run."""
    rng = random.Random(seed)
    strat = S.get(name)
    real = _stitch([r for p in exam.PAIRS
                    for r in exam.exam_pair(p, strat, exam.FEE, exam.SLIP)])
    beats = 0
    for _ in range(n_iter):
        rows = []
        for p in exam.PAIRS:
            cl, _d = exam.load_closes(p)
            if len(cl) < 2:
                continue
            rets = [cl[i] / cl[i - 1] for i in range(1, len(cl))]
            rng.shuffle(rets)
            shuf = [cl[0]]
            for r in rets:
                shuf.append(shuf[-1] * r)
            rows += exam.exam_pair_closes(p, strat, shuf, exam.FEE, exam.SLIP)
        if rows and _stitch(rows) >= real:
            beats += 1
    p = (beats + 1) / (n_iter + 1)
    return {"real": real, "p_value": p, "iters": n_iter}


# ------------------------------------------------------------ bootstrap
def bootstrap_ci(name, n_iter=2000, seed=0, lo=5, hi=95):
    """Resample exam windows with replacement -> CI on stitched return."""
    rng = np.random.default_rng(seed)
    strat = S.get(name)
    rows = [r for p in exam.PAIRS
            for r in exam.exam_pair(p, strat, exam.FEE, exam.SLIP)]
    if not rows:
        return None
    rets = np.array([r["ret"] for r in rows])
    bh = np.array([r["bh"] for r in rows])
    draws, edge = [], []
    n = len(rets)
    for _ in range(n_iter):
        idx = rng.integers(0, n, n)
        draws.append(np.prod(1 + rets[idx]) - 1)
        edge.append(np.mean(rets[idx] - bh[idx]))
    return {"n_windows": n,
            "median": float(np.median(draws)),
            "ci": (float(np.percentile(draws, lo)),
                   float(np.percentile(draws, hi))),
            "edge_vs_bh_mean": float(np.mean(edge)),
            "edge_ci": (float(np.percentile(edge, lo)),
                        float(np.percentile(edge, hi))),
            "pct_edge_positive": float(np.mean(np.array(edge) > 0))}


# ------------------------------------------------------------ plateau
def parameter_plateau(builder, values):
    """builder(v) -> Strategy. Robust edges sit on plateaus; overfit
    ones sit on spikes surrounded by bad neighbours."""
    out = []
    for v in values:
        strat = builder(v)
        rows = [r for p in exam.PAIRS
                for r in exam.exam_pair(p, strat, exam.FEE, exam.SLIP)]
        if not rows:
            continue
        out.append({"param": v, "stitched": _stitch(rows),
                    "edge": float(np.mean([r["ret"] - r["bh"] for r in rows])),
                    "windows": len(rows)})
    return out


# ------------------------------------------------------------ deflated SR
def expected_max_sharpe(n_trials, var_sharpe):
    """False Strategy Theorem: E[max SR] across N independent trials of
    zero-skill strategies. Bailey & Lopez de Prado (2014)."""
    if n_trials < 2:
        return 0.0
    e = 0.5772156649
    z1 = _norm_ppf(1 - 1.0 / n_trials)
    z2 = _norm_ppf(1 - 1.0 / (n_trials * math.e))
    return math.sqrt(var_sharpe) * ((1 - e) * z1 + e * z2)


def _norm_ppf(p):
    return float(np.sqrt(2) * _erfinv(2 * p - 1))


def _erfinv(x):
    a = 0.147
    ln = math.log(1 - x * x) if abs(x) < 1 else -700
    t = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(max(0.0, math.sqrt(t * t - ln / a) - t)), x)


def deflated_check(observed_sharpe, n_trials, var_sharpe=0.25):
    """Compare an observed Sharpe to the max you'd EXPECT from luck
    alone after n_trials attempts. Below the hurdle => not evidence."""
    hurdle = expected_max_sharpe(n_trials, var_sharpe)
    return {"observed": observed_sharpe, "n_trials": n_trials,
            "luck_hurdle": hurdle, "clears": observed_sharpe > hurdle}


# ------------------------------------------------------------ costs
def breakeven_turnover(fee=exam.FEE, slip=exam.SLIP, target_drag=0.10):
    """How many round trips/yr before friction alone eats target_drag."""
    rt = 1 - (1 - fee - slip) ** 2
    n = math.log(1 - target_drag) / math.log(1 - rt)
    return {"round_trip_cost": rt, "max_round_trips": n,
            "drag_budget": target_drag}


def ledger_trials():
    if not os.path.exists(LEDGER):
        return 0
    with open(LEDGER) as f:
        return sum(1 for _ in csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--iters", type=int, default=300)
    a = ap.parse_args()
    nm = a.candidate
    print(f"=== VALIDATION: {nm} ===")

    b = bootstrap_ci(nm)
    if b:
        print(f"\n[bootstrap] {b['n_windows']} windows")
        print(f"  stitched median {b['median']:+.1%}  "
              f"90% CI [{b['ci'][0]:+.1%}, {b['ci'][1]:+.1%}]")
        print(f"  mean per-window edge vs buy-hold {b['edge_vs_bh_mean']:+.2%}"
              f"  CI [{b['edge_ci'][0]:+.2%}, {b['edge_ci'][1]:+.2%}]")
        print(f"  windows where edge > 0: {b['pct_edge_positive']:.0%}")
        if b["edge_ci"][0] < 0 < b["edge_ci"][1]:
            print("  -> CI straddles zero: edge NOT distinguishable from noise")

    n = ledger_trials()
    d = deflated_check(0.0, max(n, 1))
    print(f"\n[multiple testing] {n} candidates examined to date")
    print(f"  Sharpe you'd expect from LUCK alone after {n} trials: "
          f"{d['luck_hurdle']:.2f}")
    print("  -> any candidate must clear this before it is evidence")

    c = breakeven_turnover()
    print(f"\n[cost budget] round trip costs {c['round_trip_cost']:.2%}")
    print(f"  max {c['max_round_trips']:.0f} round trips/yr "
          f"before friction alone eats {c['drag_budget']:.0%}")

    if a.all:
        print(f"\n[permutation] running {a.iters} shuffles...")
        p = permutation_test(nm, n_iter=a.iters)
        print(f"  real stitched {p['real']:+.1%}")
        print(f"  p-value {p['p_value']:.4f}"
              f"  {'(not significant)' if p['p_value'] > 0.05 else '(significant)'}")


if __name__ == "__main__":
    main()
