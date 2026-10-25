# LVN: travesía de un vacío de volumen con flujo iniciador

## Por qué esta prueba
- Casi todo lo probado es rechazo o absorción en un nivel (BIG, HVN, HVF, ABS, ABI, ABV, ABK) o aceptación fuera del valor (ACC, VAR). Solo la familia de absorción dio algo, y ya está agotada: ABS gastó sus 3 versiones, ABV, HVF y ABK no repitieron.
- Los vacíos de volumen (LVN) no se han probado. Es la otra mitad del perfil: donde ayer casi no se operó.
- El motor no soporta Asia/Londres (rand.py carga solo la ventana de Nueva York y no se puede tocar), así que esta prueba va en NY 09:30–11:30.

## Qué dice la literatura (búsqueda del 25/10/2026)
- Un LVN es una zona delgada del perfil: poco interés, el precio la cruzó rápido y suele cruzarla rápido otra vez (Tradezella "low volume node", capital.com, Schwab).
- Teoría de subasta (Dalton, Steidlmayer): en un LVN no hubo aceptación; si el mercado entra con actividad iniciadora, se mueve hasta el siguiente nodo con volumen. Las fuentes web son de traders, sin pruebas estadísticas: es una hipótesis, no un hecho.
- Otra variante (esperar el retorno al LVN y buscar confirmación) no se prueba aquí.

## Definiciones operables (fijadas antes de ver resultados)
- Perfil: volumen por precio de la sesión NY del día anterior, en cubos de 8 ticks (2 puntos).
- Se ignoran 16 ticks en cada punta del rango (las colas siempre son finas).
- Cubo fino: volumen ≤ percentil 20 de los cubos del rango. Vacío = racha de cubos finos de al menos 16 ticks (4 puntos).
- Iniciativa: delta agresivo de los últimos 60 s en la dirección del cruce, ≥ 10 % del volumen de esos 60 s.
- Cruce: la celda de 10 s anterior terminó fuera del vacío y la actual entra ≥ 2 ticks adentro. Cada vacío se decide solo en su primer cruce.
- Entrada a mercado en la dirección del cruce. Objetivo: borde lejano del vacío (entre 12 y 40 ticks; si hay menos de 12, no se opera). Stop: 4 ticks detrás del borde de entrada (entre 8 y 24). Salida por tiempo a 15 min.
- Solo se contaron señales antes de fijar la regla: ~370 en 576 sesiones, ~4.8 vacíos por día. No se miró ninguna ganancia.

## Alternativas razonables que no se eligieron
- Percentil del vacío p10 o p30: no está en la sensibilidad (se fijó p20 de antemano); sería otra versión.
- Vacíos del perfil en desarrollo del propio día (futura prueba).
