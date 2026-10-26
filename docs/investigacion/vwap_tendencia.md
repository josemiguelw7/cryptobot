# VPT v1: pullback a la VWAP a favor de la tendencia

_Corrida del investigador, 26/10/2026. Nadie le preguntó a Oscar cómo definirla._

## Por qué esta prueba
- P041 (ABB v1) no pasa (−$9.0k, p 0.87). La absorción solo tiene ventaja en días que abren dentro del valor de ayer (ABU). Ya van 26 pruebas de la familia.
- Los días que abren fuera del valor (ABT, ACC, VAR, ABB) nunca se probaron con la VWAP como soporte dinámico. Es el complemento natural de ABU: ABU = balance, VPT = tendencia.
- Overnight/Londres sigue sin poder probarse (`rand.py` solo sortea en Nueva York y no se toca).

## Qué dice la literatura (fuentes secundarias; no pude abrir *Markets in Profile*)
- Abrir dentro del valor de ayer sugiere rotación (balance); abrir fuera y empujar en una dirección sugiere tendencia (LuxAlgo, "Open Types" y "VWAP Mean-reversion vs Trend Regimes").
- En días de tendencia, la VWAP se trata como soporte/resistencia dinámica y se compran los pullbacks donde los compradores absorben (TradeZella, "buyer led directional auction").
- Advertencia común: clasificar mal el día es la forma principal de perder. Por eso el día se invalida en cuanto el precio regresa al valor de ayer (regla del 80 %: eso es rotación, no tendencia).
- Estas fuentes son de divulgación, no revisadas por pares: son hipótesis, no evidencia.

## Definición fijada (antes de correr)
- Día elegible: el primer precio de las 09:30 cae fuera de [VAL, VAH] de ayer. Tendencia = lado de la apertura. El día deja de ser elegible para siempre si el precio toca el borde de ayer (solo pasado).
- Extensión: el precio ya estuvo ≥ 24 ticks (6 puntos) lejos de la VWAP del día (VWAP acumulada desde 09:30).
- Pullback: en 60 s el extremo contrario llega a ≤ 4 ticks de la VWAP.
- Confirmación (60 s siguientes): delta agresivo de la ventana de 60 s a favor de la tendencia ≥ 5 % del volumen y el precio se aleja 4 ticks del extremo del pullback.
- Entrada a mercado a favor. Stop 4 ticks más allá del extremo (entre 12 y 32). Objetivo 2R. Salida a 15 min. 2 contratos, parada tras 2 pérdidas, enfriamiento 10 min, entradas 10:00–15:30, cierre 15:45. Noticias excluidas.
- Los números (24, 4, 5 %, 4) salen de las escalas de VBR y ABU, no de resultados. Solo conté señales en humo (115 sesiones: 229 operaciones, ~1,100 esperadas); no miré ganancias.

## Intentos (MISMO estudio `vpt_v1`)
1 base + 16 sensibilidades: toque 2/3/5/6, extensión 16/20/28/32, delta 3/4/6/7 %, alejamiento 2/3/5/6. La base queda fijada; no se elige la mejor.

## Cómo se lee
- Gana si p vs RAND y RAND2 ≤ 0.05, neto > 0, positiva los 3 años. Con más de 1,000 intentos el DSR seguirá en 0: el criterio (b) depende del examen sellado.
- No es validación independiente: mismos datos de diseño.
- Si no pasa: la tendencia con VWAP queda descartada y NY sin ideas de flujo fuera de ABU.
