# Regla del 80% (VAR v1)

_Nota de reconstrucción (25/10/2026): este archivo se perdió en un rebase a medias; se rehace desde `strategies/v8.json`, `engine/strategies/v6.py` y el estudio `regla80_v1`._

- Fuente: Steidlmayer / Dalton, ver `aceptacion.md` (escenario 2): si abre fuera del valor de ayer, vuelve adentro y se queda dos períodos de 30 min, cruza hasta el otro lado del valor.
- Definición operable (fijada antes de correr): abre fuera de VAL–VAH de ayer; vuelve ≥ 2 ticks adentro; se queda 180 s seguidos; delta agresivo hacia el interior ≥ 2% del volumen. Entrada a mercado hacia el interior, stop 4 ticks fuera del borde (12–32), salida a 30 min. Un disparo por día.
- Estudio `regla80_v1`: 1 + 16 intentos (tiempo 60/120/240/300 s, delta 1/3/4%, stop 2/6/8, salida 10/20/40/50 min).
- Resultado: P019 no pasa (−$7,947, 113 operaciones, Topstep 0%, pierde 2024, 2025 y 2026).
