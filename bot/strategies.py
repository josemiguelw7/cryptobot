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


def ema_series(closes, n):
    """EMA series seeded with SMA of the first n bars. Returned list is
    aligned to closes[n-1:]."""
    if len(closes) < n:
        return []
    k = 2 / (n + 1)
    out = [sum(closes[:n]) / n]
    for c in closes[n:]:
        out.append(c * k + out[-1] * (1 - k))
    return out


def ret_stdev(closes, n):
    """Stdev of the last n bar-to-bar returns."""
    if len(closes) < n + 1:
        return None
    rets = [closes[i] / closes[i - 1] - 1 for i in range(-n, 0)]
    mu = sum(rets) / n
    return (sum((r - mu) ** 2 for r in rets) / n) ** 0.5


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


class MACDTrend(Strategy):
    """Hold while MACD line is above its signal line. The classic
    medium-speed momentum gauge."""
    def __init__(self, f=12, s=26, sig=9):
        self.f, self.s, self.sig = f, s, sig
        self.name = f"macd_{f}_{s}"
        self.warmup = s + sig + 5
    def step(self, closes, ctx):
        ef = ema_series(closes, self.f)
        es = ema_series(closes, self.s)
        if not ef or not es:
            return 0.0
        L = min(len(ef), len(es))
        macd = [a - b for a, b in zip(ef[-L:], es[-L:])]
        sig = ema_series(macd, self.sig)
        if not sig:
            return 0.0
        return 1.0 if macd[-1] > sig[-1] else 0.0


class Bollinger(Strategy):
    """Mean reversion: buy below the lower band (mid - k*sd), exit at
    the middle band, hold in between."""
    def __init__(self, n=20, k=2.0):
        self.n, self.k = n, k
        self.name = f"boll_{n}"
        self.warmup = n + 1
    def step(self, closes, ctx):
        mid = sma(closes, self.n)
        if mid is None:
            return 0.0
        w = closes[-self.n:]
        mu = sum(w) / self.n
        sd = (sum((c - mu) ** 2 for c in w) / self.n) ** 0.5
        px, held = closes[-1], ctx.get("weight", 0) > 0
        if px < mid - self.k * sd:
            return 1.0
        if px >= mid:
            return 0.0
        return 1.0 if held else 0.0


class RSIRegime(Strategy):
    """'Read the market first': the RSI dip-buyer, but ONLY allowed to
    act while price is above its 200-day SMA (uptrend regime). In a
    downtrend it stays flat no matter how oversold. Tests whether the
    regime filter rescues plain rsi_14."""
    def __init__(self, n=14, lo=30, hi=55, regime=200):
        self.n, self.lo, self.hi, self.rg = n, lo, hi, regime
        self.name = f"rsi_regime"
        self.warmup = regime + 1
    def step(self, closes, ctx):
        m = sma(closes, self.rg)
        if m is None or closes[-1] < m:
            return 0.0                     # wrong regime: stand down
        r = rsi(closes, self.n)
        if r is None:
            return 0.0
        held = ctx.get("weight", 0) > 0
        if r < self.lo:
            return 1.0
        if r > self.hi:
            return 0.0
        return 1.0 if held else 0.0


class TSMom(Strategy):
    """Time-series momentum: hold while the trailing n-day return is
    positive. Moskowitz/Ooi/Pedersen's classic, one line of logic."""
    def __init__(self, n=90):
        self.n = n
        self.name = f"tsmom_{n}"
        self.warmup = n + 1
    def step(self, closes, ctx):
        if len(closes) < self.n + 1:
            return 0.0
        return 1.0 if closes[-1] > closes[-self.n - 1] else 0.0


