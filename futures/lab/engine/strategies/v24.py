"""Estrategias v24 (tanda 25), congeladas en futures/strategies/v26.json.
  ABR v1 : ABSORCIÓN CON REPRUEBA — el mismo detector de ABU v1 (v17.py: flujo agresivo ≥ umbral relativo sin avanzar en un nivel de ayer, de la noche
           o del valor en desarrollo, solo días que abren dentro del valor de ayer, confirmado a 60 s), pero la entrada NO es a mercado tras
           alejarse el precio: se deja una orden LÍMITE 2 ticks dentro del extremo absorbido (vende 2 ticks bajo el máximo absorbido / compra 2 ticks
           sobre el mínimo) y se espera 300 s a que el precio vuelva a probarlo. Si no vuelve, no hay operación. Con cola y llenado del simulador.
           Stop 8 ticks desde el llenado (6 ticks más allá del extremo), objetivo 2R (16 ticks), salida a 15 min, 1 contrato, 09:30–15:30.
           Motivo: ABU entra tras el alejamiento con stops de 12–32 ticks (pierde el 60%); la entrada en el extremo acorta el riesgo a 8 ticks.
           Investigación y definición fijada antes de correr: docs/investigacion/absorcion_reprueba.md.
"""
from ..sim import Signal
from .v17 import PARAMS as P17, absorption_unified

PARAMS = {"ABR": {**P17["ABU"], "limit_in_ticks": 2, "stop": 8, "wait_s": 300}}


def absorption_retest(s, ref, thr, p=None):
    p = p or PARAMS["ABR"]
    out = []
    for g in absorption_unified(s, ref, thr, p):
        ext = int(round(g.meta["extreme"] * 4)); sa = g.meta["side_absorbed"]
        stop = int(p["stop"])
        out.append(Signal(sec=g.sec, side=g.side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)), max_sec=g.max_sec, kind="ABR",
                          level=g.level, order="limit", limit_px=ext - sa * int(p["limit_in_ticks"]), wait_sec=float(p["wait_s"]), meta=g.meta))
    return out


REGISTRY = {"ABR": absorption_retest}
