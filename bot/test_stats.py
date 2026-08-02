"""Tests for bot/stats.py, plus the simulation behind charter section 5.7."""
import math, random, sys
sys.path.insert(0, __file__.rsplit("/", 2)[0])
from bot import stats

def approx(a, b, tol=1e-9): assert abs(a - b) < tol, f"{a} != {b}"

# --- basics ---
r = [0.01, -0.02, 0.03, 0.00, -0.01, 0.02]
approx(stats.sharpe_annualized(r, "crypto"),
       stats.sharpe_per_period(r) * math.sqrt(365))
approx(stats.sharpe_annualized(r, "stock"),
       stats.sharpe_per_period(r) * math.sqrt(252))
assert stats.lcb(r) < stats._mean(r), "LCB must sit below the point estimate"

# normal sample: skew ~0, non-excess kurtosis ~3
random.seed(7)
g = [random.gauss(0, 1) for _ in range(200_000)]
assert abs(stats.skewness(g)) < 0.02, stats.skewness(g)
assert abs(stats.kurtosis(g) - 3.0) < 0.05, stats.kurtosis(g)

# drawdown: +10% then -20% -> peak 1.10, trough 0.88 -> 20%
approx(stats.max_drawdown([0.10, -0.20]), 0.20, 1e-12)
approx(stats.max_drawdown([0.01, 0.01, 0.01]), 0.0, 1e-12)

# PSR of a zero-mean series against a zero benchmark ~ 0.5
approx(stats.probabilistic_sharpe([0.01, -0.01] * 50, 0.0), 0.5, 0.02)

# expected max Sharpe must grow with K and vanish at K=1
assert stats.expected_max_sharpe(0.1, 1) == 0.0
assert stats.expected_max_sharpe(0.1, 100) > stats.expected_max_sharpe(0.1, 10) > 0

# DSR must be strictly harsher than undeflated PSR once K > 1
edge = [random.gauss(0.0015, 0.01) for _ in range(90)]
trials = [random.gauss(0, 0.10) for _ in range(20)]
assert stats.deflated_sharpe(edge, trials) < stats.probabilistic_sharpe(edge, 0.0)

# unit guard: annualized Sharpe fed to PSR would silently inflate it
assert stats.sharpe_annualized(edge, "crypto") > 10 * stats.sharpe_per_period(edge)

print("all assertions passed\n")

# --- the section 5.7 simulation: how often does pure noise clear the bar? ---
random.seed(42)
TRIALS, DAYS, K = 20_000, 90, 20
naive = deflated = lcb_pass = 0
for _ in range(TRIALS):
    x = [random.gauss(0.0, 0.01) for _ in range(DAYS)]   # TRUE EDGE = ZERO
    if stats.sharpe_annualized(x, "crypto") >= 1.0: naive += 1
    if stats.lcb(x) > 0: lcb_pass += 1
    ts = [random.gauss(0, 0.105) for _ in range(K)]
    if stats.deflated_sharpe(x, ts) >= 0.95: deflated += 1

print(f"{TRIALS:,} zero-edge strategies, {DAYS} days each, K={K}")
print(f"  Sharpe >= 1.0 alone : {naive/TRIALS:6.2%}  <- your draft's bar")
print(f"  LCB > 0 alone       : {lcb_pass/TRIALS:6.2%}")
print(f"  DSR >= 0.95         : {deflated/TRIALS:6.2%}  <- v1.0 gate")
print(f"\nExpected false graduates from {K} bots on the naive bar: {K*naive/TRIALS:.1f}")
print(f"Expected false graduates from {K} bots on the v1.0 gate : {K*deflated/TRIALS:.2f}")
