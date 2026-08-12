# Medición de correlación y viabilidad de cartera — 2026-08-11

Motivo: resolver el conflicto MAX_CORR=0.70 vs MAX_POS, abierto desde el
2026-08-08. Scripts: `analysis/corr_pairs.py`, `analysis/corr_universe.py`.
Retornos log horarios, solo barras contiguas (sin saltar huecos).

## Hallazgo 1 — el conflicto es de CRIPTO, no de MAX_POS

Universo actual de 8 monedas, correlación mediana por pares:

| ventana | mediana | pares < 0.70 | carteras legales k=2 | k=3 | k=4 | k=6 |
|---|---|---|---|---|---|---|
| histórico completo | 0.682 | 17/28 | 17 (60.7%) | 15 | 6 | 0 |
| últimos 365 días   | **0.807** | **1/28** | **1 (3.6%)** | **0** | **0** | **0** |

En el régimen actual MAX_CORR=0.70 es insatisfacible en cripto a
CUALQUIER tamaño ≥2 salvo una única pareja (BTC/LTC, justo en 0.70).
Bajar MAX_POS no resuelve el conflicto: lo hace irrelevante.

El acoplamiento AUMENTÓ (0.68 → 0.81). Toda regla calibrada sobre los
10 años es demasiado laxa para el mercado presente. La cifra 0.77 que el
proyecto venía citando no es estable: depende de la ventana.

## Hallazgo 2 — acciones NO tiene conflicto

Últimos 365 días: mediana 0.446, 40/45 pares legales, 52.4% de las
carteras de tamaño 4 son legales. Los únicos pares problemáticos son
solapamientos por construcción (SPY/QQQ 0.95, SPY/IWM 0.86).

## Hallazgo 3 — ampliar el universo "resuelve" el conflicto de la peor manera

58 activos con historia suficiente: 88.6% de pares legales, conjunto
mutuamente compatible de 42 activos. Pero los menos acoplados son:

- `USD1-USD` (0.066): stablecoin. Correlación baja porque no se mueve.
  Es efectivo con comisiones, no diversificación.
- `PAXG-USD` (0.130): oro tokenizado. Descorrelacionado de verdad — pero
  entonces ya no se está probando una estrategia de cripto.
- `ALLO`, `SAPIEN`, `BNKR`, `AVNT`, `ZORA`, `SPK`, `VVV`: tokens diminutos
  y recientes. La baja correlación mide ILIQUIDEZ, no independencia.

Dos riesgos concretos si se amplía sin más:
1. **Ejecución.** Con coste de ida y vuelta de 1.30%, el deslizamiento
   real en un token ilíquido excede lo que modela el motor.
2. **Sesgo de supervivencia.** `FARTCOIN`, `MOODENG`, `USELESS`, `TRUMP`,
   `PUMP` están en `data/candles` porque existen HOY. Examinar sobre el
   último año con la lista de supervivientes reintroduce exactamente el
   mecanismo que produjo el +354% vs −90% fundacional.

Ampliar solo sería defendible con (a) filtro de liquidez en dólares y
(b) universo point-in-time (`data/pit_universe.py` ya existe). Es
trabajo, no un ajuste de parámetro.

## Conclusión

Cripto a 2 con MAX_CORR y universo intactos. Consecuencia aceptada: los
bots de cripto estarán la mayor parte del tiempo con una posición o en
efectivo. Eso NO es el sistema roto — es la restricción informando que
estas 8 monedas son una sola apuesta a 0.81 de correlación.
