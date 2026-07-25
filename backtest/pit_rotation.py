"""
Point-in-time rotation backtest over ALL Coinbase USD pairs, ~4y daily.

Fixes the universe bias that fooled us: on each rebalance the strategy
may only pick from coins in the top-K by TRAILING 30-day median dollar
volume as of that date - information genuinely available at the time.
Coins enter the universe when they become liquid, exactly as a live bot
would experience.

Honesty note: pairs fully delisted before today can't be fetched at all,
so a sliver of survivorship bias remains. It is far smaller than before,
and it's disclosed rather than hidden.

Switchable upgrades: maker-fee scenario (#8), BTC>200dma regime filter
(#14), inverse-volatility sizing (#11). Metrics via metrics.py (#5).

Usage:
    python backtest/pit_rotation.py
"""
import glob, os
import numpy as np
import pandas as pd
import metrics as mx

HERE = os.path.dirname(os.path.abspath(__file__))
DAILY = os.path.join(HERE, "..", "data", "candles_daily")
START_CASH = 10_000.0
SLIP = 0.0005


def load_panels():
    """closes + dollar-volume panels: one column per pair."""
    closes, dvol = {}, {}
    for path in sorted(glob.glob(os.path.join(DAILY, "*_86400s.csv"))):
        pair = os.path.basename(path).replace("_86400s.csv", "")
        df = pd.read_csv(path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        s = df.set_index("datetime").resample("1D").last()
        closes[pair] = s["close"]
        dvol[pair] = s["close"] * s["volume"]
    return pd.DataFrame(closes), pd.DataFrame(dvol)


def precompute(c, v, lookback, univ_k):
    mom = c.pct_change(lookback, fill_method=None)
    dv30 = v.rolling(30, min_periods=20).median()
    elig = dv30.rank(axis=1, ascending=False) <= univ_k
    dvol30 = c.pct_change(fill_method=None).rolling(30).std()
    btc = c["BTC-USD"]
    btc_ok = btc > btc.rolling(200, min_periods=100).mean()
    return mom, elig, dvol30, btc_ok


def run(c, v, top_n=3, lookback=30, rebal=7, univ_k=25,
        fee=0.006, regime=False, inv_vol=False):
    mom, elig, dvol30, btc_ok = precompute(c, v, lookback, univ_k)
    cff = c.ffill()
    cash, units = START_CASH, {}
    fees, trades = 0.0, 0
    pending, last_rebal = None, -10**9
    equity = np.zeros(len(c))

    for i in range(len(c)):
        prices = cff.iloc[i]

        if pending is not None:                    # execute at today's close
            targets = dict(pending)
            for p in [p for p in list(units) if p not in targets]:
                px = prices[p]
                if px > 0:
                    gross = units.pop(p) * px * (1 - SLIP)
                    f = gross * fee
                    cash += gross - f
                    fees += f; trades += 1
            new = {p: w for p, w in targets.items()
                   if p not in units and prices[p] > 0}
            if new and cash > 1:
                wsum = sum(new.values())
                for p, w in new.items():
                    alloc = cash * w / wsum
                    f = alloc * fee
                    units[p] = (alloc - f) / (prices[p] * (1 + SLIP))
                    fees += f; trades += 1
                cash = 0.0
            pending = None

        if i - last_rebal >= rebal and i > lookback:   # decide (fills next day)
            if regime and not bool(btc_ok.iloc[i]):
                pending = []                            # bear regime -> cash
            else:
                m = mom.iloc[i][elig.iloc[i]].dropna()
                m = m[m > 0]
                sel = m.sort_values(ascending=False).head(top_n)
                if inv_vol:
                    w = 1.0 / dvol30.iloc[i][sel.index]
                    w = w.replace([np.inf, -np.inf], np.nan).dropna()
                    pending = list(zip(w.index, w / w.sum())) if len(w) else []
                else:
                    pending = [(p, 1.0) for p in sel.index]
            last_rebal = i

        equity[i] = cash + sum(u * prices[p] for p, u in units.items()
                               if prices[p] > 0)

    m = mx.compute(equity)
    m.update({"trades": trades, "fees": fees})
    return m, equity


def monte_carlo(equity, n=2000, seed=7):
    """#4: bootstrap daily returns - could this result be luck?"""
    rng = np.random.default_rng(seed)
    r = np.diff(equity) / equity[:-1]
    sims = np.array([np.prod(1 + rng.choice(r, size=len(r))) - 1
                     for _ in range(n)])
    return np.percentile(sims, [5, 50, 95])


def main():
    c, v = load_panels()
    print(f"Panel: {c.shape[0]} days x {c.shape[1]} pairs "
          f"({c.index[0]:%Y-%m-%d} -> {c.index[-1]:%Y-%m-%d})")
    btc = c["BTC-USD"].dropna()
    print(f"BTC buy&hold same period: {btc.iloc[-1]/btc.iloc[0]-1:+.1%}\n")

    scenarios = [
        ("taker 0.60%", dict()),
        ("maker 0.35%", dict(fee=0.0035)),
        ("maker + regime", dict(fee=0.0035, regime=True)),
        ("maker + regime + invvol", dict(fee=0.0035, regime=True,
                                         inv_vol=True)),
    ]
    best_eq = None
    for label, kw in scenarios:
        m, eq = run(c, v, **kw)
        print(f"{label:26s} {mx.fmt(m)}  trades {m['trades']:4d}")
        if label.startswith("maker + regime +"):
            best_eq = eq

    print("\n#3 Sensitivity grid (Sharpe), maker+regime+invvol:")
    lbs, tns = [15, 30, 45, 60], [2, 3, 5]
    print("            " + "".join(f"top{t:<8d}" for t in tns))
    for lb in lbs:
        row = []
        for tn in tns:
            m, _ = run(c, v, top_n=tn, lookback=lb,
                       fee=0.0035, regime=True, inv_vol=True)
            row.append(f"{m['sharpe']:8.2f}   ")
        print(f"lookback {lb:3d} " + "".join(row))

    p5, p50, p95 = monte_carlo(best_eq)
    print(f"\n#4 Monte Carlo (2000 bootstraps of daily returns):")
    print(f"   5th pct {p5:+.1%} | median {p50:+.1%} | 95th pct {p95:+.1%}")


if __name__ == "__main__":
    main()
