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

    def conviction_closes(self, closes, ctx):
        """Entry-strength for allocation ORDERING only (E2.2). None =
        no opinion -> engine falls back to the signal weight. Never
        consulted by the exam (exams grade one pair at a time), so
        overriding it cannot change any verdict."""
        return None


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


class Bracket(Strategy):
    """Trend entry + full bracket: hard stop below entry AND fixed
    take-profit above it. Exists to test the owner's 2026-08-03
    hypothesis ("lock gains at +X%") against the no-TP siblings.
    NOTE: the exit_autopsy of 2026-08-03 (12 trades, max MFE +1.27%)
    found nothing for a TP to harvest at hourly horizons — examine only
    if later MFE data ever reaches TP territory. Path-dependent via ctx
    like TrendStop; bar-length agnostic."""
    def __init__(self, n, stop_pct, tp_pct):
        self.n, self.stop, self.tp = n, stop_pct, tp_pct
        self.name = f"brk{n}s{int(stop_pct*100)}t{int(tp_pct*100)}"
        self.warmup = n
    def step(self, closes, ctx):
        px = closes[-1]
        if ctx.get("weight", 0) > 0:
            entry = ctx.get("entry_price") or px
            if px <= entry * (1 - self.stop):    # stop -> cash
                return 0.0
            if px >= entry * (1 + self.tp):      # take-profit -> cash
                return 0.0
        m = sma(closes, self.n)
        if m is None:
            return 0.0
        return 1.0 if px > m else 0.0


class TrailStop(Strategy):
    """Trend entry + trailing stop: exit when price falls trail_pct
    from the HIGHEST close seen since entry. Ratchets gains without
    capping them — the middle ground between a fixed TP (caps winners)
    and a pure signal exit (gives back the peak). Peak lives in ctx
    ("trail_peak"), reset on entry; path-dependent, bar-agnostic."""
    def __init__(self, n, trail_pct):
        self.n, self.trail = n, trail_pct
        self.name = f"trail{n}x{int(trail_pct*100)}"
        self.warmup = n
    def step(self, closes, ctx):
        px = closes[-1]
        if ctx.get("weight", 0) > 0:
            peak = max(ctx.get("trail_peak") or px, px)
            ctx["trail_peak"] = peak
            if px <= peak * (1 - self.trail):    # trail hit -> cash
                ctx["trail_peak"] = None
                return 0.0
            return 1.0 if px > (sma(closes, self.n) or px) else 0.0
        ctx["trail_peak"] = None
        m = sma(closes, self.n)
        if m is None:
            return 0.0
        return 1.0 if px > m else 0.0


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
    # Bracket/TrailStop classes exist above but are deliberately NOT
    # instantiated here: a registry name is a one-shot exam ticket, and
    # per exit_study_2026-08-03 (max MFE +1.27% over 12 trades) there
    # is nothing for a TP to harvest yet. Naming any variant is a
    # Saturday-review decision (charter s10.1).
}


def get(name):
    if name not in REGISTRY:
        raise KeyError(f"unknown strategy {name!r}; "
                       f"known: {sorted(REGISTRY)}")
    return REGISTRY[name]


# --------------------------------------------------------------------
# PRE-ADOPTION AMENDMENT 2026-08-04 (docs/recert_2026-08-04.md):
# per-seed ENTRY CONVICTION for the ten wave-1 families. Ordering-layer
# only: step() signatures and signal logic above are untouched, so the
# seed that is examined is still byte-for-byte the seed that trades.
# Each returns a dimensionless "how strongly does MY OWN signal fire",
# replacing the shared biggest-mover tie-break that produced the
# 2026-08-04 clone books. None -> engine falls back to signal weight.
# --------------------------------------------------------------------

def _cv_trend(self, closes, ctx):
    m = sma(closes, self.n)
    return None if m is None else closes[-1] / m - 1
Trend.conviction_closes = _cv_trend

def _cv_cross(self, closes, ctx):
    mf, ms = sma(closes, self.f), sma(closes, self.s)
    return None if (mf is None or ms is None) else mf / ms - 1
Cross.conviction_closes = _cv_cross

def _cv_tsmom(self, closes, ctx):
    if len(closes) < self.n + 1:
        return None
    return closes[-1] / closes[-self.n - 1] - 1
