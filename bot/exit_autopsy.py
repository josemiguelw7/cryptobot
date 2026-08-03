"""
EXIT AUTOPSY — counterfactual exit study over CLOSED squad trades.

Reads logs/squad_trades.csv + hourly candles and asks, for every closed
round trip: what would net P&L have been under (a) a fixed take-profit,
(b) a hard stop-loss, (c) a trailing stop, instead of the exit that
actually fired?  Pure analysis: reads logs, writes a report, touches no
state, decides nothing (charter s9.7).  Costs the exam ledger nothing.

Honesty rules:
  - counterfactual exits trigger on hourly CLOSES only (bots act at
    cycles; anything finer would be fiction)
  - fills pay the charter cost model: taker 0.40%, slip 2bps BTC/ETH /
    10bps others, stop-outs at 2x slip (s4.1)
  - if a rule never triggers before the actual exit, the actual exit
    stands (same bar, same net)
  - trades still open are excluded; sample size is printed first, and
    with N this small every number is a hint, not a verdict

Usage: .venv/bin/python bot/exit_autopsy.py [--md out.md]
"""
from __future__ import annotations
import argparse, csv, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TRLOG = os.path.join(ROOT, "logs", "squad_trades.csv")
CANDLES = os.path.join(ROOT, "data", "candles")
FEE = 0.004
SLIP = {"BTC-USD": 0.0002, "ETH-USD": 0.0002}
SLIP_OTHER = 0.0010
STOP_MULT = 2.0

TP_GRID = [0.02, 0.03, 0.05, 0.10, 0.20, 0.30]
STOP_GRID = [0.03, 0.05, 0.10]
TRAIL_GRID = [0.03, 0.05, 0.08, 0.10]

def slip_for(p):
    return SLIP.get(p, SLIP_OTHER)

def ts(s):
    return datetime.fromisoformat(s).timestamp()

def bars(pair, t0, t1):
    """Hourly (timestamp, close) fully inside (t0, t1]."""
    out = []
    try:
        with open(os.path.join(CANDLES, f"{pair}_3600s.csv")) as f:
            for r in csv.DictReader(f):
                t = int(r["timestamp"])
                if t0 < t + 3600 <= t1 + 1:
                    out.append((t, float(r["close"])))
    except Exception:
        pass
    return sorted(out)

def round_trips():
    """Pair each BUY with the next SELL for the same bot+pair."""
    rows = list(csv.DictReader(open(TRLOG)))
    open_by, trips = {}, []
    for r in rows:
        k = (r["bot"], r["pair"])
        if r["action"] == "BUY":
            open_by[k] = r
        elif r["action"] == "SELL" and k in open_by:
            trips.append((open_by.pop(k), r))
    return trips

def sell_net(u, c, pair, cost, stop=False):
    px = c * (1 - slip_for(pair) * (STOP_MULT if stop else 1))
    proceeds = u * px
    return proceeds - proceeds * FEE - cost

def replay(buy, sell, kind, lvl):
    """Return (net, fired) for one rule on one closed trip."""
    pair, base = buy["pair"], float(buy["px"])
    u, t0, t1 = float(buy["units"]), ts(buy["utc"]), ts(sell["utc"])
    cost = u * base + float(buy["fee"])
    peak = base
    for _, c in bars(pair, t0, t1):
        peak = max(peak, c)
        if kind == "tp" and c >= base * (1 + lvl):
            return sell_net(u, c, pair, cost), True
        if kind == "stop" and c <= base * (1 - lvl):
            return sell_net(u, c, pair, cost, stop=True), True
        if kind == "trail" and c <= peak * (1 - lvl):
            return sell_net(u, c, pair, cost, stop=True), True
    return float(sell["net_pnl"]), False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="also write a markdown report here")
    a = ap.parse_args()
    trips = round_trips()
    lines = []
    say = lambda s: (print(s), lines.append(s))
    say(f"# Exit autopsy — {len(trips)} closed round trips "
        f"({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)")
    say("")
    actual = sum(float(s["net_pnl"]) for _, s in trips)
    say(f"Actual net P&L over these trips: **${actual:+,.2f}**")
    say("")
    say("Per-trade excursions (hourly closes, entry->actual exit):")
    say("")
    say("| bot | pair | hold_h | MFE% | MAE% | net$ | exit |")
    say("|---|---|---|---|---|---|---|")
    for b, s in trips:
        base = float(b["px"])
        xs = [c for _, c in bars(b["pair"], ts(b["utc"]), ts(s["utc"]))]
        mfe = (max(xs) / base - 1) * 100 if xs else 0.0
        mae = (min(xs) / base - 1) * 100 if xs else 0.0
        say(f"| {b['bot']} | {b['pair']} | {s['hold_h']} "
            f"| {mfe:+.2f} | {mae:+.2f} | {float(s['net_pnl']):+.2f} "
            f"| {s['exit_kind']} |")
    say("")
    say("Counterfactual rules (unfired rules fall back to the actual exit):")
    say("")
    say("| rule | level | fired | net$ | vs actual |")
    say("|---|---|---|---|---|")
    grids = [("tp", TP_GRID), ("stop", STOP_GRID), ("trail", TRAIL_GRID)]
    for kind, grid in grids:
        for lvl in grid:
            res = [replay(b, s, kind, lvl) for b, s in trips]
            tot = sum(n for n, _ in res)
            n_f = sum(1 for _, f in res if f)
            say(f"| {kind} | {lvl:.0%} | {n_f}/{len(res)} "
                f"| {tot:+,.2f} | {tot - actual:+,.2f} |")
    say("")
    say(f"_Sample is {len(trips)} trades; treat every row as a hint._")
    if a.md:
        os.makedirs(os.path.dirname(a.md), exist_ok=True)
        with open(a.md, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"\nwrote {a.md}")

if __name__ == "__main__":
    main()
