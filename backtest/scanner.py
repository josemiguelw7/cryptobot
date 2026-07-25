"""
Multi-coin, multi-timeframe strategy scanner.

Runs the backtest engine over every pair in data/candles/ at 5min, 15min,
and 1h (resampled from the 5-min data). Ranks results by "edge vs hold":
strategy net return minus buy-and-hold return. In a falling market raw
return flatters nothing; edge shows whether the strategy added value.

Usage:
    python backtest/scanner.py --fast 20 --slow 50 --fee 0.006
"""
import argparse, glob, os
import pandas as pd
import engine

HERE = os.path.dirname(os.path.abspath(__file__))
CANDLES = os.path.join(HERE, "..", "data", "candles")
RESULTS = os.path.join(HERE, "results")

TIMEFRAMES = ["5min", "15min", "1h"]


def resample(df, rule):
    """Aggregate 5-min OHLCV up to a larger timeframe."""
    if rule == "5min":
        return df
    d = df.set_index("datetime")
    out = d.resample(rule).agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna().reset_index()
    return out


def scan(fast, slow, fee, slip):
    rows = []
    paths = sorted(glob.glob(os.path.join(CANDLES, "*_300s.csv")))
    for path in paths:
        pair = os.path.basename(path).replace("_300s.csv", "")
        base = engine.load_candles(path)
        for tf in TIMEFRAMES:
            df = resample(base.copy(), tf)
            df = engine.add_signals(df, fast, slow)
            res = engine.run_backtest(df, fee_rate=fee, slip_rate=slip)
            rows.append({
                "pair": pair,
                "timeframe": tf,
                "strat_return": res["total_return"],
                "buy_hold": res["buy_hold_return"],
                "edge_vs_hold": res["total_return"] - res["buy_hold_return"],
                "trades": res["n_trades"],
                "win_rate": res["win_rate"],
                "fees_paid": res["fees_paid"],
                "max_dd": res["max_drawdown"],
            })
    return pd.DataFrame(rows)


def report(df):
    pd.set_option("display.width", 120)
    fmt = df.copy()
    for col in ["strat_return", "buy_hold", "edge_vs_hold", "win_rate", "max_dd"]:
        fmt[col] = (fmt[col] * 100).round(1)
    fmt["fees_paid"] = fmt["fees_paid"].round(0)

    print("\n=== Average edge vs hold, by timeframe (all 25 pairs) ===")
    agg = df.groupby("timeframe").agg(
        avg_edge=("edge_vs_hold", "mean"),
        avg_trades=("trades", "mean"),
        avg_fees=("fees_paid", "mean"),
    ).reindex(TIMEFRAMES)
    agg["avg_edge"] = (agg["avg_edge"] * 100).round(1)
    print(agg.round(1).to_string())

    print("\n=== Top 12 pair/timeframe combos by edge vs hold ===")
    top = fmt.sort_values("edge_vs_hold", ascending=False).head(12)
    print(top.to_string(index=False))

    print("\n=== Bottom 5 (worst) ===")
    print(fmt.sort_values("edge_vs_hold").head(5).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    ap.add_argument("--fee", type=float, default=0.006)
    ap.add_argument("--slip", type=float, default=0.0005)
    args = ap.parse_args()

    df = scan(args.fast, args.slow, args.fee, args.slip)
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, f"scan_sma{args.fast}_{args.slow}.csv")
    df.to_csv(out, index=False)
    report(df)
    print(f"\nFull results -> {out}")


if __name__ == "__main__":
    main()
