# ¿Qué hace "poderoso" a un HVN? (E-HVN-FUERZA → HVF v1)

Pedido de Oscar (buzón, 24/10/2026): un indicador de ATAS que muestre HVN poderosos. Investigado por el laboratorio el 25/10/2026.

## Qué encontré
- Market Profile (Steidlmayer/Dalton): un nodo de alto volumen (HVN) es un precio donde el mercado aceptó negociar mucho; es "valor justo" y el precio tiende a frenarse o chapotear ahí. El POC es el HVN más grande; VAH y VAL son los bordes del 70% del volumen.
- Descripciones de traders y de vendedores de indicadores (LuxAlgo, TradingView, NinjaTrader): el HVN puede actuar como soporte o resistencia según el lado de llegada; el primer regreso a un nivel "desnudo" (no revisitado) es el que se vigila; un volume profile solo no dice quién agredió, por eso se combina con footprint/delta para distinguir absorción de participación normal.
- No encontré estudios estadísticos sobre cuánto rebota un HVN. Todo es heurística: hay que medirlo (aquí).
- Fuentes: https://www.luxalgo.com/library/concept/naked-poc/ · https://www.luxalgo.com/library/indicator/CHxGnqBD-volume-profile-with-hvn-lvn-detector/ · https://ninjatrader.com/de/support/helpGuides/nt8/order_flow_volume_profile.htm

## Escenarios y lo que ya sabe el laboratorio
- HVN v1 (rebote ciego en cualquier nodo ≥ p90): perdió con p 0.999 contra RAND. Tocar el nodo no basta.
- Absorción (ABS v2) es la única familia positiva; lo que la hace distinta es que decide por flujo agresivo.
- Definiciones razonables de "poderoso": (a) volumen del pico muy alto, (b) intacto/primer toque, (c) confluencia con POC/VAH/VAL, (d) velocidad de llegada.

## Lo que probé al diseñar (solo conteos de señales, sin mirar ganancias)
- (b) "intacto desde la apertura": 2–3 señales en 576 sesiones; (b') "llega de lejos en 30 min": 0–2 señales. Motivo: la absorción exige que el precio ya esté parado junto al nodo, y el nodo de ayer casi siempre ya fue visitado hoy. **Descartadas por vacías**, no por resultado.
- (c) confluencia: con p95 y 4 puntos de cercanía al POC/VAH/VAL: 73 señales (insuficiente); con 8 puntos: 115.

## Definición operable fijada (HVF v1)
HVN poderoso = grupo contiguo de precios del perfil NY de ayer con volumen ≥ percentil 95, cuyo pico queda a ≤ 8 puntos (32 ticks) del POC, VAH o VAL de ayer. Sobre esa zona se aplica el detector de absorción de ABS (flujo agresivo ≥ p95 en 60 s, precio sin avanzar > 2 ticks, extremo a ≤ 4 ticks de la zona, confirmación a 60 s), entrada contra el lado absorbido, stop 4 ticks más allá (12–32), salida a 15 min. Una vez por zona y día. Las alternativas (p91–p99, 4–12 puntos, cercanía 2–6, confirmación 40–80 s) se corren como sensibilidades dentro del mismo estudio.

## Límites
La salida a 15 min sin objetivo y la confirmación vienen de P012 (periodo de diseño): exploratorio, el DSR lo penaliza. Esto prueba el HVN poderoso con una regla de trading; el estudio de reacción en el primer toque (con corrección de Holm) y el indicador de ATAS siguen pendientes: el orquestador solo corre estrategias.
