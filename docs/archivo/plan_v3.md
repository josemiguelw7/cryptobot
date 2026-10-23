# Plan v3 — cambios exactos (2026-08-07)

ESTADO: PROPUESTA, SIN FIRMAR. Nada de este documento esta implementado.
El roster de la seccion F1 queda CONGELADO aqui antes de cualquier
examen. Fundamento: Tanda A completa (analysis/, 2026-08-07) + curva de
costos + MFE/MAE + meseta de parametros + consistencia entre pares.

## 0. Que NO cambia (declarado primero)

- Los escuadrones armados actuales NO se tocan. Corren sus 90 dias como
  cohorte baseline. No hay cuarto reset.
- K = 91 y sigue subiendo. El ledger no se toca.
- Descartado con evidencia, no se implementa:
  - trailing stops intrabarra (MFE mediano +0.27% nunca alcanza el
    umbral de 0.84%: no hay ganancia que proteger)
  - ordenes maker como rescate (curva de costo: "nunca" incluso a 0%)
  - escaneo intradia / velas de 5 min (aritmetica: acierto requerido 215%)
  - LLM en el loop de decisiones en vivo (lookahead + no-determinismo)
  - elegir parametros del escaneo de meseta (n=240 rinde mejor que
    n=168 EN LA MUESTRA — usarlo seria mineria de datos; los horizontes
    v3 se derivan de la aritmetica de costos, declarada antes)

## F0. Sabado — decisiones de charter (0 lineas de trading, 0 K)

- **C0.1 `stitched()` se retira como metrica.** Reemplazo exacto: el
  examen reporta mediana de retorno neto POR VENTANA + % de ventanas
  que ganan a B&H. Las columnas stitched del ledger quedan como legacy
  (filas viejas intactas); se agregan `median_win_net` y `beat_bh_pct`.
  Archivos: backtest/exam.py (solo lectura de stitched), exam_1h.py
  (resumen + ledger), portal.
- **C0.2 Desglose por regimen** en cada examen: ventanas partidas por
  signo de B&H (alcista / bajista / lateral ±2%), mediana por grupo.
  Reporte, NO puerta (ratchet-legal). Responde: ¿defensa o alfa?
- **C0.3 DSR como puerta explicita**: veredicto PASS requiere ademas
  DSR > 0 con el K vigente al momento del examen. Endurecimiento s2.1.
- **C0.4 Curva de costo como requisito de admision**: ninguna semilla
  entra al examen sin publicar su breakeven (analysis/cost_curve.py).
  Si es "nunca" a <= 0.32%/lado, no quema nombre del ledger.
- **C0.5 Firma del roster F1** tal como esta escrito abajo.

## F1. Wave 3 — lo unico que gasta K (91 -> 97)

Universo: los mismos 8 pares. Barras diarias via resample 24x1h
(S.SlowClock, ya existe en strategies.py). Prefijo permanente `d3_`/`h3_`.

| nombre | definicion exacta | hold declarado | por que |
|---|---|---|---|
| d3_trend | SlowClock(Trend(20), 24) | >= 240h (10d) | familia mas defensiva del examen, reloj donde el umbral es 55-60% |
| d3_nearhi | SlowClock(NearHigh(60, 0.02), 24) | >= 360h | la pendiente de meseta apunta a horizontes largos; el parametro sale de la aritmetica, no del escaneo |
| d3_calm | SlowClock(CalmRegime(5, 20), 24) | >= 240h | mejor beta+timing de la atribucion |
| d3_cash | MarketRegime diario: BTC > SMA200d Y propio > SMA20d, si no EFECTIVO | >= 240h | ataca el handicap long-only: efectivo como posicion activa |
| h3_crossconf | Cross(24,168) + confirmacion de vela alcista (engulfing o pin, OHLC) dentro de <=12 barras de la senal | >= 72h | UNICA horaria: unica familia con patron "entra temprano y devuelve" (MFE +1.53% / MAE -2.76%). Nison donde los datos lo piden |
| d3_rand | RandomEntry diario turnover-matched | >= 240h | yardstick de suerte; FAIL pre-registrado |

