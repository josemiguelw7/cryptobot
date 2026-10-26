"""Estrategias v26 (tanda 27), congeladas en futures/strategies/v28.json.
  ABU v3 : mismas señales y mismo tamaño que ABU v2 (v17.py, 2 contratos); única regla nueva: el día se detiene tras 2 pérdidas seguidas
           (v2: 3). Es una regla de riesgo, no de señal. Última versión de ABU (máximo 3).
           Motivo: en P031 214 de 517 cuentas Topstep rompen el MLL; muchas arrancan en enero 2024 y caen por el mismo racimo de pérdidas.
           Con 2 contratos, 3 pérdidas al stop máximo ≈ $1,000 = el límite diario (Topstep); 2 pérdidas ≈ $660, dentro del límite con margen.
           El 2 viene de ese cálculo con las reglas de la cuenta, no de probar valores.
           Investigación y justificación: docs/investigacion/riesgo_diario.md.
"""
from .v17 import PARAMS as P17, absorption_unified

PARAMS = {"ABU3": dict(P17["ABU"])}
CONTRACTS = 2
MAX_CONSEC_LOSSES = 2


def absorption_unified_v3(s, ref, thr, p=None):
    return absorption_unified(s, ref, thr, p or PARAMS["ABU3"])


REGISTRY = {"ABU3": absorption_unified_v3}
