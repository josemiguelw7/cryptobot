"""Pruebas unitarias del motor con una cinta sintética (no necesitan datos reales).
  cd futures/lab && python -m pytest tests -q      (o python tests/test_engine.py)
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.sim import Signal, Rules, simulate, fill_limit
from engine import topstep, stats
from engine.data import Session, NY_OPEN
import polars as pl


def tape(prices, start=NY_OPEN, dt=1.0, vol=1, side=1):
    """Sesión sintética: un llenado por segundo, bid/ask = precio ∓/± 1 tick."""
    n = len(prices)
    ts = [int((1700000000 + start + k * dt) * 1e9) for k in range(n)]  # UTC ficticio
    df = pl.DataFrame({"ts": pl.Series(ts).cast(pl.Datetime("ns", "UTC")), "trade_id": list(range(n)),
                       "price_t": prices, "volume": [vol] * n, "side": [side] * n,
                       "bid_after_t": [p - 1 for p in prices], "ask_after_t": [p + 1 for p in prices],
                       "bid_before_t": [p - 1 for p in prices], "ask_before_t": [p + 1 for p in prices],
                       "bid_size_after": [10] * n, "ask_size_after": [10] * n, "contract": ["NQZ9"] * n})
    s = Session("2030-01-01", df)
    s.sec = np.array([start + k * dt for k in range(n)])  # hora ET sintética
    return s


def test_target_through_rule():
    s = tape([100] * 5 + [110, 111, 113] + [100] * 5)
    sig = Signal(sec=NY_OPEN + 2, side=1, stop_ticks=5, target_ticks=10, max_sec=60)
    tr = simulate(s, [sig], Rules(), slip=1, commission_rt=3.78)
    assert len(tr) == 1
    t = tr[0]
    assert t["entry_px"] == (101 + 1) / 4          # ask + 1 tick de deslizamiento
    assert t["reason"] == "objetivo"               # 113 > 112: cinta pasó de largo
    assert t["exit_px"] == 112 / 4 and t["pnl_ticks"] == 10
    assert abs(t["net_usd"] - (10 * 5 - 3.78)) < 1e-9


def test_target_touch_not_enough():
    s = tape([100] * 5 + [112] + [100] * 5)        # toca 112 exacto, no lo pasa
    sig = Signal(sec=NY_OPEN + 2, side=1, stop_ticks=50, target_ticks=10, max_sec=60)
    tr = simulate(s, [sig], Rules(), slip=1, commission_rt=0)
    assert tr[0]["reason"] in ("tiempo", "cierre") or tr[0]["reason"] == "stop"
    assert tr[0]["reason"] != "objetivo"


def test_stop_with_slip():
    s = tape([100] * 5 + [95, 90] + [100] * 5)
    sig = Signal(sec=NY_OPEN + 2, side=1, stop_ticks=5, target_ticks=50, max_sec=60)
    tr = simulate(s, [sig], Rules(), slip=1, commission_rt=0)
    t = tr[0]
    assert t["reason"] == "stop" and t["exit_px"] == (102 - 5 - 1) / 4 and t["pnl_ticks"] == -6


def test_short_symmetry():
    s = tape([100] * 5 + [90, 89, 87] + [100] * 5)
    sig = Signal(sec=NY_OPEN + 2, side=-1, stop_ticks=5, target_ticks=10, max_sec=60)
    tr = simulate(s, [sig], Rules(), slip=1, commission_rt=0)
    assert tr[0]["entry_px"] == (99 - 1) / 4 and tr[0]["reason"] == "objetivo" and tr[0]["pnl_ticks"] == 10


def test_daily_limits_and_one_position():
    s = tape([100] * 600)
    sigs = [Signal(sec=NY_OPEN + k, side=1, stop_ticks=5, target_ticks=5, max_sec=30) for k in range(0, 600, 5)]
    tr = simulate(s, sigs, Rules(max_trades=6, max_consec_losses=3), slip=1, commission_rt=3.78)
    assert len(tr) == 3                              # 3 pérdidas seguidas (comisión) y se detiene
    assert all(tr[i]["exit_sec"] <= tr[i + 1]["entry_sec"] for i in range(len(tr) - 1))


def test_forced_close():
    s = tape([100] * 100, start=42300 - 50)
    sig = Signal(sec=42300 - 40, side=1, stop_ticks=50, target_ticks=50, max_sec=3600)
    tr = simulate(s, [sig], Rules(last_entry=42300), slip=1, commission_rt=0)
    assert tr[0]["reason"] == "cierre" and tr[0]["exit_sec"] <= 42300


def test_limit_queue():
    # orden límite de compra en 99 con 10 en cola; se llena cuando se venden > 10 contratos en 99
    prices = [100] * 3 + [99] * 20
    s = tape(prices, side=-1)
    i = 3
    r = fill_limit(s, i, 1, 99, wait_sec=60)
    assert r is not None and r[1] == 99 and r[0] >= i + 10


def test_topstep_rules():
    dates = [f"2030-01-{k:02d}" for k in range(1, 21)]
    paths = {dates[0]: [(1000, -100)], dates[1]: [(1200, -200)], dates[2]: [(900, -50)]}
    r = topstep.run_account(dates, paths, consistency=0.50)
    assert r["resultado"] == "pasa" and r["dias"] == 3        # 3100 ganados, mejor día 1200 ≤ 50%
    r55 = topstep.run_account(dates, {dates[0]: [(2000, -10)], dates[1]: [(1100, -10)]}, consistency=0.55)
    assert r55["resultado"] != "pasa"                          # 2000/3100 = 64% > 55%
    r_mll = topstep.run_account(dates, {dates[0]: [(500, -100)], dates[1]: [(-1500, -2600)]})
    assert r_mll["resultado"] == "rompe_mll" and r_mll["dias"] == 2   # 50500 - 2600 <= 48500 (MLL subió a 48500)
    r_dll = topstep.run_account(dates, {dates[0]: [(-900, -900), (-900, -900)]})
    assert r_dll["resultado"] == "sin_resolver" and r_dll["balance"] == 49000   # DLL corta el día en -1000


def test_stats_basic():
    daily = np.array([100, -50, 80, 120, -30, 60, 90, -10, 40, 70] * 5, dtype=float)
    assert 0.5 < stats.psr(daily) <= 1.0
    assert stats.dsr(daily, 1, 0.0) == stats.psr(daily)
    assert stats.min_btl_years(1) == 0.0 and stats.min_btl_years(50) > stats.min_btl_years(10)
    c = stats.cpcv_paths(daily); assert c["total"] == 15


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
