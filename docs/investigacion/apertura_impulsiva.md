# Apertura impulsiva (open drive) medida por flujo · OPD v1

Investigado el 26/10/2026.

## Qué encontré
- Dalton (Mind Over Markets) clasifica la apertura en cuatro tipos: open-drive (el precio sale en una dirección y no mira atrás), open-test-drive, open-rejection-reverse y open-auction. El open-drive es iniciativa de corto plazo y suele definir el día. Es la contraparte de ABU (balance/rechazo): aquí se prueba el lado de iniciativa, medido con flujo y no con velas.
- El laboratorio nunca midió la iniciativa de apertura con delta. ORB v1 usó el rango de precio (no pasó) y BIG siguió órdenes grandes (no pasó); ninguna mide el flujo neto de los primeros minutos.

## Definición operable (una sola, fijada antes de correr)
En los primeros 300 s desde las 09:30: (1) |delta agresivo| ≥ 3 % del volumen; (2) el precio avanza ≥ 40 ticks (10 puntos) en la dirección del delta; (3) el mayor retroceso desde el extremo corrido del avance es ≤ 1.0 × el avance. Entrada a mercado a favor a las 09:35, stop en el contra-extremo de la ventana (12–32 ticks), objetivo 1.5R, salida a 15 min, 2 contratos, una operación por día.

## Cómo fijé los umbrales (solo distribución de las variables, sin ganancias)
En 296 sesiones, mediana de |delta| = 2.3 %, percentil 75 = 4.7 %; mediana del avance 92 ticks. Con umbrales de "no mira atrás" estrictos (retroceso ≤ 0.33, delta 10 %) salían 1–6 señales en 576 sesiones: imposible. El retroceso se midió con celdas de 10 s y es ruidoso en la apertura (mediana 1.4 del avance), por eso 1.0. Resultado: ~135 operaciones esperadas en 576 sesiones. Es una definición más laxa que la de Dalton; se declara.

## Alternativas
Ventana de 240/360 s, delta 1/2/4/5 %, avance 30/50 ticks, retroceso 0.6/0.8/1.2/1.4 corren como sensibilidades dentro del mismo estudio (16 intentos).

## Límites
Una señal por día, a las 09:35: el RAND se sortea entre 09:34 y 09:38, justo después de la apertura, y la apertura es la parte más ruidosa y cara del día. El motor 1.1 cobra deslizamiento. Exploratoria, mismos datos de diseño: no es validación independiente.