TSMom.conviction_closes = _cv_tsmom

def _cv_macd(self, closes, ctx):
    ef, es = ema_series(closes, self.f), ema_series(closes, self.s)
    if not ef or not es:
        return None
    L = min(len(ef), len(es))
    macd = [a - b for a, b in zip(ef[-L:], es[-L:])]
    sg = ema_series(macd, self.sig)
    return None if not sg else (macd[-1] - sg[-1]) / closes[-1]
MACDTrend.conviction_closes = _cv_macd

def _cv_donch2(self, closes, ctx):
    if len(closes) < self.n_in + 1:
        return None
    hi = max(closes[-self.n_in - 1:-1])
    return closes[-1] / hi - 1
Donchian2.conviction_closes = _cv_donch2

def _cv_volbrk(self, closes, ctx):
    vf, vs = ret_stdev(closes, self.nf), ret_stdev(closes, self.ns)
    if vf is None or vs is None or vs == 0:
        return None
    return 1 - vf / vs
VolBreak.conviction_closes = _cv_volbrk

def _cv_rsireg(self, closes, ctx):
    r = rsi(closes, self.n)
    return None if r is None else (self.lo - r) / self.lo
RSIRegime.conviction_closes = _cv_rsireg

def _cv_boll(self, closes, ctx):
    mid = sma(closes, self.n)
    if mid is None:
        return None
    w = closes[-self.n:]
    mu = sum(w) / self.n
    sd = (sum((c - mu) ** 2 for c in w) / self.n) ** 0.5
    return None if sd == 0 else (mid - closes[-1]) / sd - self.k
Bollinger.conviction_closes = _cv_boll

def _cv_calm(self, closes, ctx):
    vf, vs = ret_stdev(closes, self.nf), ret_stdev(closes, self.ns)
    if vf is None or vs is None or vs == 0:
        return None
    return 1 - vf / vs
CalmRegime.conviction_closes = _cv_calm

def _cv_nearhi(self, closes, ctx):
    if len(closes) < self.n:
        return None
    hi = max(closes[-self.n:])
    return (closes[-1] / hi - (1 - self.band)) / self.band
NearHigh.conviction_closes = _cv_nearhi


# ====================================================================
# EPOCH 2 ADDITIONS (docs/seed_proposals_v2.md)
#
# Everything below is ADDITIVE. No class above this line is modified:
# epoch 1 seeds are immortal and immutable (charter s9.3), and their
# code must stay byte-for-byte what the exam graded.
#
# Three new optional contracts, all opt-in via class attributes:
#
#   wants_bars = True   -> engine calls step_bars(bars, ctx) instead of
#                          step(closes, ctx). bars is a list of tuples
#                          (ts, open, high, low, close, volume), oldest
#                          first, COMPLETED bars only.
#   wants_market = True -> ctx['market'] holds the market proxy's bars
#                          (BTC-USD for crypto, SPY for stocks).
#   cross_sectional     -> engine calls step_all(data, ctx) -> {pair: w}
#                          for strategies that compare names to each
#                          other rather than to their own past.
#
#   conviction(...)     -> float >= 0, "how much do I like this one".
#                          Used ONLY to order candidates when a bot has
#                          more signals than slots. It does NOT grant
#                          permission to trade: the s4.3 cost gate is
#                          unchanged and still signal-free. Default
#                          implementation returns the signal weight, so
#                          a strategy that does not override it keeps
#                          the old behaviour.
# ====================================================================

O, H, L, C, V, TS = 1, 2, 3, 4, 5, 0


def closes_of(bars):
    return [b[C] for b in bars]


def true_range(bars, i):
    prev = bars[i - 1][C] if i > 0 else bars[i][O]
    return max(bars[i][H] - bars[i][L], abs(bars[i][H] - prev),
               abs(bars[i][L] - prev))


def atr(bars, n):
    if len(bars) < n + 1:
        return None
    return sum(true_range(bars, i) for i in range(len(bars) - n,
                                                  len(bars))) / n


def vol_ratio(bars, fast, slow):
    """Recent volume vs its own baseline. 1.0 = normal, 2.0 = double."""
    if len(bars) < slow:
        return None
    f = sum(b[V] for b in bars[-fast:]) / fast
    s = sum(b[V] for b in bars[-slow:]) / slow
    return None if s <= 0 else f / s


