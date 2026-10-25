"""Estrategias v7 (tanda 8), congeladas en futures/strategies/v9.json.
  ACC v2 : ACEPTACIÓN fuera de los bordes de la subasta anterior, SOLO en días que abren dentro del valor de ayer.
           Misma regla de aceptación que ACC v1 (v4.py); cambia el universo de niveles y agrega el filtro de apertura.
           Investigación y justificación: docs/investigacion/aceptacion_v2.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "ACC2": {"hold_s": 180, "delta_pct": 5, "stop_beyond": 4, "max_min": 20, "tol_ticks": 2, "chase_max": 100, "stop_min": 12, "stop_max": 32},
}
# (nivel, lado de la ruptura): +1 = sale por arriba, -1 = sale por abajo
LEVELS = (("prev_vah", 1), ("prev_val", -1), ("prev_high", 1), ("prev_low", -1), ("night_high", 1), ("night_low", -1))


def acceptance_outside_v2(s, ref, thr, p=None):
    """Igual que ACC v1 (aceptación = `hold_s` segundos seguidos fuera del nivel sin volver más de `tol_ticks` adentro, con delta
    agresivo neto ≥ `delta_pct`% a favor; entrada a mercado a favor; stop `stop_beyond` ticks adentro del nivel, 12–32; sin objetivo;
    salida por tiempo `max_min`; un disparo por nivel y por día; no persigue a más de `chase_max` ticks), con dos cambios:
      1. Niveles: VAH, VAL, máximo y mínimo de ayer, máximo y mínimo de la noche (v1 solo usaba VAH y VAL).
      2. Filtro: solo si el primer llenado de las 09:30 cae DENTRO del área de valor de ayer (conocido a las 09:30, sin futuro).
    Un nivel que ya está rebasado en la apertura (hueco) no cuenta como ruptura, igual que en v1."""
    p = p or PARAMS["ACC2"]
    if not ref or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600)
    px = s.px[i:j]; sec = s.sec[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]
    if len(px) < 50:
        return []
    if not (ref["prev_val"] <= px[0] <= ref["prev_vah"]):
        return []                                       # abre fuera del valor: el filtro excluye el día
    out = []
    for name, side in LEVELS:
        lvl = ref.get(name)
        if lvl is None:
            continue
        outside = (px > lvl) if side > 0 else (px < lvl)
        broke = (px <= lvl - p["tol_ticks"]) if side > 0 else (px >= lvl + p["tol_ticks"])
        k = 0
        while k < len(px):
            nz = np.flatnonzero(outside[k:])
            if not len(nz):
                break
            a = k + int(nz[0])
            if a == 0:                                  # el nivel ya estaba rebasado a las 09:30: no es una ruptura de la sesión
                ins = np.flatnonzero(~outside)
                if not len(ins):
                    break
                k = int(ins[0]); continue
            t_end = sec[a] + p["hold_s"]
            e = int(np.searchsorted(sec, t_end, side="left"))
            if e >= len(px):
                break
            bad = np.flatnonzero(broke[a:e + 1])
            if len(bad):
                k = a + int(bad[0]) + 1; continue       # volvió adentro: no hubo aceptación, se reinicia
            v = vol[a:e].astype(float); dl = float((v * sd[a:e]).sum()); tot = float(v.sum())
            ok_flow = tot > 0 and side * dl >= p["delta_pct"] / 100.0 * tot
            ext = int((px[e] - lvl) * side)
            if ok_flow and 0 < ext <= p["chase_max"]:
                dist = abs(int(px[e]) - (lvl - side * p["stop_beyond"]))
                stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
                out.append(Signal(sec=float(t_end) + 1e-6, side=side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                                  kind="ACC", level=name, meta={"delta_share": round(dl / tot, 3), "vol_hold": int(tot), "ext_ticks": ext}))
            break                                       # un disparo (o nivel usado sin respaldo de flujo) por nivel y por día
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ACC2": acceptance_outside_v2}
