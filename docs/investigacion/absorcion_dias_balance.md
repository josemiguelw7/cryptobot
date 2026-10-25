# ABD v1: absorción en los niveles de ayer, solo en días que abren dentro del valor

## Por qué esta prueba
- Las pruebas de absorción con niveles de ayer ganan SOLO en días que abren dentro del valor de ayer: ABS v1 (P014) +$4,314 dentro y +$6 fuera; ABS v2 (P012) +$7,479 dentro y +$395 fuera. ACC v1/v2 muestran lo mismo (ver aceptacion_v2.md).
- Esa observación sale de los datos de diseño: es exploratoria y el DSR la penaliza. No se presenta como validación.
- Problema de potencia: con el umbral de ABS v1 solo hay ~44 señales en días dentro del valor (insuficiente). Se amplía la ventana a la tarde (ABI v2 mostró que la tarde da ~0 señales con el p95 de 20 sesiones).

## Qué dice la literatura (búsqueda del 25/10/2026)
- Market Profile (Dalton): abrir dentro del rango y del valor de ayer = sentimiento sin cambio, mercado en balance, sesión de rotación (marketcalls.in, "Market Profile open type"; notas de Dalton, Mind Over Markets). Abrir fuera = intento direccional.
- En balance, los extremos del valor se rechazan: es la lógica de absorción en el borde (compradores/vendedores pasivos). La "regla del 80 %" es folklore sin estadística verificada (NexusFi, LuxAlgo): ya se probó como VAR v1 (P019, no pasa).
- Fuentes de traders: dan una hipótesis, no un hecho.

## Definición (fijada antes de ver ninguna ganancia)
- Filtro: el primer precio de las 09:30 cae entre VAL y VAH de ayer (idéntico a ACC v2).
- Detector, niveles de ayer y de la noche, confirmación a 60 s, stop 12–32, objetivo 2R, salida a 15 min: idénticos a ABS v1.
- Ventana de entradas 09:30–15:30, cierre forzado 15:45.
- Umbral de volumen agresivo de 60 s: el MENOR entre el p95 de 20 sesiones (ABS v1) y el p90 de los 60 min anteriores de la propia cinta; piso 0.5 × el p95 de 20 sesiones. Con menos de 10 min de cinta solo se usa el de 20 sesiones.
- Solo se contaron señales, nunca ganancias: p95 relativo 70 señales, p90 115, p85 137. Se eligió p90 por ser el primero que supera 100. Con p90 la sensibilidad cubre 86–94.

## Alternativas razonables (no se prueban; serían otra versión)
- Sin filtro de apertura; solo mañana; umbral por lado; salida sin objetivo (ABS v2).

## Riesgos
- ~115 señales, justo sobre el mínimo de 100. Ganancia concentrada en pocos días como toda la familia.
- Filtro elegido mirando los mismos datos de diseño: exploratorio.
