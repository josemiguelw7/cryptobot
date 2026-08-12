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
import argparse, csv, hashlib, json, math, os, sys
from datetime import date, datetime, timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam                      # simulate_window, _dd, ledger helpers
import validation                # expected_max_sharpe
import os as _os
_ROSTER = _os.environ.get("EXAM_ROSTER", "seeds_crypto")
SEEDS = __import__(_ROSTER)          # EXAM_ROSTER=seeds_crypto_v2 for epoch 2

RESULTS = os.path.join(HERE, "results")
LEDGER = exam.LEDGER
SCREEN_COUNT = os.path.join(RESULTS, "screened_1h.json")
CANDLES = os.path.join(ROOT, "data", "candles")

WIN, STEP = 2160, 1080           # 90d / 45d in hourly bars
HOLDOUT_DAYS = 120
GAP_LIMIT_S = 6 * 3600           # windows containing a >6h gap: discarded
FEE, SLIP = 0.006, 0.0005        # the standard's costs, not the charter's
PAIRS = SEEDS.PAIRS
MARKET = _os.environ.get("EXAM_MARKET", "BTC-USD")
TIMEFRAME = "1h"
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


def load_bars_exam(pair):
    """Full completed candles, same completeness rule as load_hourly."""
    path = os.path.join(CANDLES, f"{pair}_3600s.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    now = datetime.now(timezone.utc).timestamp()
    out = []
    for r in rows:
        t = int(r["timestamp"])
        if t + 3600 <= now:
            out.append((t, float(r["open"]), float(r["high"]),
                        float(r["low"]), float(r["close"]),
                        float(r["volume"])))
    return out


BARS_CACHE = {}


def permute_bars(bars, rng):
    """Criterion-9 permutation for full candles.

    Each bar is decomposed into its shape RELATIVE to the previous close
    (open/high/low/close ratios + volume), the sequence of shapes is
    shuffled, and a new path is rebuilt. Every individual candle keeps
    its geometry -- a hammer is still a hammer -- but the ORDER is
    destroyed. That is precisely the null criterion 9 tests: is the
    sequence informative, or would any order have done as well?"""
    if len(bars) < 2:
        return list(bars)
    shapes = []
    for i in range(1, len(bars)):
        pc = bars[i - 1][4]
        shapes.append((bars[i][1] / pc, bars[i][2] / pc, bars[i][3] / pc,
                       bars[i][4] / pc, bars[i][5]))
    rng.shuffle(shapes)
    out = [bars[0]]
    c = bars[0][4]
    for i, (ro, rh, rl, rc, v) in enumerate(shapes, start=1):
        o, h, l = c * ro, c * rh, c * rl
        c = c * rc
        out.append((bars[i][0], o, max(h, o, c), min(l, o, c), c, v))
    return out


def windows_for(pair, strat, closes, ts, lo_idx, hi_idx, fee, slip,
                dates=True, bars_map=None):
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
        if getattr(strat, "wants_bars", False):
            src = bars_map if bars_map is not None else BARS_CACHE
            if bars_map is None:
                src.setdefault(pair, load_bars_exam(pair))
            bars = src[pair]
            mkt = None
            if getattr(strat, "wants_market", False):
                if bars_map is None:
                    src.setdefault(MARKET, load_bars_exam(MARKET))
                mkt = src.get(MARKET)
            panel = None
            if getattr(strat, "cross_sectional", False):
                if bars_map is None:
                    for p in PAIRS:
                        src.setdefault(p, load_bars_exam(p))
                panel = {p: src[p] for p in PAIRS if p in src}
            curve, trades = exam.simulate_window_bars(
                strat, bars, start, start + WIN, fee, slip,
                market=mkt, panel=panel, pair=pair)
        else:
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

def median_window(rows, key="ret"):
    """C0.1: mediana del retorno neto POR VENTANA.

    Reemplaza a stitched() como metrica de magnitud. stitched() compone
    ventanas que se solapan al 50% (WIN=2160, STEP=1080), asi que la
    misma semana calendario entra dos veces en el producto: en cripto
    bajista clava todo en el piso de -100%, y en un mercado alcista
    largo explota a millones de por ciento. Las magnitudes del ledger
    hasta 2026-08-07 no son interpretables por eso. stitched() se
    conserva solo para reproducir filas viejas.
    """
    if not rows:
        return float("nan")
    v = sorted(r[key] for r in rows)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def beat_bh_pct(rows):
    """C0.1: fraccion de ventanas donde la semilla gana a B&H neto."""
    if not rows:
        return float("nan")
    return sum(1 for r in rows if r["ret"] > r["bh_net"]) / len(rows)


def pct_windows_traded(rows):
    """C0.1b (2026-08-08, endurecida 2026-08-08b): fraccion de ventanas
    con al menos una IDA Y VUELTA completa.

    Version original contaba `trades > 0`. Pero `trades` cuenta CAMBIOS
    DE PESO, y una ida y vuelta son dos. `trades == 1` significa "entro
    y nunca salio": un clon de buy-and-hold, no actividad. Medido en
    d3_trend: 48% ventanas en efectivo, 50% con trades==1 (clones B&H),
    1.4% con ida y vuelta real -- y la metrica original reportaba 51%
    de "cobertura". El mismo agujero que intentaba tapar, un nivel mas
    abajo (revision externa 2026-08-08, H-2).
    """
    if not rows:
        return float("nan")
    return sum(1 for r in rows if r["trades"] >= 2) / len(rows)


def median_window_traded(rows):
    """Mediana neta contando SOLO ventanas con ida y vuelta: que hace
    la semilla cuando efectivamente juega."""
    t = [r for r in rows if r["trades"] >= 2]
    return median_window(t) if t else float("nan")


def regime_split(rows, band=0.02):
    """C0.2: particiona por signo de B&H. Reporte, NO puerta.

    Responde la pregunta que el total esconde: 6 de 11 semillas le ganan
    a B&H mientras pierden dinero, o sea son DEFENSIVAS (pierden menos
    que aguantar). Esto separa defensa de alfa.
    """
    g = {"alcista": [], "bajista": [], "lateral": []}
    for r in rows:
        k = ("lateral" if abs(r["bh"]) <= band
             else ("alcista" if r["bh"] > 0 else "bajista"))
        g[k].append(r)
    return {k: {"n": len(v), "median_net": median_window(v),
                "beat_bh": beat_bh_pct(v)} for k, v in g.items() if v}


def stitched(rows, key="ret"):
    return float(np.prod([1 + r[key] for r in rows]) - 1)


def base_checks(rows):
    """Criteria 2-4 on a row set (used for main, stress, and holdout).

    2026-08-08b (revision externa, C-3 y H-2):

    * Criterio 4 se decide con la MEDIANA POR VENTANA, no con stitched().
      C0.1 retiro stitched() como "no interpretable" pero seguia
      decidiendo los criterios 4/6/7/8/9 -- el retiro cambio lo impreso,
      no lo que puertea. Las magnitudes de orden 10^12 en el ledger del
      2026-08-08 salen de ahi.
    * Criterio 3 excluye ventanas SIN ida y vuelta: el 96% del credito
      de "drawdown mas superficial" de d3_trend venia de ventanas donde
      la semilla no hizo nada. Abstenerse no puede puntuar como acierto.
    """
    n = len(rows)
    worse = sum(1 for r in rows if r["dd"] < r["bh_dd"] - DD_EPS)
    active = [r for r in rows if r["trades"] >= 2]
    shallow = sum(1 for r in active if r["dd"] > r["bh_dd"] + DD_EPS)
    return {
        "2_safety": n > 0 and worse == 0,
        "3_riskedge": len(active) > 0 and shallow / len(active) >= 0.60,
        "4_return": median_window(rows) >= median_window(rows, "bh_net"),
    }, {"worse_dd": worse,
        "shallower_pct": (shallow / len(active)) if active else 0.0,
        "active_windows": len(active)}


def daily_returns_from_rows(rows):
    """Per-window hourly equity curves -> daily returns, aggregated
    WITHIN each window (2026-08-08b, M-8: the old version concatenated
    all curves into one stream and folded blocks of 24 across window
    and even PAIR boundaries -- some "days" were 14 hours of BTC plus
    10 of ETH). Leftover hours shorter than a day are dropped."""
    daily = []
    for r in rows:
        c = r["curve"]
        hourly = [c[0] - 1] + [c[i] / c[i - 1] - 1
                               for i in range(1, len(c))]
        daily += [float(np.prod([1 + x for x in hourly[i:i + 24]]) - 1)
                  for i in range(0, len(hourly) - 23, 24)]
    return daily


def nonoverlap_rows(rows):
    """Every other window PER PAIR (windows overlap 50%: WIN=2160,
    STEP=1080). This is the series the statistical gates run on, so
    the same calendar hour is never counted twice."""
    by_pair = {}
    for r in rows:
        by_pair.setdefault(r["pair"], []).append(r)
    out = []
    for p in sorted(by_pair):
        out += by_pair[p][::2]
    return out


# Cross-pair correlation of the examined universe, measured by
# analysis/engine_sim.py on 2026-08-07 (median pairwise 0.77). Eight
# pairs this correlated carry roughly the information of 1.3
# independent ones; the effective sample size for the luck hurdle is
# discounted accordingly. Re-measure when the universe changes.
UNIVERSE_RHO = 0.77


def effective_daily_obs(rows):
    """Effective number of independent daily observations backing the
    Sharpe estimate: non-overlapping windows only, discounted for
    cross-pair correlation via n_eff = n / (1 + (n-1)*rho).

    This replaces the hardcoded var_sharpe=0.25 (2026-08-08b, H-3): the
    old hurdle assumed a Sharpe dispersion that corresponded to no
    sample size the exam actually uses. Now the dispersion is derived
    from the data actually graded: var(annualized SR) ~= 365 / T_eff."""
    nov = nonoverlap_rows(rows)
    daily = daily_returns_from_rows(nov)
    pairs = len({r["pair"] for r in nov})
    if not daily or pairs == 0:
        return 0.0
    n_eff_pairs = pairs / (1.0 + (pairs - 1) * UNIVERSE_RHO)
    return len(daily) * (n_eff_pairs / pairs)


def sharpe_annualized_from_rows(rows):
    """Annualized Sharpe of daily net returns over NON-OVERLAPPING
    windows (2026-08-08b: the overlapping set double-counts calendar
    time, inflating nominal sample size ~2x on top of the pair
    correlation)."""
    daily = daily_returns_from_rows(nonoverlap_rows(rows))
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
    # K carried across the 2026-08-04 ledger wipe. The names were
    # cleared; the trials were not un-run. See k_offset.json.
    off = os.path.join(RESULTS, "k_offset.json")
    if os.path.exists(off):
        try:
            d = json.load(open(off))
            ledger += int(d.get("carried_ledger_rows", 0))
        except Exception:
            pass
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


def permutation_p(strat, data, cutoff_idx, real_stat, n_iter, seed=0):
    """Shuffle each pair's hourly returns inside the main region (keeps
    the timestamp skeleton, so the gap policy bites identically), regrade,
    count how often chance matches the real result.

    2026-08-08b: the test statistic is the PER-WINDOW MEDIAN net return
    (C0.1), not stitched() -- stitched compounds 50%-overlapping windows
    and was formally retired as uninterpretable. Both the real and
    permuted sides travel identical geometry, so overlap does not bias
    the p-value; the statistic just has to mean something.

    Known limitation (M-5, documented not fixed): permute_bars clamps
    high/low after reshuffling, so wick geometry is distorted. For
    candle-PATTERN seeds this null tests order AND shape, not order
    alone. No current seed reads wicks; re-open before examining one."""
    import random
    rng = random.Random(seed)
    beats = 0
    bar_mode = getattr(strat, "wants_bars", False)
    for _ in range(n_iter):
        rows = []
        bmap = None
        if bar_mode:
            # every pair (and the market proxy) permuted independently,
            # so cross-sectional and cross-asset structure dies too
            bmap = {}
            for p in set(PAIRS) | {MARKET}:
                rb = BARS_CACHE.setdefault(p, load_bars_exam(p))
                bmap[p] = permute_bars(rb, rng) if rb else rb
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
                                 dates=False, bars_map=bmap)
            rows += rws
        if rows and median_window(rows) >= real_stat:
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
    s2 = sm.get("slip2x_net")
    rg = sm.get("regimes") or {}
    def _rg(k):
        d = rg.get(k)
        return f"{d['median_net']:.4f}" if d else ""
    # H-4: the hash pinned at run START, never re-read at write time.
    ghash = sm.get("git_hash_start") or exam.git_hash()
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow(
            [name, date.today().isoformat(),
             "PASS" if verdict else "FAIL", sm["windows"], sm["pairs"],
             f"{sm['stitched']:.4f}", f"{sm['stitched_bh']:.4f}",
             sm["trades"], ghash, n_examined,
             fingerprint_1h(), TIMEFRAME,
             f"{sm.get('realized_hold', 0):.1f}",
             sm.get("declared_hold", 0), sm.get("turnover_flag", "?"),
             (f"{s2:.4f}" if s2 == s2 else ""),
             f"{sm.get('median_win_net', float('nan')):.4f}",
             f"{sm.get('beat_bh_pct', float('nan')):.4f}",
             _rg("alcista"), _rg("bajista"),
             sm.get("dsr_clears", ""),
             # 2026-08-08: estas dos se agregaron al ENCABEZADO pero no
             # a la fila, asi que se leian como None. Los numeros salian
             # por pantalla y no llegaban al archivo.
             f"{sm.get('pct_traded', float('nan')):.4f}",
             f"{sm.get('median_traded', float('nan')):.4f}"])


