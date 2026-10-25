"""Estrategias v6 (tanda 7), congeladas en futures/strategies/v8.json.
  VAR v1 : REGLA DEL 80% (Steidlmayer/Dalton) con flujo agresivo: abre fuera del área de valor de ayer, vuelve adentro y se queda
           → rotación hacia el otro lado del valor. Investigación: docs/investigacion/regla80.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "VAR": {"hold_s": 180, "delta_pct": 2, "stop_beyond": 4, "max_min": 30, "tol_ticks": 2, "stop_min": 12, "stop_max": 32},
}


def reentry_accepted(s, ref, thr, p=None):
    """Regla del 80%: el primer llenado de la sesión (09:30) está fuera del área de valor de ayer (por encima del VAH o por debajo
    del VAL). Re-entrada aceptada = el precio vuelve a operar al menos `tol_ticks` adentro del borde y PERMANECE adentro `hold_s`
    segundos seguidos (ningún llenado vuelve a salir; si sale, la cuenta se reinicia con la siguiente entrada), y el flujo agresivo
    de esa ventana no lo contradice: delta neto en dirección al interior ≥ `delta_pct`% del volumen (base 2%).
    Entra a mercado hacia el interior (en contra de la apertura) al cumplirse la ventana. Stop `stop_beyond` ticks fuera del borde
    cruzado (entre `stop_min` y `stop_max` ticks); sin objetivo, sale por tiempo (`max_min`). Un disparo por día."""
    p = p or PARAMS["VAR"]
    if not ref or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    vah, val = ref["prev_vah"], ref["prev_val"]
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600)
    px = s.px[i:j]; sec = s.sec[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]
    if len(px) < 50:
        return []
    o = px[0]
    if o > vah:
        d_in, edge = -1, vah                    # abrió arriba: la rotación va hacia abajo
    elif o < val:
        d_in, edge = 1, val
    else:
        return []                               # abrió dentro del valor: la regla no aplica
    tol = p["tol_ticks"]
    inside = (px <= vah - tol) & (px >= val + tol)
    k = 0
    while k < len(px):
        nz = np.flatnonzero(inside[k:])
        if not len(nz):
            break
        a = k + int(nz[0])
        t_end = sec[a] + p["hold_s"]
        e = int(np.searchsorted(sec, t_end, side="left"))
        if e >= len(px):
            break                               # la ventana no cabe antes de las 11:30
        bad = np.flatnonzero(~inside[a:e + 1])
        if len(bad):
            k = a + int(bad[0]) + 1; continue   # volvió a salir: no hubo aceptación, se reinicia
        v = vol[a:e].astype(float); dl = float((v * sd[a:e]).sum()); tot = float(v.sum())
        if tot > 0 and d_in * dl >= p["delta_pct"] / 100.0 * tot:
            outside_edge = edge - d_in * p["stop_beyond"]            # fuera del borde, del lado de la apertura
            dist = abs(int(px[e]) - outside_edge)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            return [Signal(sec=float(t_end) + 1e-6, side=d_in, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                           kind="VAR", level="prev_vah" if d_in < 0 else "prev_val",
                           meta={"delta_share": round(d_in * dl / tot, 3), "vol_hold": int(tot)})]
        return []                               # aceptada en tiempo pero el flujo la contradice: se descarta el día
    return []


REGISTRY = {"VAR": reentry_accepted}
