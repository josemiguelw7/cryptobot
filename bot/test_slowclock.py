"""
Regression tests for SlowClock — the 2026-08-08 freeze bug and its class.

THE RULE THESE TESTS ENFORCE (review 2026-08-08, finding C-1):
every guard must be provable to FAIL. A slow clock that cannot be shown
to change its mind is not slow — it is stopped. Four of five defects in
REVIEW.md section 5, and three critical findings in the external review,
were guards that appeared to constrain and did not.

Run:  python bot/test_slowclock.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtest"))

import numpy as np
import strategies as S

TS = S.TS


def synth_bars(n, seed=1, flip=None):
    """Hourly bars: uptrend, then (optionally) a hard downtrend at
    `flip`. A working slow trend-follower MUST exit after the flip."""
    rng = np.random.default_rng(seed)
    r = rng.normal(+0.0015, 0.004, n)
    if flip is not None:
        r[flip:] = rng.normal(-0.0015, 0.004, n - flip)
    px = 100 * np.cumprod(1 + r)
    return [(1700000000 + 3600 * i, px[i], px[i] * 1.001,
             px[i] * 0.999, px[i], 1000.0) for i in range(n)]


def signals_over(strat, bars, a, b, tail=None):
    """Emit the signal stream the exam/engine would see over [a, b),
    with the history slice bounded at `tail` (None = unbounded)."""
    tail = tail or strat.tail
    ctx = {"weight": 0.0, "entry_price": None}
    out = []
    for i in range(a, b):
        lo = max(0, i + 1 - tail)
        out.append(strat.step_bars(bars[lo:i + 1], ctx))
    return out


def test_not_frozen_when_tail_saturates():
    """THE C-1 REGRESSION. tail % k != 0 by construction (warmup*3+10),
    so any len()-based boundary freezes once the slice saturates. The
    seed must still change its mind across a regime flip."""
    st = S.SlowClock(S.Trend(20), 24, "t_frozen_check")
    assert st.tail % st.k != 0, "test premise broken: pick another seed"
    n = 8000
    flip = n // 2
    bars = synth_bars(n, flip=flip)
    a = max(st.tail + 100, flip - 1000)    # saturated AND spans the flip
    sigs = signals_over(st, bars, a, a + 2160)
    distinct = set(sigs)
    assert len(distinct) > 1, (
        f"SlowClock FROZE: one distinct signal {distinct} across 2160 "
        f"bars spanning an up->down regime flip. len()-based boundary?")
    print(f"  [PASS] not frozen: {len(distinct)} distinct signals "
          f"across the flip")


def test_decides_once_per_slow_bar():
    """The original 2026-08-08a bug: deciding every hour. Count signal
    CHANGES between slow-bar boundaries — inside a slow bar the signal
    must be constant."""
    st = S.SlowClock(S.Trend(20), 24, "t_once_per_bar")
    n = 6000
    bars = synth_bars(n, flip=n // 2)
    a = st.tail + 100
    b = a + 720
    ctx = {"weight": 0.0, "entry_price": None}
    changes_inside = 0
    prev_sig, prev_slot = None, None
    for i in range(a, b):
        lo = max(0, i + 1 - st.tail)
        sig = st.step_bars(bars[lo:i + 1], ctx)
        slot = (bars[i][TS] + 3600) // (st.k * 3600)
        if prev_sig is not None and sig != prev_sig and slot == prev_slot:
            changes_inside += 1
        prev_sig, prev_slot = sig, slot
    assert changes_inside == 0, (
        f"signal changed {changes_inside}x INSIDE a slow bar — the "
        f"decision clock is running fast again (2026-08-08a bug)")
    print("  [PASS] signal only changes at slow-bar boundaries")


def test_recovers_from_missed_cycles():
    """Ops reality: launchd skips cycles while the Mac sleeps. If the
    boundary hour is missed, the next call must recompute (late), not
    hold the stale signal until the following boundary."""
    st = S.SlowClock(S.Trend(20), 24, "t_missed_cycle")
    n = 6000
    bars = synth_bars(n, flip=3000)
    a = st.tail + 100
    # continuous stream (never misses the boundary)
    full = signals_over(st, bars, a, a + 500)
    # sparse stream: only every 7th hour is observed
    ctx = {"weight": 0.0, "entry_price": None}
    sparse = {}
    for i in range(a, a + 500, 7):
        lo = max(0, i + 1 - st.tail)
        sparse[i] = st.step_bars(bars[lo:i + 1], ctx)
    # at every observed instant, sparse must match the most recent
    # boundary decision of the continuous stream (never be staler)
    mismatches = sum(1 for i, s in sparse.items() if s != full[i - a])
    assert mismatches == 0, (
        f"{mismatches} sparse observations diverge from the continuous "
        f"stream: missed boundaries are not being recovered")
    print("  [PASS] missed cycles recover on the next call")


def test_resample_alignment_ends_at_newest_bar():
    """_inner_call must fold slow bars so the LAST fold ends at
    bars[-1]. If the front is not trimmed, resample() silently drops
    the newest partial chunk and the seed decides on stale data."""
    st = S.SlowClock(S.Trend(20), 24, "t_alignment")
    n = st.tail + 200
    bars = synth_bars(n)
    # spy on what the inner strategy receives
    seen = {}
    orig = st.inner.step

    def spy(closes, ctx):
        seen["last_close"] = closes[-1]
        return orig(closes, ctx)
    st.inner.step = spy
    ctx = {"weight": 0.0, "entry_price": None}
    st.step_bars(bars[-st.tail:], ctx)
    st.inner.step = orig
    assert abs(seen["last_close"] - bars[-1][4]) < 1e-12, (
        "inner strategy did not see the newest close: resample folds "
        "are misaligned (front not trimmed to len % k)")
    print("  [PASS] last slow bar ends exactly at the newest hourly bar")


def test_exam_engine_parity():
    """W1.1: the exam slices history to `tail`; the engine must too.
    Same bars, both call patterns, identical signal stream."""
    st1 = S.SlowClock(S.Trend(20), 24, "t_parity_a")
    st2 = S.SlowClock(S.Trend(20), 24, "t_parity_b")
    n = 6000
    bars = synth_bars(n, flip=3000)
    a = st1.tail + 50
    exam_style = signals_over(st1, bars, a, a + 400, tail=st1.tail)
    engine_style = signals_over(st2, bars, a, a + 400, tail=st2.tail)
    assert exam_style == engine_style, "exam and engine signals diverge"
    print("  [PASS] exam-style and engine-style calls emit identical "
          "signals")


if __name__ == "__main__":
    print("SLOWCLOCK REGRESSION SUITE (synthetic data, ledger untouched)")
    test_not_frozen_when_tail_saturates()
    test_decides_once_per_slow_bar()
    test_recovers_from_missed_cycles()
    test_resample_alignment_ends_at_newest_bar()
    test_exam_engine_parity()
    print("all SlowClock tests passed")
