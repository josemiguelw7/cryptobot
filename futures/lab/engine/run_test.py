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
from . import config, registry, report, stats, topstep, redteam
from .data import load
from .levels import Levels, precompute_stats
from .rand import run_rand, summarize as rand_summary
from .sim import Rules, simulate
from .strategies import v1 as S1

SENS_STEPS = {
    "BIG": {"stop": 4, "target": 8, "confirm_s": 10, "near_ticks": 1},
    "ABS": {"near_ticks": 1, "stop_min": 4, "rr": 0.5, "confirm_s": 10},
    "POC": {"touch_ticks": 1, "back_ticks": 1, "stop_min": 4, "confirm_s": 30},
}


def news_windows(date):
    n, _ = config._load("news.json")
    out = []
    for k, w in n["ventanas"].items():
        if date in n.get(k, []):
            h, m = map(int, w["hora_et"].split(":")); c = h * 3600 + m * 60
            out.append((c - 60 * w["antes_min"], c + 60 * w["despues_min"]))
    return tuple(out)


def gen_for(strategy, version):
    if version != 1:
        raise SystemExit("solo v1 implementada en el motor; una v2 requiere código nuevo registrado")
    return S1.REGISTRY[strategy], dict(S1.PARAMS[strategy])


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
    ok = (r["p_rand"] <= 0.05 and r["estres_neto"] > 0 and r["p_rand_estres"] <= 0.10 and neg_years == 0
          and r["topstep_pct"] >= 50 and r["topstep_pct"] > r["topstep_rand_pct"])
    return "pasa" if ok else "no_pasa"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True); ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--study", required=True); ap.add_argument("--rand", type=int, default=1000)
    ap.add_argument("--rand-estres", type=int, default=300); ap.add_argument("--flip", type=int, default=200)
    ap.add_argument("--sens", action="store_true"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--notas", default=""); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--isolated", action="store_true", help="contenedor efímero: sin registro, sin bitácora, id por huella de configuración")
    ap.add_argument("--n-trials", type=int, default=0); ap.add_argument("--var-sr", type=float, default=-1.0)
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
    rules = Rules()
    sig_by_date, trades, possible = {}, [], 0
    for d in dates:
        ref, thr = L.reference(d), L.thresholds(d)
        if not ref or not thr:
            continue
        possible += 1
        s = load(d, ny_only=True)
        kw = {"open_in_value": L.open_in_value(d)} if a.strategy == "POC" else {}
        sigs = gen(s, ref, thr, params, **kw)
        r = Rules(news=news_windows(d))
        sig_by_date[d] = sigs
        trades += simulate(s, sigs, r, slip, comm)
    print(f"[{a.strategy}] {len(trades)} operaciones en {possible} sesiones · {time.time()-t0:.0f}s", flush=True)
    test_id = ("X" + config.config_hash({"s": a.strategy, "v": a.version, "p": params, "c": c.as_dict()})[:10]) if a.isolated else registry.next_test_id()
    daily = stats.daily_series(trades, dates)
    net = float(daily.sum())
    # RAND base y de estrés
    _, rd = run_rand(test_id, trades, rules, slip, comm, n_runs=a.rand, sessions=dates, progress=lambda j: print(f"  RAND {j}/{len(dates)}", flush=True))
    rs = rand_summary(daily, rd)
    stress_net, stress_tr = redteam.resim(sig_by_date, rules, 2, comm)
    stress_daily = stats.daily_series(stress_tr, dates)
    _, rds = run_rand(test_id + "s", stress_tr, rules, 2, comm, n_runs=a.rand_estres, sessions=dates)
    p_stress = rand_summary(stress_daily, rds)["p_valor"]
    print(f"  neto {net:.0f} · p RAND {rs['p_valor']} · estrés {stress_net:.0f} (p {p_stress}) · {time.time()-t0:.0f}s", flush=True)
    # Topstep: estrategia y RAND (100 corridas, solo P&L diario)
    acc = topstep.run_all(trades, dates, consistency=0.50)
    ts = topstep.summarize(acc); ts["cuentas_detalle"] = [{"arranque": x["arranque"], "resultado": x["resultado"], "dias": x["dias"], "balance": round(x["balance"], 0)} for x in acc]
    ts55 = topstep.summarize(topstep.run_all(trades, dates, consistency=0.55))
    ts5 = topstep.summarize(topstep.run_all(trades, dates, consistency=0.50, contracts_mult=5))
    rand_pass = []
    for k in range(min(100, rd.shape[0])):
        fake = [{"date": d, "entry_sec": 0, "net_usd": float(rd[k, j]), "mae_ticks": 0, "commission_usd": 0.0, "contracts": 1} for j, d in enumerate(dates) if rd[k, j] != 0]
        rand_pass.append(topstep.summarize(topstep.run_all(fake, dates))["pct_pasan"])
    ts["rand_pct_pasan"] = round(float(np.mean(rand_pass)), 1) if rand_pass else None
    ts["rand_pct_p95"] = round(float(np.percentile(rand_pass, 95)), 1) if rand_pass else None
    ts["oficial_55"] = {k: ts55[k] for k in ("pasan", "rompen_mll", "pct_pasan")}
    ts["cinco_contratos"] = {k: ts5[k] for k in ("pasan", "rompen_mll", "pct_pasan")}
    # Red Team
    rt = {"placebo_desplazado": redteam.placebo_shift(sig_by_date, rules, slip, comm),
          "direcciones_barajadas": redteam.placebo_flip(sig_by_date, rules, slip, comm, net, n=a.flip, test_id=test_id),
          "curva_costos": redteam.cost_curve(sig_by_date, rules, comm)}
    leak = net > 0 and rt["placebo_desplazado"]["neto"] >= 0.5 * net
    rt["fuga_sospechada"] = bool(leak)   # protocolo v2: sospecha -> 'revisar' (revisión de código), no error automático
    print(f"  Topstep {ts['pct_pasan']}% (RAND {ts['rand_pct_pasan']}%) · placebo desplazado {rt['placebo_desplazado']['neto']:.0f} · {time.time()-t0:.0f}s", flush=True)
    extra = {}
    if a.sens:
        oiv = (lambda d: L.open_in_value(d)) if a.strategy == "POC" else None
        extra["sensibilidad"] = redteam.sensitivity(gen, dates, L, params, SENS_STEPS[a.strategy], rules, slip, comm, oiv)
        print(f"  sensibilidad lista · {time.time()-t0:.0f}s", flush=True)
    sm = stats.summary(trades, daily, dates)
    res = {"operaciones": len(trades), "ganancia_neta": round(net, 2), "p_rand": rs["p_valor"], "estres_neto": round(stress_net, 2),
           "p_rand_estres": p_stress, "por_anio": sm["por_anio"], "topstep_pct": ts["pct_pasan"], "rompen_pct": round(100 * ts["rompen_mll"] / max(1, ts["cuentas"]), 1),
           "topstep_rand_pct": ts["rand_pct_pasan"] or 0.0, "sesiones_con_senal_posible": possible, "error": False, "revisar": leak,
           "sharpe_diario": round(stats.sharpe(daily), 4), "psr": sm["psr"], "concentracion": sm["concentracion"], "cpcv": sm["cpcv"]}
    v = verdict(res, True)
    if a.isolated:
        n_trials = a.n_trials or 1; var_sr = max(a.var_sr, 0.0)
    else:
        n_trials = len(registry.read(registry.TRIALS)) + 1
        shs = registry.all_sharpes() + [res["sharpe_diario"]]; var_sr = float(np.var(shs)) if len(shs) > 1 else 0.0
    res["dsr"] = round(stats.dsr(daily, n_trials, var_sr), 3)
    res["min_btl_anios"] = round(stats.min_btl_years(n_trials), 2)
    res["intentos_totales_al_cerrar"] = n_trials
    meta = {"estrategia": a.strategy, "version": a.version, "fecha": time.strftime("%Y-%m-%d"), "tanda": a.study,
            "periodo": f"{dates[0]} a {dates[-1]} · {len(dates)} sesiones válidas", "veredicto": v, "notas": a.notas,
            "receta": {"git_commit": config.git_commit(), "motor": "1.0.0", "sesiones_sha256": sess_sha, "costos": c.as_dict(),
                       "parametros": params, "protocol_sha256": config.protocol()[1], "estrategias_sha256": config.strategies(a.version)[1],
                       "rand_corridas": a.rand, "semilla": f"sha256({test_id}:<fecha>:k)"},
            "estres": {"neto": round(stress_net, 2), "p_rand": p_stress, "operaciones": len(stress_tr)},
            "dsr": res["dsr"], "min_btl_anios": res["min_btl_anios"], "intentos_totales": n_trials,
            "muerte": _death_reason(res, v)}
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
                                      c.as_dict(), {"ganancia_neta": cell["neto"], "operaciones": cell["operaciones"]}, "vecino", "")
    _bitacora(test_id, a.strategy, a.version, v, res, ts)
    print(f"{test_id} {a.strategy} v{a.version}: {v} · {time.time()-t0:.0f}s", flush=True)


def _death_reason(r, v):
    if v == "error":
        return "error de programa"
    if v == "revisar":
        return "el placebo desplazado gana parecido o más: hay que revisar el código antes de poder pasar (protocolo v2)"
    if v == "insuficiente":
        return f"{r['operaciones']} operaciones / {r['sesiones_con_senal_posible']} sesiones: por debajo del mínimo"
    if v == "pasa":
        return None
    causes = []
    if r["ganancia_neta"] <= 0: causes.append("pierde con costos base")
    if r["p_rand"] > 0.05: causes.append(f"no gana a RAND (p={r['p_rand']})")
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
