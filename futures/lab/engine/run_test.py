"""Corre una prueba completa de una estrategia y la publica.

  python -m engine.run_test --strategy BIG --version 1 --study tanda1 [--rand 1000] [--flip 200] [--sens] [--limit N]

Pasos (en este orden, siempre):
  1. lista congelada de sesiones + niveles y umbrales (solo pasado)
  2. señales -> operaciones con costos base
  3. RAND emparejado (p valor) · costos de estrés · por año
  4. Topstep (todos los arranques, 50% y 55%)
  5. Red Team: placebo desplazado, direcciones barajadas, curva de costos, concentración
  6. sensibilidad (cada corrida se registra como intento)
  7. veredicto según protocol.json · hoja de resultados · registro · bitácora
"""
import argparse, json, os, sys, time
import numpy as np
from . import config, registry, report, stats, topstep, redteam, ENGINE_VERSION
from .data import load
from .levels import Levels, precompute_stats
from .rand import run_rand, summarize as rand_summary
from .sim import Rules, simulate
from .strategies import v1 as S1, v2 as S2, v3 as S3, v4 as S4, v5 as S5, v6 as S6, v7 as S7, v8 as S8, v9 as S9, v10 as S10, v11 as S11, v12 as S12, v13 as S13, v14 as S14, v15 as S15, v16 as S16, v17 as S17, v18 as S18, v19 as S19, v20 as S20, v21 as S21, v22 as S22, v23 as S23, v24 as S24, v25 as S25, v26 as S26, v27 as S27, v28 as S28, v29 as S29, v30 as S30, v31 as S31, v32 as S32, v33 as S33, v34 as S34, v35 as S35, v36 as S36
import polars as pl

MODULES = {("BIG", 1): S1, ("ABS", 1): S1, ("POC", 1): S1, ("FADE", 1): S2, ("HVN", 1): S2, ("ABS", 2): S2, ("FADE", 2): S2, ("FADEL", 1): S2, ("BIG", 2): S2, ("ORB", 1): S2, ("ABS", 3): S3, ("ACC", 1): S4, ("SMT", 1): S5, ("VAR", 1): S6, ("ACC", 2): S7, ("ABI", 1): S8, ("ABV", 1): S9, ("HVF", 1): S10, ("ABK", 1): S11, ("LVN", 1): S12, ("ABI", 2): S13, ("ABD", 1): S14, ("VBR", 1): S15, ("IMB", 1): S16, ("ABU", 1): S17, ("ABU", 2): S18, ("ABT", 1): S19, ("ABQ", 1): S20, ("DVG", 1): S21, ("FAF", 1): S22, ("ABF", 1): S23, ("ABR", 1): S24, ("ABE", 1): S25, ("ABU", 3): S26, ("ABM", 1): S27, ("ABB", 1): S28, ("VPT", 1): S29, ("ABW", 1): S30, ("OPD", 1): S31, ("ABP", 1): S32, ("ABG", 1): S33, ("IBX", 1): S34, ("CLX", 1): S35, ("ATR", 1): S36}
REG_KEY = {("FADE", 2): "FADE2", ("BIG", 2): "BIG2", ("ABS", 3): "ABS3", ("ACC", 2): "ACC2", ("ABI", 2): "ABI2", ("ABU", 2): "ABU2", ("ABU", 3): "ABU3"}   # nombre del generador/parámetros cuando difiere del id

