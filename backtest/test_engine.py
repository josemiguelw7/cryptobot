"""
Unit tests for the backtest engine - test the tester itself.
Includes a deliberate lookahead 'canary': we build a cheating engine
and assert that it outperforms the honest one, proving the honest
engine's next-bar execution actually prevents lookahead.

Run:  python backtest/test_engine.py
"""
import numpy as np
import pandas as pd
import engine


def test_fee_math():
    # Flat price, zero slippage: one round trip must cost exactly
    # start * (1-fee)^2. If not, fee accounting is broken.
    df = pd.DataFrame({"open": [100.0] * 10, "close": [100.0] * 10,
                       "position": [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]})
    res = engine.run_backtest(df, fee_rate=0.006, slip_rate=0.0)
    expected = 10_000 * (1 - 0.006) ** 2
    assert abs(res["final_equity"] - expected) < 1e-6, res["final_equity"]
    print("PASS  fee math exact on known round trip")


def test_position_is_shifted():
    # position must equal signal shifted one bar (act on NEXT open)
    df = pd.DataFrame({"close": np.linspace(100, 300, 200),
                       "open": np.linspace(100, 300, 200)})
    out = engine.add_signals(df.copy(), 5, 20)
    a = out["position"].to_numpy()[1:]
    b = out["signal"].to_numpy()[:-1]
    assert (a == b).all()
    print("PASS  position is signal shifted by one bar")


def test_lookahead_canary():
    # Price jumps +10% at bar 5. Signal fires at bar 4 (the bar before).
    # Honest engine (shifted) executes at bar 5's open - AFTER the jump -
    # and earns nothing. A cheating engine (unshifted, same-bar fill)
    # buys at bar 4 pre-jump and profits. If the cheat does NOT beat the
    # honest engine, our anti-lookahead protection isn't real.
    px = [100.0] * 5 + [110.0] * 5
    sig = [0, 0, 0, 0, 1, 1, 0, 0, 0, 0]
    base = pd.DataFrame({"open": px, "close": px})

    honest = base.copy()
    honest["position"] = pd.Series(sig).shift(1).fillna(0).astype(int)
    cheat = base.copy()
    cheat["position"] = sig

    rh = engine.run_backtest(honest, fee_rate=0.0, slip_rate=0.0)
    rc = engine.run_backtest(cheat, fee_rate=0.0, slip_rate=0.0)

    assert abs(rh["final_equity"] - 10_000) < 1e-6, rh["final_equity"]
    assert rc["final_equity"] > rh["final_equity"] + 500
    print("PASS  lookahead canary: honest engine misses same-bar jump, "
          "cheat captures it")


if __name__ == "__main__":
    test_fee_math()
    test_position_is_shifted()
    test_lookahead_canary()
    print("\nAll engine tests passed.")