def obv_series(bars):
    out, run = [], 0.0
    for i in range(1, len(bars)):
        if bars[i][C] > bars[i - 1][C]:
            run += bars[i][V]
        elif bars[i][C] < bars[i - 1][C]:
            run -= bars[i][V]
        out.append(run)
    return out


def body(bar):
    return abs(bar[C] - bar[O])


def upper_wick(bar):
    return bar[H] - max(bar[O], bar[C])


def lower_wick(bar):
    return min(bar[O], bar[C]) - bar[L]


def resample(bars, k):
    """Fold k consecutive bars into one. Used for the slow-clock family
    so the same maths runs on a genuinely different timescale."""
    out = []
    for i in range(0, len(bars) - k + 1, k):
        w = bars[i:i + k]
        out.append((w[0][TS], w[0][O], max(b[H] for b in w),
                    min(b[L] for b in w), w[-1][C],
                    sum(b[V] for b in w)))
    return out


class BarStrategy(Strategy):
    """Base for seeds that need full candles. Subclasses implement
    step_bars; step() raises so a mis-wired engine fails loudly instead
    of silently trading on a degraded signal."""
    wants_bars = True
    wants_market = False

    @property
    def tail(self):
        """How much history the seed is ALLOWED to see, in bars.

        Declared, bounded, and identical in the exam and in forward
        trading -- that identity is the point (W1.1). It exists because
        some of these seeds (OBV, anything resampled) are cumulative:
        given unbounded history their cost per bar grows with the store,
        and worse, their value would silently depend on how much history
        happened to be on disk that day. A bounded window makes the seed
        a fixed function of recent data instead of a function of the
        archive. Declared BEFORE any exam, per pre-registration."""
        return max(200, self.warmup * 3 + 10)

    def step(self, closes, ctx):
        raise RuntimeError(
            f"{self.name} needs full bars; engine called step() with "
            f"closes only. Wire step_bars() (charter E2.1).")

    def step_bars(self, bars, ctx):
        raise NotImplementedError

    def conviction(self, bars, ctx):
        return self.step_bars(bars, ctx)


# ---------------------------------------------------- volume family
class VolConfirmBreak(BarStrategy):
    """Donchian-style breakout that only counts when volume expands.
    Hysteresis kept (exit on a shorter low) so turnover stays low."""
    def __init__(self, n_hi, n_lo, vmult=1.5):
        self.hi, self.lo, self.vm = n_hi, n_lo, vmult
        self.name = f"volconf_{n_hi}_{n_lo}"
        self.warmup = max(n_hi, 60) + 1

    def _vr(self, bars):
        return vol_ratio(bars, 3, 30)

    def step_bars(self, bars, ctx):
        if len(bars) < self.warmup:
            return 0.0
        c = bars[-1][C]
        if ctx.get("weight", 0) > 0:
            lo = min(b[L] for b in bars[-self.lo - 1:-1])
            return 0.0 if c < lo else 1.0
        hi = max(b[H] for b in bars[-self.hi - 1:-1])
        vr = self._vr(bars)
        return 1.0 if (c > hi and vr is not None and vr >= self.vm) else 0.0

    def conviction(self, bars, ctx):
        if self.step_bars(bars, ctx) <= 0:
            return 0.0
        vr = self._vr(bars) or 1.0
        return vr - 1.0


class OBVTrend(BarStrategy):
    """Hold while on-balance-volume is above its own moving average:
    accumulation, not price. Conviction = OBV slope in baseline units."""
    def __init__(self, n):
        self.n = n
        self.name = f"obv_{n}"
        self.warmup = n + 2

    def step_bars(self, bars, ctx):
        o = obv_series(bars)
        m = sma(o, self.n)
        return 1.0 if m is not None and o and o[-1] > m else 0.0

    def conviction(self, bars, ctx):
        o = obv_series(bars)
        m = sma(o, self.n)
        if m is None or not o:
            return 0.0
        base = sum(b[V] for b in bars[-self.n:]) / self.n or 1.0
        return max(0.0, (o[-1] - m) / (base * self.n ** 0.5))


