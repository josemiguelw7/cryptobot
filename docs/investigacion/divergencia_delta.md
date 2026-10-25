# DVG v1: divergencia de delta en el extremo del día

## Por qué esta prueba
- La familia de absorción (ABU) es la única con ventaja (P030/P031: p 0.001, positiva 2024-2026), pero solo opera cerca de niveles y en días que abren dentro del valor: ~180 operaciones, Topstep lento. ABQ (P033, escala de 30 s) no pasó: −$1,961, p 0.24.
- Falta una señal de flujo agresivo que **no dependa de un nivel de ayer ni del tipo de día**. El propio extremo del día es el nivel (contexto de perfil: máximo/mínimo de sesión).

## Qué dice la literatura (búsqueda 25/10/2026)
- Divergencia bajista de delta acumulado (CVD): el precio hace un máximo más alto pero el CVD hace un máximo más bajo (NexusFi, "Delta Analysis CVD"; indicadores abiertos de TradingView "Orderflow Suite" y "Delta Microstructure Analysis" usan la misma regla con pivotes). Es "agotamiento": el empuje nuevo llegó con menos flujo agresivo.
- Las mismas fuentes advierten que es una alerta, no un disparador: pide confirmación (retorno del precio) y estructura (nivel). Por eso la confirmación es obligatoria y el extremo del día es la estructura.
- No encontré una definición única de "exceso" de Dalton ligada a delta. Mi definición operable es mía y se declara abajo.

## Definición (una sola, fijada antes de correr)
- Celdas de 10 s desde las 09:30; delta acumulado de la sesión (compras agresivas − ventas agresivas).
- Nuevo máximo de sesión en la celda e, no antes de 10 min, si: (1) el máximo anterior se marcó hace ≥ 2 min; (2) entre ambos el precio retrocedió ≥ 10 ticks bajo el máximo anterior; (3) el delta acumulado en e es **menor** que el delta acumulado en la celda del máximo anterior. Espejo para mínimos.
- Confirmación: en los 30 s siguientes el precio cae 3 ticks bajo el extremo sin hacer otro máximo (espejo para mínimos).
- Entrada a mercado en contra del extremo; stop 3 ticks más allá del extremo (entre 8 y 24 ticks); objetivo 2R; salida a 5 min; 1 contrato; hasta 8 operaciones al día; 09:30–15:30 ET; sin noticias fuertes.
- No se compararon otras definiciones (pivotes, delta por vela, delta de 60 s): una sola.

## Sensibilidad (12 intentos)
Retroceso 6/8/12/14 ticks, alejamiento 1/2/4/5 ticks, objetivo 1/1.5/2.5/3 R.

## Humo (solo cuenta señales y que el código corre)
3 días (2024-05-22 a 24): 4, 5 y 3 señales, todas pasan por el simulador. ~4 por día: frecuencia mucho mayor que ABU (~0.3 por día). Nunca se miraron ganancias.

## Riesgos
- Exploratoria: sale de ver que la absorción es lo único que funciona; no es validación independiente.
- Con ~4 señales por día y 1000+ operaciones el costo ($13.78 + deslizamiento) pesa: si la ventaja bruta es chica, muere por costos.
- Contra-tendencia: en días de tendencia fuerte los máximos siguen subiendo; el stop de 8-24 ticks acota la pérdida.
