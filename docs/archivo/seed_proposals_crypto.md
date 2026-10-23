# Semillero intradía cripto — PROPUESTA para adopción

**Estado: PROPUESTO — no adoptado.** Charter §9.3: las 10 semillas
adoptadas son inmortales e inmutables, los controles congelados que toda
generación posterior debe vencer. Por eso adoptarlas es decisión del
owner, no de ingeniería. Este documento existe para que esa decisión se
tome con los ojos abiertos y quede registrada.

## Qué se propone

10 semillas horarias, largas/flat, máx. 2 posiciones, sobre los 8 pares
fijos del estándar (BTC, ETH, SOL, XRP, ADA, DOGE, LINK, LTC). Código en
`bot/seeds_crypto.py`; toda la lógica vive en `bot/strategies.py` (la
semilla examinada es byte a byte la que opera, W1.1).

| # | nombre | familia | regla (barras HORARIAS) | warmup | hold |
|---|--------|---------|-------------------------|--------|------|
| 1 | h_trend_168 | tendencia | precio > SMA(168) | 168 | ~7d |
| 2 | h_cross_24_168 | tendencia | SMA(24) > SMA(168) | 168 | ~3d |
| 3 | h_tsmom_72 | momentum | retorno 72h > 0 | 73 | ~3d |
| 4 | h_macd_12_26 | momentum | MACD(12,26,9) > señal | 40 | ~2d |
| 5 | h_donch_48_24 | ruptura | máx 48h entra / mín 24h sale | 49 | ~2d |
| 6 | h_volbrk_24_96 | ruptura | squeeze: vol(24)<vol(96) y máx 24h | 97 | ~2d |
| 7 | h_rsi14_reg168 | reversión | RSI(14)<25 compra, >55 sale, solo sobre SMA(168) | 169 | ~1d |
| 8 | h_boll_48 | reversión | < banda −2σ(48) compra, media sale | 49 | ~1d |
| 9 | h_calm_24_168 | régimen | mantener solo si vol(24)<vol(168) | 169 | ~3d |
| 10 | h_nearhi_168 | anomalía | dentro del 5% del máx 168h | 168 | ~5d |

## Por qué estas y no otras

Solo se usaron los tres priors publicados ANTES del experimento (commit
997c7d3), que miden coste y estructura, nunca retornos:

1. **move_scale**: mediana de |movimiento| — 1h 0.31%, 12h 1.21%, 1d
   1.80%, 3d 3.27%, 7d 4.83%. El umbral §4.3 es 2× el coste ida-vuelta
   (1.6% con costes del charter). Conclusión estructural: **decisiones
   cada hora, retenciones medidas en días.** Ninguna semilla con hold
   objetivo < 1 día tiene espacio para existir.
2. **signal_correlation**: 20 familias clásicas cargan ~6.24 opiniones
   independientes; tendencia y reversión anticorrelacionan (−0.222).
   Por eso: pocas semillas por familia, familias deliberadamente
   repartidas (4 tendencia/momentum, 2 ruptura, 2 reversión, 2 régimen).
3. **hysteresis_frequency**: separar línea de entrada y de salida corta
   los round-trips ~10×. Todas las semillas salen por una línea distinta
   de la que entran, o mantienen un régimen.

Los parámetros son convencionales (24h=1d, 168h=7d, RSI 14, MACD
12/26/9, bandas 2σ) elegidos por convención, **no por cribado**: cada
variante cribada sube la valla de suerte del criterio 9 para todos los
que vienen después. Diez exámenes limpios valen más que diez ajustados.

## La puerta de coste §4.3, declarada por adelantado

Proxy de edge esperado = mediana móvil incondicional de |retorno| sobre
el horizonte de retención declarado de la semilla (la estadística de
move_scale, rodante, libre de señal). Puerta: proxy ≥ 2× coste
ida-vuelta modelado al momento de decidir (2×(0.40% + slip) + spread
vivo). El horizonte está declarado en la tabla y no se ajusta después.

## Proceso de adopción (en orden, sin saltos)

1. El owner revisa esta lista: aprueba, edita o veta semillas.
2. Cada semilla adoptada pasa UNA VEZ por `backtest/exam_1h.py`
   (criterios 1–9 del estándar). PASS → candidata; FAIL → control.
   El estándar predice CERO passes; un fail no expulsa del escuadrón,
   lo etiqueta.
3. Se registra en la revisión del sábado la interpretación §2.5:
   *"examen primero; el veredicto etiqueta candidata/control; los
   controles jamás son elegibles para capital real"* (precedente:
   MOM-ROT, CROSS-BTC, DONCH-BTC, RSI-BTC en la liga diaria).
4. `ARMED = True` en `bot/seeds_crypto.py` + commit. Desde ese momento
   la lista es inmutable.
