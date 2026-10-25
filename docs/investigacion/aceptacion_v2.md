# ACC v2 · aceptación en los bordes de la subasta anterior

_Investigado por el laboratorio el 25/10/2026. Nadie le preguntó nada a Oscar._

## De dónde sale
- Oscar pidió probar aceptación, no solo rechazo (ver `aceptacion.md`). ACC v1 (P017) dio +$2,028, p 0.19, solo 97 operaciones: no concluyente.
- Teoría (Dalton, Steidlmayer): el valor de ayer y los extremos de la subasta anterior son los bordes que el mercado debe aceptar o rechazar. Aceptar un nivel nuevo = tiempo + volumen allí. El máximo/mínimo de ayer y de la noche son bordes de la misma subasta, no solo VAH/VAL.
- Regla de la apertura (Dalton): abrir dentro del valor de ayer es "apertura en rango"; abrir fuera es "apertura con hueco". Con hueco, los niveles ya fueron rebasados o el día ya viene dirigido.

## Lo que vimos en nuestros propios datos (periodo de diseño, ya publicados)
| Prueba | Abre dentro del valor | Abre fuera |
|---|---|---|
| ABS v2 (P012) | +$7,479 (44 op.) | +$395 (82 op.) |
| ABS v3 (P016) | +$5,235 (53 op.) | −$830 (90 op.) |
| ACC v1 (P017) | +$4,610 (41 op.) | −$2,582 (56 op.) |
Tres pruebas distintas, mismo sentido. **Limitación honesta:** esto sale de mirar resultados del mismo periodo de diseño, así que el filtro es exploratorio. Tres tablas no son tres validaciones independientes (comparten días). Por eso: se declara, cuenta en el DSR y solo el examen sellado lo puede confirmar.

## Definición fijada
Igual que ACC v1 (180 s fuera sin volver más de 2 ticks, delta agresivo ≥ 5% a favor, entrada a mercado, stop 4 ticks adentro del nivel de 12 a 32, sin objetivo, salida a 20 min). Dos cambios:
1. Niveles: VAH, VAL, máximo y mínimo de ayer, máximo y mínimo de la noche (v1: solo VAH y VAL).
2. Filtro: el primer llenado de las 09:30 debe estar dentro de VAL–VAH de ayer.

## Definiciones que se comparan en el MISMO estudio (`aceptacion_v2`)
Tiempo 90/270/360 s, delta 3/7/9%, stop 2/6/8 ticks, salida 5/15/25 min. 1 + 16 intentos declarados. No se elige la mejor después.

## Lo único que se miró antes de fijar
Solo el número de señales (110 en 556 sesiones; por nivel: night_high 33, prev_vah 26, prev_high 19, prev_val 15, night_low 12, prev_low 5). Ninguna ganancia de ACC v2.

## Riesgos
- ~110 señales: apenas sobre el mínimo (100). Si quedan menos, el veredicto es "insuficiente".
- El placebo desplazado probablemente salte otra vez (la ruptura misma es el movimiento); iría a "revisar".
- Es la segunda de máximo tres versiones de ACC.
