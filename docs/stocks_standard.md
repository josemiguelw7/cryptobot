# Estándar de entrada — track de ACCIONES (1h RTH)
**Pre-registrado 2026-08-02, antes de ver ningún resultado de
estrategia sobre el store de stocks.** Cubierto por el ratchet: solo
puede volverse más estricto.

## Universo (CONGELADO)
SPY, QQQ, IWM, AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA.
Datos: `data/stocks/{TICKER}_1h.csv` (730d, ajustados por splits y
dividendos) y `_1d.csv` (10 años). **Caveat pre-registrado:** los 7
nombres individuales se eligieron por su liquidez DE HOY → cualquier
backtest sobre ellos carga optimismo de supervivencia. El juez real es
el forward squad, no el examen. Cambiar el universo = nueva generación.

## Reloj de mercado
Señales SOLO en barras RTH cerradas (9:30–16:00 ET, L–V). Los gaps
nocturnos y de fin de semana son NORMALES y no descartan ventanas; solo
descartan barras faltantes dentro de una sesión. Sin trading pre/post.

## Costes modelados (por lado)
Comisión $0 (era retail); spread+slippage: 0.02% ETFs, 0.05% nombres
individuales. Stress VINCULANTE: slippage ×2. Stop-outs: slip ×2.
Escala horaria: DAY=7 barras RTH, WEEK=33, MONTH=140.

## Examen (mismo esqueleto de 9 criterios, adaptado)
Ventana 630 barras (~90 sesiones), step 315, HOLDOUT: últimos 120 días
calendario reservados. Benchmark: **SPY-HOLD**. Criterio 4: ≥ SPY-HOLD
neto-a-neto. Criterio 9: permutación p<0.05 Y Sharpe > valla de suerte
con el **K GLOBAL compartido** (mismo `exam_ledger.csv`,
timeframe="1h-stk" — cada examen de stocks sube la valla de crypto y
viceversa; una sola contabilidad de intentos). Un examen por nombre,
PARA SIEMPRE. FAIL → control; PASS → candidata.

## Regla PDT (§4.6 del charter)
Paper: sin restricción. Dinero real futuro: cuenta <$25K limita a 3
day-trades/5 sesiones — irrelevante por diseño: todas las semillas
declaran hold ≥ 1 sesión.

## Predicción pre-registrada
0 de 10 PASS. Razón: los megacaps 2024–2026 fueron fuertemente
alcistas; una long/flat que entra y sale paga peaje y pierde contra
SPY-HOLD en criterio 4, o sobrevive por suerte y cae en el 9.