# ---------------------------------------------------------------- the exam

def source_fingerprint():
    """SHA-256 of the code actually LOADED for this exam: the runner,
    the shared simulator, the strategies, and the roster module. This
    pins provenance to what executed, not to what HEAD said at write
    time (2026-08-08b, H-4: d3_calm's row carried the hash of a fix
    committed 14 minutes into its run, while the row itself was written
    by the pre-fix code -- 21 fields against a 23-field header)."""
    h = hashlib.sha256()
    mods = [os.path.abspath(__file__), exam.__file__,
            os.path.join(ROOT, "bot", "strategies.py"), SEEDS.__file__]
    for m in mods:
        try:
            with open(m.rstrip("c"), "rb") as f:
                h.update(f.read())
        except OSError:
            h.update(b"?")
    return h.hexdigest()[:12]


def run(name, record, n_iter, screen=False):
    # H-4: provenance is captured ONCE, before any simulation. A long
    # permutation run can straddle a commit; the row must pin the code
    # that produced it, not the code that existed when it finished.
    provenance = {"git_hash_start": exam.git_hash(),
                  "src_sha": source_fingerprint(),
                  "started_utc":
                      f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}"}
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
    # 2026-08-08b (H-3): the luck hurdle's dispersion is DERIVED from
    # the effective sample actually graded, not hardcoded. The old
    # var_sharpe=0.25 corresponded to no sample size the exam uses.
    T_eff = effective_daily_obs(main_rows)
    var_sr = (365.0 / T_eff) if T_eff > 0 else 4.0
    hurdle = validation.expected_max_sharpe(K, var_sharpe=var_sr)

    checks = {
        "1_sample   (>=24 win, >=4 pairs)": n >= 24 and pairs >= 4,
        "2_safety   (DD never worse)": bc["2_safety"],
        "3_riskedge (shallower >=60% activas)": bc["3_riskedge"],
        "4_return   (mediana >= B&H net)": bc["4_return"],
        "5_activity (>=4 trades)": trades >= 4,
        "5b_cobertura(ida+vuelta en >=50% ventanas)":
            pct_windows_traded(main_rows) >= 0.50,
        "6_feestress(2-4 hold @1.5x)": all(sc.values()),
        "7_beatsdaily(no daily pass -> =4)": bc["4_return"],
        "8_holdout  (2-4 on final 120d)": all(hc.values()),
    }
    p_val = None
    if not screen:
        print(f"[criterion 9] permutation x{n_iter} ... (minutes)",
              flush=True)
        p_val = permutation_p(strat, data, cutoff_idx,
                              median_window(main_rows), n_iter)
        checks["9_notluck  (p<0.05 & SR>hurdle)"] = (
            p_val < 0.05 and sr > hurdle)

    dsr_prob = float("nan")
    if not screen:
        # C0.3 (plan_v3 F0), reconstruida 2026-08-08b (C-2): la version
        # anterior era LITERALMENTE la segunda mitad del criterio 9
        # (misma llamada, mismos argumentos) -- una puerta que no
        # filtraba nada. Ahora es el DSR real de Bailey & Lopez de
        # Prado (bot/stats.py, el archivo que el charter s5.7 nombra):
        # probabilidad, ajustada por sesgo y curtosis de la serie
        # diaria, de que el Sharpe verdadero supere al maximo esperado
        # de K intentos sin ventaja. Unidades POR PERIODO, como exige
        # stats.py. Umbral de referencia del charter: 0.95.
        import stats as _stats
        daily = daily_returns_from_rows(nonoverlap_rows(main_rows))
        if len(daily) >= 30 and T_eff > 0:
            sr0_daily = _stats.expected_max_sharpe(
                1.0 / math.sqrt(T_eff), K)
            dsr_prob = _stats.probabilistic_sharpe(daily, sr0_daily)
        checks["10_dsr     (DSR >= 0.95 @ K)"] = (
            dsr_prob == dsr_prob and dsr_prob >= 0.95)

    verdict = all(checks.values())
    sm_dsr = "" if (screen or dsr_prob != dsr_prob) else (dsr_prob >= 0.95)
    sm = {"windows": n, "pairs": pairs,
          "median_win_net": median_window(main_rows),
          "pct_traded": pct_windows_traded(main_rows),
          "median_traded": median_window_traded(main_rows),
          "beat_bh_pct": beat_bh_pct(main_rows),
          "regimes": regime_split(main_rows),
          "stitched": stitched(main_rows),
          "stitched_bh": stitched(main_rows, "bh"),
          "stitched_bhn": stitched(main_rows, "bh_net"),
          "trades": trades, "sharpe": sr, "luck_hurdle": hurdle,
          "T_eff_daily": T_eff, "var_sharpe_used": var_sr,
          "dsr_prob": dsr_prob,
          "K_trials": K, "p_value": p_val, "dropped_gap_windows": dropped,
          "holdout_windows": len(holdout_rows),
          "shallower_pct": bd["shallower_pct"],
          "active_windows": bd.get("active_windows", 0),
          "dsr_clears": sm_dsr}
    sm.update(provenance)

    label = "SCREEN (unrecorded, counted)" if screen else "HOURLY EXAM"
    print(f"\n=== {label}: {name} ===")
    print(f"main windows {n} ({pairs} pairs, {dropped} dropped for gaps)"
          f" | holdout windows {len(holdout_rows)} | trades {trades}")
    print(f"POR VENTANA (C0.1): mediana neta {sm['median_win_net']:+.2%}"
          f" · gana a B&H en {sm['beat_bh_pct']:.0%} de las ventanas")
    print(f"COBERTURA (C0.1b): opera en {sm['pct_traded']:.0%} de las "
          f"ventanas · mediana CUANDO OPERA {sm['median_traded']:+.2%}")
    for k, d in (sm.get("regimes") or {}).items():
        print(f"  regimen {k:8s} n={d['n']:3d}  mediana "
              f"{d['median_net']:+7.2%}  gana B&H {d['beat_bh']:4.0%}")
    print(f"[legacy, no interpretable] stitched {sm['stitched']:+.1%} "
          f"vs B&H {sm['stitched_bh']:+.1%} (net {sm['stitched_bhn']:+.1%})")
    print(f"Sharpe {sr:.2f} vs luck hurdle {hurdle:.2f} "
          f"(K={K}, T_eff={T_eff:.0f}d, var_sr={var_sr:.3f})"
          + (f" | permutation p={p_val:.4f}" if p_val is not None else ""))
    if dsr_prob == dsr_prob:
        print(f"DSR (B&LdP, per-period, skew/kurtosis-adjusted): "
              f"{dsr_prob:.4f} vs 0.95")
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
        # -- recorded metrics (amendment 2026-08-04, non-gating) --------
        # turnover honesty: the h2_obv failure mode was a seed declaring
        # a 120h hold while trading every ~28 bars. Realized hold =
        # 2 * evaluated bars / trades (a round trip is two trades).
        declared = 0
        try:
            declared = SEEDS.SEEDS[name].get("hold_h", 0)
        except Exception:
            pass
        total_bars = sm["windows"] * WIN
        realized = (2.0 * total_bars / sm["trades"]) if sm["trades"] \
            else float("inf")
        flag = "CHURN" if (declared and realized < declared / 3.0) else "OK"
        sm["realized_hold"], sm["declared_hold"] = realized, declared
        sm["turnover_flag"] = flag
        print(f"turnover: realized ~{realized:.0f} bars/round-trip vs "
              f"declared {declared} -> {flag}"
              + ("  [WARN: churns >=3x faster than its label]"
                 if flag == "CHURN" else ""))
        s2_rows = []
        for p2 in PAIRS:
            closes2, ts2 = data[p2]
            if not closes2:
                continue
            r2, _ = windows_for(p2, strat, closes2, ts2, 0,
                                cutoff_idx[p2], FEE, SLIP * 2)
            s2_rows += r2
        sm["slip2x_net"] = stitched(s2_rows) if s2_rows else float("nan")
        print(f"slip-stress (2x slippage, recorded not gating): "
              f"stitched {sm['slip2x_net']:+.1%}")

        # ledger FIRST: writing the artifact dirties the tree, and
        # ledger_record_1h re-checks for a clean tree. Writing the CSV
        # first made recording impossible for every candidate.
        ledger_record_1h(name, verdict, sm)
        pd.DataFrame(main_rows + holdout_rows).to_csv(out, index=False)
        # sidecar metrics (2026-08-08b, H-3): full statistical record
        # per exam, JSON-per-line, no ledger schema migration. Future
        # exams estimate the empirical Sharpe dispersion from here.
        metrics = {k: v for k, v in sm.items() if k != "regimes"}
        metrics.update({"candidate": name, "date": date.today().isoformat(),
                        "verdict": "PASS" if verdict else "FAIL",
                        "regimes": sm.get("regimes")})
        with open(os.path.join(RESULTS, "exam_metrics.jsonl"), "a") as f:
            f.write(json.dumps(metrics, default=str) + "\n")
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
