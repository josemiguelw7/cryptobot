"""
backtest/signal_correlation.py - how many independent opinions are actually
in a basket of "classic" indicator families?

THIS IS A DIAGNOSTIC, NOT AN EXAM. It measures the correlation structure
BETWEEN SIGNALS and the trade frequency they imply. It deliberately does not
compute returns, Sharpe, or any measure of edge. That separation is the whole
point: knowing that two indicators agree 94% of the time tells you nothing
about whether either makes money, so running this does not contaminate a
universe or a standard that was pre-committed while blind to results.

If this script ever grows a P&L column, it stops being safe to run before
the seeds are frozen.

Every parameter below is a textbook default, chosen for being conventional
rather than for anything observed in this data. No parameter here was tuned.

Universe is the eight pairs fixed in docs/intraday_standard.md.
Signals are long/flat, matching spot crypto with no shorting.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDLES = os.path.join(ROOT, "data", "candles")
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


def load(pair):
    df = pd.read_csv(os.path.join(CANDLES, f"{pair}_3600s.csv"))
    df = df.sort_values("timestamp").drop_duplicates("timestamp")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["close"]).reset_index(drop=True)


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(df, n=14):
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()],
                   axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()


def signals(df):
    """20 classic families -> long/flat position series. Textbook defaults."""
    c, h, l = df["close"], df["high"], df["low"]
    s = {}

    # --- trend / momentum block
    s["sma_cross_50_200"] = (c.rolling(50).mean() > c.rolling(200).mean())
    s["ema_cross_12_26"] = (c.ewm(span=12).mean() > c.ewm(span=26).mean())
    s["price_over_sma200"] = (c > c.rolling(200).mean())
    s["price_over_sma50"] = (c > c.rolling(50).mean())
    macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
    s["macd_signal"] = (macd > macd.ewm(span=9).mean())
    s["macd_zero"] = (macd > 0)
    s["momentum_24"] = (c > c.shift(24))
    s["momentum_168"] = (c > c.shift(168))
    s["donchian_20"] = (c >= c.rolling(20).max())
    s["donchian_55"] = (c >= c.rolling(55).max())
    s["keltner_upper"] = (c > c.ewm(span=20).mean() + atr(df, 20))
    tr_up = (c.diff().clip(lower=0).rolling(14).sum() >
             (-c.diff().clip(upper=0)).rolling(14).sum())
    s["dm_direction_14"] = tr_up
    s["supertrend_like"] = (c > (c.rolling(10).mean() - 3 * atr(df, 10)))
    s["hh_hl_20"] = ((h.rolling(20).max() > h.rolling(20).max().shift(20)) &
                     (l.rolling(20).min() > l.rolling(20).min().shift(20)))

    # --- mean reversion block
    m, sd = c.rolling(20).mean(), c.rolling(20).std()
    s["bollinger_lower"] = (c < m - 2 * sd)
    s["zscore_low_20"] = ((c - m) / sd < -1)
    s["rsi_oversold_14"] = (rsi(c, 14) < 30)
    s["rsi_mid_50"] = (rsi(c, 14) < 50)
    lo, hi = l.rolling(14).min(), h.rolling(14).max()
    s["stoch_oversold"] = (100 * (c - lo) / (hi - lo) < 20)
    s["reversal_3down"] = (c.diff() < 0).rolling(3).sum() == 3

    out = pd.DataFrame({k: v.astype(float) for k, v in s.items()})
    return out.iloc[200:].reset_index(drop=True)


BLOCK = {k: ("reversion" if k in {
    "bollinger_lower", "zscore_low_20", "rsi_oversold_14", "rsi_mid_50",
    "stoch_oversold", "reversal_3down"} else "trend") for k in [
    "sma_cross_50_200", "ema_cross_12_26", "price_over_sma200",
    "price_over_sma50", "macd_signal", "macd_zero", "momentum_24",
    "momentum_168", "donchian_20", "donchian_55", "keltner_upper",
    "dm_direction_14", "supertrend_like", "hh_hl_20", "bollinger_lower",
    "zscore_low_20", "rsi_oversold_14", "rsi_mid_50", "stoch_oversold",
    "reversal_3down"]}


def effective_n(corr):
    """Participation ratio of the eigenvalue spectrum: how many independent
    signals a correlated basket is actually worth. 20 uncorrelated signals
    give 20; 20 identical ones give 1."""
    ev = np.linalg.eigvalsh(np.nan_to_num(corr.values, nan=0.0))
    ev = np.clip(ev, 0, None)
    return (ev.sum() ** 2) / (ev ** 2).sum()


def main():
    cors, fires, flips, per_pair_eff = [], [], [], []
    names = None

    for pair in PAIRS:
        sig = signals(load(pair))
        names = list(sig.columns)
        cors.append(sig.corr())
        per_pair_eff.append(effective_n(sig.corr()))
        votes = sig.sum(axis=1)
        for thr in (3, 5, 7, 10, 13):
            pos = (votes >= thr).astype(int)
            fires.append((pair, thr, pos.mean(),
                          int((pos.diff() != 0).sum())))
        flips.append((pair, len(sig)))

    avg = sum(cors) / len(cors)
    n_hours = flips[0][1]
    years = n_hours / 8760

    print(f"\n{'='*70}")
    print("SIGNAL INDEPENDENCE DIAGNOSTIC")
    print(f"20 classic families · 8 pairs · {n_hours} hourly bars "
          f"(~{years:.2f} years) each")
    print("Measures agreement between signals and trade frequency ONLY.")
    print("No returns, no Sharpe, no edge. Nothing here says what wins.")
    print(f"{'='*70}\n")

    tr = [n for n in names if BLOCK[n] == "trend"]
    rv = [n for n in names if BLOCK[n] == "reversion"]

    def blockmean(a, b):
        sub = avg.loc[a, b].values.copy()
        if a is b or a == b:
            np.fill_diagonal(sub, np.nan)
        return np.nanmean(sub)

    print("MEAN PAIRWISE CORRELATION (averaged over the 8 pairs)")
    print(f"  within trend block  ({len(tr)} signals) .... {blockmean(tr, tr):+.3f}")
    print(f"  within reversion    ({len(rv)} signals) .... {blockmean(rv, rv):+.3f}")
    print(f"  trend vs reversion .................. {blockmean(tr, rv):+.3f}")

    print(f"\nEFFECTIVE NUMBER OF INDEPENDENT SIGNALS (participation ratio)")
    print(f"  nominal ................. 20.00")
    print(f"  effective, pooled ....... {effective_n(avg):.2f}")
    print(f"  effective, per pair ..... "
          f"{np.mean(per_pair_eff):.2f} (min {min(per_pair_eff):.2f}, "
          f"max {max(per_pair_eff):.2f})")

    print(f"\nCONSENSUS THRESHOLD: how often does 'N of 20 agree' hold?")
    print(f"  {'thr':>4} {'% of hours in position':>24} {'round trips/yr':>16}")
    for thr in (3, 5, 7, 10, 13):
        rows = [f for f in fires if f[1] == thr]
        occ = np.mean([r[2] for r in rows])
        rt = np.mean([r[3] for r in rows]) / 2 / years
        print(f"  {thr:>4} {occ*100:>23.1f}% {rt:>16.0f}")
    print()


if __name__ == "__main__":
    main()
