"""
Risk-adjusted performance metrics. Pros never rank by raw return:
a +30% with -15% drawdown beats +600% with -55% every time.

  CAGR    - compound annual growth rate
  Sharpe  - return per unit of volatility (rough guide: >1 good, >2 rare)
  Sortino - like Sharpe but only penalizes downside moves
  MaxDD   - worst peak-to-trough loss
  Calmar  - CAGR / |MaxDD|: growth per unit of worst pain
"""
import numpy as np


def compute(equity, periods_per_year=365):
    eq = np.asarray(equity, dtype=float)
    r = np.diff(eq) / eq[:-1]
    total = eq[-1] / eq[0] - 1
    years = len(eq) / periods_per_year
    cagr = (eq[-1] / eq[0]) ** (1 / years) - 1 if years > 0 else np.nan
    sd = r.std()
    sharpe = r.mean() / sd * np.sqrt(periods_per_year) if sd > 0 else np.nan
    dsd = r[r < 0].std() if (r < 0).any() else np.nan
    sortino = r.mean() / dsd * np.sqrt(periods_per_year) if dsd and dsd > 0 else np.nan
    run_max = np.maximum.accumulate(eq)
    max_dd = (eq / run_max - 1).min()
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan
    return {"total": total, "cagr": cagr, "sharpe": sharpe,
            "sortino": sortino, "max_dd": max_dd, "calmar": calmar}


def fmt(m):
    return (f"ret {m['total']:+8.1%}  CAGR {m['cagr']:+7.1%}  "
            f"Sharpe {m['sharpe']:5.2f}  Sortino {m['sortino']:5.2f}  "
            f"maxDD {m['max_dd']:6.1%}  Calmar {m['calmar']:5.2f}")
