"""
EPOCH-2 DRY RUN — signal sanity, NOT a backtest and NOT an exam.

Reads real bars from the local store and reports, for each proposed
seed: does it produce signals at all, how often, and how many names it
would pick right now. It computes NO returns, so it cannot be used to
pick seeds on performance -- that is exactly what it is designed to
prevent. The exam is the only thing that judges.

Run: .venv/bin/python bot/dryrun_v2.py [crypto|stocks]
"""
from __future__ import annotations
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main(cls="crypto"):
    import squad as Q
    if cls == "stocks":
        import squad_stocks                      # installs overrides
        import seeds_stocks_v2 as R
        load = Q.load_bars
    else:
        import seeds_crypto_v2 as R
        load = Q.load_bars

    bars = {p: load(p) for p in R.PAIRS}
    mkt = bars.get(Q.MARKET) or load(Q.MARKET)
    print(f"{cls} epoch-2 dry run · MAX_POS={R.MAX_POS} · "
          f"market proxy {Q.MARKET}")
    print(f"  bars available: " +
          ", ".join(f"{p}:{len(bars[p])}" for p in R.PAIRS))
    print()

    for n, cfg in R.SEEDS.items():
        s = cfg["strat"]
        short = [p for p in R.PAIRS if len(bars[p]) < s.warmup + 1]
        if getattr(s, "cross_sectional", False):
            elig = {p: bars[p] for p in R.PAIRS if p not in short}
            ctx = {p: {"weight": 0.0} for p in elig}
            try:
                w = s.step_all(elig, ctx)
            except Exception as e:
                print(f"  {n:12s} ERROR {e}")
                continue
            picks = [p for p, v in w.items() if v > 0]
            print(f"  {n:12s} picks now: {picks or 'none'}"
                  + (f"  [short history: {short}]" if short else ""))
            continue

        fires, picks = 0, []
        for p in R.PAIRS:
            if p in short:
                continue
            ctx = {"weight": 0.0, "entry_price": None}
            if getattr(s, "wants_market", False):
                ctx["market"] = mkt
            try:
                sig = s.step_bars(bars[p], ctx)
            except Exception as e:
                print(f"  {n:12s} ERROR on {p}: {e}")
                break
            if sig > 0:
                picks.append(p)
            # historical fire rate on the last 300 closed bars
            for i in range(max(s.warmup + 1, len(bars[p]) - 300),
                           len(bars[p])):
                c2 = {"weight": 0.0, "entry_price": None}
                if getattr(s, "wants_market", False):
                    c2["market"] = mkt[:i]
                try:
                    if s.step_bars(bars[p][:i], c2) > 0:
                        fires += 1
                except Exception:
                    pass
        else:
            n_eval = max(1, (len(R.PAIRS) - len(short)) * 300)
            print(f"  {n:12s} signals now: {len(picks)}/"
                  f"{len(R.PAIRS)-len(short)}  "
                  f"fire rate {100*fires/n_eval:5.1f}%  {picks[:5]}"
                  + (f"  [short: {short}]" if short else ""))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "crypto")
