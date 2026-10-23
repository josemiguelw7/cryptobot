"""Registra un estudio ANTES de correr sus intentos (protocol.json › pruebas_multiples).

  python -m engine.register_study tanda1
  python -m engine.register_study mapa_v1
"""
import sys
from . import registry, config

STUDIES = {
    "tanda2b": {
        "hypothesis": "FADE v2 (objetivo 8, stop 12, 10 min) y FADEL v1 (entrada pasiva con cola) capturan el efecto de 6–7 ticks contra las órdenes grandes y ganan a RAND después de costos.",
        "n_declared": 2 + 32,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["FADE v2", "FADEL v1"],
        "notes": "Reemplaza a FADE v1 (descartada sin correr tras el humo). Aprobado por Jose Miguel el 23/10/2026.",
    },
    "tanda2": {
        "hypothesis": "FADE v1 (desvanecer órdenes grandes), HVN v1 (rechazo de nodos de ayer) y ABS v2 (dejar correr al ganador), con números medidos en el mapa v1 y el estudio de salidas, ganan a RAND después de costos y pasan Topstep.",
        "n_declared": 3 + 48,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["FADE v1", "HVN v1", "ABS v2"],
        "notes": "3 pruebas + 48 de sensibilidad. Arranca solo cuando el comité pase las pruebas a 'congelada' en el backlog.",
    },
    "mapa_v2": {
        "hypothesis": "Las 12 señales, además del azar de la misma dirección, se comparan contra un azar con dirección aleatoria (¿la dirección es rentable?), se parten por régimen (tendencia/balance) y por media hora, y se exige que el signo del efecto a 15 min sea el mismo en 2024 y en 2025.",
        "n_declared": 48 + 24,
        "kill": ["no sobrevive Holm (48 principales / 24 de régimen)", "signo distinto en 2024 y 2025"],
        "strategies": ["12 señales × régimen"],
        "notes": "Aprobado por Jose Miguel (método, no estrategia). El desglose por media hora es descriptivo: no se cuenta como prueba.",
    },
    "salidas_v1": {
        "hypothesis": "Pedido de Oscar (23/10/2026): con las mismas señales v1, un take profit fijo (20/30/40/50 puntos), otro stop fijo (3/4/6/8 puntos), más tiempo, o agregar contratos a favor, mejoran el resultado neto y forman una meseta (no un pico aislado).",
        "n_declared": 159,
        "kill": ["sin meseta: solo celdas aisladas ganan", "la celda mejor pierde con costos al doble o depende de 5 días"],
        "strategies": ["BIG v1", "ABS v1", "POC v1 (salidas)"],
        "notes": "5 TP × 5 SL × 2 tiempos = 50 celdas por estrategia (menos la base ya publicada) + 4 variantes de piramidar × 3 estrategias. Explora la dimensión de salida, no la señal. Nada se adopta sin versión nueva y protocolo completo.",
    },
    "mapa_v1": {
        "hypothesis": "Alguna de las 12 señales de order flow mueve el precio en la dirección predicha a 1, 5, 15 o 30 min más de lo que lo hacen momentos al azar a la misma hora.",
        "n_declared": 48,
        "kill": ["p de permutación no sobrevive Holm 5% sobre 48 pruebas", "menos de 100 eventos en el periodo de diseño"],
        "strategies": ["12 señales"],
        "notes": "Fase 1 del plan. Sin stops ni objetivos. Mide y publica todo; nada se descarta antes de medir.",
    },
    "tanda1": {
        "hypothesis": "Las estrategias BIG, ABS y POC v1 (reglas de los videos con números propuestos sin medir) ganan a RAND emparejado después de costos.",
        "n_declared": 3 + 48,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["BIG v1", "ABS v1", "POC v1"],
        "notes": "3 pruebas principales + 48 corridas de sensibilidad (4 parámetros × 4 vecinos × 3 estrategias). Es el 'intento ingenuo': los números no salen de los datos.",
    },
}


def main():
    sid = sys.argv[1]
    s = STUDIES[sid]
    registry.register_study(sid, s["hypothesis"], s["n_declared"], s["kill"], s["strategies"], s["notes"])
    print("estudio registrado:", sid, registry.study_counts(sid))


if __name__ == "__main__":
    main()