class Donchian2(Strategy):
    """Turtle-style asymmetric channel: enter on an n_in-day high,
    exit on an n_out-day low. Slower entry, quicker exit."""
    def __init__(self, n_in=55, n_out=20):
        self.n_in, self.n_out = n_in, n_out
        self.name = f"donch_{n_in}_{n_out}"
        self.warmup = n_in + 1
    def step(self, closes, ctx):
        if len(closes) < self.n_in + 1:
            return 0.0
        px = closes[-1]
        held = ctx.get("weight", 0) > 0
        if px >= max(closes[-self.n_in - 1:-1]):
            return 1.0
        if px <= min(closes[-self.n_out - 1:-1]):
            return 0.0
        return 1.0 if held else 0.0


class EMACross(Strategy):
    """Fast EMA over slow EMA. The archetypal short-term trader's
    signal — in the screen mostly to measure what its turnover costs."""
    def __init__(self, f=9, s=21):
        self.f, self.s = f, s
        self.name = f"ema_{f}_{s}"
        self.warmup = s + 5
    def step(self, closes, ctx):
        ef, es = ema_series(closes, self.f), ema_series(closes, self.s)
        if not ef or not es:
            return 0.0
        return 1.0 if ef[-1] > es[-1] else 0.0


class NearHigh(Strategy):
    """52-week-high proximity: hold while price is within band of its
    n-day high. Momentum anomaly classic (George & Hwang)."""
    def __init__(self, n=250, band=0.20):
        self.n, self.band = n, band
        self.name = f"near_hi_{n}"
        self.warmup = n
    def step(self, closes, ctx):
        if len(closes) < self.n:
            return 0.0
        hi = max(closes[-self.n:])
        return 1.0 if closes[-1] >= hi * (1 - self.band) else 0.0


class CalmRegime(Strategy):
    """Pure regime reader: hold ONLY when recent volatility (n_fast) is
    below the longer baseline (n_slow). No price signal at all — tests
    whether 'trade the calm, sit out the storm' has value by itself."""
    def __init__(self, n_fast=30, n_slow=100):
        self.nf, self.ns = n_fast, n_slow
        self.name = f"calm_{n_fast}_{n_slow}"
        self.warmup = n_slow + 1
    def step(self, closes, ctx):
        vf = ret_stdev(closes, self.nf)
        vs = ret_stdev(closes, self.ns)
        if vf is None or vs is None:
            return 0.0
        return 1.0 if vf < vs else 0.0


class VolBreak(Strategy):
    """Volatility-compression breakout ('squeeze'). Enter when recent
    realized vol (n_fast) sits below the longer baseline (n_slow) AND
    price makes a new n_fast-bar high — quiet coil, then expansion.
    Exit on an n_fast-bar low. Path-dependent via ctx. Written for the
    hourly seed squad; bar-length agnostic like every class here."""
    def __init__(self, n_fast=24, n_slow=96):
        self.nf, self.ns = n_fast, n_slow
        self.name = f"volbrk_{n_fast}_{n_slow}"
        self.warmup = n_slow + 1
    def step(self, closes, ctx):
        if len(closes) < self.ns + 1:
            return 0.0
        px = closes[-1]
        held = ctx.get("weight", 0) > 0
        window = closes[-self.nf - 1:-1]     # prior n_fast bars, excl. now
        hi, lo = max(window), min(window)
        if held:
            return 0.0 if px <= lo else 1.0
        vf = ret_stdev(closes, self.nf)
        vs = ret_stdev(closes, self.ns)
        if vf is None or vs is None:
            return 0.0
        return 1.0 if (vf < vs and px >= hi) else 0.0


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
    # research wave 2 (2026-07-31) — screened, none examined yet:
    "macd_12_26":  MACDTrend(),
    "boll_20":     Bollinger(),
    "rsi_regime":  RSIRegime(),
    "tsmom_90":    TSMom(90),
    "donch_55_20": Donchian2(55, 20),
    "ema_9_21":    EMACross(9, 21),
    "near_hi_250": NearHigh(250, 0.20),
    "calm_30_100": CalmRegime(30, 100),
}


def get(name):
    if name not in REGISTRY:
        raise KeyError(f"unknown strategy {name!r}; "
                       f"known: {sorted(REGISTRY)}")
    return REGISTRY[name]
