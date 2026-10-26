"""Estrategias v33 (tanda 34), congeladas en futures/strategies/v35.json.
  ABG v1 : MANEJO DE LA OPERACIÓN SOBRE ABU v2 (G2, pedido de Jose 26/10/2026). Mismo detector, filtro de día, niveles, confirmación y
           tamaño (2 contratos) de ABU v2 (v17.py), con SOLO tres cambios de salida, fijados antes de correr:
           stop máximo 24 ticks (ABU: 32), objetivo 1.5R (ABU: 2R), salida por tiempo a 10 min (ABU: 15).
           Motivo: P031 pierde 107 de 181 operaciones, casi todas con el stop en el tope de 32 ticks ($320 con 2 contratos);
           214 de 517 cuentas Topstep rompen el MLL. Pérdida menor y objetivo más cercano buscan menos racimos de pérdidas.
           Breakeven, salida parcial y stop dinámico por flujo NO se prueban: exigen cambiar sim.py/rand.py (prohibido).
           Investigación: docs/investigacion/manejo_abu.md.
"""
from .v17 import PARAMS as P17, absorption_unified

PARAMS = {"ABG": dict(P17["ABU"], stop_max=24, rr=1.5, max_min=10)}
CONTRACTS = 2


def absorption_manejo(s, ref, thr, p=None):
    out = absorption_unified(s, ref, thr, p or PARAMS["ABG"])
    for x in out:
        x.kind = "ABG"
    return out


REGISTRY = {"ABG": absorption_manejo}
