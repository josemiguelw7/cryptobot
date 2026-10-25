"""Registra un estudio ANTES de correr sus intentos (protocol.json › pruebas_multiples).

  python -m engine.register_study tanda1
  python -m engine.register_study mapa_v1
"""
import sys
from . import registry, config

STUDIES = {
    "aceptacion_v1": {
        "hypothesis": "Pedido de Oscar (25/10/2026): cuando el precio sale del área de valor de ayer (VAH/VAL) y la acepta (180 s seguidos fuera con delta agresivo a favor ≥ 5%), continúa más de lo que lo hace un RAND emparejado, y la estrategia ACC v1 gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026 y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ACC v1"],
        "notes": "1 prueba + 16 de sensibilidad. Las definiciones alternativas de aceptación (tiempo 90/270/360 s, delta 2/8/11%, stop 2/6/8, salida 10/15/25/30 min) se comparan aquí y cuentan como intentos. Definición base fijada antes de correr (docs/investigacion/aceptacion.md).",
    },
    "abs_v3": {
        "hypothesis": "ABS v3 (absorción con entrada temprana, sin confirmación de 60 s, stop v1, salida por tiempo a 15 min) gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026, y sube la tasa de Topstep sobre el 41-43% de ABS v2.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABS v3"],
        "notes": "1 prueba + 16 de sensibilidad (4 parámetros x 4 vecinos). Tercera y última versión de ABS. T2-ABS-HOURS descartada (requiere cambio de motor).",
    },
    "salidas_1_1": {"hypothesis": "Repetición del estudio de salidas (pedido de Oscar) con el motor 1.1 y percentiles exactos.", "n_declared": 159, "kill": ["sin meseta"], "strategies": ["BIG v1", "ABS v1", "POC v1 (salidas)"], "notes": "Repite salidas_v1 (motor 1.0, superado)."},
    "mapa_v4": {"hypothesis": "Repetición del mapa v3 con percentiles exactos de órdenes y ventanas (los umbrales de 'órdenes grandes' y 'absorción' cambian).", "n_declared": 72, "kill": ["no sobrevive Holm", "signo distinto 2024/2025"], "strategies": ["12 señales × régimen"], "notes": "Repite mapa_v3 (umbrales del motor 1.0)."},
    "repeticion_1_1": {
        "hypothesis": "Repetición de P002–P008 con el motor 1.1 (llenados corregidos tras la revisión ciega del 24/10/2026). Las reglas selladas no cambian. Se espera que los resultados empeoren.",
        "n_declared": 7 + 112,
        "kill": ["los mismos criterios del protocolo v3"],
        "strategies": ["BIG v1", "ABS v1", "POC v1", "ABS v2", "HVN v1", "BIG v2", "ORB v1"],
        "notes": "7 pruebas + 16 de sensibilidad cada una. Los intentos cuentan igual que cualquier otro.",
    },
    "tanda3": {
        "hypothesis": "BIG v2 (seguir la orden grande con entrada inmediata, objetivo 12, stop 16) y ORB v1 (ruptura del rango inicial, 16/16, 30 min), con premisas del mapa v3 medido desde precios operables, ganan a RAND después de costos y pasan Topstep.",
        "n_declared": 2 + 32,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["BIG v2", "ORB v1"],
        "notes": "Aprobadas por Jose Miguel el 24/10/2026. Corre el orquestador.",
    },
    "proxy_v1": {
        "hypothesis": "Con el rango y el cuerpo de los primeros 15 minutos, la apertura dentro/fuera del valor y la distancia al VWAP a las 09:45 se puede anticipar si el día terminará en balance o tendencia claramente mejor que la base.",
        "n_declared": 1,
        "kill": ["ningún proxy separa más de 15 puntos porcentuales de la base"],
        "strategies": ["proxy de régimen"],
        "notes": "Descriptivo salvo la precisión del mejor proxy (1 intento). Aprobado por Jose Miguel el 23/10/2026.",
    },
    "mapa_v3": {
        "hypothesis": "Repetición del mapa v2 midiendo desde el mid del libro operable (bid/ask antes del primer llenado posterior) en vez del último llenado, que en un barrido queda ~8 ticks atrás del libro real. Se espera que 'desvanecer órdenes grandes' desaparezca y que el resto se corrija en menor medida.",
        "n_declared": 48 + 24,
        "kill": ["no sobrevive Holm", "signo distinto en 2024 y 2025"],
        "strategies": ["12 señales × régimen"],
        "notes": "Corrección metodológica tras el hallazgo del 23/10/2026 (FADE). El mapa v2 queda en signal_map_v2.json como registro del error.",
    },
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