SENS_STEPS = {
    ("BIG", 1): {"stop": 4, "target": 8, "confirm_s": 10, "near_ticks": 1},
    ("ABS", 1): {"near_ticks": 1, "stop_min": 4, "rr": 0.5, "confirm_s": 10},
    ("POC", 1): {"touch_ticks": 1, "back_ticks": 1, "stop_min": 4, "confirm_s": 30},
    ("FADE", 1): {"stop": 4, "cooldown_s": 30, "min_levels": 1, "max_min": 5},
    ("HVN", 1): {"stop": 4, "target": 4, "far_ticks": 4, "hvn_pct": 2},
    ("ABS", 2): {"near_ticks": 1, "stop_min": 4, "target_fixed": 40, "max_min": 5},
    ("FADE", 2): {"stop": 2, "target": 2, "max_min": 3, "cooldown_s": 30},
    ("FADEL", 1): {"stop": 2, "target": 2, "wait_s": 15, "max_min": 3},
    ("BIG", 2): {"stop": 4, "target": 4, "max_min": 5, "cooldown_s": 60},
    ("ORB", 1): {"stop": 4, "target": 4, "max_min": 10, "range_min": 5},
    ("ABS", 3): {"near_ticks": 1, "stop_min": 4, "stop_beyond": 2, "max_min": 5},
    ("ACC", 1): {"hold_s": 90, "delta_pct": 3, "stop_beyond": 2, "max_min": 5},
    ("SMT", 1): {"lookback_s": 30, "fail_s": 30, "stop_beyond": 2, "max_min": 5},
    ("VAR", 1): {"hold_s": 60, "delta_pct": 1, "stop_beyond": 2, "max_min": 10},
    ("ACC", 2): {"hold_s": 90, "delta_pct": 3, "stop_beyond": 2, "max_min": 5},
    ("ABI", 1): {"near_ticks": 1, "confirm_s": 10, "stop_min": 4, "max_min": 5},
    ("HVF", 1): {"hvn_pct": 2, "conf_ticks": 8, "near_ticks": 1, "confirm_s": 10},
    ("ABK", 1): {"refill_pct": 25, "confirm_s": 10, "stop_min": 4, "max_min": 5},
    ("LVN", 1): {"delta_pct": 5, "min_width": 4, "stop_beyond": 2, "max_min": 5},
    ("ABV", 1): {"near_ticks": 2, "confirm_s": 10, "stop_min": 4, "max_min": 5},
    ("ABI", 2): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "max_min": 5},
    ("ABD", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "rr": 0.5},
    ("VBR", 1): {"k_sigma": 0.25, "away_ticks": 1, "max_min": 5, "sigma_floor": 2},
    ("IMB", 1): {"ratio": 0.5, "min_vol": 2, "away_ticks": 1, "max_min": 5},
    ("ABU", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "rr": 0.5},
    ("ABU", 2): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "rr": 0.5},
    ("ABT", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "rr": 0.5},
    ("ABQ", 1): {"near_ticks": 1, "confirm_s": 5, "rel_pct": 2, "rr": 0.5},
    ("DVG", 1): {"pullback_ticks": 2, "away_ticks": 1, "rr": 0.5},
    ("FAF", 1): {"pen_ticks": 1, "fail_s": 30, "stop_max": 4, "rr": 0.5},
    ("ABF", 1): {"brk_ticks": 1, "break_s": 60, "stop": 4, "rr": 0.5},
    ("ABR", 1): {"limit_in_ticks": 1, "stop": 2, "rr": 0.5, "wait_s": 60},
    ("ABU", 3): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "rr": 0.5},
    ("ABM", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "comp_days": 2},
    ("ABB", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "accept_s": 150},
    ("VPT", 1): {"touch_ticks": 2, "ext_min": 8, "delta_pct": 2, "away_ticks": 2},
    ("ABW", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "ib_ratio": 0.1},
    ("ABP", 1): {"near_ticks": 1, "confirm_s": 10, "rel_pct": 2, "shift_ticks": 8},
    ("ABG", 1): {"rr": 0.5, "max_min": 5, "stop_max": 4, "stop_min": 4},
    ("ATR", 1): {"trap_frac": 0.1, "wait_s": 30, "delta_s": 10, "ext_ticks": 1},
    ("CLX", 1): {"vol_mult": 0.5, "delta_min": 0.05, "rise_ticks": 2, "away_ticks": 1},
    ("IBX", 1): {"win_s": 30, "delta_min": 0.02, "brk_ticks": 1, "rr": 0.5},
    ("OPD", 1): {"win_s": 60, "delta_min": 0.01, "move_min": 10, "retrace": 0.2},
    ("ABE", 1): {"es_adv_max": 1, "es_window_s": 30, "rr": 0.5, "confirm_s": 15},
}

