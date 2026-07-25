"""
Walk-forward tester.

For each pair: slide a window across a year of 1h candles.
  train = 90 days -> pick whichever strategy config had the best edge
  test  = next 30 days -> grade that pick on unseen data
  slide forward 30 days, repeat.

Stitching all test windows together simulates what a live bot that
re-tunes monthly would actually have experienced. No test data is ever
used to choose anything.

Configs in the menu: three SMA crossovers + the multi-signal model.

Usage:
    python backtest/walkforward.py --fee 0.006
"""
import argparse, glob, os
from collections import Counter
import numpy as np
import pandas as pd
import engine
import multi as multi_mod
from scanner import CANDLES, RESULTS

TRAIN_BARS = 24 * 90   # 90 days of 1h candles
TEST_BARS = 24 * 30    # 30 days


def build_configs(df):
    """{name: full-history position array}. Indicators only look backward,
    so computing on full history then slicing leaks nothing."""
    out = {}
    for fast, slow in [(10, 30), (20, 50), (30, 100)]:
        d = engine.add_signals(df.copy(), fast, slow)
        out[f"sma_{fast}_{slow}"] = d["position"].to_numpy()
    d = multi_mod.build_position(df.copy())
    out["multi"] = d["position"].to_numpy()
    return out


def run_slice(opens, closes, pos, a, b, fee, slip):
    sl = pd.DataFrame({"open": opens[a:b], "close": closes[a:b],
                       "position": pos[a:b]})
    return engine.run_backtest(sl, fee_rate=fee, slip_rate=slip)


def walk_forward(path, fee, slip):
    df = engine.load_candles(path)
    opens = df["open"].to_numpy(float)
    closes = df["close"].to_numpy(float)
    poss = build_configs(df)

    windows, start = [], 0
    while start + TRAIN_BARS + TEST_BARS <= len(df):
        a, b = start, start + TRAIN_BARS
        c = b + TEST_BARS

        best_name, best_edge = None, -np.inf
        for name, pos in poss.items():
            r = run_slice(opens, closes, pos, a, b, fee, slip)
            e = r["total_return"] - r["buy_hold_return"]
            if e > best_edge:
                best_edge, best_name = e, name

        rt = run_slice(opens, closes, poss[best_name], b, c, fee, slip)
        windows.append({
            "picked": best_name,
            "test_return": rt["total_return"],
            "test_bh": rt["buy_hold_return"],
            "trades": rt["n_trades"],
        })
        start += TEST_BARS
    return windows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fee", type=float, default=0.006)
    ap.add_argument("--slip", type=float, default=0.0005)
    args = ap.parse_args()

    rows, all_picks, skipped = [], Counter(), []
    for path in sorted(glob.glob(os.path.join(CANDLES, "*_3600s.csv"))):
        pair = os.path.basename(path).replace("_3600s.csv", "")
        wins = walk_forward(path, args.fee, args.slip)
        if not wins:
            skipped.append(pair)  # not enough history for even one window
            continue
        strat = np.prod([1 + w["test_return"] for w in wins]) - 1
        bh = np.prod([1 + w["test_bh"] for w in wins]) - 1
        pos_windows = sum(
            1 for w in wins if w["test_return"] > w["test_bh"])
        picks = Counter(w["picked"] for w in wins)
        all_picks.update(picks)
        rows.append({
            "pair": pair,
            "windows": len(wins),
            "strat_total": strat * 100,
            "bh_total": bh * 100,
            "edge": (strat - bh) * 100,
            "windows_beat_bh": f"{pos_windows}/{len(wins)}",
            "trades": sum(w["trades"] for w in wins),
            "top_pick": picks.most_common(1)[0][0],
        })

    df = pd.DataFrame(rows).sort_values("edge", ascending=False)
    pd.set_option("display.width", 140)
    print(df.round(1).to_string(index=False))
    print(f"\nSkipped (too little history): {skipped}")
    print(f"\nAvg edge vs hold: {df['edge'].mean():+.1f}% | "
          f"pairs with positive edge: {(df['edge'] > 0).sum()}/{len(df)}")
    print(f"Config picks across all windows: {dict(all_picks)}")

    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, "walkforward.csv")
    df.to_csv(out, index=False)
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
