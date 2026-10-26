# ABM v1: absorción en el valor de varios días (perfil compuesto)

_Corrida del investigador, 26/10/2026. Nadie le preguntó a Oscar cómo definirlo._

## Por qué esta prueba
- P039 (ABU v3, parada tras 2 pérdidas): +$11,107, p 0.002, positiva, pero Topstep **39.1%** (P031: 41.2%). El riesgo diario no era el cuello. ABU gastó sus 3 versiones.
- ABU solo mira niveles de **ayer**, de la noche y del día en desarrollo. Nunca se probó un nivel de **varios días**. Es el único hueco que queda en la familia con ventaja, y apunta al problema real: pocas operaciones (≈170 en 576 sesiones).
- Overnight/Londres sigue sin poder probarse (rand.py solo sortea en NY y no se toca).

## Qué dice la literatura (búsqueda del 26/10/2026)
- Dalton (Mind Over Markets) y ATAS: un mercado en balance muestra áreas de valor de varios días que se superponen; las tendencias nacen de un balance. En balance los bordes se rotan: compradores cerca del borde inferior, vendedores cerca del superior (resumen de ATAS y Bookmap). Dalton tiene un capítulo de "días compuestos" y perfiles de largo plazo.
- POC "desnudo": POC de una sesión anterior que el precio no ha vuelto a cruzar; LuxAlgo y NinjaTrader dicen que actúa como imán o soporte/resistencia. Son fuentes de vendedores: **no hay pruebas estadísticas**; se trata como hipótesis.
- Fuentes: atas.net (blog "Analyzing TPO"), bookmap.com ("Understanding market profile"), luxalgo.com/library/concept/naked-poc, ninjatrader.com (Order Flow Volume Profile).

## Definición fijada (antes de ver ninguna ganancia)
- Detector, umbral relativo, confirmación a 60 s, entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, ventana 09:30–15:30, 2 contratos, parada tras 2 pérdidas: **idénticos a ABU v3** (misma lógica que v17.py).
- Perfil compuesto = suma del volumen por precio de los **5 días válidos anteriores** (NY). Niveles: POC, VAH, VAL (70%, igual que features.value_area), máximo y mínimo del compuesto, y los POC desnudos de esos 5 días (ningún día posterior, hasta ayer, cruzó ese precio).
- Día válido: la apertura de las 09:30 cae dentro de [VAL, VAH] **compuesto** (balance de varios días).
- Para no repetir ABU: se descartan los niveles a ≤ 8 ticks de cualquier nivel de ayer o de la noche. Cada nivel dispara una vez por día.
- 5 días: una semana de trading, la unidad natural de un perfil compuesto semanal. Otros largos (1, 3, 7, 9) van en la sensibilidad.

## Qué NO es esta prueba
- No es validación independiente: mismos datos de diseño, mismo detector que ABU. Es una pregunta sobre **niveles nuevos**.
- Humo (120 sesiones, solo conteo de señales): 21 señales; se esperan ≈100 en 576 sesiones, justo en el mínimo. Riesgo real de "insuficiente". No se ajustó nada para evitarlo.
- El DSR sigue penalizado (más de 1,000 intentos): el criterio (b) no cambia.

## Intentos (estudio abm_v1)
1 base + 16 de sensibilidad: cercanía al nivel, confirmación, umbral relativo y días del compuesto (1, 3, 7, 9). 17 en total. La base queda fijada.

## Cómo se lee
- Ganancia > 0, p ≤ 0.05, positiva 3 años y ≥ 100 operaciones → los niveles multi-día aportan frecuencia; se mira si junto con ABU mejora Topstep (carteras distintas).
- Si no → la ventaja de la absorción se agota en los niveles de ayer; NY queda sin ideas de absorción.
