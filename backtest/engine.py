"""
Long-only moving-average crossover backtester with fee + slippage modeling.

Signals are computed on candle close; trades execute at the NEXT candle's
open (no lookahead bias). All-in / all-out position for now - proper
position sizing comes later.

Usage:
    python backtest/engine.py data/candles/BTC-USD_300s.csv --fast 20 --slow 50
"""
import argparse
import numpy as np
import pandas as pd


def load_candles(path):
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.sort_values("timestamp").reset_index(drop=True)


def add_signals(df, fast, slow):
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)
    # shift(1): we only know a signal AFTER the candle closes, so we act
    # on the next candle's open. Skipping this shift is the classic
    # lookahead bug that makes bad strategies look brilliant in tests.
    df["position"] = df["signal"].shift(1).fillna(0).astype(int)
    return df


def run_backtest(df, fee_rate=0.006, slip_rate=0.0005, start_cash=10_000.0):
    opens = df["open"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)
    pos = df["position"].to_numpy()

    cash, units = start_cash, 0.0
    fees_paid, entry_cost = 0.0, None
    trades = []  # (cost_in, proceeds_out) per completed round trip
    equity = np.zeros(len(df))

    for i in range(len(df)):
        prev = pos[i - 1] if i > 0 else 0
        if pos[i] == 1 and prev == 0 and cash > 0:
            # BUY at this candle's open, paying slippage + fee
            fee = cash * fee_rate
            units = (cash - fee) / (opens[i] * (1 + slip_rate))
            fees_paid += fee
            entry_cost, cash = cash, 0.0
        elif pos[i] == 0 and prev == 1 and units > 0:
            # SELL at this candle's open
            gross = units * opens[i] * (1 - slip_rate)
            fee = gross * fee_rate
            cash = gross - fee
            fees_paid += fee
            trades.append((entry_cost, cash))
            units = 0.0
        equity[i] = cash + units * closes[i]

    run_max = np.maximum.accumulate(equity)
    drawdown = equity / run_max - 1.0
    wins = sum(1 for cost, out in trades if out > cost)

    return {
        "start_cash": start_cash,
        "final_equity": equity[-1],
        "total_return": equity[-1] / start_cash - 1,
        "buy_hold_return": closes[-1] / closes[0] - 1,
        "n_trades": len(trades),
        "win_rate": wins / len(trades) if trades else float("nan"),
        "fees_paid": fees_paid,
        "max_drawdown": drawdown.min(),
    }


def print_report(res, label=""):
    print(f"\n=== Backtest {label} ===")
    print(f"Start cash:        ${res['start_cash']:,.2f}")
    print(f"Final equity:      ${res['final_equity']:,.2f}")
    print(f"Strategy return:   {res['total_return']:+.2%}  (net of fees)")
    print(f"Buy & hold:        {res['buy_hold_return']:+.2%}  (no fees)")
    print(f"Round trips:       {res['n_trades']}")
    print(f"Win rate:          {res['win_rate']:.1%}")
    print(f"Fees paid:         ${res['fees_paid']:,.2f}")
    print(f"Max drawdown:      {res['max_drawdown']:.1%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    ap.add_argument("--fee", type=float, default=0.006,
                    help="per-side fee rate, e.g. 0.006 = 0.6%%")
    ap.add_argument("--slip", type=float, default=0.0005,
                    help="per-side slippage rate")
    ap.add_argument("--cash", type=float, default=10_000.0)
    args = ap.parse_args()

    df = add_signals(load_candles(args.csv_path), args.fast, args.slow)
    res = run_backtest(df, args.fee, args.slip, args.cash)
    name = args.csv_path.split("/")[-1]
    print_report(res, label=f"{name} | SMA {args.fast}/{args.slow} | "
                            f"fee {args.fee:.2%}/side")


if __name__ == "__main__":
    main()