# Ventana de entradas propia de una estrategia (segundos ET): el control RAND usa la misma ventana. Por defecto 09:30–11:30, cierre 11:45.
RULES_WINDOW = {("ABI", 2): {"first_entry": 41400.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABD", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("VBR", 1): {"first_entry": 36000.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("IMB", 1): {"first_entry": 36000.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABU", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABU", 2): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2},
                ("ABT", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABQ", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "max_trades": 12},
                ("DVG", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "max_trades": 8},
                ("FAF", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABF", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABR", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABE", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0},
                ("ABU", 3): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("ABM", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("ABB", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("VPT", 1): {"first_entry": 36000.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("ABW", 1): {"first_entry": 36000.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("OPD", 1): {"first_entry": 34440.0, "last_entry": 34680.0, "forced_close": 36000.0, "contracts": 2, "max_consec_losses": 2, "max_trades": 1},
                ("ABP", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2},
                ("ABG", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2},
                ("IBX", 1): {"first_entry": 37800.0, "last_entry": 52200.0, "forced_close": 56700.0, "max_trades": 2, "max_consec_losses": 2},
                ("ATR", 1): {"first_entry": 34200.0, "last_entry": 55800.0, "forced_close": 56700.0, "contracts": 2, "max_consec_losses": 2},
                ("CLX", 1): {"first_entry": 36000.0, "last_entry": 55800.0, "forced_close": 56700.0, "max_trades": 4, "max_consec_losses": 2}}   # 11:30–15:30, cierre 15:45


def strat_kwargs(strategy, version, L, d):
    """Argumentos extra que necesita una estrategia (siempre del pasado)."""
    if (strategy, version) == ("POC", 1):
        return {"open_in_value": L.open_in_value(d)}
    if strategy in ("HVN", "HVF", "LVN"):
        prev = L.prev_date(d); pp = os.path.join(config.FEAT, "profile", "NQ", f"{prev}.parquet") if prev else None
        if pp and os.path.exists(pp):
            pr = pl.read_parquet(pp).filter(pl.col("seg") == "ny"); return {"prof": np.c_[pr["price_t"].to_numpy(), pr["vol"].to_numpy()]}
        return {"prof": None}
    if (strategy, version) == ("ABM", 1):
        i = L.pos.get(d, 0); days = []
        for pd_ in L.dates[max(0, i - 10):i]:           # solo días anteriores, de viejo a nuevo
            pp = os.path.join(config.FEAT, "profile", "NQ", f"{pd_}.parquet"); sm = L.summ.get(pd_, {}).get("ny")
            if not sm or not os.path.exists(pp):
                continue
            pr = pl.read_parquet(pp).filter(pl.col("seg") == "ny")
            days.append({"px": pr["price_t"].to_numpy(), "vol": pr["vol"].to_numpy(), "poc": sm["poc_t"], "hi": sm["high_t"], "lo": sm["low_t"]})
        return {"days": days}
    return {}


def news_windows(date):
    n, _ = config._load("news.json")
    out = []
    for k, w in n["ventanas"].items():
        if date in n.get(k, []):
            h, m = map(int, w["hora_et"].split(":")); c = h * 3600 + m * 60
            out.append((c - 60 * w["antes_min"], c + 60 * w["despues_min"]))
    return tuple(out)


def gen_for(strategy, version):
    m = MODULES.get((strategy, int(version)))
    if m is None:
        raise SystemExit(f"{strategy} v{version} no tiene código registrado en el motor")
    key = REG_KEY.get((strategy, int(version)), strategy)
    return m.REGISTRY[key], dict(m.PARAMS[key])


def verdict(res, protocol_ok):
    r = res
    if r["error"]:
        return "error"
    if r.get("revisar"):
        return "revisar"
    if r["operaciones"] < 100 or r["sesiones_con_senal_posible"] < 120:
        return "insuficiente"
    years = {y: v["neto"] for y, v in r["por_anio"].items()}
    y26_decides = r["por_anio"].get("2026", {}).get("operaciones", 0) >= 30
    neg_years = sum(1 for y, v in years.items() if v <= 0 and (y != "2026" or y26_decides))
    if r["ganancia_neta"] <= 0 or r["p_rand"] > 0.20 or neg_years >= 2 or r["topstep_pct"] is not None and r["rompen_pct"] > 50:
        return "no_pasa"
    ok = (r["p_rand"] <= 0.05 and r.get("p_rand2", 1.0) <= 0.05 and r["estres_neto"] > 0 and r["p_rand_estres"] <= 0.10 and neg_years == 0
          and r["topstep_pct"] >= 50 and r["topstep_pct"] > r["topstep_rand_pct"] and r.get("dsr", 0.0) >= 0.95)
    return "pasa" if ok else "no_pasa"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True); ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--study", required=True); ap.add_argument("--rand", type=int, default=1000)
    ap.add_argument("--rand-estres", type=int, default=1000); ap.add_argument("--flip", type=int, default=200)
    ap.add_argument("--sens", action="store_true"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--notas", default=""); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--isolated", action="store_true", help="contenedor efímero: sin registro, sin bitácora, id por huella de configuración")
    ap.add_argument("--n-trials", type=int, default=0); ap.add_argument("--var-sr", type=float, default=-1.0)
    ap.add_argument("--n-sharpes", type=int, default=-1, help="cuántos intentos aportaron Sharpe a la varianza del DSR (lo pasa el orquestador)")
    ap.add_argument("--replay-de", default="", help="repetición de corrección de una prueba ya publicada (p. ej. P031): diagnóstico, nunca 'pasa'")
    a = ap.parse_args()
    t0 = time.time()
    st = next((s for s in registry.read(registry.STUDIES) if s["study_id"] == a.study), None)
    if not st and not a.isolated:
        raise SystemExit(f"estudio {a.study} no registrado: registra hipótesis y N declarado antes de correr")
    dates, sess_sha = config.design_sessions()
    if a.limit:
        dates = dates[:a.limit]
    if a.isolated:
        from . import data_manifest, regime as _regime
        bad, man_sha = data_manifest.verify()
        if bad or man_sha != sess_sha:
            raise SystemExit("DATOS DIFIEREN del manifiesto canónico: " + "; ".join(bad[:5]))
        _regime.OUT = os.path.join(os.environ.get("LAB_OUT", "/tmp"), "regimes.json"); _regime.build(dates)
    precompute_stats(dates)
    L = Levels(dates)
    gen, params = gen_for(a.strategy, a.version)
    c = config.Costs(); slip, comm = c.slip_ticks, c.commission_rt
    win = RULES_WINDOW.get((a.strategy, int(a.version)), {})
    rules = Rules(**win)
    news = {d: news_windows(d) for d in dates}      # motor 1.2.0: las MISMAS ventanas de noticias para la estrategia y todos los controles
    sig_by_date, trades, possible = {}, [], 0
    for d in dates:
        ref, thr = L.reference(d), L.thresholds(d)
        if not ref or not thr:
            continue
        possible += 1
        s = load(d, ny_only=True)
        kw = strat_kwargs(a.strategy, a.version, L, d)
        sigs = gen(s, ref, thr, params, **kw)
        r = Rules(news=news[d], **win)
        sig_by_date[d] = sigs
        trades += simulate(s, sigs, r, slip, comm)
    print(f"[{a.strategy}] {len(trades)} operaciones en {possible} sesiones · {time.time()-t0:.0f}s", flush=True)
    test_id = ("X" + config.config_hash({"s": a.strategy, "v": a.version, "p": params, "c": c.as_dict()})[:10]) if a.isolated else registry.next_test_id()
    daily = stats.daily_series(trades, dates)
    net = float(daily.sum())
    # RAND base y de estrés
    _, rd, rc = run_rand(test_id, trades, rules, slip, comm, n_runs=a.rand, sessions=dates, progress=lambda j: print(f"  RAND {j}/{len(dates)}", flush=True),
                         news_by_date=news, return_counts=True)
    rs = rand_summary(daily, rd)
    _, rd2, rc2 = run_rand(test_id + "x", trades, rules, slip, comm, n_runs=a.rand, sessions=dates, with_exits=True, news_by_date=news, return_counts=True)   # RAND2: mismas salidas
    rs2 = rand_summary(daily, rd2); rs["p_valor_rand2"] = rs2["p_valor"]; rs["rand2_media"] = rs2["rand_media"]
    stress_net, stress_tr = redteam.resim(sig_by_date, rules, 2, comm, news_by_date=news)
    stress_daily = stats.daily_series(stress_tr, dates)
    _, rds = run_rand(test_id + "s", stress_tr, rules, 2, comm, n_runs=a.rand_estres, sessions=dates, news_by_date=news)
    p_stress = rand_summary(stress_daily, rds)["p_valor"]
    # ¿RAND llenó la misma cantidad de operaciones que la estrategia? (el protocolo lo promete; aquí se mide y se publica)
    conteo = {"estrategia": len(trades), "rand_media": round(float(rc.sum(axis=1).mean()), 1), "rand_min": int(rc.sum(axis=1).min()), "rand_max": int(rc.sum(axis=1).max()),
              "rand2_media": round(float(rc2.sum(axis=1).mean()), 1), "estres": len(stress_tr)}
    conteo["coinciden"] = bool(conteo["rand_min"] == conteo["rand_max"] == len(trades) and conteo["rand2_media"] == len(trades))
    conteo["nota"] = ("RAND llenó exactamente las mismas operaciones que la estrategia." if conteo["coinciden"] else
                      "RAND NO llenó siempre la misma cantidad: sorteos solapados en una misma sesión se suprimen (una posición a la vez), igual que en la estrategia; "
                      "las ventanas de noticias ya no restan operaciones porque el instante se sortea fuera de ellas.")
    rs["conteo_operaciones"] = conteo
    print(f"  neto {net:.0f} · p RAND {rs['p_valor']} · estrés {stress_net:.0f} (p {p_stress}) · {time.time()-t0:.0f}s", flush=True)
    # Topstep: estrategia (con MAE intradía) y RAND (100 corridas; RAND solo tiene P&L diario, SIN MAE: no es la misma prueba)
    acc = topstep.run_all(trades, dates, consistency=0.50)
    ts = topstep.summarize(acc); ts["cuentas_detalle"] = [{"arranque": x["arranque"], "resultado": x["resultado"], "dias": x["dias"], "balance": round(x["balance"], 0)} for x in acc]
    ts55 = topstep.summarize(topstep.run_all(trades, dates, consistency=0.55))
    n_contr = int(win.get("contracts", 1) or 1); mult5 = 5.0 / n_contr        # motor 1.2.0: 'cinco contratos' = 5 minis en total, no 5 × el tamaño de la estrategia
    ts5 = topstep.summarize(topstep.run_all(trades, dates, consistency=0.50, contracts_mult=mult5))
    rand_pass = []
    for k in range(min(100, rd.shape[0])):
        fake = [{"date": d, "entry_sec": 0, "net_usd": float(rd[k, j]), "mae_ticks": 0, "commission_usd": 0.0, "contracts": 1} for j, d in enumerate(dates) if rd[k, j] != 0]
        rand_pass.append(topstep.summarize(topstep.run_all(fake, dates))["pct_pasan"])
    ts["rand_pct_pasan"] = round(float(np.mean(rand_pass)), 1) if rand_pass else None
    ts["rand_pct_p95"] = round(float(np.percentile(rand_pass, 95)), 1) if rand_pass else None
    ts["rand_que_es"] = "RAND Topstep usa SOLO el P&L al cierre de cada sesión (sin MAE intradía): es una prueba más benigna que la de la estrategia. Compárese con solo_cierre_diario.estrategia_pct_pasan, no con pct_pasan."
    # misma prueba para la estrategia (solo cierre diario, MAE ignorada): la única comparación como-con-como contra RAND
    ts_sc = topstep.summarize(topstep.run_all([{**t, "mae_ticks": 0} for t in trades], dates, consistency=0.50))
    ts["solo_cierre_diario"] = {"estrategia_pct_pasan": ts_sc["pct_pasan"], "estrategia_rompen_mll": ts_sc["rompen_mll"], "rand_pct_pasan": ts["rand_pct_pasan"], "rand_pct_p95": ts["rand_pct_p95"],
                               "nota": "ambas sin MAE intradía: comparable. pct_pasan (con MAE) sigue siendo la cifra que juzga a la estrategia."}
    ts["oficial_55"] = {k: ts55[k] for k in ("pasan", "rompen_mll", "pct_pasan")}
    ts["cinco_contratos"] = {**{k: ts5[k] for k in ("pasan", "rompen_mll", "pct_pasan")}, "contratos": 5, "multiplicador": round(mult5, 3),
                             "nota": f"5 minis en total (la estrategia opera {n_contr}); hasta el motor 1.1 este escenario multiplicaba por 5 el tamaño de la estrategia"}
    ts["modelado"] = "DLL siempre activo; cuenta abandonada a los 120 días de sesión; arranques solapados cada sesión; MLL/DLL contra la MAE de cada operación; el límite que la excursión toca primero manda (motor 1.2.0)"
    # Red Team
    rt = {"placebo_desplazado": redteam.placebo_shift(sig_by_date, rules, slip, comm, news_by_date=news),
          "direcciones_barajadas": redteam.placebo_flip(sig_by_date, rules, slip, comm, net, n=a.flip, test_id=test_id, news_by_date=news),
          "curva_costos": redteam.cost_curve(sig_by_date, rules, comm, news_by_date=news)}
    leak = net > 0 and rt["placebo_desplazado"]["neto"] >= 0.5 * net
    rt["fuga_sospechada"] = bool(leak)   # protocolo v2: sospecha -> 'revisar' (revisión de código), no error automático. OJO: el placebo desplazado NO prueba fuga; es un disparador conservador de revisión.
    print(f"  Topstep {ts['pct_pasan']}% (RAND {ts['rand_pct_pasan']}%) · placebo desplazado {rt['placebo_desplazado']['neto']:.0f} · {time.time()-t0:.0f}s", flush=True)
    extra = {}
    if a.sens:
        extra["sensibilidad"] = redteam.sensitivity(gen, dates, L, params, SENS_STEPS[(a.strategy, a.version)], rules, slip, comm,
                                                     kw_fn=lambda d: strat_kwargs(a.strategy, a.version, L, d), news_by_date=news)
        print(f"  sensibilidad lista · {time.time()-t0:.0f}s", flush=True)
    sm = stats.summary(trades, daily, dates)
    anom = sum(1 for t in trades if t.get("cotizacion_anomala"))
    res = {"operaciones": len(trades), "ganancia_neta": round(net, 2), "p_rand": rs["p_valor"], "p_rand2": rs2["p_valor"], "estres_neto": round(stress_net, 2),
           "cotizaciones_anomalas": anom,
           "p_rand_estres": p_stress, "por_anio": sm["por_anio"], "topstep_pct": ts["pct_pasan"], "rompen_pct": round(100 * ts["rompen_mll"] / max(1, ts["cuentas"]), 1),
           "topstep_rand_pct": ts["rand_pct_pasan"] or 0.0, "sesiones_con_senal_posible": possible, "error": False, "revisar": leak,
           "sharpe_diario": round(stats.sharpe(daily), 4), "psr": sm["psr"], "concentracion": sm["concentracion"], "cpcv": sm["cpcv"]}
    if a.isolated:
        n_trials = a.n_trials or 1; var_sr = max(a.var_sr, 0.0); n_sh = a.n_sharpes if a.n_sharpes >= 0 else None
    else:
        n_trials = len(registry.read(registry.TRIALS)) + 1
        shs = registry.all_sharpes() + [res["sharpe_diario"]]; var_sr = float(np.var(shs)) if len(shs) > 1 else 0.0; n_sh = len(shs)
    res["dsr"] = round(stats.dsr(daily, n_trials, var_sr), 3)
    res["min_btl_anios"] = round(stats.min_btl_years(n_trials), 2)
    res["intentos_totales_al_cerrar"] = n_trials
    # motor 1.2.0: el DSR dice con qué se calculó. Hasta el motor 1.1 casi ningún intento guardaba sharpe_diario, así que la
    # varianza entre intentos salía de 4–5 números mientras N contaba todos: ese DSR no medía nada.
    res["dsr_insumos"] = {"n_intentos": n_trials, "intentos_con_sharpe": n_sh, "intentos_sin_sharpe": (n_trials - n_sh) if n_sh is not None else None,
                          "var_sharpe_diario": round(var_sr, 6), "sharpe_esperado_del_mejor": round(stats.expected_max_sr(n_trials, var_sr), 4),
                          "nota": "la varianza usa solo los intentos que guardaron sharpe_diario; los que no lo tienen cuentan en N pero no en la varianza (no se rellenan con 0)"}
    res["conteo_operaciones"] = rs["conteo_operaciones"]
    v = verdict(res, True)
    if a.replay_de:   # repetición de corrección: diagnóstico del motor sobre una regla ya elegida en esta misma cinta. Nunca 'pasa', nunca abre el sello.
        res["replay_de"] = a.replay_de; res["veredicto_mecanico"] = v
        v = "revisar"
    meta = {"estrategia": a.strategy, "version": a.version, "fecha": time.strftime("%Y-%m-%d"), "tanda": a.study,
            "periodo": f"{dates[0]} a {dates[-1]} · {len(dates)} sesiones válidas", "veredicto": v, "notas": a.notas,
            "receta": {"git_commit": config.git_commit(), "motor": ENGINE_VERSION, "sesiones_sha256": sess_sha, "costos": c.as_dict(),
                       "parametros": params, "protocol_sha256": config.protocol()[1], "estrategias_sha256": (config.strategy_file(a.strategy, a.version) or ("", {}, None))[2],
                       "rand_corridas": a.rand, "semilla": f"sha256({test_id}:<fecha>:k)"},
            "estres": {"neto": round(stress_net, 2), "p_rand": p_stress, "operaciones": len(stress_tr)},
            "dsr": res["dsr"], "min_btl_anios": res["min_btl_anios"], "intentos_totales": n_trials, "dsr_insumos": res["dsr_insumos"],
            "muerte": _death_reason(res, v)}
    if a.replay_de:
        meta["tipo"] = "correccion_replay"; meta["replay_de"] = a.replay_de
        meta["muerte"] = (f"repetición de corrección de {a.replay_de} con el motor {ENGINE_VERSION}: diagnóstico de una regla ya elegida en esta cinta, no validación; "
                          f"no puede recibir 'pasa' ni abrir el examen sellado (veredicto mecánico que habría salido: {res['veredicto_mecanico']})")
        meta["notas"] = (a.notas + " · " if a.notas else "") + meta["muerte"]
    if a.dry:
        print(json.dumps({"veredicto": v, **res}, ensure_ascii=False, indent=1)); return
    ficha = report.build(test_id, meta, trades, dates, daily, rs, ts, rt, extra)
    if a.isolated:
        print(f"{test_id} {a.strategy} v{a.version}: {v} · {time.time()-t0:.0f}s (aislado: el orquestador registra y publica)", flush=True); return
    report.publish(ficha)
    from . import replay
    replay.build(test_id, trades, L)
    registry.record_trial(test_id, a.study, a.strategy, a.version, "prueba", params, sess_sha, len(dates), meta["receta"]["semilla"],
                          c.as_dict(), res, v, a.notas, error=None)
    if a.sens:
        for name, row in extra["sensibilidad"].items():
            for cell in row:
                if cell.get("neto") is None or cell["valor"] == params[name]:
                    continue
                p2 = dict(params); p2[name] = cell["valor"]
                registry.record_trial(f"{test_id}-{name}{cell['valor']}", a.study, a.strategy, a.version, "sensibilidad", p2, sess_sha, len(dates), "-",
                                      c.as_dict(), {"ganancia_neta": cell["neto"], "operaciones": cell["operaciones"], "sharpe_diario": cell.get("sharpe_diario")}, "vecino", "")
    _bitacora(test_id, a.strategy, a.version, v, res, ts)
    print(f"{test_id} {a.strategy} v{a.version}: {v} · {time.time()-t0:.0f}s", flush=True)


def _death_reason(r, v):
    if v == "error":
        return "error de programa"
    if v == "revisar":
        r2 = dict(r); r2["revisar"] = False
        otras = _death_reason(r2, verdict(r2, True))
        return "placebo desplazado sospechoso: revisión de código pendiente" + (f"; además: {otras}" if otras else "")
    if v == "insuficiente":
        return f"{r['operaciones']} operaciones / {r['sesiones_con_senal_posible']} sesiones: por debajo del mínimo"
    if v == "pasa":
        return None
    causes = []
    if r["ganancia_neta"] <= 0: causes.append("pierde con costos base")
    if r["p_rand"] > 0.05: causes.append(f"no gana a RAND (p={r['p_rand']})")
    if r.get("p_rand2", 1.0) > 0.05: causes.append(f"no gana a RAND2 con las mismas salidas (p={r.get('p_rand2')})")
    if r.get("dsr", 0) < 0.95: causes.append(f"DSR {r.get('dsr')} < 0.95 con {r.get('intentos_totales_al_cerrar')} intentos")
    if r.get("concentracion", {}).get("depende_de_pocos_dias"): causes.append(f"{r['concentracion'].get('top5_dias_pct')}% de la ganancia en 5 días")
    if r["estres_neto"] <= 0 or r["p_rand_estres"] > 0.10: causes.append("muere con costos al doble")
    neg = [y for y, x in r["por_anio"].items() if x["neto"] <= 0]
    if neg: causes.append("pierde en " + ", ".join(neg))
    if r["topstep_pct"] is not None and r["topstep_pct"] < 50: causes.append(f"pasa Topstep solo {r['topstep_pct']}%")
    return "; ".join(causes) or "no cumple todos los criterios"


def _bitacora(test_id, strategy, version, v, r, ts):
    p = os.path.join(config.FUT, "updates.json"); d = json.load(open(p, encoding="utf-8"))
    lbl = {"pasa": "pasa", "no_pasa": "no pasa", "insuficiente": "insuficiente", "error": "error", "revisar": "revisar"}[v]
    body = (f"{strategy} v{version}: {r['operaciones']} operaciones, ganancia neta ${r['ganancia_neta']:,.0f} con costos base, "
            f"p contra RAND {r['p_rand']}, estrés ${r['estres_neto']:,.0f}, Topstep {ts['pct_pasan']}% de las cuentas (RAND {ts['rand_pct_pasan']}%). "
            f"Veredicto: {lbl}." + (f" Causa: {_death_reason(r, v)}." if v != "pasa" else ""))
    d["entries"].insert(0, {"date": time.strftime("%Y-%m-%d"), "kind": "prueba", "title": f"Prueba {test_id} · {strategy} v{version} · {lbl}", "body": body, "test_id": test_id})
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
