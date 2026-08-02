"""
backtest/move_scale.py - is the market even moving enough to pay for a trade?

WHAT THIS MEASURES, AND THE LINE IT DOES NOT CROSS

§4.3 requires modeled expected edge >= 2x modeled round-trip cost before a
bot may trade. Setting that threshold sensibly needs one prior fact: how far
does price actually travel over a given holding period, regardless of
direction and regardless of any signal.

So this computes the UNCONDITIONAL distribution of |return| over fixed
horizons. No signal is involved. No direction is involved. Nothing here is
conditioned on an indicator, so it cannot tell you which rule wins, and
reading it does not contaminate a standard pre-committed while blind to
results. It answers a different question: whether a 2.60% hurdle is even
reachable at an hourly holding horizon, which is a property of the asset and
the fee schedule, not of any strategy.

The boundary is direction. The moment this file conditions on a signal, or
uses signed rather than absolute returns, it becomes a backtest.

Cost references, both from documents already committed:
  0.80% round trip - charter 4.1, taker 0.40%/side
  1.30% round trip - intraday_standard.md
Under charter 2.4 the stricter reading governs, so 1.30% is carried as the
binding figure and 0.80% is shown for contrast only.
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signal_correlation import PAIRS, load  # noqa: E402

HORIZONS = [1, 4, 12, 24, 72, 168, 336, 720]   # hours
RT_STRICT, RT_CHARTER = 0.0130, 0.0080


def main():
    per_h = {h: [] for h in HORIZONS}
    for pair in PAIRS:
        c = load(pair)["close"]
        for h in HORIZONS:
            r = (c.shift(-h) / c - 1).abs().dropna()
            per_h[h].append(r)

    print(f"\n{'='*76}")
    print("ESCALA DE MOVIMIENTO — distribucion incondicional de |retorno|")
    print("8 pares, ~1 año de barras horarias. Sin señal, sin direccion.")
    print(f"{'='*76}\n")
    print(f"{'horizonte':>10}{'mediana':>10}{'p75':>9}{'p90':>9}"
          f"{'% >2.60%':>11}{'% >1.60%':>11}")
    print("-" * 60)
    for h in HORIZONS:
        r = pd.concat(per_h[h])
        lbl = f"{h}h" if h < 24 else f"{h//24}d"
        print(f"{lbl:>10}{r.median()*100:>9.2f}%{r.quantile(.75)*100:>8.2f}%"
              f"{r.quantile(.90)*100:>8.2f}%"
              f"{(r > 2*RT_STRICT).mean()*100:>10.1f}%"
              f"{(r > 2*RT_CHARTER).mean()*100:>10.1f}%")
    print("-" * 60)
    print(f"  2.60% = 2x coste ida y vuelta a 1.30% (lectura estricta, §2.4)")
    print(f"  1.60% = 2x coste ida y vuelta a 0.80% (modelo del charter §4.1)")
    print()
    print("Lectura: la columna '% >2.60%' es la fraccion de momentos en que el")
    print("mercado se mueve lo suficiente para que una operacion PUEDA cumplir")
    print("§4.3. Es un techo, no un resultado: acertar la direccion es otro")
    print("problema y este script no lo toca.")
    print()


if __name__ == "__main__":
    main()