class VolDryUp(BarStrategy):
    """Quiet accumulation then a volume thrust. Compression measured on
    volume, not price, which is what makes it independent of VolBreak."""
    def __init__(self, quiet, thrust=2.0, regime=168):
        self.q, self.t, self.regime = quiet, thrust, regime
        self.name = f"dryup_{quiet}"
        self.warmup = max(quiet * 3, regime) + 2

    def step_bars(self, bars, ctx):
        if len(bars) < self.warmup:
            return 0.0
        cl = closes_of(bars)
        m = sma(cl, self.regime)
        if m is None or cl[-1] <= m:
            return 0.0
        if ctx.get("weight", 0) > 0:
            vr_now = vol_ratio(bars, self.q, self.q * 3)
            return 0.0 if (vr_now is not None and vr_now < 0.8) else 1.0
        prior = vol_ratio(bars[:-1], self.q, self.q * 3)
        now = vol_ratio(bars, 1, self.q * 3)
        return 1.0 if (prior is not None and prior < 0.8 and
                       now is not None and now >= self.t) else 0.0

    def conviction(self, bars, ctx):
        if self.step_bars(bars, ctx) <= 0:
            return 0.0
        return (vol_ratio(bars, 1, self.q * 3) or 0.0)


# ------------------------------------------------ candlestick family
class Engulfing(BarStrategy):
    """Bullish engulfing, permitted only above the regime MA. Exits on
    a close back below the pattern low (a different line than entry)."""
    def __init__(self, regime=168, hold=None):
        self.regime = regime
        self.name = f"engulf_{regime}"
        self.warmup = regime + 3

    def _pattern(self, bars):
        a, b = bars[-2], bars[-1]
        return (a[C] < a[O] and b[C] > b[O] and
                b[C] >= a[O] and b[O] <= a[C] and
                body(b) > body(a))

    def step_bars(self, bars, ctx):
        if len(bars) < self.warmup:
            return 0.0
        cl = closes_of(bars)
        m = sma(cl, self.regime)
        if m is None:
            return 0.0
        if ctx.get("weight", 0) > 0:
            stop = ctx.get("pattern_low")
            if stop is not None and cl[-1] < stop:
                ctx["pattern_low"] = None
                return 0.0
            return 1.0 if cl[-1] > m else 0.0
        if cl[-1] > m and self._pattern(bars):
            ctx["pattern_low"] = min(bars[-2][L], bars[-1][L])
            return 1.0
        return 0.0

    def conviction(self, bars, ctx):
        if self.step_bars(bars, ctx) <= 0:
            return 0.0
        a = atr(bars, 14)
        return 0.0 if not a else body(bars[-1]) / a


class PinBar(BarStrategy):
    """Long lower wick (hammer) on a pullback inside an uptrend: sellers
    tried and failed. Wick ratio is the conviction."""
    def __init__(self, regime=168, ratio=2.0):
        self.regime, self.ratio = regime, ratio
        self.name = f"pin_{regime}"
        self.warmup = regime + 3

    def _ratio(self, bars):
        b = bars[-1]
        d = body(b) or (b[H] - b[L]) * 0.01
        return 0.0 if d <= 0 else lower_wick(b) / d

    def step_bars(self, bars, ctx):
        if len(bars) < self.warmup:
            return 0.0
        cl = closes_of(bars)
        m = sma(cl, self.regime)
        if m is None or cl[-1] <= m:
            return 0.0
        if ctx.get("weight", 0) > 0:
            return 1.0
        b = bars[-1]
        return 1.0 if (self._ratio(bars) >= self.ratio and
                       lower_wick(b) > upper_wick(b) * 2) else 0.0

    def conviction(self, bars, ctx):
        return self._ratio(bars) if self.step_bars(bars, ctx) > 0 else 0.0


