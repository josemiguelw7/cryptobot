"""
CRYPTO EPOCH-2 SEED ROSTER — the 11 wave-2 seeds.

STATUS: PROPOSED. NOT ADOPTED. ARMED = False.

Roster frozen in docs/seed_proposals_v2.md BEFORE any exam was run.
ARMED flips only after (a) the owner signs section 8 of that document
and (b) every seed has a recorded verdict from backtest/exam_1h.py.
Charter s9.3: adoption is an owner decision, not an engineering one.

Admission rule, declared in advance: each seed must use information NO
other seed uses. signal_correlation.py measured that 20 classic
families carry only ~6.24 independent opinions, so another moving
average variant adds nothing and is not admitted. What is new here is
VOLUME, BAR SHAPE, THE OTHER NAMES, ANOTHER ASSET, THE DATE, AGREEMENT,
and TIMESCALE.

Names are permanent: one exam per name, EVER. 11 names here + 11 stock
names + 20 already run = 42 in the multiple-testing ledger.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import strategies as S

ARMED = False         # owner signature required (docs/seed_proposals_v2.md s8)
ASSET_CLASS = "crypto"
EPOCH = 2

# Same eight pairs as epoch 1 so results stay directly comparable.
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]

# E2.3: 3 of 8 names. Recommendation only -- this number is the owner's
# (charter s2). At 2 of 8 the cap, not the strategy, picks the book.
MAX_POS = 3


def _named(s, n):
    s.name = n
    return s


SEEDS = {
    # --- volume family: how many people showed up -------------------
    "h2_volconf":  {"strat": _named(S.VolConfirmBreak(48, 24, 1.5),
                                    "h2_volconf"),
                    "hold_h": 48,
                    "note": "2d-high breakout, only on volume expansion"},
    "h2_obv":      {"strat": _named(S.OBVTrend(168), "h2_obv"),
                    "hold_h": 120,
                    "note": "on-balance-volume above its 7d average"},
    "h2_dryup":    {"strat": _named(S.VolDryUp(24, 2.0, 168), "h2_dryup"),
                    "hold_h": 72,
                    "note": "volume compression then thrust"},
    # --- candlestick family: the shape of the bar -------------------
    "h2_engulf":   {"strat": _named(S.Engulfing(168), "h2_engulf"),
                    "hold_h": 72,
                    "note": "bullish engulfing above the 7d SMA"},
    "h2_pin":      {"strat": _named(S.PinBar(168, 2.0), "h2_pin"),
                    "hold_h": 48,
                    "note": "long lower wick on a pullback in uptrend"},
    "h2_inside":   {"strat": _named(S.InsideBreak(168), "h2_inside"),
                    "hold_h": 48,
                    "note": "inside-bar compression, break of mother high"},
    # --- cross-sectional: the OTHER names ---------------------------
    "h2_rs":       {"strat": _named(S.RelStrength(168, top=3, keep=5,
                                                  regime=168), "h2_rs"),
                    "hold_h": 168,
                    "note": "slow sticky relative strength vs the pack"},
    # --- cross-asset: a DIFFERENT asset -----------------------------
    "h2_regime":   {"strat": _named(S.MarketRegime(168, 48), "h2_regime"),
                    "hold_h": 120,
                    "note": "alts only while BTC itself is healthy"},
    # --- calendar: the date -----------------------------------------
    "h2_cal":      {"strat": _named(S.Calendar("weekend", 168), "h2_cal"),
                    "hold_h": 48,
                    "note": "weekend effect, gated by trend regime"},
    # --- committee: the owner's 'mix of both' -----------------------
    "h2_vote":     {"strat": _named(S.Committee(
                        [S.OBVTrend(168), S.Engulfing(168),
                         S.VolConfirmBreak(48, 24, 1.5)],
                        need=2, name="h2_vote"), "h2_vote"),
                    "hold_h": 120,
                    "note": "2 of 3 unrelated families must agree"},
    # --- slow clock: another timescale ------------------------------
    "h2_slow":     {"strat": _named(S.SlowClock(S.OBVTrend(30), 24,
                                                "h2_slow"), "h2_slow"),
                    "hold_h": 240,
                    "note": "OBV trend on DAILY bars (24h resample)"},
}


def get(name):
    if name not in SEEDS:
        raise KeyError(f"unknown seed {name!r}; known: {sorted(SEEDS)}")
    return SEEDS[name]["strat"]


if __name__ == "__main__":
    print(f"crypto epoch-2 roster - "
          f"{'ARMED' if ARMED else 'PROPOSED (not adopted)'} "
          f"· MAX_POS={MAX_POS}")
    for n, cfg in SEEDS.items():
        s = cfg["strat"]
        print(f"  {n:12s} warmup {s.warmup:5d}  hold ~{cfg['hold_h']:4d}h  "
              f"{cfg['note']}")
