# Clímax de volumen y delta en el extremo del día (CLX v1) · G5

Investigado el 26/10/2026 (G5-CLIMAX, pedido de Jose).

## Qué encontré
- Wyckoff: el clímax de compra/venta es volumen muy alto con avance amplio en el extremo, seguido de rechazo; marca el final de un empuje. Dalton: "exceso" = rechazo decisivo en un extremo; subasta terminada vs no terminada.
- Herramientas de order flow: el agotamiento se lee como volumen inusual (los indicadores abiertos de TradingView usan 2x la media en intradía) con delta que se agota o se invierte. Ninguna fuente da una definición estadística estándar. Fuentes: https://it.tradingview.com/script/WBhuasLl-Delta-Microstructure-Analysis/ · https://cn.tradingview.com/scripts/climax/ · https://www.mql5.com/en/blogs/post/775818
- Las advertencias de DVG (P034) y FAF (P035) valen: reversar sin confirmación pierde. Por eso se exige que el rechazo ocurra de verdad antes de entrar.

## Definición (una sola, fijada antes de correr)
- Ventana de 60 s que marca nuevo máximo (mínimo) de la sesión, no antes de 30 min desde la apertura (10:00).
- Volumen de la ventana ≥ 3 veces el volumen medio por 60 s de los 30 min previos (solo pasado); delta agresivo ≥ 20 % del volumen a favor del empuje; avance de la ventana ≥ 12 ticks.
- "Terminada": en los 60 s siguientes el precio no supera el extremo, cae 4 ticks bajo él y el delta de los últimos 30 s es contrario. Si hace otro extremo, no hay señal.
- Entrada a mercado en contra; stop 3 ticks más allá del extremo (12–32); objetivo 1.5R; salida a 10 min; 1 contrato; 10:00–15:30; máx. 4 al día; alto tras 2 pérdidas; sin noticias.
- Distinta de DVG (delta acumulado sin volumen), FAF/ABF (niveles de ayer) y PEX (extremo pobre del perfil).

## Sensibilidad (16 intentos)
Múltiplo de volumen 2/2.5/3.5/4, delta 10/15/25/30 %, avance 8/10/14/16 ticks, alejamiento 2/3/5/6 ticks. No se compara la variante "no terminada" (continuación) porque ABF ya midió seguir la ruptura.

## Humo (solo conteo)
40 sesiones espaciadas: 12 señales (~170 esperadas en 576 sesiones). Se comprobó que una señal pasa por el simulador; ninguna ganancia se usó para fijar umbrales.

## Riesgos
Exploratoria, mismos datos de diseño. Pocas operaciones (cerca del mínimo de 100). Stops grandes con 1 contrato. Los reversos sin nivel (DVG, FAF) perdieron con p≈1: se espera no_pasa.
