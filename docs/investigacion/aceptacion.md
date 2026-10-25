# Aceptación vs rechazo en el área de valor (VAH / VAL)

_Investigado por el laboratorio el 25/10/2026, a pedido de Oscar. Nadie le preguntó cómo definirla._

## Qué encontré (fuentes)
- **Regla del 80%** (Steidlmayer, CME/CBOT, años 80; recogida por Dalton en *Mind Over Markets*, 1990): si el precio abre fuera del área de valor de ayer, vuelve adentro y se queda **dos períodos seguidos de 30 min**, hay alta probabilidad de que cruce hasta el otro extremo del valor. El "80%" es una regla práctica, no una estadística auditada. Falla más en días de tendencia y con noticias. [LuxAlgo](https://www.luxalgo.com/library/concept/80-percent-rule/), [NexusFi](https://nexusfi.com/a/concepts/80-percent-rule), [MetroTrade](https://www.metrotrade.com/what-is-the-80-rule-in-futures-trading/), [MarketCalls](https://www.marketcalls.in/market-profile/market-profile-how-to-play-80-percentage-rule.html).
- **Aceptación = tiempo + volumen** en el nivel nuevo; sin ninguno de los dos es rechazo (subasta fallida, exceso). Nadie fija cuánto tiempo ni cuánto volumen: "es del que prueba". [Bookmap](https://bookmap.com/blog/inside-the-auction-what-it-means-when-the-market-rejects-a-price), [NexusFi · failed auction](https://nexusfi.com/a/concepts/failed-auction), [Tradezella](https://www.tradezella.com/strategies/auction-market-theory-strategy).
- **Rechazo** se lee en order flow como absorción: el precio choca con un bloque de órdenes y no avanza; el stop va justo más allá. Cuidado: un pico por stops que revierte parece subasta fallida pero puede ser un vacío de liquidez.

## Escenarios
1. **Ruptura aceptada** (VAH arriba o VAL abajo): el precio sale del valor y se queda fuera → continuación. *(esto se prueba ahora: ACC v1)*
2. **Re-entrada aceptada** (regla del 80%): abre fuera, vuelve y se queda dentro → rotación al otro extremo/POC. *(pendiente: VAR v1; necesita días que abren fuera)*
3. **Rechazo / subasta fallida**: sale y vuelve rápido → reversión al valor. Ya hay rechazo medido en el mapa (VA, HVN) y no ganó.
4. **Hueco de apertura fuera del valor**: caso aparte, se excluye de ACC v1.

## Definición operable fijada (antes de ver resultados)
Tiempo de las dos medias horas de Dalton (60 min) es demasiado largo para scalping y para una ventana de entradas de 2 h. Se traduce a ventana corta, con flujo agresivo en lugar de "volumen del perfil":
- **Salida**: primer llenado más allá del VAH (o bajo el VAL) del perfil NY de ayer, viniendo de adentro.
- **Aceptación en tiempo**: ningún llenado vuelve más de 2 ticks hacia adentro durante `hold_s` = 180 s seguidos. Si vuelve, se reinicia con la siguiente salida.
- **Aceptación en flujo**: delta agresivo neto de esa ventana ≥ `delta_pct` = 5% del volumen, en la dirección de la salida.
- No persigue si ya se alejó más de 100 ticks (25 puntos). Un disparo por nivel y por día.
- Entrada a mercado a favor, stop 4 ticks adentro del nivel (12–32), sin objetivo, salida a 20 min.

## Definiciones que se comparan dentro del MISMO estudio (`aceptacion_v1`)
Cada una cuenta como intento: tiempo exigido 90 / 270 / 360 s (base 180; 0 s queda fuera), delta mínimo 2 / 8 / 11 % (base 5), stop 2 / 6 / 8 ticks adentro, salida a 10 / 15 / 25 / 30 min. Total 1 + 16 = 17 intentos declarados. La definición base se fijó antes de correr; no se elige la mejor después.
Lo único que se miró antes de fijarla: cuántas señales produce (número de eventos, no ganancias). Con la primera versión (hold 300 s, delta 10%, perseguir ≤ 24 ticks) había 0 señales; se corrigió el diseño por eso, sin mirar ganancias.

## Pendiente
- VAR v1 (regla del 80%) como siguiente prueba.
- Aceptación en HVN: va dentro de E-HVN-FUERZA (estudio de medición, el orquestador hoy solo corre estrategias).
