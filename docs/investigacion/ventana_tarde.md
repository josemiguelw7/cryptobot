# ABI v2: absorción en los niveles del día, en la tarde de Nueva York

## Por qué esta prueba
- Todo lo probado hasta hoy entra entre 09:30 y 11:30. La tarde (11:30–15:30) nunca se midió en el diseño: es la parte de los datos que no hemos mirado.
- ABI v1 (P021, mañana) fue lo mejor de la familia de absorción: +$7,261, p 0.045 contra RAND. Pero DSR 0.0, Topstep 23 %, pierde 2024 y 2026. ABS agotó sus 3 versiones.
- La pregunta es simple: ¿la absorción en los niveles del propio día también existe en la tarde? Las operaciones de la mañana no se repiten, así que las dos pruebas son independientes entre sí dentro del diseño.

## Qué dice la literatura (búsqueda del 25/10/2026)
- El volumen tiene forma de U: fuerte tras la apertura, hueco al mediodía y repunte hacia el cierre (LuxAlgo, "Intraday Time-of-day Effects"; arXiv 2508.06788 sobre E-mini).
- Bookmap (NQ): las compresiones del mediodía se resuelven con rupturas, y la absorción aparece cerca del VWAP antes de continuar. Es descripción de un proveedor, sin prueba estadística.
- Órdenes MOC: el desequilibrio de cierre se publica desde las 15:50 ET (NexusFi, LuxAlgo). Por eso las entradas terminan a las 15:30 y el cierre forzado es a las 15:45.
- Son fuentes de traders: dan una hipótesis, no un hecho.

## Definición (fijada antes de ver ninguna ganancia)
- Detector, niveles, confirmación, stop y salida a 15 min: idénticos a ABI v1 (docs/investigacion/absorcion_intradia.md).
- Ventana: entradas de 11:30 a 15:30 ET; cierre forzado 15:45. Los niveles se calculan desde las 09:30, solo con lo ya ocurrido.
- ÚNICO cambio del detector: el umbral de "volumen agresivo grande en 60 s". El p95 de las 20 sesiones anteriores (todo el día) da 2 señales en 57 sesiones por la tarde, porque la tarde es más tranquila. Con eso la prueba saldría "insuficiente".
- Umbral relativo a la hora: p95 de los volúmenes agresivos de 60 s (compra y venta juntas) terminados en los 60 min anteriores, de la propia cinta del día, con piso de 0.5 × el p95 de las 20 sesiones anteriores.
- Solo se contaron señales (≈35 en 143 sesiones con p95; ≈47 con p90), nunca ganancias. Se eligió p95 por coherencia con la familia; p90 queda dentro de la sensibilidad (91).

## Alternativas razonables
- Umbral por lado en vez de juntas, o ventana de 30 min: no se prueban; serían otra versión.
- Mañana + tarde juntas: no, para no mezclar con P021.
- Absorción con niveles de ayer (ABS) en la tarde: ABS ya gastó sus versiones.

## Riesgos
- Nuevo umbral = una decisión más sin validar; el DSR lo penaliza.
- Cerca de 130 operaciones esperadas, justo sobre el mínimo de 100.
