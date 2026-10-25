# Absorción confirmada por ES (ABE v1)

_Corrida del investigador, 25/10/2026. Nadie le preguntó a Oscar cómo definirla._

## Por qué esta prueba
- P037 (ABR v1, entrada pasiva): −$1,186 en 77 operaciones, p 0.34. Cambiar la entrada no ayudó. Se cierra esa línea.
- La única familia con ventaja sigue siendo ABU (P030/P031: +$6.0k / +$11.9k, p 0.001, positiva 3 años). Pero pierde el 60% de las operaciones con el stop.
- Ya probé: más tamaño (ABU v2), otros días (ABT), ventana rápida (ABQ), entrada pasiva (ABR), seguir la ruptura (ABF), niveles nuevos (ABI, ABV, HVF, LVN). Todo con la misma información: solo NQ.
- Lo que nunca probé como **filtro** es la información de ES. SMT v1 (P018) usó ES como disparador y perdió; aquí es un filtro sobre la única señal con ventaja.

## Qué encontré (fuentes)
- Confirmación entre mercados correlacionados (NQ/ES): la idea de SMT (ver `docs/investigacion/smt.md`, con sus fuentes: LuxAlgo, TradingView, El Trader Financiado). Un movimiento visto en un solo índice se lee como local; visto en ambos, como del mercado completo. Las mismas guías admiten que **no hay estadística pública**: aquí se mide contra RAND.
- Absorción en auction market theory (Dalton, *Mind over Markets*; footprint/delta): pasivos grandes que frenan al flujo agresivo. Si los pasivos son grandes de verdad, el otro índice (misma cesta, arbitraje) también debería frenarse. Es una interpretación mía, no un resultado.
- No hice búsqueda web nueva en esta corrida: reuso las fuentes ya registradas en `smt.md` y `absorcion_unificada.md`.

## Escenarios
1. **ES también se detuvo** (no avanzó en la dirección del flujo absorbido) → absorción de todo el mercado → reversión. *(se prueba: ABE v1)*
2. **ES sí avanzó y NQ aguantó solo** → hueco local; NQ tiende a alcanzar a ES (retraso). Es el espejo; **no se prueba ahora** y no se mezcla para no elegir después. Si ABE v1 mejora a ABU, el escenario 2 servirá de control negativo.

## Definición operable fijada (antes de ver resultados)
- Señales: detector de ABU v1 sin cambios (`v17.py`), 1 contrato, mismas salidas (stop 12–32, 2R, 15 min), 09:30–15:30.
- Ventana de ES: los 120 s que terminan en la confirmación de la señal (cubre el flujo absorbido y la confirmación).
- ES "se detuvo": el máximo avance de ES (en ticks de 0.25) en la dirección del flujo agresivo absorbido, medido desde su primer llenado de la ventana, es ≤ 2 ticks. Mínimo 20 llenados de ES en la ventana; si no hay o no hay datos de ES, no se opera.
- Contrato de ES: el de más volumen en 09:30–15:45. Solo llenados y precio; sin velas ni indicadores.

## Intentos (en el MISMO estudio `abe_v1`)
1 base + 16 sensibilidades = 17: umbral de avance de ES 0/1/3/4 ticks, ventana de ES 90/150/... (±30 s), objetivo 1/1.5/2.5/3 R, confirmación 30/45/75/90 s. La base se fijó antes; no se elige la mejor después. Escenario 2 no cuenta porque no se corre.

## Lo único que se miró antes de fijar
Solo conteo de señales (no ganancias) en 120 sesiones: ABU 43 señales, ABE 24 (~115 esperadas en 576 sesiones). Cerca del mínimo de 100 operaciones: si queda por debajo, la prueba muere por "pocas operaciones" y se acepta.

## Límite honesto
- Mismas señales que ABU: **no es validación independiente**. Es un filtro sobre datos ya usados (más de 1,000 intentos en el registro; el DSR no se puede cumplir).
- Los datos de ES no están en el manifiesto de huellas (ver `smt.md`).
- Aunque mejore, 24 señales por 120 sesiones no resuelven Topstep (frecuencia). Esto mide si la calidad sube, no si pasa la cuenta.