class InsideBreak(BarStrategy):
    """Inside bar = range compression = coiled spring. Enter on the
    break of the mother bar's high, exit below its low."""
    def __init__(self, regime=168):
        self.regime = regime
        self.name = f"inside_{regime}"
        self.warmup = regime + 4

    def step_bars(self, bars, ctx):
        if len(bars) < self.warmup:
            return 0.0
        cl = closes_of(bars)
        m = sma(cl, self.regime)
        if m is None:
            return 0.0
        if ctx.get("weight", 0) > 0:
            lo = ctx.get("mother_low")
            if lo is not None and cl[-1] < lo:
                ctx["mother_low"] = None
                return 0.0
            return 1.0
        mother, inside = bars[-3], bars[-2]
        is_inside = inside[H] <= mother[H] and inside[L] >= mother[L]
        if cl[-1] > m and is_inside and cl[-1] > mother[H]:
            ctx["mother_low"] = mother[L]
            return 1.0
        return 0.0

    def conviction(self, bars, ctx):
        if self.step_bars(bars, ctx) <= 0:
            return 0.0
        mother, inside = bars[-3], bars[-2]
        rng = mother[H] - mother[L]
        return 0.0 if rng <= 0 else 1.0 - (inside[H] - inside[L]) / rng


# ------------------------------------------- cross-sectional family
class RelStrength(BarStrategy):
    """Ranks names AGAINST EACH OTHER, not against their own past —
    the only family here that asks a cross-sectional question.

    Deliberately slow and sticky, because MOM-ROT already proved that
    fast rotation on retail fees is negative-sum: a held name is kept
    until it falls out of the top `keep` band, not the top `top` band.
    Hysteresis is the whole point.
    """
    cross_sectional = True

    def __init__(self, look, top=2, keep=4, regime=168):
        self.look, self.top, self.keep = look, top, keep
        self.regime = regime
        self.name = f"rs_{look}_{top}"
        self.warmup = max(look, regime) + 2

    def _score(self, bars):
        cl = closes_of(bars)
        if len(cl) < self.look + 1:
            return None
        m = sma(cl, self.regime)
        if m is None or cl[-1] <= m:
            return None          # absolute filter: no shorting the pack
        return cl[-1] / cl[-1 - self.look] - 1

    def step_all(self, data, ctx):
        scores = {}
        for p, bars in data.items():
            s = self._score(bars)
            if s is not None:
                scores[p] = s
        order = sorted(scores, key=lambda p: (-scores[p], p))
        held = {p for p, c in ctx.items()
                if isinstance(c, dict) and c.get("weight", 0) > 0}
        out = {}
        for i, p in enumerate(order):
            if i < self.top or (p in held and i < self.keep):
                out[p] = 1.0
        self._scores = scores
        return out

    def conviction_all(self, pair):
        return getattr(self, "_scores", {}).get(pair, 0.0)


# ------------------------------------------------ cross-asset family
class MarketRegime(BarStrategy):
    """Trades a name only while the MARKET PROXY is healthy — the
    signal comes from a different asset than the one being traded
    (BTC-USD for crypto, SPY for stocks). Naturally low turnover."""
    wants_market = True

    def __init__(self, mkt_n=168, own_n=48):
        self.mkt_n, self.own_n = mkt_n, own_n
        self.name = f"regime_{mkt_n}_{own_n}"
        self.warmup = max(mkt_n, own_n) + 2

    def step_bars(self, bars, ctx):
        mkt = ctx.get("market")
        if not mkt:
            return 0.0
        mc = closes_of(mkt)
        mm = sma(mc, self.mkt_n)
        if mm is None or mc[-1] <= mm:
            return 0.0
        cl = closes_of(bars)
        om = sma(cl, self.own_n)
        return 1.0 if om is not None and cl[-1] > om else 0.0

    def conviction(self, bars, ctx):
        if self.step_bars(bars, ctx) <= 0:
            return 0.0
        cl = closes_of(bars)
        om = sma(cl, self.own_n)
        return 0.0 if not om else (cl[-1] / om - 1)


# -------------------------------------------------- calendar family
class Calendar(BarStrategy):
    """The date is the signal. Turn-of-month for stocks, weekend for
    crypto. Nearly free on fees, probably weak — a clean control."""
    def __init__(self, mode, regime=168):
        assert mode in ("tom", "weekend")
        self.mode, self.regime = mode, regime
        self.name = f"cal_{mode}"
        self.warmup = regime + 2

    def _on(self, ts):
        from datetime import datetime, timezone
        d = datetime.fromtimestamp(ts, timezone.utc)
        if self.mode == "weekend":
            return d.weekday() >= 4
        return d.day >= 26 or d.day <= 5

    def step_bars(self, bars, ctx):
        cl = closes_of(bars)
        m = sma(cl, self.regime)
        if m is None or cl[-1] <= m:
            return 0.0
        return 1.0 if self._on(bars[-1][TS]) else 0.0

    def conviction(self, bars, ctx):
        return self.step_bars(bars, ctx)


