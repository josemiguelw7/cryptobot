"""
HOURLY ENTRANCE EXAM — the formal gate for intraday (hourly) candidates.

Spec: docs/intraday_standard.md (pre-registered 2026-07-31, stricter-only).
That document predicts ZERO passes at these costs; this runner exists to
give the hourly hypothesis a fair, one-shot chance to overturn that.

Shares simulate_window() and _dd() with the daily exam so both timeframes
travel the identical simulation path. Strategy objects come from
bot/seeds_crypto.py — the same objects bot/squad.py trades forward (W1.1).

The nine criteria, verbatim from the standard:
  1 SAMPLE   >= 24 windows across >= 4 pairs
  2 SAFETY   drawdown never worse than buy-and-hold, same window
  3 RISKEDGE shallower drawdown in >= 60% of windows
  4 RETURN   stitched >= buy-and-hold charged the SAME fees
  5 ACTIVITY >= 4 trades
  6 FEESTRESS criteria 2-4 must ALSO hold at 1.5x fee+slip (BINDING)
  7 BEATSDAILY stitched >= best daily PASS on these pairs; no daily
    strategy has ever passed, so this resolves to criterion 4
  8 HOLDOUT  criteria 2-4 on the reserved final 120 days
  9 NOTLUCK  permutation p < 0.05 AND Sharpe > expected_max_sharpe(K)
    where K = every ledger row (any timeframe) + every hourly variant
    ever screened (results/screened_1h.json)

One exam per candidate name, EVER — enforced via the shared ledger.
Screening (--screen) is unlimited but COUNTED: it increments
screened_1h.json, which raises the criterion-9 luck hurdle for everyone
after it. Curiosity is free; it is not invisible.

Usage:
    python backtest/exam_1h.py --selftest
    python backtest/exam_1h.py --screen h_trend_168
    python backtest/exam_1h.py --candidate h_trend_168 --iters 200
"""
import argparse, csv, hashlib, json, os, sys
from datetime import date, datetime, timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam                      # simulate_window, _dd, ledger helpers
import validation                # expected_max_sharpe
import seeds_crypto as SEEDS

RESULTS = os.path.join(HERE, "results")
LEDGER = exam.LEDGER
SCREEN_COUNT = os.path.join(RESULTS, "screened_1h.json")
CANDLES = os.path.join(ROOT, "data", "candles")

WIN, STEP = 2160, 1080           # 90d / 45d in hourly bars
HOLDOUT_DAYS = 120
GAP_LIMIT_S = 6 * 3600           # windows containing a >6h gap: discarded
FEE, SLIP = 0.006, 0.0005        # the standard's costs, not the charter's
PAIRS = SEEDS.PAIRS
DD_EPS = exam.DD_EPS


# ---------------------------------------------------------------- data

def load_hourly(pair):
    """Completed hourly closes + epoch timestamps, oldest..newest.
    Drops the still-forming bar so exam and live see identical data."""
    path = os.path.join(CANDLES, f"{pair}_3600s.csv")
    if not os.path.exists(path):
        return [], []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    now = datetime.now(timezone.utc).timestamp()
    closes, ts = [], []
    for r in rows:
        t = int(r["timestamp"])
        if t + 3600 <= now:                  # bar has fully closed
            closes.append(float(r["close"]))
            ts.append(t)
    return closes, ts


def holdout_cutoff(all_ts):
    """Epoch second where the reserved final 120 days begin."""
    return max(t for p in PAIRS for t in (all_ts.get(p) or [0])[-1:]) \
        - HOLDOUT_DAYS * 86400


def window_has_gap(ts, a, b):
    return any(ts[i] - ts[i - 1] > GAP_LIMIT_S for i in range(a + 1, b))


