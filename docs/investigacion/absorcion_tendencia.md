# ABT v1: absorción a favor de la tendencia (días que abren fuera del valor)

## Por qué esta prueba
- P031 (ABU v2, 2 contratos): +$11,912, p 0.001 contra RAND, positiva los 3 años. Pero Topstep **41.2%** y **214 de 517 cuentas rompen el MLL**. Con 1 contrato (P030) eran 0 rotas pero 9.9% por lentitud. El tamaño no arregla Topstep: subir el riesgo rompe cuentas.
- Lo que falta es frecuencia con 1 contrato. ABU, ABD, ABI y ABV solo operan días que abren **dentro** del valor de ayer. Los días que abren fuera nunca se probaron con el detector de absorción que sí funciona (ABS v1 los mezclaba con los demás).
- Además: P031 muestra el 2024–2026 sin pérdidas anuales, y la hora/nivel sin cambios. No hay más que apretar en ese filtro; hay que ampliar el universo de días.

## Qué dice la teoría (de las notas ya recogidas por el laboratorio; no hay búsqueda nueva)
- Dalton / Steidlmayer, Market Profile: una apertura fuera del valor de ayer indica posible día de tendencia (o un intento de aceptación en valor nuevo). Si el mercado acepta, los retrocesos hacia el borde anterior del valor son comprados (o vendidos) por el lado de la tendencia. Ver `aceptacion.md` y `absorcion_dias_balance.md`.
- Order flow: un retroceso con flujo agresivo contrario que no mueve el precio (absorción) en el nivel de reaparición sugiere que el lado pasivo a favor del sesgo defiende.

## Definición (fijada antes de correr, una sola)
- Sesgo: primer precio de las 09:30 > VAH de ayer → +1 (solo largos); < VAL de ayer → −1 (solo cortos); dentro → no se opera (es de ABU).
- Detector, umbral relativo, niveles (ayer, noche, POC/VAH/VAL en desarrollo), confirmación a 60 s, stop 12–32, objetivo 2R, salida a 15 min, ventana 09:30–15:30: idénticos a ABU v1.
- Único cambio de señal: solo se acepta la absorción del flujo contrario al sesgo (ventas absorbidas si abre arriba; compras si abre abajo).
- 1 contrato. No se compararon otras definiciones de "tendencia".

## Humo (solo señales, nunca ganancias)
- 56 sesiones (una de cada 10): 16 señales en 8 días → unas 165 en el periodo. Corrida corta de 80 sesiones: el motor la ejecuta de punta a punta.

## Riesgos
- Exploratoria: la idea nace de ver resultados de diseño (la familia ganó en balance). El DSR (más de 900 intentos) la penaliza; no es validación independiente.
- Día de tendencia = menos retrocesos que absorben; puede salir pocas operaciones (<100 → "insuficiente").
- Una cuenta Topstep necesitaría combinar ABT con ABU: eso sería otra estrategia, no se prueba aquí.
