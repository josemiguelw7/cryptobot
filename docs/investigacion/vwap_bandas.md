# Reversión a la VWAP desde las bandas de desviación (VBR v1)

_Investigado por el laboratorio el 25/10/2026. Nadie le preguntó cómo definirla._

## Qué encontré (fuentes)
- Las bandas de VWAP ± σ (desviación estándar ponderada por volumen) son una convención de los traders: 1σ = rango normal, 2σ = zona de agotamiento donde el precio suele volver a la VWAP, 3σ = casi siempre noticias. [TradingView · bandas de desviación](https://it.tradingview.com/scripts/deviationbands/), [LuxAlgo · VWAP Z-Score & Exhaustion Matrix](https://www.luxalgo.com/library/indicator/fis8Fb3K-vwap-z-score-exhaustion-matrix/), [Tradezella · VWAP](https://www.tradezella.com/blog/vwap-trading-strategy).
- La señal de "fade" combina extremo de z-score + volumen que se agota + delta que cambia a favor del rebote. Esos indicadores estiman el delta con velas; aquí usamos el delta agresivo real de la cinta.
- Advertencias: "1σ = 68%" solo vale si los precios fueran normales (no lo son); en tendencia fuerte la reversión falla. Nadie publica una prueba auditada: son reglas prácticas.
- Teoría de subasta (Dalton): en días de balance (abre dentro del valor de ayer) el mercado rota alrededor del valor; en tendencia, no.

## Por qué ahora
El laboratorio ya vio que absorción y aceptación solo ganan en días que abren dentro del valor (P012, P016, P017, P027; exploratorio). Pero esas pruebas dan ~100 operaciones y por eso Topstep da 0–40%. La VWAP con bandas existe todo el día: da más señales con una idea distinta (reversión al valor intradía, no rebote en un nivel de ayer).

## Definición operable fijada (antes de ver resultados)
- Solo días que abren dentro del valor de ayer (dato de las 09:30).
- VWAP y σ ponderadas por volumen acumuladas desde las 09:30 con datos ya ocurridos; σ con piso de 10 ticks. Entradas desde las 10:00 (30 min de cinta) hasta las 15:30.
- Extensión: el precio toca VWAP ± 2σ en los últimos 60 s.
- Agotamiento (flujo agresivo): en los 60 s siguientes el delta agresivo de la ventana cambia de signo y el precio se aleja 4 ticks del extremo.
- Entrada a mercado hacia la VWAP. Stop 4 ticks más allá del extremo (12–32). Objetivo = distancia a la VWAP al entrar (16–80 ticks). Salida por tiempo a 20 min. Un disparo por lado cada 5 min.
- Sin noticias fuertes; 6 operaciones por día máximo, regla común.

## Comparación dentro del MISMO estudio (`vbr_v1`)
Cada una cuenta como intento: k = 1.5 / 1.75 / 2.25 / 2.5 σ (base 2), alejamiento 2 / 3 / 5 / 6 ticks (base 4), salida 10 / 15 / 25 / 30 min (base 20), piso de σ 6 / 8 / 12 / 14 ticks (base 10). Total 1 + 16 = 17.
Lo único que se miró antes de fijar: que el código corre y produce señales (73 operaciones en 60 sesiones, P&L apenas negativo, sin cambiar ningún parámetro después de verlo).

## Escenarios
1. Día de balance: reversión a la VWAP (esto se prueba).
2. Día de tendencia: el precio se pega a la banda y rompe el stop. El filtro de apertura es solo una aproximación (el laboratorio ya midió que el régimen no se anticipa bien a las 09:45).
3. Pendiente para otra versión: espejo en tendencia (continuación desde la VWAP) y bandas en Asia/Londres (el motor aún no carga esas ventanas).
