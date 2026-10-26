# Placebo de niveles de ABU v2 · ABP v1 (validación G1)

Escrito el 26/10/2026. Pedido de Jose: antes de gastar más versiones, comprobar si la ventaja de ABU (P031, +$11.9k, p 0.001) viene de **dónde está el nivel** o es un artefacto.

## Por qué hace falta
- P031 quedó en "revisar": el placebo desplazado en el tiempo (5 min antes) ganó ≥ 50% de lo real. En P003/P005 se explicó (entrar antes, más cerca del extremo, el valor está en el nivel y no en el momento), pero esa explicación **nunca se probó con un placebo directo**. Es lo que falta.
- El progreso del laboratorio (40%) se apoya en ABU. Si el placebo rinde parecido, el 40% es ilusión.

## Qué dice la literatura (método, de memoria; no se abrió ninguna fuente nueva)
- Aronson, *Evidence-Based Technical Analysis* (2007) y White (2000, *Reality Check*): una regla solo tiene valor si gana a las versiones "sin información" de sí misma (señales o niveles al azar), no solo a cero.
- En order flow, el placebo natural de "reacción en un nivel" es **mover el nivel** y dejar todo lo demás (mismo flujo, mismos filtros, mismas salidas). Si la ventaja desaparece, el nivel importaba.
- Bailey y López de Prado (2014): cada variante cuenta como intento; por eso se declaran en n_declared.

## Definición operable (una sola, fijada antes de correr)
ABP v1 = ABU v2 sin cambios (detector 60 s, p90 relativo, confirmación 60 s, filtro "abre dentro del valor de ayer" con el valor REAL, stop 12–32, 2R, salida 15 min, 2 contratos, 09:30–15:30) con UN cambio: todos los niveles (ayer, noche, POC/VAH/VAL del día) se desplazan 40 ticks (10 puntos). Signo: + en fechas de ordinal par, − en impares (sin sesgo direccional, sin mirar precios). 40 ticks ≈ 10 puntos: lejos de la tolerancia de 4 ticks, así que ningún nivel falso coincide con uno real.

## Cómo se lee el resultado (fijado antes de ver nada)
- Referencia: ABU v2 = +$11,912, 181 operaciones (P031).
- **Placebo pierde** (neto ≤ 50% de ABU v2 y p vs RAND > 0.05): la ventaja depende del nivel → ABU se sostiene como hipótesis (sigue siendo exploratoria, no validada).
- **Placebo rinde ≥ 50% de ABU v2** (o p vs RAND ≤ 0.05): la ventaja es del detector de flujo + salida, no del nivel, o hay artefacto; el 40% de progreso se rebaja a 20% y no se invierte más en variantes de nivel.
- El resultado no cambia la regla de muerte del protocolo (ganancia, p, años, MLL): corre con el mismo motor.

## Humo (solo conteo)
100 sesiones: ABU v2 33 señales, ABP 33; solo 2 coinciden en hora y lado. Sin ganancias miradas.

## Alternativas descartadas
Niveles de otro día (5 sesiones atrás): requiere código de datos nuevo en run_test; se deja como futura segunda validación. Desplazar siempre hacia arriba: mete sesgo de tendencia.

## Límites
Mismos datos de diseño; es una validación interna, no el examen sellado. 1 base + 16 sensibilidades (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94 y desplazamiento 24/32/48/56 ticks).
