"""
STOCK EPOCH-2 SEED ROSTER — symmetric mirror of seeds_crypto_v2.

STATUS: PROPOSED. NOT ADOPTED. ARMED = False.

Parameters are in RTH BARS (1 bar = 1 session hour; 7 bars = 1 session,
33 = 1 week, 140 = 1 month). Same eleven families as crypto, declared
symmetrically BEFORE any stock exam ran, so a family that passes in one
asset class and fails in the other is informative rather than suspicious.

Two stock-specific notes, both pre-registered:
  - The market proxy is SPY (E2.4), not BTC.
  - Calendar mode is turn-of-month, the stock analogue of the crypto
    weekend seed.

Universe caveat stands: the 10-name menu is survivorship-contaminated
and docs/seed_proposals_v2.md s5 FORBIDS widening it without a
point-in-time membership rule. data/pit_stocks.py exists for that.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import strategies as S

ARMED = False         # owner signature required (docs/seed_proposals_v2.md s8)
ASSET_CLASS = "stocks"
EPOCH = 2

PAIRS = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN",
         "GOOGL", "META", "TSLA"]

# E2.3: 4 of 10 names. This is the number that most directly fixes the
# 2026-08-04 finding (8 of 10 bots holding identical books). Owner's
# call, charter s2 -- recommended, not decided.
MAX_POS = 4


def _named(s, n):
    s.name = n
    return s


SEEDS = {
    # --- volume family ---------------------------------------------
    "s2_volconf":  {"strat": _named(S.VolConfirmBreak(14, 7, 1.5),
                                    "s2_volconf"),
                    "hold_h": 14,
                    "note": "2-session-high break on volume expansion"},
    "s2_obv":      {"strat": _named(S.OBVTrend(33), "s2_obv"),
                    "hold_h": 33,
                    "note": "on-balance-volume above its 1-week average"},
    "s2_dryup":    {"strat": _named(S.VolDryUp(7, 2.0, 33), "s2_dryup"),
                    "hold_h": 21,
                    "note": "volume dry-up then thrust"},
    # --- candlestick family ----------------------------------------
    "s2_engulf":   {"strat": _named(S.Engulfing(33), "s2_engulf"),
                    "hold_h": 21,
                    "note": "bullish engulfing above the 1-week SMA"},
    "s2_pin":      {"strat": _named(S.PinBar(33, 2.0), "s2_pin"),
                    "hold_h": 14,
                    "note": "hammer on a pullback inside an uptrend"},
    "s2_inside":   {"strat": _named(S.InsideBreak(33), "s2_inside"),
                    "hold_h": 14,
                    "note": "inside-bar compression, break of mother high"},
    # --- cross-sectional -------------------------------------------
    "s2_rs":       {"strat": _named(S.RelStrength(33, top=4, keep=6,
                                                  regime=33), "s2_rs"),
                    "hold_h": 33,
                    "note": "slow sticky relative strength vs the pack"},
    # --- cross-asset -----------------------------------------------
    "s2_regime":   {"strat": _named(S.MarketRegime(33, 14), "s2_regime"),
                    "hold_h": 33,
                    "note": "single names only while SPY is trending"},
    # --- calendar ---------------------------------------------------
    "s2_cal":      {"strat": _named(S.Calendar("tom", 33), "s2_cal"),
                    "hold_h": 14,
                    "note": "turn-of-month, gated by trend regime"},
    # --- committee ---------------------------------------------------
    "s2_vote":     {"strat": _named(S.Committee(
                        [S.OBVTrend(33), S.Engulfing(33),
                         S.VolConfirmBreak(14, 7, 1.5)],
                        need=2, name="s2_vote"), "s2_vote"),
                    "hold_h": 33,
                    "note": "2 of 3 unrelated families must agree"},
    # --- slow clock --------------------------------------------------
    "s2_slow":     {"strat": _named(S.SlowClock(S.OBVTrend(20), 7,
                                                "s2_slow"), "s2_slow"),
                    "hold_h": 70,
                    "note": "OBV trend on DAILY bars (7 RTH resample)"},
}


def get(name):
    if name not in SEEDS:
        raise KeyError(f"unknown seed {name!r}; known: {sorted(SEEDS)}")
    return SEEDS[name]["strat"]


if __name__ == "__main__":
    print(f"stock epoch-2 roster - "
          f"{'ARMED' if ARMED else 'PROPOSED (not adopted)'} "
          f"· MAX_POS={MAX_POS}")
    for n, cfg in SEEDS.items():
        s = cfg["strat"]
        print(f"  {n:12s} warmup {s.warmup:5d}  "
              f"hold ~{cfg['hold_h']:3d} RTH bars  {cfg['note']}")
