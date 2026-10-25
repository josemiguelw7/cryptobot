# ABV v1 · absorción en el valor en desarrollo (POC / VAH / VAL del día)

_Investigado por el laboratorio el 25/10/2026. Nadie le preguntó nada a Oscar._

## Qué pasó antes (resultados que motivan la idea)
- P021 (ABI v1): +$7,261, p 0.045 contra RAND, 120 operaciones. Pero: 206% de la ganancia en 5 días, pierde en 2024 y 2026, Topstep 23%, placebo desplazado sospechoso (revisar).
- Por nivel en P021 (periodo de diseño): POC/VAH/VAL en desarrollo +$9.4 mil en 72 operaciones; máximo/mínimo de la sesión y VWAP −$2.2 mil en 48.
- La forma de la ganancia: 88% de las operaciones salen por stop; la ganancia viene de pocos días de tendencia fuerte (hasta 900 ticks a favor). Es una estrategia "de lotería convexa". Esto es honesto decirlo: ABS y ABI comparten esa forma.

## Por qué los bordes del valor del propio día (teoría)
- Market Profile (Steidlmayer, Dalton): el área de valor del día en desarrollo (70% del volumen) es donde la subasta encuentra aceptación; POC es el precio más aceptado. Un borde del valor es donde el mercado decide si "rechaza" (vuelve al valor) o "acepta" (sale). La absorción de flujo agresivo ahí (mucho volumen, nada de avance) es la huella de un rechazo con participación.
- Order flow/footprint: absorción = volumen agresivo grande con poco avance, sobre todo en niveles clave (VWAP, POC, extremos). Fuentes (ya citadas en absorcion_intradia.md): https://www.mql5.com/en/blogs/post/775807 y https://www.mql5.com/en/blogs/post/775818. No hay una definición estándar de absorción en el valor en desarrollo; fijamos la nuestra.
- Por qué quitar máximo/mínimo y VWAP: extremos del día que se rompen son justo los días de tendencia; VWAP y POC suelen estar pegados (señales repetidas). Es una decisión basada en P021 (exploratoria).

## Definición fijada (antes de correr)
- Igual a ABI v1 salvo: solo POC, VAH y VAL del perfil en desarrollo; cercanía ≤ 8 ticks (antes 4); enfriamiento por nivel 5 min (antes 10); no antes de 10 min.
- Lo único que se miró para fijar la tolerancia y el enfriamiento: el CONTEO de señales (nunca ganancias). Variantes contadas en 576 sesiones: mínimo 20 min = 86 señales; 30 min = 58; cercanía 4 = 50; cercanía 6 = 70; base elegida (10 min, cercanía 8, enfriamiento 5 min) = 132 señales en ~109 días. Hace falta ≥ 100 operaciones para no quedar "insuficiente".

## Comparación en el MISMO estudio (`abv_v1`)
Base + 16 vecinos: cercanía 4/6/10/12 ticks, confirmación 40/50/70/80 s, stop mínimo 4/8/16/20, salida 5/10/20/25 min. 17 intentos declarados.

## Riesgos
- Probable concentración en pocos días (como ABI y ABS) y Topstep bajo.
- La partición por nivel salió de P021: es exploratoria, no validación independiente.
- Placebo desplazado probablemente salta (revisar).
