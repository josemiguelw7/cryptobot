"""Estrategias v4 (tanda 5), congeladas en futures/strategies/v6.json.
  ACC v1 : ACEPTACIÓN fuera del área de valor del día anterior (VAH / VAL) → continuación.
           Pedido de Oscar (25/10/2026). Definiciones investigadas en docs/investigacion/aceptacion.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "ACC": {"hold_s": 180, "delta_pct": 5, "stop_beyond": 4, "max_min": 20, "tol_ticks": 2, "chase_max": 100, "stop_min": 12, "stop_max": 32},
}


def acceptance_outside(s, ref, thr, p=None):
    """Aceptación = el precio sale del área de valor de ayer (por encima del VAH o por debajo del VAL), PERMANECE fuera
    durante `hold_s` segundos seguidos (ningún llenado vuelve más de `tol_ticks` hacia adentro del nivel) y el flujo
    agresivo de esa ventana respalda la salida (delta neto ≥ `delta_pct`% del volumen, en la dirección de la salida).
    Solo cuenta una ruptura dentro de la sesión (el precio venía de dentro del nivel; los huecos de apertura quedan fuera). Entra a mercado a favor de la salida al cumplirse la ventana. Una vez por nivel y por día; si se ha extendido más de
    `chase_max` (100) ticks del nivel no persigue. Stop `stop_beyond` ticks adentro del nivel (12–32 ticks); sin objetivo:
    sale por tiempo (`max_min`). Si el precio no cumple la ventana, el intento se reinicia con la siguiente salida."""
    p = p or PARAMS["ACC"]
    if not ref:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600)
    px = s.px[i:j]; sec = s.sec[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]
    if len(px) < 50:
        return []
    out = []
    for name, side in (("prev_vah", 1), ("prev_val", -1)):
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
            if a == 0:                                  # abre ya fuera del valor (hueco): otro escenario, no es una ruptura
                ins = np.flatnonzero(~outside)
                if not len(ins):
                    break
                k = int(ins[0]); continue
            t_end = sec[a] + p["hold_s"]
            e = int(np.searchsorted(sec, t_end, side="left"))
            if e >= len(px):
                break                                   # la ventana no cabe antes de las 11:30
            bad = np.flatnonzero(broke[a:e + 1])
            if len(bad):
                k = a + int(bad[0]) + 1; continue       # volvió adentro: no hubo aceptación, se reinicia
            v = vol[a:e].astype(float); dl = float((v * sd[a:e]).sum()); tot = float(v.sum())
            ok_flow = tot > 0 and side * dl >= p["delta_pct"] / 100.0 * tot
            ext = int((px[e] - lvl) * side)
            if ok_flow and 0 < ext <= p["chase_max"]:
                entry_est = int(px[e])
                dist = abs(entry_est - (lvl - side * p["stop_beyond"]))
                stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
                out.append(Signal(sec=float(t_end) + 1e-6, side=side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                                  kind="ACC", level=name, meta={"delta_share": round(dl / tot, 3), "vol_hold": int(tot), "ext_ticks": ext}))
                break
            break   # aceptado en tiempo pero sin respaldo de flujo (o ya extendido): el nivel queda usado, no se opera
    return out


REGISTRY = {"ACC": acceptance_outside}
