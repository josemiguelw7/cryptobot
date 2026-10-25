"""Estrategias v18 (tanda 19), congeladas en futures/strategies/v20.json.
  ABU v2 : mismas señales que ABU v1 (v17.py: absorción unificada en niveles de ayer y del día, solo días que abren dentro del valor),
           pero con 2 contratos por operación en vez de 1.
           Motivo: P030 (ABU v1) no rompió ninguna cuenta Topstep (0 de 517) y pasó solo 9.9%: 466 cuentas quedaron sin resolver
           porque 1 contrato junta ~$10 por día y el límite es 120 sesiones. El tamaño es una regla de la estrategia, no un ajuste de señal.
           Tamaño fijado por el límite diario de Topstep (DLL $1,000): 3 pérdidas seguidas al stop máximo (32 ticks = $160 + comisión)
           con 2 contratos ≈ $1,000. Con 3 o más ya podría romper el DLL en un solo día.
           Investigación y justificación: docs/investigacion/tamano_posicion.md.
"""
from .v17 import PARAMS as P17, absorption_unified

PARAMS = {"ABU2": dict(P17["ABU"])}
CONTRACTS = 2


def absorption_unified_v2(s, ref, thr, p=None):
    return absorption_unified(s, ref, thr, p or PARAMS["ABU2"])


REGISTRY = {"ABU2": absorption_unified_v2}
