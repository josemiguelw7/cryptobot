"""
Cross-sectional momentum rotation backtest.

Every week: rank all coins by trailing 30-day return, hold the top N.
Optional absolute filter: only hold coins whose 30d return is positive;
if none qualify, sit entirely in cash (classic dual momentum).

Decisions use data through day t; execution happens at day t+1 close
(no lookahead). Fees + slippage charged on every buy and sell.

Usage:
    python backtest/rotation.py
"""
import glob, os
import numpy as np
import pandas as pd
from scanner import CANDLES, RESULTS

FEE, SLIP = 0.006, 0.0005
START_CASH = 10_000.0


def load_panel():
    """Daily close prices, one column per pair, from the 1h files."""
    frames = {}
    for path in sorted(glob.glob(os.path.join(CANDLES, "*_3600s.csv"))):
        pair = os.path.basename(path).replace("_3600s.csv", "")
        df = pd.read_csv(path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        frames[pair] = df.set_index("datetime")["close"].resample("1D").last()
    return pd.DataFrame(frames).ffill()


def run_rotation(panel, top_n=3, lookback=30, rebal_days=7, abs_filter=True):
    mom = panel.pct_change(lookback, fill_method=None)
    cash, units = START_CASH, {}
    fees, trades = 0.0, 0
    pending, last_rebal = None, -10**9
    equity = np.zeros(len(panel))

    for i in range(len(panel)):
        prices = panel.iloc[i]

        # execute yesterday's decision at today's close
        if pending is not None:
            for p in [p for p in list(units) if p not in pending]:
                px = prices[p]
                if px > 0:
                    gross = units.pop(p) * px * (1 - SLIP)
                    f = gross * FEE
                    cash += gross - f
                    fees += f; trades += 1
            new = [p for p in pending if p not in units and prices[p] > 0]
            if new and cash > 1:
                per = cash / len(new)
                for p in new:
                    f = per * FEE
                    units[p] = (per - f) / (prices[p] * (1 + SLIP))
                    fees += f; trades += 1
                cash = 0.0
            pending = None

        # decide at close every rebal_days (executed next day)
        if i - last_rebal >= rebal_days and i > lookback:
            m = mom.iloc[i].dropna()
            if abs_filter:
                m = m[m > 0]
            pending = list(m.sort_values(ascending=False).head(top_n).index)
            last_rebal = i

        equity[i] = cash + sum(u * prices[p] for p, u in units.items()
                               if prices[p] > 0)

    run_max = np.maximum.accumulate(equity)
    return {
        "ret": equity[-1] / START_CASH - 1,
        "max_dd": (equity / run_max - 1).min(),
        "trades": trades,
        "fees": fees,
    }


def main():
    panel = load_panel()
    print(f"Period: {panel.index[0]:%Y-%m-%d} -> {panel.index[-1]:%Y-%m-%d} "
          f"| {panel.shape[1]} pairs\n")

    btc = panel["BTC-USD"].dropna()
    full = panel.dropna(axis=1)  # coins listed the whole year
    ew = (full.iloc[-1] / full.iloc[0] - 1).mean()
    print(f"Benchmark BTC buy&hold:          {btc.iloc[-1]/btc.iloc[0]-1:+8.1%}")
    print(f"Benchmark equal-weight buy&hold: {ew:+8.1%} "
          f"({full.shape[1]} full-history coins)\n")

    variants = [
        ("top3 + cash filter", dict(top_n=3, abs_filter=True)),
        ("top3, always invested", dict(top_n=3, abs_filter=False)),
        ("top5 + cash filter", dict(top_n=5, abs_filter=True)),
    ]
    for label, kw in variants:
        r = run_rotation(panel, **kw)
        print(f"{label:22s} ret {r['ret']:+8.1%}  maxDD {r['max_dd']:6.1%}  "
              f"trades {r['trades']:3d}  fees ${r['fees']:,.0f}")


if __name__ == "__main__":
    main()
