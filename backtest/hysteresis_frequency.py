"""
backtest/hysteresis_frequency.py - trade frequency of consensus rules with
hysteresis, on the eight fixed universe pairs.

SAME DISCIPLINE AS signal_correlation.py: this computes trade COUNTS and
time-in-position ONLY. No returns, no Sharpe, no edge. Nothing here can tell
you which rule makes money, so tuning against it is not curve fitting - it is
sizing a rule to a cost budget that was known in advance.

That distinction is the only reason it is safe to iterate here. The budget
comes from docs/intraday_standard.md, written before any of this existed:
round trip cost 1.30% at current fees, ~8 round trips/year affordable before
friction alone eats 10% of capital. Cost is a constraint, not a result.

The moment this file computes a P&L column, that argument collapses.

Candidate parameters below were chosen by reasoning about the structure the
diagnostic revealed - a wide band because signals flicker, a dwell because
flicker is the whole problem - not by searching for a number that scored well.
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signal_correlation import PAIRS, BLOCK, load, signals  # noqa: E402

COST_ROUND_TRIP = 0.0130      # docs/intraday_standard.md
BUDGET_ROUND_TRIPS = 8        # same source


def apply_hysteresis(votes, enter, exit_, dwell=0, min_hold=0):
    """Long/flat with separate entry and exit thresholds.

    enter/exit_  : vote counts. exit_ < enter creates the dead band.
    dwell        : bars the condition must hold before acting (confirmation).
    min_hold     : bars a position must be held before an exit is allowed.
    """
    v = votes.values
    n = len(v)
    pos = np.zeros(n, dtype=int)
    state, held, streak_in, streak_out = 0, 0, 0, 0
    for i in range(n):
        streak_in = streak_in + 1 if v[i] >= enter else 0
        streak_out = streak_out + 1 if v[i] < exit_ else 0
        if state == 0:
            if streak_in > dwell:
                state, held = 1, 0
        else:
            held += 1
            if streak_out > dwell and held >= min_hold:
                state = 0
        pos[i] = state
    return pd.Series(pos, index=votes.index)


# Reasoning for each, recorded before measurement so it can be checked later:
#
# A  Wide band on all 20. 13 is a clear two-thirds majority; 7 is barely over
#    a third. The dead band between them is where flicker used to live.
# B  Trend block only. The diagnostic put trend-vs-reversion at -0.222, so
#    the reversion signals are voting against the others, not confirming
#    them. Dropping them removes a source of churn rather than of opinion.
# C  A plus a one-week dwell and a one-week minimum hold. Attacks the cause
#    directly: if the condition cannot survive 24 bars, it was noise.
# D  Trend block with a monthly re-evaluation instead of hourly. The cheapest
#    possible way to cut frequency: look less often.
CANDIDATES = [
    ("A_banda_amplia",      dict(enter=13, exit_=7,  dwell=0,   min_hold=0),   "all"),
    ("B_solo_tendencia",    dict(enter=10, exit_=5,  dwell=0,   min_hold=0),   "trend"),
    ("C_banda_mas_dwell",   dict(enter=13, exit_=7,  dwell=24,  min_hold=168), "all"),
    ("D_tendencia_lenta",   dict(enter=10, exit_=5,  dwell=168, min_hold=336), "trend"),
]


def main():
    rows = []
    for pair in PAIRS:
        sig = signals(load(pair))
        years = len(sig) / 8760
        cols = {"all": list(sig.columns),
                "trend": [c for c in sig.columns if BLOCK[c] == "trend"]}
        for name, kw, which in CANDIDATES:
            votes = sig[cols[which]].sum(axis=1)
            pos = apply_hysteresis(votes, **kw)
            rt = (pos.diff().fillna(0) != 0).sum() / 2 / years
            rows.append((name, pair, rt, pos.mean()))

    print(f"\n{'='*72}")
    print("FRECUENCIA DE OPERACION CON HISTERESIS")
    print("Solo cuenta operaciones y tiempo en posicion. Sin retornos.")
    print(f"Presupuesto declarado en intraday_standard.md: "
          f"~{BUDGET_ROUND_TRIPS} round trips/año")
    print(f"{'='*72}\n")
    print(f"{'regla':<22}{'round trips/año':>17}{'% horas dentro':>16}"
          f"{'capital tras 1a':>18}")
    print(f"{'':<22}{'(media 8 pares)':>17}{'':>16}{'(solo friccion)':>18}")
    print("-" * 73)
    for name, kw, which in CANDIDATES:
        sub = [r for r in rows if r[0] == name]
        rt = np.mean([r[2] for r in sub])
        occ = np.mean([r[3] for r in sub])
        rem = (1 - COST_ROUND_TRIP) ** rt
        flag = "  OK" if rt <= BUDGET_ROUND_TRIPS else ""
        print(f"{name:<22}{rt:>17.0f}{occ*100:>15.1f}%{rem*100:>17.1f}%{flag}")
    print("-" * 73)
    print(f"{'buy_and_hold (ref)':<22}{1:>17}{100.0:>15.1f}%"
          f"{(1-COST_ROUND_TRIP)*100:>17.1f}%  OK")
    print(f"{'umbral 5 sin histeresis':<22}{479:>17}{73.9:>15.1f}%"
          f"{(1-COST_ROUND_TRIP)**479*100:>17.2f}%")
    print()
    print("dispersion por par (round trips/año):")
    for name, kw, which in CANDIDATES:
        sub = sorted(r[2] for r in rows if r[0] == name)
        print(f"  {name:<22} min {sub[0]:>5.0f}   mediana {sub[len(sub)//2]:>5.0f}"
              f"   max {sub[-1]:>5.0f}")
    print()


if __name__ == "__main__":
    main()
