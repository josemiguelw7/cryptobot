"""
SHARED STRATEGY MODULE — the single source of truth for strategy logic.

Both the entrance exam (backtest/exam.py) and the live league
(bot/league.py) import strategies from here. The strategy that passes
the exam is byte-for-byte the strategy that trades forward — no
duplicated logic that can drift apart. (Build plan W1.1.)

A Strategy maps price history -> a target weight in [0, 1] for a single
asset (0 = all cash, 1 = fully invested). Strategies may be stateful
(they see their own entry price via `ctx`) so stop-losses and
volatility sizing are expressible. (Build plan W1.2.)

Contract:
  name           unique, permanent (one exam per name, ever)
  warmup         bars of history needed before the first real signal
  pairs          declared universe; None means "any single pair the
                 caller drives" (single-asset strategies)
  step(closes, ctx) -> float in [0,1]
       closes : list of completed daily closes, oldest..newest,
                the LAST element being the most recent COMPLETED bar
       ctx    : dict the caller persists between calls for this
                strategy+pair. Keys the engine maintains:
                  'weight'      current held weight (0..1)
                  'entry_price' close when the position was opened
"""
from __future__ import annotations


def sma(xs, n):
    return sum(xs[-n:]) / n if len(xs) >= n else None


def realized_vol(closes, n):
    """Std dev of the last n daily returns."""
    if len(closes) < n + 1:
        return None
    rets = [closes[i] / closes[i - 1] - 1 for i in range(-n, 0)]
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / len(rets)
    return var ** 0.5


def rsi(closes, n):
    """Simple RSI over the last n bar-to-bar changes. 0..100."""
    if len(closes) < n + 1:
        return None
    gains = losses = 0.0
    for i in range(-n, 0):
        ch = closes[i] - closes[i - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch
    avg_gain, avg_loss = gains / n, losses / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


class Strategy:
    name = "base"
    warmup = 1
    pairs = None

    def step(self, closes, ctx):
        raise NotImplementedError


class Hold(Strategy):
    name, warmup = "hold", 1
    def step(self, closes, ctx):
        return 1.0


class Trend(Strategy):
    """Hold while close > SMA(n), else cash. Signal on completed close."""
    def __init__(self, n):
        self.n = n
        self.name = f"trend_{n}"
        self.warmup = n
    def step(self, closes, ctx):
        m = sma(closes, self.n)
        if m is None:
            return 0.0
        return 1.0 if closes[-1] > m else 0.0


class TrendStop(Strategy):
    """Trend entry + hard stop-loss. Path-dependent: once in, exit if
    price falls stop_pct below the ENTRY price, regardless of the MA.
    Re-entry only on a fresh trend signal. Attacks tail windows the
    plain trend filters failed on. (Build plan W4.1.)"""
    def __init__(self, n, stop_pct):
        self.n = n
        self.stop = stop_pct
        self.name = f"t{n}s{int(stop_pct*100)}"
        self.warmup = n
    def step(self, closes, ctx):
        px = closes[-1]
        held = ctx.get("weight", 0) > 0
        if held:
            entry = ctx.get("entry_price", px)
            if px <= entry * (1 - self.stop):   # stop hit -> cash
                return 0.0
        m = sma(closes, self.n)
        if m is None:
            return 0.0
        return 1.0 if px > m else 0.0


class VolTarget(Strategy):
    """Volatility-targeted sizing on top of a trend filter. Weight =
    target_vol / realized_vol, capped at 1, zero when below the MA.
    Shrinks exposure when the coin gets wild -> directly attacks the
    −20% window rule. (Build plan W4.1.)"""
    def __init__(self, n, target_vol=0.03, vol_window=20):
        self.n = n
        self.tv = target_vol
        self.vw = vol_window
        self.name = f"voltgt_{n}"
        self.warmup = max(n, vol_window + 1)
    def step(self, closes, ctx):
        m = sma(closes, self.n)
        if m is None or closes[-1] <= m:
            return 0.0
        rv = realized_vol(closes, self.vw)
        if not rv:
            return 0.0
        return max(0.0, min(1.0, self.tv / rv))


class Cross(Strategy):
    """Fast trend: hold while SMA(fast) > SMA(slow), else cash. Flips on
    medium-term momentum shifts — far more active than one long MA."""
    def __init__(self, fast, slow):
        self.f, self.s = fast, slow
        self.name = f"cross_{fast}_{slow}"
        self.warmup = slow
    def step(self, closes, ctx):
        mf, ms = sma(closes, self.f), sma(closes, self.s)
        if mf is None or ms is None:
            return 0.0
        return 1.0 if mf > ms else 0.0


class Breakout(Strategy):
    """Donchian channel. Enter on a new n-day high; exit to cash on a new
    n-day low; hold in between. Channel uses the n bars BEFORE today, so
    the breakout is real, not self-referential. Path-dependent via ctx."""
    def __init__(self, n):
        self.n = n
        self.name = f"donch_{n}"
        self.warmup = n + 1
    def step(self, closes, ctx):
        if len(closes) < self.n + 1:
            return 0.0
        px = closes[-1]
        window = closes[-self.n - 1:-1]      # prior n bars, excl. today
        hi, lo = max(window), min(window)
        held = ctx.get("weight", 0) > 0
        if px >= hi:
            return 1.0
        if px <= lo:
            return 0.0
        return 1.0 if held else 0.0


class RSIRevert(Strategy):
    """Mean reversion. Buy when RSI(n) < lo (oversold); exit when RSI(n)
    > hi (recovered); hold between. Counter-trend — profits from the
    whipsaws that punish trend-followers, and trades often."""
    def __init__(self, n=14, lo=30, hi=55):
        self.n, self.lo, self.hi = n, lo, hi
        self.name = f"rsi_{n}"
        self.warmup = n + 1
    def step(self, closes, ctx):
        r = rsi(closes, self.n)
        if r is None:
            return 0.0
        held = ctx.get("weight", 0) > 0
        if r < self.lo:
            return 1.0
        if r > self.hi:
            return 0.0
        return 1.0 if held else 0.0


# ---------------------------------------------------------------- registry
# Every examinable candidate, by permanent name. exam.py reads this;
# league.py builds live members from the same classes.

REGISTRY = {
    "hold":      Hold(),
    "trend_150": Trend(150),
    "trend_200": Trend(200),
    "trend_250": Trend(250),
    # risk-managed candidates (W4.1) — not yet examined:
    "t200s10":   TrendStop(200, 0.10),
    "t150s10":   TrendStop(150, 0.10),
    "t200s15":   TrendStop(200, 0.15),
    "voltgt_200": VolTarget(200),
    "voltgt_150": VolTarget(150),
    # active daily candidates — the "more active" push:
    "cross_20_50": Cross(20, 50),
    "donch_20":    Breakout(20),
    "rsi_14":      RSIRevert(14),
}


def get(name):
    if name not in REGISTRY:
        raise KeyError(f"unknown strategy {name!r}; "
                       f"known: {sorted(REGISTRY)}")
    return REGISTRY[name]