def windows_for(pair, strat, closes, ts, lo_idx, hi_idx, fee, slip,
                dates=True):
    """Grade rolling windows whose [a, a+WIN) lies inside [lo_idx,
    hi_idx). Warmup may reach back before lo_idx — history is visible,
    the GRADED span is what's restricted. Windows containing a >6h gap
    are discarded, never interpolated."""
    rows, dropped = [], 0
    start = max(strat.warmup, lo_idx)
    while start + WIN <= hi_idx:
        if window_has_gap(ts, start, start + WIN):
            dropped += 1
            start += STEP
            continue
        curve, trades = exam.simulate_window(strat, closes, start,
                                             start + WIN, fee, slip)
        if curve:
            w = closes[start:start + WIN]
            bh = [c / w[0] for c in w]
            rows.append({
                "pair": pair,
                "start": datetime.fromtimestamp(
                    ts[start], timezone.utc).strftime("%Y-%m-%d %H:%M")
                    if dates else "",
                "ret": curve[-1] - 1, "bh": w[-1] / w[0] - 1,
                "bh_net": (w[-1] / w[0]) * (1 - fee - slip) - 1,
                "dd": exam._dd(curve), "bh_dd": exam._dd(bh),
                "trades": trades, "curve": curve})
        start += STEP
    return rows, dropped


# ---------------------------------------------------------------- grading

def stitched(rows, key="ret"):
    return float(np.prod([1 + r[key] for r in rows]) - 1)


def base_checks(rows):
    """Criteria 2-4 on a row set (used for main, stress, and holdout)."""
    n = len(rows)
    worse = sum(1 for r in rows if r["dd"] < r["bh_dd"] - DD_EPS)
    shallow = sum(1 for r in rows if r["dd"] > r["bh_dd"] + DD_EPS)
    return {
        "2_safety": n > 0 and worse == 0,
        "3_riskedge": n > 0 and shallow / n >= 0.60,
        "4_return": stitched(rows) >= stitched(rows, "bh_net"),
    }, {"worse_dd": worse, "shallower_pct": (shallow / n) if n else 0.0}


def sharpe_annualized_from_rows(rows):
    """Annualized Sharpe of the stitched simulation: per-window hourly
    equity curves -> hourly returns -> 24-bar daily aggregation ->
    sqrt(365). Hourly bars are NOT independent observations (see the
    standard's statistical warning); daily aggregation removes the
    worst of the sample-size inflation before annualizing."""
    hourly = []
    for r in rows:
        c = r["curve"]
        hourly += [c[0] - 1] + [c[i] / c[i - 1] - 1
                                for i in range(1, len(c))]
    daily = [float(np.prod([1 + x for x in hourly[i:i + 24]]) - 1)
             for i in range(0, len(hourly) - 23, 24)]
    if len(daily) < 30:
        return 0.0
    mu, sd = float(np.mean(daily)), float(np.std(daily, ddof=1))
    return (mu / sd) * (365 ** 0.5) if sd > 0 else 0.0


def n_trials():
    """Global multiple-testing count: every ledger row, any timeframe,
    plus every hourly variant ever screened. Baseline 30 screened comes
    from the standard itself ('10 recorded + ~30 screened')."""
    ledger = 0
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            ledger = sum(1 for _ in csv.DictReader(f))
    screened = 30
    if os.path.exists(SCREEN_COUNT):
        try:
            screened = json.load(open(SCREEN_COUNT))["count"]
        except Exception:
            pass
    return ledger + screened


