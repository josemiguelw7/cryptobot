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

## Firma y deltas de implementación (2026-08-02)

**Adoptado por el owner: Jose Miguel — vía chat: "aprobado".** Roster
de 10 semillas espejo cerrado (bot/seeds_stocks.py); desde aquí aplica
§9.3. Deltas del adaptador (`backtest/exam_1h_stocks.py`), todos en
dirección MÁS estricta, ratchet-compatible:

1. **Slippage plano 0.05% ambos lados** para las 10 (el estándar
   permitía 0.02% a los ETFs; se les cobra como a los nombres).
2. **Criterio 4 contra el B&H del universo completo** (stitched de los
   10, mismo método que crypto) — vara más alta que SPY-HOLD solo,
   porque el universo incluye los megacaps 2024-26.
3. **Sharpe anualizado por sesiones** (agregación de 7 barras RTH,
   √252). Usar el √365 de crypto habría inflado el Sharpe de stocks
   ~20% — corregido antes de examinar a nadie.
4. **Política de gaps precisa:** >96h = ventana descartada; gaps de
   2–96h solo son válidos si aterrizan en la barra de apertura (9:30
   ET); todo lo demás descarta. Dryrun: 120 ventanas main, ~1
   descartada por ticker.
5. El armado del track espera al **motor con reloj de mercado**
   (squad_stocks) — los veredictos etiquetan candidata/control desde
   ya, pero ARMED se enciende cuando exista quien ejecute.

## Motor forward (2026-08-02)

`bot/squad_stocks.py` es un **adaptador sobre `bot/squad.py`**: no
duplica lógica. Todas las reglas del charter (§4.1 costes, §4.3
compuerta, §4.5 integridad, §8 kill switches, §3 días contados, §12.1
taxonomía) las ejecuta el MISMO código que corre crypto. Un motor, dos
mercados. Overrides: reloj RTH, comisión 0, slip 5bps plano, sizing con
escala de sesión (7 barras), datos del store de stocks, ledgers propios.

**Referencia de ejecución, declarada:** las acciones no tienen un
top-of-book público 24/7 como el ticker de Coinbase, así que el fill se
referencia al cierre de la última barra RTH CERRADA más slippage
modelado. El requisito del §4.5 se mantiene — la señal lee la barra
cerrada y el fill nunca usa la misma barra que generó la señal — pero
queda registrado como una diferencia real frente al track de crypto:
**el escuadrón de acciones no ve spread vivo.** Al pasar a dinero real
esto se sustituye por quotes del broker, y hasta entonces cualquier
resultado de stocks lleva esta nota.

Fuera de sesión el ciclo marca equity y sale con 0: los feriados no
necesitan calendario (sin barra fresca no hay ciclo contado).
