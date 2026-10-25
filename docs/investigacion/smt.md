# Divergencia NQ vs ES (SMT)

_Investigado por el laboratorio el 25/10/2026. Nadie le preguntó a Oscar cómo definirla._

## Qué encontré (fuentes)
- **SMT (Smart Money Technique)** = una no-confirmación entre dos índices correlacionados en el mismo extremo. SMT bajista: un índice rompe su máximo previo y el otro no. SMT alcista: espejo con el mínimo. [LuxAlgo · SMT divergence](https://www.luxalgo.com/library/concept/smart-money-technique-divergence.md), [TradingView · SMT Divergence](https://es.tradingview.com/scripts/smtdivergence/), [El Trader Financiado](https://www.eltraderfinanciado.com/de/blog/smt-divergence).
- Los dos extremos tienen que ser **de la misma sesión** (no el máximo de NQ del lunes contra el de ES del martes).
- La lectura de order flow: el barrido que no confirma es liquidez tomada sin interés real del otro índice → posible reversión. Es una interpretación; **las mismas guías admiten que no hay estadística pública** (ni porcentaje de aciertos ni grupo de control). Aquí se mide contra RAND.
- Casi todas lo usan como capa de confirmación sobre un nivel (bloque, hueco). Aquí el "nivel" es el extremo de la sesión de NQ.

## Escenarios
1. **NQ barre el máximo (mínimo) de la sesión, ES no** → reversión contra el barrido. *(se prueba: SMT v1)*
2. **ES barre y NQ no** (el espejo). Mismo mecanismo con el índice débil como el que se opera. *(pendiente, SMT v2 si el escenario 1 muestra algo; no se mezcla ahora para no elegir después)*
3. **Ambos rompen** → no hay divergencia; es continuación normal.

## Definición operable fijada (antes de ver resultados)
- Extremo de la sesión = máximo/mínimo desde las 09:30 ET. Solo después de las 09:45 (hay historia).
- **Barrido**: un llenado de NQ por encima (debajo) del máximo (mínimo) previo de la sesión.
- **ES no confirma**: en los `lookback_s` = 120 s anteriores al barrido y hasta el momento de la entrada, ningún llenado de ES supera el máximo (mínimo) que ES tenía antes de esa ventana.
- **Fallo del barrido** (flujo agresivo): NQ vuelve a operar en o dentro del extremo previo en menos de `fail_s` = 120 s y el delta agresivo de NQ desde el barrido hasta el regreso no favorece al barrido (≤ 0 tras un máximo, ≥ 0 tras un mínimo).
- Entrada a mercado en contra del barrido al regreso. Stop `stop_beyond` = 4 ticks más allá del extremo del barrido (12–32 ticks). Sin objetivo; sale por tiempo a 15 min. Cooldown 300 s por lado. Horario 09:45–11:30, reglas comunes del laboratorio.
- Contrato de ES: el de más volumen en la ventana de NY. Precios en ticks de 0.25 (igual que NQ). No se compara nivel contra nivel: solo "ES superó o no su propio extremo".
- Sin velas ni indicadores: solo llenados, extremos de la sesión y delta.

## Definiciones que se comparan dentro del MISMO estudio (`smt_v1`)
Cada una cuenta como intento: ventana de ES 60 / 90 / 150 / 180 s (base 120), plazo del fallo 60 / 90 / 150 / 180 s (base 120), stop 0 / 2 / 6 / 8 ticks más allá, salida 5 / 10 / 20 / 25 min (base 15). Total 1 + 16 = 17. La base se fijó antes de correr; no se elige la mejor después.
Lo único que se miró antes de fijarla fue el número de señales (no ganancias): 591 señales en 362 de las 576 sesiones con la base (687 con ventana de ES de 60 s; 589 con plazo de 60 s). Suficiente para el largo mínimo (100 operaciones).

## Límite honesto
Los datos de ES no están en el manifiesto de huellas de NQ (`canonical_manifest.json`). Las dos corridas idénticas del orquestador dan fe de reproducibilidad, pero no de integridad de ES. Pendiente: sumar ES al manifiesto (no se toca ese código en esta corrida).