5. Shakedown: los días previos a 7 días contados consecutivos NO cuentan
   para el reloj (§3). Cuando los 10 completen 7 días contados
   consecutivos, empieza la semana 1.

## Matemática del reloj (para la meta de "probar unas semanas")

Con la asignación inicial de $3,000 por bot, el camino más corto a dinero real es:
7 días de shakedown mínimo → 90 días contados (Stage 1, ruta A) →
60 días frescos (Stage 2) → piloto $500. **~5 meses, mínimo teórico.**
"Unas semanas" de forward testing alcanzan para: validar la fontanería,
acumular las primeras autopsias, matar semillas rotas por kill switch, y
llenar la matriz familia × régimen — no para calificar nada. El charter
lo predijo (P5) y el ratchet existe para esto. La única palanca legítima
de velocidad es el PARALELISMO: 10 semillas a la vez, y el track de
acciones corriendo su propio reloj en paralelo.

## Firma

**Adoptado por el owner: Jose Miguel — fecha: 2026-08-02** (aprobación
expresa vía chat: "lets go with your recommendation yes"). La lista de
10 semillas queda cerrada; desde aquí aplica §9.3 (inmortales e
inmutables). Cubierto por el ratchet: este documento solo puede volverse
más estricto.

## Decisiones registradas en la misma aprobación

1. **Roster adoptado** tal como está (10/10, sin ediciones ni vetos).
2. **Interpretación §2.5 confirmada**, a asentar en la revisión del
   sábado 2026-08-08 09:00 America/Chicago: examen primero; el
   veredicto etiqueta candidata (PASS) o control (FAIL); los controles
   corren para siempre como demostración forward y jamás son elegibles
   para capital real. Precedente: MOM-ROT en la liga diaria.
3. **Expansión del store 5m: diferida.** Ninguna semilla adoptada opera
   bajo la hora; ampliar 25→65 pares en 5m sería coste sin hipótesis.
   Se reabre solo si algún candidato futuro declara horizonte sub-1h.
4. **Track de acciones (SPY/QQQ, swing, §4.6/PDT): próxima sesión**,
   con su propio reloj en paralelo — la palanca de velocidad legítima.

## Erratum + predicciones pre-registradas (2026-08-02, antes de exámenes 2–10)

**Erratum.** La frase "todas las semillas salen por una línea distinta de
la que entran" es falsa tal como quedó implementado: h_trend_168 y
h_tsmom_72 son de línea única; h_cross_24_168 y h_macd_12_26 cruzan
líneas suavizadas (histéresis débil). Solo donch, volbrk, rsi, boll
tienen histéresis verdadera; calm y nearhi son de régimen/banda. Bajo
§9.3 las semillas NO se corrigen: quedan como están y el examen las
juzga. El primer examen ya lo demostró: h_trend_168 = FAIL con 62–93
trades por ventana de 90 días (churn de línea única, dominado por
fees) — el prior de histéresis (997c7d3) predijo exactamente esto.

**Predicciones registradas ANTES de correr los exámenes 2–10:**
1. h_tsmom_72 fallará igual que h_trend_168: churn de línea única,
   taxonomía dominante fees_spread, criterio 6 (fee-stress) FAIL.
2. Las 4 con histéresis verdadera (donch, volbrk, rsi, boll) mostrarán
   un orden de magnitud menos trades por ventana (~5–15 vs 60–90).
3. Veredicto agregado: 0 de 10 PASS (predicción del estándar, en un año
   donde B&H por ventana promedió ~−18% ninguna larga/flat pasa el
   criterio 4 y 9 a la vez).
4. Si alguna pasa, será por suerte de ventana, no por edge — y la valla
   del criterio 9 (K=40+) existe para atraparlo.

**Nota de display (no de criterio):** "stitched" imprime el producto de
ventanas SOLAPADAS (step 12 < ventana 2160/24 días); a 1 decimal un año
bajista colapsa a "-100.0%". Los números por ventana en el CSV del
examen son la lectura sana. Cambiar el print es cosmético y se hará
después de la tanda para no mezclar versiones del instrumento en un
mismo log.

## Aclaración del owner sobre el monto (2026-08-02)

Los $3,000 por bot son la **asignación inicial**, no un techo de
crecimiento. En paper ya es así: cada slice del escuadrón nace con
$3,000 y compone sin límite. Para dinero real, la lectura compatible
con el charter sellado queda registrada así: la escalera del piloto
($500 → $1,500 → $3,000) es **cómo llega** la asignación inicial de
$3,000 a un bot que se la ganó; por encima de esa cifra el crecimiento
no tiene techo, pero SOLO con ganancias realizadas del propio bot —
jamás capital fresco. Esto no afloja el ratchet: añade una restricción
(prohibición de recargas) en vez de quitar una.
