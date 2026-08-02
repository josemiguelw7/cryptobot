"""
bot/report_gates.py - apply the charter's statistical gates to an equity log.

DIAGNOSTIC ONLY. The daily Strategy League remains governed by
docs/success_criteria.md. Nothing here changes that document's criteria; this
just answers "what would the intraday charter's gates say about this data?"
so the machinery is exercised on real numbers before the squad exists.

Usage:
    python3 bot/report_gates.py [path/to/equity.csv] [--asset-class crypto|stock]
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(os.path.dirname(HERE), "logs", "league_equity.csv")


def load_daily_equity(path):
    """-> {strategy: [(date, equity), ...]} keeping the LAST point of each day.

    The league logs on an hourly heartbeat, so intra-day rows would otherwise
    inflate the observation count and understate the standard error - which is
    the exact direction of error the charter is built to avoid."""
    per_day = defaultdict(dict)
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["time"])
            try:
                eq = float(row["equity"])
            except (TypeError, ValueError):
                continue
            per_day[row["strategy"]][ts.date()] = (ts, eq)
    out = {}
    for strat, days in per_day.items():
        out[strat] = [(d, days[d][1]) for d in sorted(days)]
    return out


def daily_returns(series):
    return [b / a - 1.0 for (_, a), (_, b) in zip(series, series[1:]) if a > 0]


def build_report(path, asset_class="crypto"):
    series = load_daily_equity(path)
    rets = {s: daily_returns(v) for s, v in series.items()}
    usable = {s: r for s, r in rets.items() if len(r) >= 3}

    # K per charter section 3: every configuration that has ever accumulated
    # counted days in this asset class. Here: every strategy in the log.
    k_trials = len(rets)
    trial_sharpes = [stats.sharpe_per_period(r) for r in usable.values()]

    rows = []
    for strat in sorted(usable):
        r = usable[strat]
        st = stats.compute(r, asset_class, trial_sharpes)
        rows.append((strat, st, len(r)))
    return rows, k_trials, len(series)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else DEFAULT_CSV
    ac = "stock" if "--asset-class=stock" in sys.argv else "crypto"

    rows, k_trials, n_strats = build_report(path, ac)
    if not rows:
        print("Not enough history yet - need at least 4 daily equity points per strategy.")
        return

    n_days = max(n for _, _, n in rows)
    print(f"\nGate diagnostic - {os.path.basename(path)} | asset class: {ac}")
    print(f"{n_strats} strategies, K={k_trials}, longest series {n_days} daily returns")
    print("DIAGNOSTIC ONLY - the daily league is governed by docs/success_criteria.md\n")

    hdr = f"{'strategy':<14}{'days':>5}{'net':>9}{'Sharpe':>9}{'LCB':>10}{'maxDD':>8}{'DSR':>8}"
    print(hdr); print("-" * len(hdr))
    for strat, st, n in rows:
        print(f"{strat:<14}{n:>5}{st.net_pnl:>8.2%}{st.sharpe_annual:>9.2f}"
              f"{st.lcb:>10.5f}{st.max_drawdown:>8.2%}{st.dsr:>8.3f}")

    print(f"\nCharter gates (section 5) - Sharpe>=1.0, LCB>0, maxDD<=10%")
    print(f"(DSR is reported above but does not gate at v1.0 - charter section 5.7)")
    for strat, st, n in rows:
        g = st.stage1_gates(n_closed_trades=0, window_days=n, breaches=0)
        stat_gates = {k: v for k, v in g.items() if k in
                      ("sharpe_floor", "lcb_positive", "max_drawdown")}
        failed = [k for k, v in stat_gates.items() if not v]
        verdict = "PASS" if not failed else "fails: " + ", ".join(failed)
        print(f"  {strat:<14} {verdict}")

    if n_days < 90:
        print(f"\nNote: {n_days} days of history. The charter's window is 90 (path A) "
              f"or 180 (path B). Nothing here can graduate yet - by design.")


if __name__ == "__main__":
    main()
