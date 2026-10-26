# Traders atrapados (ATR v1) · G6

Investigado el 26/10/2026 (G6-ATRAPADOS, pedido de Jose).

## Qué encontré
- Definición de los traders de footprint: un atrapado entró agresivo de un lado (compró en el ask en un máximo) y el precio se fue en su contra; queda en pérdida y su salida (stop o cierre a mercado) empuja el precio en la misma dirección. Fuentes: https://ninjatrader.com/futures/blogs/footprint-charts-guide/ · https://it.tradingview.com/script/AhH1CM72-Bookmap-Traps/ · https://ninjatrader.com/Futures/Blogs/ninjatrader-order-flow
- No hay una definición estadística estándar ni estudio académico. Todas las fuentes son heurísticas de plataformas.
- Idea clave: se mide DESDE EL LADO DEL PERDEDOR. Cuánto volumen agresivo quedó con precio peor que el actual. ABU entra por la distancia al extremo (4 ticks); ATR entra por la fracción de agresores en pérdida.
- Lecciones previas: reversar sin nivel pierde (DVG, FAF); la absorción en niveles de ayer/noche/valor en días que abren dentro del valor sí tiene ventaja (P030/P031; el placebo P045 confirmó que el nivel importa). Por eso el contexto de ABU se mantiene.

## Definición (una sola, fijada antes de correr)
- Ráfaga: la de ABU v2 (flujo agresivo de 60 s ≥ umbral relativo p90/p95, avance ≤ 2 ticks, a ≤ 4 ticks de un nivel de ayer, de la noche o del valor en desarrollo; días que abren dentro del valor de ayer).
- Volumen atrapado = volumen agresivo de la ráfaga (a nivel de operación) ejecutado a un precio peor que el precio actual. Fracción atrapada = atrapado / volumen agresivo de la ráfaga.
- Señal: en los 180 s siguientes, la fracción atrapada llega a ≥ 0.70, el delta de los últimos 30 s es contrario a los atrapados y el precio no superó el extremo en más de 4 ticks (si lo supera, ganaron: no hay señal).
- Entrada a mercado contra los atrapados; stop 4 ticks más allá del extremo (12–32); objetivo 2R; salida a 15 min; 2 contratos; 09:30–15:30; alto tras 2 pérdidas; sin noticias.
- Distinta de ABU (entra a 4 ticks del extremo con delta de 60 s, sin medir volumen en pérdida) y de ABF (opera cuando falla la absorción).

## Sensibilidad (16 intentos)
Fracción atrapada 0.50/0.60/0.80/0.90, ventana de espera 120/150/210/240 s, delta de 30 s 10/20/40/50 s (ventana), tolerancia de extensión 2/3/5/6 ticks.

## Riesgos
Comparte señales con ABU (misma ráfaga): no es independiente. Exploratoria, mismos datos de diseño. Si la fracción 0.70 se cumple casi siempre al mismo tiempo que el alejamiento de ABU, ATR será casi ABU con otra entrada; se espera resultado parecido a ABU v2, no una mejora.
