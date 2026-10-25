# ABI v1 · absorción en los niveles del propio día

_Investigado por el laboratorio el 25/10/2026. Nadie le preguntó nada a Oscar._

## Por qué
- La absorción es la única familia con ganancia neta positiva y p bajo contra RAND (ABS v2, P012: +$7,874, p 0.005). Pero ABS usa solo niveles del día anterior, tiene ~128 operaciones y no llega a Topstep (41%).
- Los niveles de ayer (VAH, VAL, extremos) ya fueron probados con rechazo (HVN, POC), aceptación (ACC v1, v2) y re-entrada (VAR): sin éxito. ABS ya gastó sus 3 versiones.
- Idea nueva: la misma señal de flujo, pero en los niveles que el propio día construye (máximo y mínimo de la sesión, VWAP, POC/VAH/VAL del perfil en desarrollo). Más niveles y más cerca del precio = más operaciones.

## Fuentes
- Definición de práctica (footprint): absorción = mucho volumen agresivo en un nivel con poco avance del precio; se usa en niveles clave (VWAP, POC, extremos), no sola. Resumen de blogs de order flow: https://www.mql5.com/en/blogs/post/775807 y https://www.mql5.com/en/blogs/post/775818 . No encontré una definición estándar de "absorción en POC/VAH/VAL en desarrollo": la fijamos nosotros.
- Teoría: Dalton / Steidlmayer (Market Profile): el valor en desarrollo del día (POC, 70% del volumen) y el VWAP son los puntos de equilibrio de la subasta del día.

## Definición fijada (idéntica a ABS v1 salvo los niveles)
- Detector: ≥ p95 de volumen agresivo de un lado en 60 s, el precio no avanza más de 2 ticks, extremo a ≤ 4 ticks de un nivel. Confirmación en 60 s (delta cambia de signo y precio se aleja 4 ticks). Entrada a mercado contra el lado absorbido. Stop 4 ticks más allá del extremo (12–32). Sin objetivo. Salida a 15 min.
- Niveles (solo con datos anteriores a la ventana): máximo de la sesión y VAH en desarrollo solo con compra absorbida; mínimo y VAL en desarrollo solo con venta absorbida; VWAP y POC en desarrollo con cualquiera. VAH/VAL = 70% del volumen acumulado.
- No antes de 10 min desde la apertura; un disparo por nivel cada 10 min.
- Elegí "confirmación + salida por tiempo" porque ya hay resultados de diseño (P012 vs P016) que prefieren ABS v1/v2 sobre la entrada temprana. Es una decisión tomada con datos del periodo de diseño: se declara y el DSR la penaliza.

## Lo único que se miró antes de fijar
Solo el conteo de señales, nunca ganancias: con máximo/mínimo/VWAP sólo salieron 48 señales (insuficiente); agregando POC/VAH/VAL en desarrollo, 126 señales en 106 días (day_high 7, day_low 12, vwap 29, dev_poc 58, dev_vah 13, dev_val 7).

## Riesgos
- Cerca del mínimo de 100 operaciones.
- VWAP y POC en desarrollo suelen estar juntos: las señales no son independientes.
- Placebo desplazado probablemente salte (como en ABS): iría a "revisar".
- Se mezcla con las señales de ABS cuando el nivel de ayer coincide con el del día.

## Comparación en el MISMO estudio (`abi_v1`)
Base + 16 vecinos: cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, stop mínimo 4/8/16/20, salida 5/10/20/25 min. 17 intentos declarados.
