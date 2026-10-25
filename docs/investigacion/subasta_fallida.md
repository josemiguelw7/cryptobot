# FAF v1: subasta fallida en los extremos de ayer y de la noche

## Por qué esta prueba
- DVG (P034) perdió −$57k: el agotamiento de delta sin nivel no sirve. ABQ (P033) tampoco. Solo la absorción en niveles (ABU) tiene ventaja, pero opera ~0.3 veces al día.
- Pregunta nueva: ¿la salida **fallida** de un nivel clave (intento de iniciativa que no se sostiene) aleja el precio? No se había probado el intento de ruptura que revierte; ACC/VAR miden aceptación y re-entrada con apertura fuera.

## Qué encontré (búsqueda 25/10/2026)
- Market Profile: "exceso" = rechazo decisivo en un extremo; "subasta fallida" = exceso más débil: se rompe un extremo y el precio vuelve hacia el otro lado (marketcalls.in/market-profile/market-profile-failed-auction.html, ...-excess-end-of-auction.html; NexusFi: nexusfi.com/a/concepts/failed-auction). El término viene de Ray Barros, no del Market Profile clásico.
- Advertencia: se atribuye a Dalton que la regla del 80% y la subasta fallida "no funcionan realmente" (fuente de segunda mano). Una espiga de barrido de stops puede parecer subasta fallida y ser solo un vacío de liquidez. Por eso exijo flujo agresivo en la salida y delta contrario en el regreso.
- No hay definición estadística estándar; la fijo yo abajo.

## Definición (una sola, fijada antes de correr)
- Niveles superiores: VAH de ayer, máximo de ayer, máximo de la noche. Inferiores: VAL, mínimo de ayer, mínimo de la noche. Un intento por nivel y día.
- Salida: una celda de 10 s cruza el nivel ≥ 2 ticks, con flujo agresivo del lado de la salida en los últimos 60 s ≥ 0.5 × p95 de las 20 sesiones previas (iniciativa real, no un roce).
- Fallo: en los 120 s siguientes el precio vuelve al nivel (cierre de celda en o dentro del nivel) y el delta de los últimos 30 s es contrario a la salida. Si vuelve sin delta contrario, o no vuelve, el nivel se da por gastado.
- Entrada a mercado contra la salida; stop 4 ticks más allá del extremo de la excursión (12–32); objetivo 2R; salida a 15 min; 1 contrato; 09:30–15:30; sin noticias; reglas comunes (máx. 6 operaciones por día, alto tras 3 pérdidas).
- Todos los días, no solo los que abren dentro del valor. Lo decidí por conteo de señales: con el filtro de apertura, ~0.12 señales al día (insuficiente, <100 operaciones); sin filtro, ~0.5 al día. Nunca miré ganancias.
- Alternativas no corridas como definición propia: "cierre de 1 minuto fuera" y niveles del día en desarrollo (se solapan con DVG/ABU).

## Sensibilidad (16 intentos)
Penetración 0/1/3/4 ticks, ventana de fallo 60/90/150/180 s, stop máximo 24/28/36/40 ticks, objetivo 1/1.5/2.5/3 R.

## Humo (solo señales)
40 días de 2024: ~19 señales (21–22 sin el filtro de ráfaga: el filtro casi no recorta). Los stops casi siempre llegan al máximo de 32 ticks: la excursión previa al fallo es grande; riesgo por operación alto.

## Riesgos
- Exploratoria; no es validación independiente.
- Stops grandes (~$160) con 1 contrato: Topstep lento y MLL sensible.
- Barridos de stops pueden continuar tras el regreso al nivel.
