"""
bot/stats.py - statistics for the intraday squad.

Implements the gates named in docs/intraday_success_criteria.md sections 5.3-5.5:
  - annualized Sharpe (sqrt(365) crypto, sqrt(252) stocks)
  - LCB: mean daily net return - 1.28 * standard error
  - max drawdown from a daily net return series
  - PSR / DSR: Bailey & Lopez de Prado's Probabilistic and Deflated Sharpe Ratio

WHY DSR EXISTS (charter section 5.7, in short):
The standard error of an annualized Sharpe over 90 daily observations is roughly
sqrt(365)/sqrt(90) ~= 2.0. A strategy with exactly zero edge clears Sharpe >= 1.0
about a third of the time by luck. Run K strategies and the best one looks great
by construction. DSR asks: does this Sharpe beat what the LUCKIEST of K coin-flippers
would have shown? It gets harder as K grows, which is correct, because breeding is
what manufactures false positives.

Reference: Bailey, D. and Lopez de Prado, M. (2014), "The Deflated Sharpe Ratio:
Correcting for Selection Bias, Backtest Overfitting and Non-Normality."

NOTE ON UNITS: PSR and DSR operate on the PER-PERIOD (daily) Sharpe, never the
annualized one. Mixing these up silently inflates DSR. Guarded in the tests.

No dependency beyond the standard library.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Sequence

EULER_MASCHERONI = 0.5772156649015329
_N = NormalDist()

PERIODS_PER_YEAR = {"crypto": 365, "stock": 252}
LCB_Z = 1.28  # ~90% one-sided lower bound, per charter section 3


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def _std(xs: Sequence[float], ddof: int = 1) -> float:
    n = len(xs)
    if n - ddof <= 0:
        raise ValueError(f"need more than {ddof} observations, got {n}")
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - ddof))


def _moment(xs: Sequence[float], k: int) -> float:
    m = _mean(xs)
    return sum((x - m) ** k for x in xs) / len(xs)


def skewness(returns: Sequence[float]) -> float:
    """Population skewness (gamma_3)."""
    s = _std(returns, ddof=0)
    if s == 0:
        return 0.0
    return _moment(returns, 3) / s ** 3


def kurtosis(returns: Sequence[float]) -> float:
    """NON-excess kurtosis (gamma_4). Normal distribution = 3.0."""
    s = _std(returns, ddof=0)
    if s == 0:
        return 3.0
    return _moment(returns, 4) / s ** 4


def sharpe_per_period(returns: Sequence[float]) -> float:
    """Daily (per-observation) Sharpe. This is the input to PSR/DSR."""
    s = _std(returns, ddof=1)
    if s == 0:
        return 0.0
    return _mean(returns) / s


def sharpe_annualized(returns: Sequence[float], asset_class: str) -> float:
    """Charter section 3: sqrt(365) for crypto, sqrt(252) for stocks."""
    if asset_class not in PERIODS_PER_YEAR:
        raise ValueError(f"asset_class must be one of {sorted(PERIODS_PER_YEAR)}")
    return sharpe_per_period(returns) * math.sqrt(PERIODS_PER_YEAR[asset_class])


def lcb(returns: Sequence[float], z: float = LCB_Z) -> float:
    """Lower confidence bound on mean daily net return (charter section 5.4 gate)."""
    n = len(returns)
    se = _std(returns, ddof=1) / math.sqrt(n)
    return _mean(returns) - z * se


def max_drawdown(returns: Sequence[float]) -> float:
    """Max peak-to-trough drawdown of the compounded equity curve, as a
    POSITIVE fraction. 0.10 means a 10% drawdown (the charter section 5.6 limit)."""
    equity, peak, worst = 1.0, 1.0, 0.0
    for r in returns:
        equity *= (1.0 + r)
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) / peak)
    return worst


def probabilistic_sharpe(returns: Sequence[float], sr_benchmark: float = 0.0) -> float:
    """
    PSR: probability the TRUE per-period Sharpe exceeds sr_benchmark, given the
    observed series' length, skewness and kurtosis.

        PSR = Phi[ (SR - SR*) * sqrt(n - 1) / sqrt(1 - g3*SR + (g4-1)/4 * SR^2) ]

    Negative skew and fat tails shrink it - which is the point, since both are
    exactly what a strategy that sells volatility looks like right up until it
    stops looking like that.
    """
    n = len(returns)
    if n < 3:
        raise ValueError("PSR needs at least 3 observations")
    sr = sharpe_per_period(returns)
    g3, g4 = skewness(returns), kurtosis(returns)
    denom_sq = 1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * sr ** 2
    if denom_sq <= 0:
        return 0.0
    return _N.cdf((sr - sr_benchmark) * math.sqrt(n - 1) / math.sqrt(denom_sq))


def expected_max_sharpe(sharpe_std: float, k: int) -> float:
    """
    Expected MAXIMUM per-period Sharpe across k independent zero-edge trials.
    This is the benchmark DSR must clear - the luckiest coin-flipper's score.

        SR0 = sharpe_std * [ (1-g)*Phi^-1(1 - 1/k) + g*Phi^-1(1 - 1/(k*e)) ]

    Grows with k, which is why K (charter section 3) never decreases.
    """
    if k < 2:
        return 0.0
    a = _N.inv_cdf(1.0 - 1.0 / k)
    b = _N.inv_cdf(1.0 - 1.0 / (k * math.e))
    return sharpe_std * ((1.0 - EULER_MASCHERONI) * a + EULER_MASCHERONI * b)


def deflated_sharpe(returns: Sequence[float], trial_sharpes: Sequence[float]) -> float:
    """
    DSR = PSR evaluated against the expected-max-Sharpe benchmark for K trials.

    trial_sharpes: the PER-PERIOD Sharpes of every configuration that has ever
    accumulated counted days in this asset class (charter section 3, "K"). Their
    dispersion estimates how much Sharpe this search space generates by luck.
    Pass the full list including this bot's own - that is the definition.

    Charter section 5.7: DSR is a REPORTED METRIC at v1.0, not a gate. It is
    published in every champion writeup and weekly on the portal alongside K.
    0.95 is the reference threshold if it is ever promoted to a gate.
    """
    k = len(trial_sharpes)
    if k < 2:
        # Cannot estimate selection bias from one trial. Strictest reading
        # (charter section 2.5): fall back to the undeflated zero benchmark and
        # let the LCB gate carry the weight.
        return probabilistic_sharpe(returns, 0.0)
    sr0 = expected_max_sharpe(_std(trial_sharpes, ddof=1), k)
    return probabilistic_sharpe(returns, sr0)


@dataclass
class BotStats:
    n_days: int
    net_pnl: float
    sharpe_annual: float
    sharpe_daily: float
    lcb: float
    max_drawdown: float
    dsr: float
    k_trials: int

    def stage1_gates(self, n_closed_trades: int, window_days: int, breaches: int) -> dict:
        """Charter section 5, criteria 1-7. Returns each gate's pass/fail.

        Sample-size path A (90d/100 trades) or B (180d/50 trades).

        DSR IS DELIBERATELY NOT A GATE HERE (charter section 5.7). It is carried
        on BotStats and published, but it does not block graduation at v1.0.
        Promoting it to a gate is a tightening and is permitted; if that ever
        happens, add it here and nowhere else."""
        path_a = window_days >= 90 and n_closed_trades >= 100
        path_b = window_days >= 180 and n_closed_trades >= 50
        return {
            "sample_size": path_a or path_b,
            "net_pnl_positive": self.net_pnl > 0,
            "sharpe_floor": self.sharpe_annual >= 1.0,
            "lcb_positive": self.lcb > 0,
            "max_drawdown": self.max_drawdown <= 0.10,
            "zero_breaches": breaches == 0,
        }

    def stage2_window(self, graduation_path: str) -> tuple:
        """Charter section 6.2: (fresh counted days, min closed trades)."""
        if graduation_path.upper() == "A":
            return (60, 60)
        if graduation_path.upper() == "B":
            return (120, 30)
        raise ValueError("graduation_path must be 'A' or 'B'")


def compute(returns: Sequence[float], asset_class: str,
            trial_sharpes: Sequence[float]) -> BotStats:
    return BotStats(
        n_days=len(returns),
        net_pnl=math.prod(1.0 + r for r in returns) - 1.0,
        sharpe_annual=sharpe_annualized(returns, asset_class),
        sharpe_daily=sharpe_per_period(returns),
        lcb=lcb(returns),
        max_drawdown=max_drawdown(returns),
        dsr=deflated_sharpe(returns, trial_sharpes),
        k_trials=len(trial_sharpes),
    )