# --------------------------------------------------- committee family
class Committee(BarStrategy):
    """The owner's original 'mix of both': enter only when 2 of 3
    UNRELATED families agree; exit when any one leaves. Fewer, higher
    conviction trades — the direction the fee maths rewards."""
    wants_market = False

    def __init__(self, members, need=2, name="vote"):
        self.members = members
        self.need = need
        self.name = name
        self.warmup = max(m.warmup for m in members) + 1
        self.wants_market = any(getattr(m, "wants_market", False)
                                for m in members)

    def _votes(self, bars, ctx):
        out = []
        for i, m in enumerate(self.members):
            sub = ctx.setdefault(f"_m{i}", {})
            sub["weight"] = ctx.get("weight", 0.0)
            sub["market"] = ctx.get("market")
            try:
                out.append(1.0 if m.step_bars(bars, sub) > 0 else 0.0)
            except Exception:
                out.append(0.0)
        return out

    def step_bars(self, bars, ctx):
        v = sum(self._votes(bars, ctx))
        if ctx.get("weight", 0) > 0:
            return 1.0 if v >= len(self.members) else 0.0
        return 1.0 if v >= self.need else 0.0

    def conviction(self, bars, ctx):
        return sum(self._votes(bars, ctx)) / len(self.members)


# ------------------------------------------------- slow-clock family
class SlowClock(BarStrategy):
    """Wraps any bar strategy and feeds it resampled bars, so the same
    maths runs on a genuinely slower timescale. move_scale says the
    useful direction is UP: hourly moves cannot pay a 1.6-2.6% round
    trip, multi-day ones can."""
    def __init__(self, inner, k, name=None):
        self.inner, self.k = inner, k
        self.name = name or f"slow{k}_{inner.name}"
        self.warmup = inner.warmup * k + k
        self.wants_market = getattr(inner, "wants_market", False)

    def step_bars(self, bars, ctx):
        return self.inner.step_bars(resample(bars, self.k), ctx)

    def conviction(self, bars, ctx):
        return self.inner.conviction(resample(bars, self.k), ctx)


class RandomEntry(BarStrategy):
    """Deterministic random-entry LUCK CONTROL (pre-registered in
    docs/recert_2026-08-04.md; expected exam verdict: FAIL, and that
    expectation is the point).

    Enters on a hash coin-flip keyed to (name, bar timestamp, price),
    holds a fixed bar count, exits. Price enters only as RNG salt, so
    the strategy is economically blind; its forward record is an
    empirical luck yardstick with roster-matched turnover, complementing
    the analytic permutation test. Fully deterministic and stateless
    given the bar stream: the seed examined is the seed that trades."""

    def __init__(self, hold_bars, p_enter, tag):
        self.hold, self.p = hold_bars, p_enter
        self.name = f"rand_{tag}"
        self.warmup = 5

    def _u(self, ts, px):
        import hashlib
        h = hashlib.sha256(
            f"{self.name}:{int(ts)}:{round(px, 8)}".encode()).digest()
        return int.from_bytes(h[:8], "big") / 2 ** 64

    def step_bars(self, bars, ctx):
        ts, px = bars[-1][TS], bars[-1][C]
        if ctx.get("weight", 0) > 0:
            if ctx.get("rand_ts") != ts:          # count each bar once
                ctx["rand_ts"] = ts
                ctx["rand_held"] = ctx.get("rand_held", 0) + 1
            return 0.0 if ctx["rand_held"] >= self.hold else 1.0
        if self._u(ts, px) < self.p:
            ctx["rand_ts"], ctx["rand_held"] = ts, 0
            return 1.0
        return 0.0

    def conviction(self, bars, ctx):
        # no opinion by design: a fresh hash, so ranking among its own
        # picks is random rather than volatility-biased
        return self._u(bars[-1][TS] + 1, bars[-1][C])
