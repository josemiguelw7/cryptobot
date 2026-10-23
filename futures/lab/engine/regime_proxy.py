"""Estudio del proxy de régimen en tiempo real (E-PROXY). Pregunta: ¿a las 09:45 se puede anticipar si el día
terminará en balance o en tendencia, SIN usar el futuro? Proxies conocidos a las 09:45:
  p_rango15 : rango de los primeros 15 min ÷ mediana del rango de NY de las 20 sesiones anteriores (alto = ya se movió)
  p_cuerpo15: |precio 09:45 − apertura| ÷ rango de los primeros 15 min (alto = direccional)
  p_valor   : apertura fuera del área de valor de ayer (1) o dentro (0)
  p_vwap    : |precio 09:45 − VWAP| en ticks (lejos del VWAP = empuje)
Para cada proxy, partido en terciles, se publica: % de días que terminaron en tendencia, y el efecto de HVN y de ABS
(r30 del mapa v3 medido desde el libro) condicionado al tercil. Todo es descriptivo salvo la precisión del mejor
proxy, que se registra como 1 intento del estudio proxy_v1.
  python -m engine.regime_proxy --study proxy_v1
"""
import argparse, json, os, time
import numpy as np
from . import config, registry, regime
from .data import load, NY_OPEN
from .levels import Levels


def proxies(s, L, d, med_range):
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 900)
    if j - i < 50:
        return None
    px = s.px[i:j]; vol = s.vol[i:j]
    r15 = int(px.max() - px.min()); p945 = int(px[-1]); op = int(px[0])
    vwap = float((px * vol).sum() / max(1, vol.sum()))
    oiv = L.open_in_value(d)
    return {"p_rango15": r15 / med_range if med_range else None, "p_cuerpo15": abs(p945 - op) / r15 if r15 else 0.0,
            "p_valor": 0 if oiv else 1 if oiv is False else None, "p_vwap": abs(p945 - vwap)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--study", required=True); a = ap.parse_args()
    if not any(x["study_id"] == a.study for x in registry.read(registry.STUDIES)):
        raise SystemExit("estudio no registrado")
    dates, sess_sha = config.design_sessions(); L = Levels(dates); R = regime.load(); t0 = time.time()
    rows = []; ranges = []
    for d in dates:
        ny = L.summ.get(d, {}).get("ny"); reg = R.get(d)
        if not ny or not reg:
            continue
        med = float(np.median(ranges[-20:])) if len(ranges) >= 20 else None
        ranges.append(ny["high_t"] - ny["low_t"])
        pr = proxies(load(d, ny_only=True), L, d, med)
        if pr and med:
            rows.append({"date": d, **pr, "tendencia": reg["tendencia"] == "tendencia"})
    out = {"sesiones": len(rows), "proxies": {}}
    best = None
    for k in ("p_rango15", "p_cuerpo15", "p_vwap"):
        v = np.array([r[k] for r in rows], dtype=float); y = np.array([r["tendencia"] for r in rows])
        q = np.quantile(v, [1 / 3, 2 / 3]); terc = np.digitize(v, q)
        cells = []
        for t in range(3):
            m = terc == t; cells.append({"tercil": t + 1, "n": int(m.sum()), "pct_tendencia": round(100 * y[m].mean(), 1) if m.any() else None})
        acc = max(y[terc == 2].mean(), 1 - y[terc == 0].mean()) if (terc == 2).any() and (terc == 0).any() else 0
        out["proxies"][k] = {"cortes": q.round(3).tolist(), "terciles": cells, "precision_extremo": round(float(acc), 3)}
        if best is None or acc > best[1]:
            best = (k, acc)
    y = np.array([r["tendencia"] for r in rows]); v = np.array([r["p_valor"] for r in rows], dtype=float)
    out["proxies"]["p_valor"] = {"fuera": {"n": int((v == 1).sum()), "pct_tendencia": round(100 * y[v == 1].mean(), 1)}, "dentro": {"n": int((v == 0).sum()), "pct_tendencia": round(100 * y[v == 0].mean(), 1)}}
    out["base_pct_tendencia"] = round(100 * y.mean(), 1); out["mejor"] = {"proxy": best[0], "precision_extremo": round(float(best[1]), 3)}
    out["nota"] = "precision_extremo = en el tercil alto, % de días de tendencia (o en el bajo, % de balance), lo que sea mayor. Base = % de días de tendencia sin proxy. Un proxy útil separa bastante más que la base."
    out["fecha"] = time.strftime("%Y-%m-%d"); out["sesiones_sha256"] = sess_sha
    json.dump(out, open(os.path.join(config.FUT, "regime_proxy.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    registry.record_trial("X-proxy-regimen", a.study, "proxy", 1, "senal", {"proxies": list(out["proxies"])}, sess_sha, len(rows), "-",
                          config.Costs().as_dict(), {"mejor": out["mejor"], "base": out["base_pct_tendencia"]}, "medido")
    print(json.dumps({"base": out["base_pct_tendencia"], "mejor": out["mejor"], "p_valor": out["proxies"]["p_valor"]}, ensure_ascii=False), f"· {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