- Espejo de acciones (`s3_*`): SOLO despues de leer los 6 veredictos
  cripto. No se gastan 6 nombres mas a ciegas.
- Pre-registro de expectativa: mayoria FAIL. Un PASS se revisa contra
  la plomeria antes de celebrarse (precedente: 3 bugs en una semana).
- Pre-check obligatorio antes del examen: turnover realizado en scan
  >= hold declarado / 1.5, o la semilla vuelve a diseño sin quemar nombre.

## F2. Motor v3 (0 K) — escuadron PARALELO, el armado no se toca

Archivo nuevo `bot/squad_v3.py` (hereda de squad.py), estado propio
`bot/squad_v3_state.json`. Se arma SOLO tras veredictos F1 + firma.

- **E3.1** `MIN_HOLD_BARS` por roster: salida bloqueada antes de N
  barras salvo circuit-breaker. Mata el churn en el motor, no en la fe.
- **E3.2** Tope de correlacion: entrada rechazada si corr(retornos
  diarios, 60d) > 0.7 con cualquier posicion ya en cartera. (Medido:
  correlacion mediana del universo 0.77; 3 posiciones ~ 1.1 reales.)
- **E3.3** Sizing: cupos de $500, peso maximo 1/6, MAX_POS = 6.
- Dos cohortes comparables: baseline (motor v2) vs v3, mismos 90 dias.

## F3. Medicion permanente (0 K, sin reset)

- **M3.1** `logs/squad_trades.csv` gana columna `notional` (fill real)
  -> atribucion exacta en vez de estimada.
- **M3.2** Reporte sabatino automatico (ops/): MFE/MAE de la semana,
  diversidad, equity vs BTC-HOLD, desglose por regimen.
- **M3.3** `analysis/` queda como banco de herramientas de admision:
  cost_curve, plateau, mfe_mae, attribution corren sobre cualquier
  candidato ANTES de proponer su nombre.

## Expectativas pre-registradas

Lo mas probable sigue siendo que BTC-HOLD gane. El exito de wave 3 no
es rentabilidad prometida: es que por primera vez las semillas compiten
en un juego matematicamente ganable (55-60% de acierto requerido, no
215%). Si fallan AHI, la conclusion honesta sera sobre las señales, no
sobre el peaje — y esa conclusion se documenta aunque duela. El pivote
a futuros (otra estructura de costos) seria OTRO proyecto, no una
mutacion de este.

## Firma (sabado)

    Owner: Jose Santos            Fecha: 2026-08-08 04:15 UTC
    Firmado en sesion. Autoriza implementar F0, F1, F2 y F3 tal como
    estan escritos arriba. NO autoriza armar el escuadron v3: eso
    requiere veredictos F1 registrados + firma aparte (mismo patron
    que 2026-08-04).

---

## ADENDA 2026-08-08 — hallazgo estructural y muestra ampliada

**El problema no eran (solo) las semillas: era la MUESTRA.**

Medido al pre-chequear F1:

- La muestra de examen cubria 1 año (2025-07 a 2026-08). BTC cayo -45%.
- De las 32 ventanas: **31 bajistas (97%), 1 lateral, CERO alcistas.**
- Criterio 4 exige ganar a B&H -> en bajista eso significa estar FUERA.
- Criterio 5b exige operar en >=50% de las ventanas -> estar DENTRO.
- Las dos reglas juntas eran casi insatisfacibles para una semilla
  solo-compra. Los 22 FAIL de la ola 1 se produjeron en una muestra
  donde una estrategia long-only no podia demostrar alfa.

**Accion (no toca charter, no gasta K): historia completa descargada.**

