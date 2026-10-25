# ABR v1: absorción con reprueba (entrada pasiva en el extremo absorbido)

## Por qué esta prueba
- ABU (P030/P031) es la única familia con ventaja: +$5,956 / +$11,912, p 0.001. Pero entra a mercado después de que el precio se aleja 4 ticks, con stops de 12–32 ticks, y pierde el 60% de las veces con el stop.
- El placebo desplazado (entrar 5 min antes) ganó $19.7k, más que la señal real: el valor está en entrar cerca del extremo. Entrar antes con datos del futuro no se puede, pero se puede dejar una orden límite en el extremo y esperar a que el precio lo pruebe otra vez.
- ABF (P036, seguir la ruptura) perdió con p 0.986: la reversión es el lado correcto. ABS v3 (entrada temprana a mercado, P016) no mejoró.

## Qué encontré (búsqueda 25/10/2026)
- Las descripciones de footprint (TradingView, [Order Flow PRO](https://ar.tradingview.com/scripts/orderflowvolume/), [Order Flow Footprint & Delta](https://th.tradingview.com/scripts/deltavolume/)) hablan de absorción como volumen agresivo absorbido por órdenes pasivas, y de "barrido + absorción + recuperación" y "ruptura + reprueba + rechazo" como patrones. Son heurísticas de vendedores de indicadores, sin estudio estadístico, y no dicen dónde poner la orden ni el stop.
- Auction market theory: el nivel donde hubo absorción es información de oferta/demanda; una reprueba que se sostiene confirma al participante pasivo.
- Las definiciones concretas (2 ticks dentro del extremo, 300 s) son mías, fijadas antes de ver resultados de la prueba completa.

## Definición (una sola)
1. Detector, niveles, filtro de días (abren dentro del valor de ayer), umbral relativo y confirmación a 60 s: idénticos a ABU v1.
2. En el momento de la confirmación se deja una orden límite 2 ticks dentro del extremo absorbido (vende bajo el máximo / compra sobre el mínimo), válida 300 s. Si no se llena, no hay operación. Llenado con la cola y las reglas del simulador.
3. Stop 8 ticks desde el llenado (6 más allá del extremo), objetivo 2R (16 ticks), salida a 15 min tras el llenado, 1 contrato, 09:30–15:30.

## Sensibilidad (16 intentos)
Distancia de la orden 0/1/3/4 ticks, stop 4/6/10/12, objetivo 1/1.5/2.5/3 R, espera 180/240/360/420 s.

## Humo (solo señales y conteo de llenados)
120 sesiones: 57 señales, 28 llenados (~49%), unas 130 operaciones esperadas. Vi también el neto de esas 120 sesiones (−$626, 28 operaciones): es ruido, no decide nada. Probé 3 y 600/900 s solo para contar llenados (30–33): no mueven la frecuencia y no los usé.

## Riesgos
- Exploratoria: nace de ver ABU y su placebo en el mismo periodo de diseño; no es validación independiente. Se suma a la cuenta de intentos (DSR seguirá en 0).
- Selección adversa: solo se llenan las ordenes cuando el precio vuelve; si vuelve fuerte, puede seguir. El simulador lo mide.
- Mismo conjunto de señales que ABU: no es evidencia independiente de ventaja.
