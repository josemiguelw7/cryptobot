# ABW v1: absorción en días de apertura ancha

_Corrida del investigador, 26/10/2026. Nadie le preguntó a Oscar cómo definirla._

## Por qué esta prueba
- P042 (VPT v1) no pasa: −$45.8k, p 0.98. Su espejo no tiene base: ganó 30 % de objetivos con 2R, es decir casi azar menos costos y saltos de stop.
- La única familia con ventaja es ABU (P030, P031, P039: p ≤ 0.002, positiva 3 años). Pero su filtro de día ("abre dentro del valor de ayer") casi no separa balance de tendencia (`futures/regime_proxy.json`: 45.6 % vs 49.3 %).
- Idea: clasificar el día con lo que ya pasó en la apertura, no con el precio de las 09:30.

## Qué dice la literatura (fuentes secundarias; no pude abrir *Mind Over Markets* de Dalton)
- Balance inicial (IB) ancho: el mercado ya hizo su movimiento, tiende a rotar y los bordes del IB funcionan como paredes. IB estrecho: suele preceder días de tendencia. Son tendencias, no reglas. (LuxAlgo, "Initial Balance"; NexusFi.)
- Fade de extremos paga en días normales/rotacionales y falla en tendencia.
- Umbrales: unos usan <30 % / >60 % de un rango de referencia, otros percentiles 20/80 de una distribución móvil. Ninguno es canónico.

## Definición fijada (antes de correr)
- Apertura = primeros 30 min (09:30–10:00). Rango de apertura / rango de ayer (máx−mín NY) ≥ 0.5 → día "ancho". 0.5 = la mitad del rango de ayer, número redondo; solo se miró la distribución de la razón, nunca ganancias.
- Detector, niveles, confirmación 60 s, umbral relativo, stop 12–32, objetivo 2R, 15 min, 2 contratos, parada tras 2 pérdidas: idénticos a ABU v3. Cambios: sin filtro de apertura dentro del valor; la ventana de absorción empieza después de las 10:00; se agregan máximo y mínimo de apertura como niveles.
- Estrategia nueva (ABW) porque ABU ya gastó sus 3 versiones: cambia el criterio de día y los niveles.

## Intentos (MISMO estudio `abw_v1`)
1 base + 16 sensibilidades: cercanía al nivel 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94, razón de apertura 0.3/0.4/0.6/0.7.

## Humo
112 sesiones (1 de cada 5): 50 señales, 29 días con señal; ~257 esperadas en 576. Solo conteo.

## Cómo se lee
Gana si p vs RAND y RAND2 ≤ 0.05, neto > 0, positiva los 3 años. Con >1,000 intentos el DSR seguirá en 0. Exploratoria, mismos datos de diseño: no es validación independiente. Si pierde, el filtro de día no era la clave y la familia de absorción queda sin más variantes de contexto.
