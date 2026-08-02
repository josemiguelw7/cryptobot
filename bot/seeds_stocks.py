"""
Stock seed roster - PROPOSED, not adopted. Mirror of the ten crypto
seed families (symmetric generation design, declared before any stock
backtest was run) on RTH hourly bars: DAY=7 bars, WEEK=33, MONTH=140.

Same contract as seeds_crypto: exam runner and squad import THIS
module, so the seed examined is byte-for-byte the seed that trades.
ARMED flips only after owner signature (docs/stocks_standard.md gets
the verdicts) plus one exam per seed. Once adopted: immortal (s9.3).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import strategies as S

ARMED = False          # flips only per the procedure in the docstring
ASSET_CLASS = "stocks"

# Frozen universe, docs/stocks_standard.md (3 ETFs + 7 megacaps;
# survivorship caveat on the single names is pre-registered there).
PAIRS = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN",
         "GOOGL", "META", "TSLA"]


def _named(strat, name):
    strat.name = name
    return strat


# hold_h = declared holding horizon in RTH BARS (1 bar = 1 hour of
# session time; 7 bars = 1 session). Load-bearing for the s4.3 cost
# gate, declared in advance so it cannot be tuned per-seed later.
SEEDS = {
    # --- trend / momentum family ---
    "s_trend_33":    {"strat": _named(S.Trend(33), "s_trend_33"),
                      "hold_h": 33,
                      "note": "1-week SMA regime (33 RTH bars)"},
    "s_cross_7_33":  {"strat": _named(S.Cross(7, 33), "s_cross_7_33"),
                      "hold_h": 21,
                      "note": "1-session/1-week SMA cross"},
    "s_tsmom_21":    {"strat": _named(S.TSMom(21), "s_tsmom_21"),
                      "hold_h": 21,
                      "note": "3-session time-series momentum"},
    "s_macd_12_26":  {"strat": _named(S.MACDTrend(12, 26, 9),
                                      "s_macd_12_26"),
                      "hold_h": 14,
                      "note": "classic MACD at RTH-hourly speed"},
    # --- breakout family (hysteresis built in) ---
    "s_donch_14_7":  {"strat": _named(S.Donchian2(14, 7), "s_donch_14_7"),
                      "hold_h": 14,
                      "note": "2-session-high entry, 1-session-low exit"},
    "s_volbrk_7_33": {"strat": _named(S.VolBreak(7, 33), "s_volbrk_7_33"),
                      "hold_h": 14,
                      "note": "vol-compression squeeze breakout"},
    # --- mean-reversion family ---
    "s_rsi14_reg33": {"strat": _named(S.RSIRegime(14, 25, 55, regime=33),
                                      "s_rsi14_reg33"),
                      "hold_h": 7,
                      "note": "dip-buyer, permitted only above the "
                              "1-week SMA"},
    "s_boll_14":     {"strat": _named(S.Bollinger(14, 2.0), "s_boll_14"),
                      "hold_h": 7,
                      "note": "2-sigma reversion to the 2-session mean"},
    # --- regime / anomaly family ---
    "s_calm_7_33":   {"strat": _named(S.CalmRegime(7, 33), "s_calm_7_33"),
                      "hold_h": 21,
                      "note": "hold only while 1-session vol < 1-week vol"},
    "s_nearhi_33":   {"strat": _named(S.NearHigh(33, 0.05), "s_nearhi_33"),
                      "hold_h": 26,
                      "note": "persistence within 5% of the 1-week high"},
}


def get(name):
    if name not in SEEDS:
        raise KeyError(f"unknown seed {name!r}; known: {sorted(SEEDS)}")
    return SEEDS[name]["strat"]


if __name__ == "__main__":
    print(f"stock seed roster - status: "
          f"{'ARMED' if ARMED else 'PROPOSED (not adopted)'}")
    for n, cfg in SEEDS.items():
        s = cfg["strat"]
        print(f"  {n:14s} warmup {s.warmup:4d} bars  "
              f"hold ~{cfg['hold_h']:3d} RTH bars  {cfg['note']}")
