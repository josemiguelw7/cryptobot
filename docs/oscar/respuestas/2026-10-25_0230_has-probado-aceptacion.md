---
nota: 2026-10-25_0230_has-probado-aceptacion.md
autor_nota: Oscar
accion: en_cola
fecha: 2026-10-25T03:00:12Z
asunto: Aceptación vs rechazo en HVN/VAL/VAH: no está probado aún
---

Tienes razón en lo esencial: no hemos probado aceptación. Lo que hay hoy en el laboratorio:

- HVN v1 (P006, repetida en P011) solo opera rechazo/rebote del nodo del día anterior. Resultado: −$87,676 con motor 1.1 y p vs azar 0.999 (P011). No pasa.
- El mapa de señales tiene "Rechazo del área de valor" (246 eventos; −1.27 ticks a 15 min y −13.05 a 30 min, 'distinta del azar · a favor'). Es rechazo, no aceptación.
- Zonas HVN en el mapa: −11.8 ticks a 15 min y −4.52 a 30 min. El rebote que esperaba la v1 no apareció, pero eso no dice nada sobre la aceptación.

Lo que NO está medido: aceptación (el precio entra al área de valor o a un HVN y se queda, por ejemplo con cierres o tiempo dentro, y luego continúa hacia el otro extremo del valor), operar VAL/VAH como niveles propios (entrada, continuación o rotación hacia el POC), ni el "80% rule". Tampoco hay un estudio que compare aceptación contra rechazo en el mismo nivel. Eso no está medido todavía.

Cómo se haría con el método del lab: un estudio registrado antes de correr, con definición de "aceptación" congelada con huella y sello (por ejemplo, N minutos o N cierres de 5 min dentro del valor o más allá del nivel, sin mirar datos antes). Se mediría a 5, 15 y 30 min contra niveles al azar y contra el azar de dirección aleatoria, con precios operables y contando todos los intentos. Si algo sale, recién entonces iría a una estrategia con reglas selladas.

Hay un punto de contacto con E-HVN-FUERZA (aprobado): ahí ya se mide la reacción en el primer toque. Se puede ampliar para separar rechazo de aceptación, pero VAL/VAH necesitan estudio propio.

Para fijar la definición necesito de ti: ¿cuánto tiempo o cuántos cierres cuentan como "aceptación" para ti? ¿Y qué operas exactamente: entrada en el retesteo del nivel o en la ruptura?

Queda en la cola; el investigador autónomo lo toma primero y el resultado te llega por correo. La decisión de aprobarlo para estrategia es tuya en el comité.
