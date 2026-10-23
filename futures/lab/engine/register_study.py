"""Registra un estudio ANTES de correr sus intentos (protocol.json › pruebas_multiples).

  python -m engine.register_study tanda1
  python -m engine.register_study mapa_v1
"""
import sys
from . import registry, config

STUDIES = {
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
