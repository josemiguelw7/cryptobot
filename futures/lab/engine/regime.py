"""Régimen de mercado por sesión, con reglas fijas y simples (sin ajustar a ningún resultado):

  tendencia : |cierre − apertura| de Nueva York ≥ 50% del rango del día   → "tendencia", si no "balance"
  volatilidad: rango de Nueva York ≥ mediana del rango de las 20 sesiones válidas anteriores → "alta", si no "baja"
  noticias  : día con Fed, CPI o NFP (futures/news.json) → "noticias", si no "normal"
  apertura  : abre dentro / fuera del área de valor del día anterior

Salida: futures/lab/regimes.json {fecha: {...}} y resumen. Se usa para partir los resultados de cada prueba
por régimen (hoja › por_regimen). Una estrategia que solo gana en un régimen no es una estrategia.
  python -m engine.regime
"""
import json, os
import numpy as np
from . import config
from .levels import Levels

OUT = os.path.join(os.environ.get("LAB_OUT", config.LAB), "regimes.json")


def build(dates=None):
    dates = dates or config.design_sessions()[0]
    L = Levels(dates); news, _ = config._load("news.json")
    newsdays = set(news.get("fed", []) + news.get("cpi", []) + news.get("nfp", []))
    out, ranges = {}, []
    for d in dates:
        ny = L.summ.get(d, {}).get("ny")
        if not ny:
            continue
        rng = ny["high_t"] - ny["low_t"]; body = abs(ny["close_t"] - ny["open_t"])
        med = float(np.median(ranges[-20:])) if len(ranges) >= 20 else None
        oiv = L.open_in_value(d)
        out[d] = {"tendencia": "tendencia" if rng and body / rng >= 0.5 else "balance",
                  "volatilidad": ("alta" if rng >= med else "baja") if med else "sin_referencia",
                  "noticias": "noticias" if d in newsdays else "normal",
                  "apertura": "dentro_del_valor" if oiv else ("fuera_del_valor" if oiv is False else "sin_referencia"),
                  "rango_ticks": int(rng), "cuerpo_pct": round(100 * body / rng, 1) if rng else None}
        ranges.append(rng)
    res = {}
    for k in ("tendencia", "volatilidad", "noticias", "apertura"):
        res[k] = {}
        for v in out.values():
            res[k][v[k]] = res[k].get(v[k], 0) + 1
    json.dump({"reglas": __doc__.strip().split("\n")[1:6], "resumen": res, "sesiones": out}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


def load():
    return json.load(open(OUT, encoding="utf-8"))["sesiones"] if os.path.exists(OUT) else {}


def by_regime(trades):
    """{dimensión: {valor: {operaciones, neto}}} para la hoja de resultados."""
    R = load(); out = {}
    for k in ("tendencia", "volatilidad", "noticias", "apertura"):
        o = out.setdefault(k, {})
        for t in trades:
            v = R.get(t["date"], {}).get(k, "sin_dato"); c = o.setdefault(v, {"operaciones": 0, "neto": 0.0})
            c["operaciones"] += 1; c["neto"] = round(c["neto"] + t["net_usd"], 2)
    return out


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=1))
