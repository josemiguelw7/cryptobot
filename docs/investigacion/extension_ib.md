# Extensión del balance inicial (IB) confirmada por delta · IBX v1

Investigado el 26/10/2026 (G4-IB-DELTA, pedido de Jose).

## Qué encontré
- El IB es el rango de la primera hora de la sesión regular (dos periodos TPO de 30 min): 09:30–10:30 en NY. Viene de Steidlmayer (CBOT) y Dalton (Mind Over Markets).
- Idea de la teoría: los operadores del día prueban dentro del IB; salir del IB (extensión de rango) indica participantes de otro horizonte, es decir iniciativa. Un estudio de CBOT de 1988 halló que la primera extensión ocurre sobre todo justo después de la primera hora.
- No encontré estudios estadísticos rigurosos sobre la tasa de éxito de las extensiones; los números de los vendedores de indicadores no están verificados. Por eso se mide aquí con el protocolo completo.
- Fuentes: https://en.wikipedia.org/wiki/Market_profile · https://nexusfi.com/a/market-structure/initial-balance · https://www.luxalgo.com/library/concept/initial-balance/
- Distinta de ORB v1 (rango de 15 min, sin flujo, P008/P009 no pasa) y de OPD v1 (apertura, P044 no pasa): aquí el rango es de 60 min y la ruptura exige delta agresivo.

## Definición operable (una sola, fijada antes de correr)
- IB = máximo y mínimo de 09:30 a 10:30.
- Entre 10:30 y 14:30, una celda de 10 s supera el borde en ≥ 4 ticks, el último precio de la celda sigue fuera del borde y el delta agresivo de los últimos 120 s (sin mirar antes de las 10:30) es ≥ 5 % del volumen a favor de la ruptura.
- Entrada a mercado a favor al cerrar la celda; stop 4 ticks dentro del IB (entre 12 y 32 ticks); objetivo 1.5R; salida por tiempo a 20 min. Una vez por lado y por día (máx. 2), 1 contrato, parada tras 2 pérdidas.

## Alternativas
Ventana de flujo 60/90/150/180 s, delta 1/3/7/9 %, ruptura 2/3/5/6 ticks y objetivo 0.5/1.0/2.0/2.5R corren como sensibilidades dentro del mismo estudio (16 intentos). Los umbrales se fijaron como números redondos sin mirar ganancias; solo se contaron señales (36 en 50 sesiones de humo, unas 400 esperadas).

## Límites
Exploratoria, mismos datos de diseño: no es validación independiente. Sin filtro de régimen. El estudio de reacción en pruebas anteriores (ACC, ORB) sugiere que las rupturas pierden con costos; esta prueba solo agrega el filtro de flujo.