def bump_screened(name):
    os.makedirs(RESULTS, exist_ok=True)
    st = {"count": 30, "log": []}
    if os.path.exists(SCREEN_COUNT):
        try:
            st = json.load(open(SCREEN_COUNT))
        except Exception:
            pass
    st["count"] = st.get("count", 30) + 1
    st.setdefault("log", []).append(
        {"name": name, "utc": f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}"})
    json.dump(st, open(SCREEN_COUNT, "w"), indent=2)
    return st["count"]


def permutation_p(strat, data, cutoff_idx, real_stitched, n_iter, seed=0):
    """Shuffle each pair's hourly returns inside the main region (keeps
    the timestamp skeleton, so the gap policy bites identically), regrade,
    count how often chance matches the real stitched return."""
    import random
    rng = random.Random(seed)
    beats = 0
    for _ in range(n_iter):
        rows = []
        for p in PAIRS:
            closes, ts = data[p]
            hi = cutoff_idx[p]
            if hi < 2:
                continue
            rets = [closes[i] / closes[i - 1] for i in range(1, hi)]
            rng.shuffle(rets)
            shuf = [closes[0]]
            for r in rets:
                shuf.append(shuf[-1] * r)
            shuf += closes[hi:]              # holdout untouched, unused
            rws, _ = windows_for(p, strat, shuf, ts, 0, hi, FEE, SLIP,
                                 dates=False)
            rows += rws
        if rows and stitched(rows) >= real_stitched:
            beats += 1
    return (beats + 1) / (n_iter + 1)


# ---------------------------------------------------------------- provenance

def fingerprint_1h():
    parts = []
    for p in PAIRS:
        path = os.path.join(CANDLES, f"{p}_3600s.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                parts.append(f"{p}:{hashlib.md5(f.read()).hexdigest()[:8]}")
    return ";".join(parts)


def ledger_record_1h(name, verdict, sm):
    exam.require_clean_tree(name)
    os.makedirs(RESULTS, exist_ok=True)
    n_examined = len(exam.ledger_names()) + 1
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow(
            [name, date.today().isoformat(),
             "PASS" if verdict else "FAIL", sm["windows"], sm["pairs"],
             f"{sm['stitched']:.4f}", f"{sm['stitched_bh']:.4f}",
             sm["trades"], exam.git_hash(), n_examined,
             fingerprint_1h(), "1h"])


# ---------------------------------------------------------------- the exam

def run(name, record, n_iter, screen=False):
    strat = SEEDS.get(name)
    data = {p: load_hourly(p) for p in PAIRS}
    cutoff = holdout_cutoff({p: data[p][1] for p in PAIRS})
    cutoff_idx = {}
    for p in PAIRS:
        ts = data[p][1]
        cutoff_idx[p] = next((i for i, t in enumerate(ts) if t >= cutoff),
                             len(ts))

    main_rows, holdout_rows, dropped = [], [], 0
    for p in PAIRS:
        closes, ts = data[p]
        if not closes:
            continue
        r, d = windows_for(p, strat, closes, ts, 0, cutoff_idx[p],
                           FEE, SLIP)
        main_rows += r
        dropped += d
        r, d = windows_for(p, strat, closes, ts, cutoff_idx[p], len(ts),
                           FEE, SLIP)
        holdout_rows += r

    if not main_rows:
        print(f"{name}: no valid main windows.")
        return False

    n, pairs = len(main_rows), len({r["pair"] for r in main_rows})
    bc, bd = base_checks(main_rows)
    trades = sum(r["trades"] for r in main_rows)

    stress_rows = []
    for p in PAIRS:
        closes, ts = data[p]
        if closes:
            r, _ = windows_for(p, strat, closes, ts, 0, cutoff_idx[p],
                               FEE * 1.5, SLIP * 1.5)
            stress_rows += r
    sc, _ = base_checks(stress_rows)
    hc, _ = base_checks(holdout_rows)

    sr = sharpe_annualized_from_rows(main_rows)
    K = n_trials()
    hurdle = validation.expected_max_sharpe(K, var_sharpe=0.25)

    checks = {
        "1_sample   (>=24 win, >=4 pairs)": n >= 24 and pairs >= 4,
        "2_safety   (DD never worse)": bc["2_safety"],
        "3_riskedge (shallower >=60%)": bc["3_riskedge"],
        "4_return   (>= B&H net-to-net)": bc["4_return"],
        "5_activity (>=4 trades)": trades >= 4,
        "6_feestress(2-4 hold @1.5x)": all(sc.values()),
        "7_beatsdaily(no daily pass -> =4)": bc["4_return"],
        "8_holdout  (2-4 on final 120d)": all(hc.values()),
    }
    p_val = None
    if not screen:
        print(f"[criterion 9] permutation x{n_iter} ... (minutes)",
              flush=True)
        p_val = permutation_p(strat, data, cutoff_idx,
                              stitched(main_rows), n_iter)
        checks["9_notluck  (p<0.05 & SR>hurdle)"] = (
            p_val < 0.05 and sr > hurdle)

    verdict = all(checks.values())
    sm = {"windows": n, "pairs": pairs, "stitched": stitched(main_rows),
          "stitched_bh": stitched(main_rows, "bh"),
          "stitched_bhn": stitched(main_rows, "bh_net"),
          "trades": trades, "sharpe": sr, "luck_hurdle": hurdle,
          "K_trials": K, "p_value": p_val, "dropped_gap_windows": dropped,
          "holdout_windows": len(holdout_rows),
          "shallower_pct": bd["shallower_pct"]}

    label = "SCREEN (unrecorded, counted)" if screen else "HOURLY EXAM"
    print(f"\n=== {label}: {name} ===")
    print(f"main windows {n} ({pairs} pairs, {dropped} dropped for gaps)"
          f" | holdout windows {len(holdout_rows)} | trades {trades}")
    print(f"stitched {sm['stitched']:+.1%} vs B&H {sm['stitched_bh']:+.1%}"
          f" (net {sm['stitched_bhn']:+.1%})")
    print(f"Sharpe {sr:.2f} vs luck hurdle {hurdle:.2f} (K={K} trials)"
          + (f" | permutation p={p_val:.4f}" if p_val is not None else ""))
    for lbl, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {lbl}")
    print(f"VERDICT: "
          f"{'PASS - candidate' if verdict else 'FAIL - control only'}"
          + (" (screen: not binding)" if screen else ""))

    if record and not screen:
        for r in main_rows + holdout_rows:
            r.pop("curve", None)
        import pandas as pd
        out = os.path.join(RESULTS, f"exam1h_{name}_{date.today()}.csv")
        pd.DataFrame(main_rows + holdout_rows).to_csv(out, index=False)
        ledger_record_1h(name, verdict, sm)
        print(f"saved -> {out}\nledger -> {LEDGER} (timeframe=1h)")
    return verdict


# ---------------------------------------------------------------- selftest

def selftest():
    """Machinery checks on SYNTHETIC data only — no real strategy is
    screened, so the trial count is untouched."""
    import strategies as S
    print("SELFTEST on synthetic series (trial count untouched)")
    rng = np.random.default_rng(7)
    n = 6000
    closes = list(100 * np.cumprod(1 + rng.normal(0.0001, 0.004, n)))
    ts = [1700000000 + 3600 * i for i in range(n)]
    hold = S.Hold()
    rows, dropped = windows_for("SYN", hold, closes, ts, 0, n, FEE, SLIP)
    ok1 = all(abs((1 + r["ret"]) / ((1 + r["bh"]) * (1 - FEE - SLIP)) - 1)
              < 1e-9 for r in rows)
    print(f"  [{'PASS' if ok1 else 'FAIL'}] hold == B&H net of entry cost "
          f"({len(rows)} windows)")
    ts2 = list(ts)
    ts2[3000] += 8 * 3600            # inject a 8h gap
    _, d2 = windows_for("SYN", hold, closes, ts2, 0, n, FEE, SLIP)
    ok2 = d2 > dropped
    print(f"  [{'PASS' if ok2 else 'FAIL'}] gap policy discards windows "
          f"({dropped} -> {d2})")
    sr = sharpe_annualized_from_rows(rows)
    print(f"  [info] synthetic-drift Sharpe {sr:.2f} "
          f"(should be near the injected drift, not inflated)")
    return ok1 and ok2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate")
    ap.add_argument("--screen")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--iters", type=int, default=200)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.screen:
        bump_screened(a.screen)
        run(a.screen, record=False, n_iter=0, screen=True)
        return
    if not a.candidate:
        sys.exit(f"--candidate NAME, --screen NAME or --selftest. "
                 f"Seeds: {sorted(SEEDS.SEEDS)}")
    if a.candidate in exam.ledger_names():
        sys.exit(f"REFUSED: {a.candidate!r} already examined. One exam "
                 f"per name, ever (docs/intraday_standard.md).")
    # fail fast: check the tree BEFORE a multi-minute permutation run,
    # not after, so a dirty tree costs seconds instead of the exam.
    exam.require_clean_tree(a.candidate)
    run(a.candidate, record=True, n_iter=a.iters)


if __name__ == "__main__":
    main()