| par | barras | desde |
|---|---|---|
| BTC-USD | 87,550 | 2016-08-10 |
| ETH-USD | 87,561 | 2016-08-10 |
| LTC-USD | 86,345 | 2016-08-17 |
| LINK-USD | 62,349 | 2019-06-27 |
| ADA-USD | 47,235 | 2021-03-18 |
| DOGE-USD | 45,387 | 2021-06-03 |
| SOL-USD | 45,051 | 2021-06-17 |
| XRP-USD | 43,537 | 2019-02-26 |

Regimen de ventanas tras la ampliacion (BTC): **59% alcista, 40%
bajista, 1% lateral** (antes 0/97/3). Ventanas por par: 80 contra 4.
Backup de la muestra vieja en `data/candles.bak_1y/`.

**Consecuencias registradas:**

1. `data_fingerprint` cambia. Las 22 filas del ledger anteriores al
   2026-08-08 apuntan a una huella que ya no existe en disco. Son una
   POBLACION DISTINTA y no son comparables con veredictos futuros. No
   se re-examinan: un FAIL registrado es permanente (una semilla por
   nombre, para siempre).
2. `d3_cash` vuelve a ser viable: su warmup de 4,872 barras (SMA 200d)
   no cabia en 2,160; con 87k barras si, sin tocar la geometria del
   examen. Recupera "efectivo como posicion activa" sin cambio de
   charter.
3. Huecos: 229 en total, 193 de ellos en LTC (iliquidez 2016-2018). La
   politica de descarte de ventanas con hueco ya los maneja.

**Lo que NO cambia:** K sigue en 93. Ninguna semilla de wave 3 ha
gastado un nombre. El pre-check de admision (C0.4 + C0.1b) sigue siendo
la puerta antes del examen.

---

## F1 EJECUCION — 2026-08-08 10:57 UTC

Pre-check de admision sobre la muestra de 10 años (analysis/admission.py):

| semilla | cobertura | mediana al operar | breakeven | admision |
|---|---|---|---|---|
| d3_trend | 51% | +5.89% | 0.420% | **ADMITIDA** |
| d3_calm | 67% | +1.50% | 0.420% | **ADMITIDA** |
| d3_rand | 100% | -4.55% | 0.100% | **ADMITIDA (control)** |
| d3_nearhi | 18% | +12.24% | 0.420% | RECHAZADA: ausente |
| d3_cash | 41% | +5.73% | 0.420% | RECHAZADA: ausente |
| h3_crossconf | 100% | -9.67% | 0.050% | RECHAZADA: exige coste institucional |

**Se examinan 3 nombres. K 93 -> 96.** Los tres nombres quedan quemados
para siempre al registrarse el veredicto.

**Expectativa PRE-REGISTRADA, escrita antes de correr:**

- El pre-check midio sobre el MISMO periodo que usara el examen. No es
  evidencia fuera de muestra: es un filtro de admision, no un veredicto.
- Con K=96 el umbral de suerte exige Sharpe > ~1.25. Una mediana de
  +5.89% por ventana NO implica eso.
- Expectativa declarada: **d3_rand FAIL** (control). d3_trend y d3_calm
  probablemente FAIL tambien, muy posiblemente en criterio 8 (holdout
  120d) o en la nueva puerta 10 (DSR).
- Si d3_rand PASA, el resultado invalida la ola completa y se investiga
  la plomeria antes de celebrar nada (precedente: 4 bugs en 2 semanas).
- Si d3_trend pasa y d3_calm no, NO se rediseña d3_calm para que pase:
  se acepta el veredicto.

**Los 3 nombres rechazados NO se examinaron, asi que siguen libres.**
Rediseñarlos es legitimo, pero el parametro nuevo debe derivarse de una
regla declarada de antemano, no de probar hasta que la cobertura llegue
a 51%. h3_crossconf se retira: ningun parametro la salva a coste retail.
Con ella se retira el uso de patrones de velas en esta ola — los datos
la rechazaron.
