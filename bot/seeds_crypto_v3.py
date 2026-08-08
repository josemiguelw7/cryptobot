"""
ROSTER CRIPTO WAVE 3 — relojes lentos (plan_v3.md F1).

ESTADO: PROPUESTO. NO ADOPTADO. ARMED = False.
Roster CONGELADO en docs/plan_v3.md antes de cualquier examen.
Firma del plan: Jose Santos, 2026-08-08 04:15 UTC — autoriza
implementar e examinar, NO autoriza armar. Armar exige veredictos
registrados + firma aparte.

POR QUE EXISTE ESTA OLA
-----------------------
Tres pruebas independientes, ninguna compartiendo supuestos, dicen lo
mismo (Tanda A, analysis/, 2026-08-07):

  1. Aritmetica: movimiento tipico 1h = 0.25% contra coste ida+vuelta
     0.84%  ->  acierto necesario 215% (imposible). A una semana el
     umbral cae a ~60%; a un mes, ~55%.
  2. MFE/MAE: la operacion horaria mediana NUNCA pasa por un instante
     rentable (mejor momento +0.27% contra umbral 0.84%).
  3. Meseta de parametros: en la familia nearhi todo mejora de forma
     monotona hacia horizontes MAS LARGOS.

Los horizontes de abajo se derivan de (1), declarados de antemano. NO
se copian del escaneo de meseta: n=240 rindio mejor que n=168 EN LA
MUESTRA, y elegirlo por eso seria mineria de datos -- exactamente el
pecado que convirtio +354% en -90%.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategies as S

ARMED = False              # exige veredictos F1 + firma aparte
ASSET_CLASS = "crypto"
EPOCH = 3

PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]

MAX_POS = 6                # E3.3: cupos de $500 sobre $3,000
MIN_HOLD_BARS = 168        # E3.1: salida bloqueada antes de 1 semana
MAX_CORR = 0.70            # E3.2: correlacion mediana medida = 0.77


def _n(s, name):
    s.name = name
    return s


SEEDS = {
    "d3_trend":     {"strat": _n(S.SlowClock(S.Trend(20), 24), "d3_trend"),
                     "hold_h": 240,
                     "note": "tendencia sobre barras DIARIAS (SMA 20d)"},
    "d3_nearhi":    {"strat": _n(S.SlowClock(S.NearHigh(60, 0.02), 24),
                                 "d3_nearhi"),
                     "hold_h": 360,
                     "note": "cerca del maximo de 60 dias"},
    "d3_calm":      {"strat": _n(S.SlowClock(S.CalmRegime(5, 20), 24),
                                 "d3_calm"),
                     "hold_h": 240,
                     "note": "regimen de baja volatilidad, reloj diario"},
    "d3_cash":      {"strat": _n(S.SlowClock(S.MarketRegime(200, 20), 24),
                                 "d3_cash"),
                     "hold_h": 240,
                     "note": "EFECTIVO salvo BTC>SMA200d y propio>SMA20d"},
    "h3_crossconf": {"strat": _n(S.ConfirmedEntry(S.Cross(24, 168), 12),
                                 "h3_crossconf"),
                     "hold_h": 72,
                     "note": "cross horario + confirmacion por vela"},
    "d3_rand":      {"strat": _n(S.RandomEntry(240, 1.0 / 240, "d240"),
                                 "d3_rand"),
                     "hold_h": 240,
                     "note": "control aleatorio lento; FAIL pre-registrado"},
}


def get(name):
    if name not in SEEDS:
        raise KeyError(f"semilla desconocida {name!r}: {sorted(SEEDS)}")
    return SEEDS[name]["strat"]


if __name__ == "__main__":
    print(f"roster cripto wave 3 — "
          f"{'ARMED' if ARMED else 'PROPUESTO (no adoptado)'} · "
          f"MAX_POS={MAX_POS} · MIN_HOLD={MIN_HOLD_BARS}h")
    for n, c in SEEDS.items():
        s = c["strat"]
        print(f"  {n:14s} warmup {s.warmup:5d}  hold >= {c['hold_h']:4d}h  "
              f"{c['note']}")
