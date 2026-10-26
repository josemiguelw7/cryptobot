# ABB v1: absorción después de una re-entrada aceptada al valor de ayer

_Corrida del investigador, 26/10/2026. Nadie le preguntó a Oscar cómo definirlo._

## Por qué esta prueba
- P040 (ABM v1, niveles de varios días): **insuficiente**, 58 operaciones, −$2,738, p 0.53. Los niveles multi-día no sirven. La absorción en NY, en los días que ABU ya cubre, está agotada.
- ABU (la única familia con ventaja: P031 +$11.9k, p 0.001, 3 años positivos) solo opera si el día **abre dentro** del valor de ayer. Eso deja fuera los días que abren fuera. ABT (P032) probó esos días con sesgo de tendencia y perdió, pero nunca se probó la absorción de ABU **después de que el precio vuelve al valor y lo acepta**.
- El problema de Topstep es la frecuencia: ABU tiene ≈170 operaciones en 576 sesiones.

## Qué dice la literatura (fuentes ya reunidas en `aceptacion.md`, 25/10/2026)
- Regla del 80% (Steidlmayer; Dalton, *Mind Over Markets*): si el precio abre fuera del valor de ayer, vuelve adentro y **se queda dos períodos de 30 min**, hay alta probabilidad de que rote por el valor. Es una regla práctica, no una estadística auditada.
- Aceptación = tiempo en el nivel (más volumen). Nadie fija cuánto: "es del que prueba".
- Un mercado aceptado dentro del valor es un mercado en balance; en balance, los bordes y el POC se rotan y el flujo agresivo contra ellos se absorbe (misma lógica que ABU).

## Definición fijada (antes de ver ninguna ganancia)
- Día elegible: el primer precio de las 09:30 está **fuera** de [VAL, VAH] de ayer (el complemento exacto de ABU).
- Aceptación: el precio lleva `accept_s` = **600 s (10 min)** seguidos dentro de [VAL, VAH] de ayer. Se conoce solo en ese instante (sin futuro).
- Habilitado el resto del día: la ventana de absorción de 60 s debe **empezar después** de la aceptación. Antes no hay señales.
- Todo lo demás es idéntico a ABU v3: niveles de ayer, de la noche y POC/VAH/VAL del día en desarrollo; umbral relativo; confirmación a 60 s; entrada contra el lado absorbido; stop 12–32; objetivo 2R; salida a 15 min; 2 contratos; ventana 09:30–15:30; parada tras 2 pérdidas.
- **Por qué 10 min y no 60 (Dalton):** con 30 min había ≈ 12 operaciones por 100 sesiones (≈ 70 en total, abajo del mínimo de 100). Se eligió **solo por conteo de señales** (26 operaciones por 100 sesiones con 600 s; 38 con 300 s; 22 con 900 s). Ninguna ganancia se miró. Los demás valores van en la sensibilidad.

## Qué NO es esta prueba
- No es validación independiente: mismo detector y mismos datos de diseño que ABU. Es una pregunta sobre **días que ABU no opera**.
- El DSR sigue penalizado por más de 1,000 intentos: el criterio (b) no cambia.

## Intentos (estudio abb_v1)
1 base + 16 de sensibilidad: cercanía al nivel (±1, ±2 ticks), confirmación (±10, ±20 s), umbral relativo (±2, ±4 puntos de percentil) y tiempo de aceptación (450/300/750/900 s). 17 en total.

## Cómo se lee
- Ganancia > 0, p ≤ 0.05, positiva 3 años y ≥ 100 operaciones → los días con re-entrada aceptada suman operaciones a ABU; se mira Topstep de ABU+ABB juntos en una prueba posterior.
- Si no → la absorción solo funciona en días que abren dentro del valor, y la familia queda cerrada en NY.
