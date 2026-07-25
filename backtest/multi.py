"""
Multi-signal "scoring" strategy: enter only when trend, momentum, and
volume all agree; exit when the trend breaks or momentum dies.

Signals (on 1h candles resampled from our 5-min data):
  trend    : SMA(fast) > SMA(slow)
  momentum : RSI(14) above entry threshold
  volume   : volume above its 20-bar average

Entry:  all three true              (high conviction, rare)
Exit:   trend false OR RSI < exit   (hysteresis - don't churn on wiggles)

Reports train (first 70%) and test (last 30%) separately, plus the plain
SMA crossover on the same splits as a baseline. The test column is the
one that matters - it's data the rules never saw.

Usage:
    python backtest/multi.py --fee 0.006
"""
import argparse, glob, os
import numpy as np
import pandas as pd
import engine
from scanner import resample, CANDLES, RESULTS


def rsi(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up = up.ewm(alpha=1 / period, min_periods=period).mean()
    avg_down = down.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_up / avg_down
    return 100 - 100 / (1 + rs)


def build_position(df, fast=20, slow=50, rsi_entry=52, rsi_exit=45, vol_len=20):
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    df["rsi"] = rsi(df["close"])
    df["vol_avg"] = df["volume"].rolling(vol_len).mean()

    trend = (df["sma_fast"] > df["sma_slow"]).to_numpy()
    mom = (df["rsi"] > rsi_entry).to_numpy()
    vol_ok = (df["volume"] > df["vol_avg"]).to_numpy()
    r = df["rsi"].to_numpy()

    sig = np.zeros(len(df), dtype=int)
    in_pos = False
    for i in range(len(df)):
        if not in_pos and trend[i] and mom[i] and vol_ok[i]:
            in_pos = True            # all three agree -> enter
        elif in_pos and (not trend[i] or r[i] < rsi_exit):
            in_pos = False           # trend broken or momentum dead -> exit
        sig[i] = 1 if in_pos else 0

    df["signal"] = sig
    df["position"] = df["signal"].shift(1).fillna(0).astype(int)
    return df


def split_run(df, fee, slip, cut_frac=0.7):
    cut = int(len(df) * cut_frac)
    train = df.iloc[:cut].reset_index(drop=True)
    test = df.iloc[cut:].reset_index(drop=True)
    res_tr = engine.run_backtest(train, fee_rate=fee, slip_rate=slip)
    res_te = engine.run_backtest(test, fee_rate=fee, slip_rate=slip)
    return res_tr, res_te


def edge(res):
    return res["total_return"] - res["buy_hold_return"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fee", type=float, default=0.006)
    ap.add_argument("--slip", type=float, default=0.0005)
    args = ap.parse_args()

    rows = []
    for path in sorted(glob.glob(os.path.join(CANDLES, "*_300s.csv"))):
        pair = os.path.basename(path).replace("_300s.csv", "")
        base = resample(engine.load_candles(path), "1h")

        m = build_position(base.copy())
        m_tr, m_te = split_run(m, args.fee, args.slip)

        s = engine.add_signals(base.copy(), 20, 50)
        s_tr, s_te = split_run(s, args.fee, args.slip)

        rows.append({
            "pair": pair,
            "multi_train_edge": edge(m_tr) * 100,
            "multi_test_edge": edge(m_te) * 100,
            "multi_test_trades": m_te["n_trades"],
            "sma_test_edge": edge(s_te) * 100,
            "test_buy_hold": m_te["buy_hold_return"] * 100,
        })

    df = pd.DataFrame(rows).sort_values("multi_test_edge", ascending=False)
    pd.set_option("display.width", 130)
    print(df.round(1).to_string(index=False))

    print("\n=== Averages across all pairs ===")
    print(f"Multi-signal test edge: {df['multi_test_edge'].mean():+.1f}%")
    print(f"Plain SMA   test edge: {df['sma_test_edge'].mean():+.1f}%")
    print(f"Avg test trades (multi): {df['multi_test_trades'].mean():.1f}")
    beats = (df["multi_test_edge"] > df["sma_test_edge"]).sum()
    pos = (df["multi_test_edge"] > 0).sum()
    print(f"Multi beats SMA on {beats}/{len(df)} pairs; "
          f"positive test edge on {pos}/{len(df)}")

    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, "multi_vs_sma.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
