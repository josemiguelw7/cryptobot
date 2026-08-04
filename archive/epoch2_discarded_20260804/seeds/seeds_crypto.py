"""
CRYPTO INTRADAY SEED ROSTER — the 10 proposed seeds for the hourly squad.

STATUS: PROPOSED. Not yet adopted. Charter section 9.3 makes the adopted
seeds IMMORTAL AND IMMUTABLE — the frozen controls every later generation
must beat — so adoption is an owner decision, not an engineering one.
Flip ARMED to True only after (a) the owner signs the roster in
docs/seed_proposals_crypto.md and (b) every seed has been through
backtest/exam_1h.py, which labels it candidate (PASS) or control (FAIL).
Once ARMED, nothing in SEEDS may ever change; new ideas are bred
descendants with their own names, per charter section 9.6.

Design inputs — only the three published priors (commit 997c7d3), all of
which compute cost and structure, never returns:
  move_scale.py       median |move|: 1h 0.31% · 12h 1.21% · 1d 1.80% ·
                      3d 3.27% · 7d 4.83%. The 2x round-trip hurdle is
                      1.60% (charter costs) / 2.60% (standard costs), so
                      only holding horizons of ~1 day and up have room.
                      Hence: decisions every hour, holds measured in days.
  signal_correlation  20 classic families carry ~6.24 independent
                      opinions; trend and reversion anticorrelate. Hence:
                      few seeds per family, families deliberately spread.
  hysteresis_freq     hysteresis (separate entry/exit lines) cuts round
                      trips ~10x. Hence: every seed here exits on a
                      different line than it enters, or holds a regime.

All strategy logic lives in bot/strategies.py (single source of truth,
W1.1); classes are bar-length agnostic, parameters below are in HOURLY
BARS. exam_1h.py and squad.py both import THIS module, so the seed that
is examined is byte-for-byte the seed that trades forward.
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategies as S

ARMED = True          # flips only per the procedure in the docstring
ASSET_CLASS = "crypto"

# The eight fixed exam pairs (docs/intraday_standard.md). Same eight as
# the daily exam so results are directly comparable.
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


def _named(strat, name):
    """Seeds get permanent h_* names (one exam per name, EVER — the name
    is the unit of the multiple-testing ledger)."""
    strat.name = name
    return strat


# hold_h = declared expected holding horizon in hours. Load-bearing:
# squad.py's section-4.3 cost gate compares the trailing unconditional
# median |return| over THIS horizon (move_scale's statistic, rolling)
# against 2x the modeled round-trip cost. Declared here, in advance,
# so the gate cannot be tuned to whatever lets a seed trade.
SEEDS = {
    # --- trend / momentum family ---
    "h_trend_168":    {"strat": _named(S.Trend(168), "h_trend_168"),
                       "hold_h": 168,
                       "note": "7-day SMA regime, the daily champion's "
                               "shape at hourly resolution"},
    "h_cross_24_168": {"strat": _named(S.Cross(24, 168), "h_cross_24_168"),
                       "hold_h": 72,
                       "note": "1d/7d SMA cross - medium-speed trend"},
    "h_tsmom_72":     {"strat": _named(S.TSMom(72), "h_tsmom_72"),
                       "hold_h": 72,
                       "note": "3-day time-series momentum"},
    "h_macd_12_26":   {"strat": _named(S.MACDTrend(12, 26, 9),
                                       "h_macd_12_26"),
                       "hold_h": 48,
                       "note": "classic MACD at hourly speed"},
    # --- breakout family (hysteresis built in) ---
    "h_donch_48_24":  {"strat": _named(S.Donchian2(48, 24),
                                       "h_donch_48_24"),
                       "hold_h": 48,
                       "note": "2-day-high entry, 1-day-low exit"},
    "h_volbrk_24_96": {"strat": _named(S.VolBreak(24, 96),
                                       "h_volbrk_24_96"),
                       "hold_h": 48,
                       "note": "vol-compression squeeze breakout"},
    # --- mean-reversion family (anticorrelated with the above) ---
    "h_rsi14_reg168": {"strat": _named(S.RSIRegime(14, 25, 55, regime=168),
                                       "h_rsi14_reg168"),
                       "hold_h": 24,
                       "note": "dip-buyer, permitted only above the "
                               "7-day SMA"},
    "h_boll_48":      {"strat": _named(S.Bollinger(48, 2.0), "h_boll_48"),
                       "hold_h": 24,
                       "note": "2-sigma band reversion to the 2-day mean"},
    # --- regime / anomaly family ---
    "h_calm_24_168":  {"strat": _named(S.CalmRegime(24, 168),
                                       "h_calm_24_168"),
                       "hold_h": 72,
                       "note": "hold only while 1-day vol < 7-day vol"},
    "h_nearhi_168":   {"strat": _named(S.NearHigh(168, 0.05),
                                       "h_nearhi_168"),
                       "hold_h": 120,
                       "note": "persistence within 5% of the 7-day high"},
}


def get(name):
    if name not in SEEDS:
        raise KeyError(f"unknown seed {name!r}; known: {sorted(SEEDS)}")
    return SEEDS[name]["strat"]


if __name__ == "__main__":
    print(f"crypto seed roster - status: "
          f"{'ARMED' if ARMED else 'PROPOSED (not adopted)'}")
    for n, cfg in SEEDS.items():
        s = cfg["strat"]
        print(f"  {n:16s} warmup {s.warmup:4d} bars  "
              f"hold ~{cfg['hold_h']:3d}h  {cfg['note']}")
