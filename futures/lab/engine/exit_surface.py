"""Estudio de salidas (pedido de Oscar, 23/10/2026): mismas señales v1, variando SOLO la salida.
  TP fijo en puntos  : v1 (la regla original), 20, 30, 40, 50
  SL fijo en puntos  : v1, 3, 4, 6, 8
  tiempo máximo      : v1 (15 o 30 min) / hasta el cierre forzado (11:45)
  piramidar          : agregar 1 contrato cada 8 o 16 ticks a favor, 1 o 2 veces, con stop a breakeven (sobre salidas v1)
Cada celda es un intento del estudio 'salidas_v1' (se registra). Se publica la superficie completa; se busca una
meseta, no la mejor celda. Lo que se adopte es versión nueva y pasa por el protocolo completo.
  python -m engine.exit_surface --study salidas_v1 [--limit N]
"""
import argparse, copy, json, os, time
import numpy as np
from . import config, registry, stats
from .data import load
from .levels import Levels, precompute_stats
from .run_test import gen_for, news_windows
from .sim import Rules, simulate, FORCED_CLOSE

TP = [None, 20, 30, 40, 50]; SL = [None, 3, 4, 6, 8]; TM = ["v1", "cierre"]
PYR = [{"add_ticks": 8, "max_adds": 1, "stop_breakeven": True}, {"add_ticks": 16, "max_adds": 1, "stop_breakeven": True},
       {"add_ticks": 8, "max_adds": 2, "stop_breakeven": True}, {"add_ticks": 16, "max_adds": 2, "stop_breakeven": True}]


def cell(sig_by_date, dates, slip, comm, tp, sl, tm, pyr=None):
    trades = []
    for d, sigs in sig_by_date.items():
        if not sigs:
            continue
        s = load(d, ny_only=True); ss = []
        for x in sigs:
            y = copy.copy(x)
            if tp is not None: y.target_ticks = tp * 4
            if sl is not None: y.stop_ticks = sl * 4
            if tm == "cierre": y.max_sec = 24 * 3600
            ss.append(y)
        trades += simulate(s, ss, Rules(news=news_windows(d), pyramid=pyr), slip, comm)
    daily = stats.daily_series(trades, dates); net = float(daily.sum()); wins = [t for t in trades if t["net_usd"] > 0]
    gp = sum(t["net_usd"] for t in wins); gl = -sum(t["net_usd"] for t in trades if t["net_usd"] < 0)
    cum = np.cumsum(daily); dd = float((cum - np.maximum.accumulate(cum)).min()) if len(cum) else 0.0
    years = {}
    for t in trades:
        years[t["date"][:4]] = years.get(t["date"][:4], 0.0) + t["net_usd"]
    top5 = float(np.sort(daily)[::-1][:5].sum())
    return {"neto": round(net, 2), "operaciones": len(trades), "aciertos": round(100 * len(wins) / len(trades), 1) if trades else None,
            "factor": round(gp / gl, 2) if gl > 0 else None, "drawdown": round(dd, 2), "anios_positivos": sum(1 for v in years.values() if v > 0),
            "anios": len(years), "top5_dias_pct": round(100 * top5 / net, 1) if net > 0 else None, "contratos_prom": round(float(np.mean([t["contracts"] for t in trades])), 2) if trades else None}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--study", required=True); ap.add_argument("--limit", type=int, default=0); a = ap.parse_args()
    if not any(s["study_id"] == a.study for s in registry.read(registry.STUDIES)):
        raise SystemExit("estudio no registrado")
    dates, sess_sha = config.design_sessions()
    if a.limit: dates = dates[:a.limit]
    precompute_stats(dates); L = Levels(dates); c = config.Costs(); t0 = time.time()
    out_dir = os.path.join(config.RESULTS, a.study); os.makedirs(out_dir, exist_ok=True)
    for sid in ("BIG", "ABS", "POC"):
        gen, params = gen_for(sid, 1); sig_by_date = {}
        for d in dates:
            ref, thr = L.reference(d), L.thresholds(d)
            if not ref or not thr: continue
            s = load(d, ny_only=True); kw = {"open_in_value": L.open_in_value(d)} if sid == "POC" else {}
            sig_by_date[d] = gen(s, ref, thr, params, **kw)
        grid = {tm: [[None] * len(SL) for _ in TP] for tm in TM}
        for tm in TM:
            for i, tp in enumerate(TP):
                for j, sl in enumerate(SL):
                    r = cell(sig_by_date, dates, c.slip_ticks, c.commission_rt, tp, sl, tm); grid[tm][i][j] = r
                    if not (tp is None and sl is None and tm == "v1"):   # la celda base ya es la prueba v1 publicada
                        registry.record_trial(f"X-{sid}-tp{tp or 'v1'}-sl{sl or 'v1'}-{tm}", a.study, sid, 1, "superficie",
                                              {"tp_puntos": tp, "sl_puntos": sl, "tiempo": tm}, sess_sha, len(dates), "-", c.as_dict(), r, "celda")
            print(f"  {sid} {tm}: {time.time()-t0:.0f}s", flush=True)
        pyr = []
        for P in PYR:
            r = cell(sig_by_date, dates, c.slip_ticks, c.commission_rt, None, None, "v1", P); r["regla"] = P; pyr.append(r)
            registry.record_trial(f"X-{sid}-pyr{P['add_ticks']}x{P['max_adds']}", a.study, sid, 1, "superficie", {"piramidar": P}, sess_sha, len(dates), "-", c.as_dict(), r, "celda")
        json.dump({"estrategia": sid, "tp_puntos": ["v1"] + TP[1:], "sl_puntos": ["v1"] + SL[1:], "tiempos": TM, "superficie": grid, "piramidar": pyr,
                   "base": grid["v1"][0][0], "sesiones": len(dates), "fecha": time.strftime("%Y-%m-%d")},
                  open(os.path.join(out_dir, f"{sid}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{sid} listo · {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
