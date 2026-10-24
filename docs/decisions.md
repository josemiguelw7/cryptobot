# Decision log (charter v2 §8)

Format: date · tier · what · why · direction · falsifier · effective.

---

**2026-08-08 · T2 · Verdicts become voidable on documented bug evidence.**
Why: d3_trend and d3_calm were graded on a frozen SlowClock (review C-1);
"one exam per name, ever" was burning names on plumbing, not verdicts.
Direction: loosening (re-exams possible) paired with a tightening (VOID
requires a committed bug reference; K never decreases; one re-exam only).
Falsifier: if the void log shows voids without reproducible bug evidence,
or the same name voided twice, this rule is being abused and reverts.
Effective: 2026-08-09 (one night, §3.1). Owner choice, external review Q&A.

**2026-08-08 · T2 · Exam criterion 4/6/7/8 statistic: stitched() → per-window median vs B&H net; criterion 9 statistic likewise.**
Why: C0.1 formally retired stitched() as uninterpretable (50% overlap
compounds the same week twice) but it still decided five gates (review
C-3). Direction: recalibration. Falsifier: if median-based gates pass a
seed that a non-overlapping-window analysis clearly rejects.
Effective: 2026-08-09.

**2026-08-08 · T2 · Criterion 10 rebuilt as the real Bailey–López de Prado DSR (bot/stats.py, per-period units, skew/kurtosis-adjusted, ≥0.95), replacing a duplicate of criterion 9.**
Why: review C-2 — the shipped gate was character-for-character the second
half of criterion 9; it could never change a verdict. Direction:
tightening (a genuine additional constraint now exists). Falsifier: if
DSR ≥0.95 passes seeds that the permutation test rejects at p>0.2, the
dispersion estimate is too generous. Effective: 2026-08-09.

**2026-08-08 · T2 · Luck-hurdle dispersion derived from effective sample (365/T_eff, non-overlapping windows, pair correlation ρ=0.77 discount) instead of hardcoded var_sharpe=0.25.**
Why: review H-3 — the old hurdle (≈1.25 at K=95) corresponded to no
sample size the exam uses. Direction: recalibration (hurdle will usually
be LOWER; the new DSR gate compensates with a stricter probability
threshold). Falsifier: exam_metrics.jsonl accumulating enough runs to
estimate dispersion empirically; if empirical σ differs from 365/T_eff
by >2×, recalibrate again from data. Effective: 2026-08-09.

**2026-08-08 · T2 · Coverage (C0.1b / criterion 5b) counts round trips (trades ≥ 2), and criterion 3 (risk edge) is judged over active windows only.**
Why: review H-2 — trades==1 is a buy-and-hold clone, and 96% of
d3_trend's criterion-3 credit came from windows where it did nothing.
Direction: tightening. Falsifier: a genuinely selective seed that holds
across whole windows by design being structurally unable to reach 50% —
if that happens, the answer is a declared hold-through seed class, not a
looser count. Effective: 2026-08-09.

**2026-08-08 · T2 (repairs, §3.2 — no entry strictly required; logged for the record).**
SlowClock decides on UTC timestamp slots, not len(bars)%k (C-1, with
regression suite `bot/test_slowclock.py`); resample folds aligned to end
at the newest bar; live engine bounds history to strat.tail restoring
W1.1 (H-1); exam exceptions raise instead of silently going flat (M-4);
provenance captured at run start + source SHA (H-4); stock loaders (live
AND exam) drop forming bars (C-4); lookahead audit implemented and
publishing (M-6); per-exam statistics recorded to exam_metrics.jsonl.

**2026-08-08 · T1-adjacent · OPEN QUESTION for Saturday: stock-track history.**
The forming-bar bug (C-4) voids the stock squad's counted days under
§4.5f and compromises the 11 `1h-stk` ledger rows in the optimistic
direction. Options: (a) archive the stock generation (2026-08-04
precedent), void the 11 rows, restart the clock on fixed loaders;
(b) keep rows as FAIL-on-record with an annotation. NOT decided
unilaterally — this is a verdict-status question and belongs to the
owner at review. The engine fix itself is live either way.

**2026-08-08 · T2 · OPEN QUESTION for Saturday: position cap is three different numbers in three places.**
Charter §3 says MAX_POS=2. The ARMED rosters override it via the E2.3
hook: seeds_crypto.py runs 3, seeds_stocks.py runs 4 (both citing a
2026-08-04 "pre-adoption" amendment that never made it into the charter
amendment log). plan_v3 E3.3 signs 6 for v3. And the smoke tests
(`test_squad_smoke.py`, `test_squad_stocks_smoke.py`) still assert ≤2 —
they FAIL on main today, which means the test suite has been red and
nobody noticed (the review's "guards that don't bite" pattern, again).
State files confirm: 8 crypto bots hold 3 positions, 8 stock bots hold 4.
Needs ONE owner decision: pick the number per track, record it here,
update charter §3, roster, and tests to agree. Interaction to respect:
the 0.70 correlation cap is unsatisfiable at 6 positions in a
0.77-correlated universe (28/28 six-coin portfolios illegal).

**2026-08-11 · T1-adjacent · RESUELTA: las 11 filas `1h-stk` quedan ANULADAS y el reloj de la pista de acciones se reinicia.**
Cierra la pregunta abierta del 2026-08-08 (opción (a), precedente del
2026-08-04). Why: `ops/lookahead_audit.py` midió 792 violaciones en 799
decisiones de acciones (mediana −2580s: se decidía 43 minutos dentro de
una barra viva). Los 11 exámenes corrieron por los mismos cargadores sin
filtro, así que sus veredictos están comprometidos en dirección
optimista. Dirección: conservadora — se descarta evidencia favorable, no
se admite ninguna. K NO baja: las 11 filas VOID son filas de ledger y el
recuento sube de 27 a 38, así que la barrera de suerte de todo examen
futuro es más alta, no más baja. Los 11 nombres quedan libres para UN
reexamen sobre cargadores arreglados. Falsifier: si un reexamen de estos
nombres sobre código arreglado produce métricas parecidas a las
originales, entonces el sesgo de barra en formación no era el factor
dominante y esta anulación fue una sobrerreacción — quedaría registrado.
Effective: inmediato (§4.2 no exige espera para VOID con bug documentado).
Bug ref: docs/review/2026-08-08_external_review.md#C-4

**2026-08-11 · T2 · PROPUESTA: tope de posiciones CRIPTO 3 → 2. Efectivo 2026-08-12 (§3.1, una noche).**
Cierra la mitad cripto de la pregunta abierta del 2026-08-08. Qué cambia:
`seeds_crypto.py MAX_POS 3 → 2`, alineado con charter §3 y con
`squad.py` (que ya tiene 2). Why: la medición del 2026-08-11
(`docs/review/2026-08-11_correlacion_universo.md`) muestra que en los
últimos 365 días solo 1 de 28 pares de cripto cumple MAX_CORR=0.70 y
CERO carteras de tamaño ≥3 son legales — el tope de 3 estaba autorizando
carteras que la regla de correlación prohíbe. Dirección: **tightening**
(vuelve al número del charter, no lo supera). Falsifier: si a 2 posiciones
los bots de cripto quedan en efectivo >90% del tiempo durante 60 días
seguidos, el problema no es el tope sino el universo, y la respuesta
correcta es un universo point-in-time con filtro de liquidez — NO subir
MAX_CORR. Consecuencia aceptada: discontinuidad administrativa en las
curvas de equity el día que entre (los bots cierran el exceso al precio
que haya); anotarla para no leerla como señal.
Propuesta redactada por Claude a partir de la medición; el propietario
tiene hasta el 2026-08-12 para cancelarla antes de que toque el código.

**2026-08-11 · T1-adjacent · PROPUESTA: tope de posiciones ACCIONES 2 (charter) → 4 (lo que ya corre). Efectivo 2026-08-18 (§3.3, una semana).**
Why: la medición muestra que acciones NO tiene conflicto de correlación
(mediana 0.446, 52.4% de las carteras de tamaño 4 son legales), así que
el 4 es defendible sobre la evidencia. Dirección: **loosening** — sube un
tope por encima del charter. Por §3.3 esto es Tier 1-adyacente porque
hace más fácil que una estrategia pase el examen, y necesita una semana,
no una noche. **Quién se beneficia si la decisión es errónea:** cualquier
semilla de acciones que hubiera sido rechazada por concentración. Ese es
el riesgo y queda escrito. Falsifier: si las semillas que pasen a 4
posiciones no superan a las mismas semillas a 2 en un reexamen
comparativo, el tope alto no aportó nada y se revierte a 2.
NOTA: los bots de acciones llevan semanas corriendo con 4 fuera del
charter. Esta entrada legaliza el hecho consumado; el propietario debe
decidir conscientemente si eso es lo que quiere, o si la respuesta
correcta es bajar los bots a 2 y no mover el charter.


---

**2026-08-22 · MEDICIÓN (no es decisión): diagnóstico de "curvas paralelas".**
Origen: el propietario reportó que el dashboard mostraba bots sosteniendo
una sola posición sin operar, y curvas indistinguibles entre sí.
La medición NO confirma esa lectura, pero encuentra algo peor.
Ventana cripto: 2026-08-05 → 2026-08-22 (17 días, 387 ventanas).
Acciones: 80 ventanas.
- Los bots SÍ operan: 319 trades cripto, 361 acciones.
- Las curvas NO son paralelas: corr. de retornos cripto mediana 0.271
  (1 de 55 pares >0.9); acciones mediana 0.479 (3 de 55). Rango de
  retorno total cripto: 33.76 pp entre mejor y peor.
- Lo que se vio como "sosteniendo" son 8 de 11 bots cripto en 100%
  efectivo. Una línea de efectivo se ve igual que una posición dormida.
- CERO de 11 bots cripto superan comprar-y-sostener equiponderado
  (+29.57% en la ventana). Mejor bot: +26.19%. Mediana: +11.77%.
- El bot ALEATORIO (`h_rand_72`) es el #1 de cripto y el #3 de acciones.
- Acciones: los 11 bots negativos (−0.22% a −4.73%).
- Concentración real SÍ existe, pero en acciones: 6 de 11 bots tienen
  TSLA, 5 tienen META. En cripto está disperso solo porque están en caja.
- 3,828 de 4,359 decisiones son `SKIP-cap` (88%): el tope de posiciones,
  no la falta de señal, es lo que limita la actividad.
ADVERTENCIA: 17 días. Por §P2 del charter (10 bots × 7 días ⇒ 99.9% de
que uno se vea positivo por azar), NADA de lo anterior es veredicto.
Se registra como medición, no como evidencia de aprobación o rechazo.

**2026-08-22 · MEDICIÓN (no es decisión): anatomía de las salidas.**
Segunda pasada sobre `logs/squad_trades.csv` y `squad_stocks_trades.csv`
(columnas `exit_kind`, `loss_cause`, `mfe_pct`, `mae_pct` — nunca
analizadas hasta hoy). Hallazgos:
- CRIPTO, P&L neto por tipo de salida: `signal` = −102.26 sobre 131
  cierres; `stop` = +2,435.94 sobre 25 cierres. Las salidas por señal
  son netamente destructivas y 9 de 11 bots tienen P&L de salida-por-
  señal negativo. TODA la ganancia cripto viene de 25 salidas por stop.
- ACCIONES: 166 cierres, el 100% por `signal`. CERO salidas por stop.
  No existe mecanismo de stop en la pista de acciones.
- ACCIONES modela `fee = 0.00` en las 361 operaciones. Es decir: la
  pista de acciones pierde −965.74 en un mundo SIN fricción. Con
  spread/slippage realista el resultado sería peor, no mejor.
- Perfil win-rate / R:R — cripto: 26.3% aciertos, R:R real 6.41
  (perfil de seguimiento de tendencia, coherente y viable).
  Acciones: 25.9% aciertos, R:R real 0.58 (pierde en ambas dimensiones
  simultáneamente; esa combinación no tiene aritmética de rescate).
- Comisiones cripto: 1,248.35, el 32.6% del P&L bruto.
- `mfe_pct`/`mae_pct` están almacenadas como FRACCIÓN, no porcentaje
  (máx. 0.6236 = 62.4%). El nombre de la columna induce a error; no es
  un bug de datos pero sí de etiquetado.
NOTA ANTI-SOBREAJUSTE: el hallazgo "las salidas por señal destruyen
valor" es la observación más tentadora de toda la medición y NO se
propone actuar sobre ella. Sobre 17 días y 131 cierres, quitar el
mecanismo que perdió dinero en la muestra observada es exactamente el
procedimiento que produjo el +354% falso. Queda como hipótesis a
pre-registrar y probar hacia adelante, no como cambio.

**2026-08-22 · T3 · PROPUESTA: registrar `bench_bh` — bot de comprar-y-sostener equiponderado, en ambas pistas. Efectivo inmediato (§3.x, medición pura).**
Qué cambia: se añade un bot no-operativo que compra el universo
equiponderado en su primer ciclo y no vuelve a operar. Aparece en
`squad_equity.csv` y en el dashboard como una curva más.
Why: hoy la comparación contra comprar-y-sostener se calculó a mano y
fuera de banda. Sin un bench permanente, ningún resultado positivo es
interpretable — un bot que hace +11% en un mercado que hizo +29% está
destruyendo valor y la curva sola no lo muestra. Es la pieza que hace
honesto todo lo demás.
Dirección: **tightening** — sube la barra que cualquier semilla debe
superar; no autoriza nada nuevo. No modifica el comportamiento de
ningún bot existente, así que no hay discontinuidad de equity.
Falsifier: si tras 120 días el bench y la mediana de los bots quedan
dentro del ruido de la comisión, la conclusión no es "el bench está
mal" sino que la familia de estrategias no aporta y debe retirarse.
Consecuencia aceptada: el bench va a ganarle a casi todo casi siempre.
Eso es información, no un fallo del bench.

**2026-08-22 · T3 · PROPUESTA: completar el registro contrafactual de señales rechazadas. Efectivo inmediato (§3.x, medición pura).**
Qué cambia: `squad_decisions.csv` ya registra QUÉ se rechazó (3,828
`SKIP-cap`, 238 `SKIP-gate`) pero no QUÉ HABRÍA PASADO. Se añade el
retorno hipotético a horizonte fijo de cada señal rechazada, en un log
paralelo. No altera ninguna decisión de ningún bot.
Why: es el mayor rendimiento estadístico por unidad de riesgo de toda
la lista. Multiplica la muestra por ~25× (4,066 señales bloqueadas
contra 162 entradas reales) sin mover un solo parámetro ni arriesgar
capital. Y responde directamente si el tope de posiciones está
protegiendo o estorbando — pregunta hoy sin evidencia.
Dirección: **neutra** — puramente aditiva, sin efecto sobre veredictos.
Falsifier: si las señales rechazadas rinden igual o peor que las
ejecutadas, el tope está haciendo su trabajo y las dos propuestas de
tope pendientes (2026-08-11) deben resolverse en dirección estricta.

**2026-08-22 · T2 · PROPUESTA: modelar fricción no-nula en la pista de ACCIONES. Efectivo 2026-08-23 (§3.1, una noche).**
Qué cambia: `fee` en acciones pasa de 0.00 a un modelo de spread +
slippage no nulo (parámetro concreto a fijar antes de aplicar, por
razonamiento y escrito, NO buscado sobre resultados).
Why: las 361 operaciones de acciones se ejecutaron con fricción cero.
Comisión cero es realista en muchos brokers; spread y slippage cero no
lo es en ninguno. Todos los resultados de la pista de acciones están
sesgados en dirección optimista, y aun así son negativos en los 11
bots. La corrección empeora un resultado ya malo — por eso es segura.
Dirección: **tightening** — hace más difícil, nunca más fácil, que una
semilla de acciones apruebe. Admisible por ratchet sin debate.
Falsifier: si al introducir fricción realista los resultados de
acciones NO empeoran, el modelo de fricción no está conectado al motor
de ejecución y hay un bug que buscar.
Consecuencia aceptada: discontinuidad en las curvas de equity de
acciones el día que entre. Anotarla para no leerla como señal.

**2026-08-22 · PREGUNTA ABIERTA (no propuesta): mecanismo de salida en ACCIONES.**
Hecho: cripto tiene salidas por stop y son el 100% de su ganancia neta;
acciones no tiene ninguna y pierde en los 11 bots. Existen las clases
`Bracket` y `TrailStop`, escritas y NO registradas.
Por qué NO se propone registrarlas hoy: (a) la asimetría cripto/acciones
se observó sobre 17 y 80 ventanas respectivamente — actuar sobre eso es
ajustar a la muestra vista; (b) sigue sin resolverse si un mecanismo
nuevo de salida cuenta como "mutación de parámetro" bajo §9.6, y esa
pregunta es previa a cualquier implementación; (c) el propietario
pre-registró en P5 que querría moverse más rápido que las reglas.
Requiere decisión explícita del propietario sobre §9.6 antes de que se
redacte propuesta alguna. Se registra la pregunta, no la respuesta.

**2026-08-22 · RECORDATORIO: pendientes que este diagnóstico NO cierra.**
(1) Las dos propuestas de tope de posiciones del 2026-08-11 siguen sin
resolver, y el hallazgo de 88% `SKIP-cap` las hace más urgentes, no
menos. (2) `MAX_CORR=0.70` vs `MAX_POS=6` sigue siendo matemáticamente
incompatible. (3) La revisión independiente NO-Claude sigue pendiente:
este diagnóstico lo hizo Claude, las propuestas las redactó Claude, y
`REVIEW.md` ya dice que eso no constituye control independiente.

**2026-08-22 · APLICADO: `ops/bench_bh.py` y `ops/counterfactual.py` (las dos propuestas T3 de medicion pura).**
Ambos modulos son SOLO LECTURA por diseno: no importan `squad.py` ni
`squad_stocks.py`, no tocan estado, no alteran ninguna decision, y
escriben a logs propios (`logs/bench_equity.csv`, `logs/counterfactual.csv`).
Un bench que puede romper el motor de trading no es medicion, es riesgo.
Verificado: `git diff HEAD -- bot/` vacio. Cero lineas del motor tocadas.

RESULTADO 1 — bench comprar-y-sostener (con friccion de entrada):
  cripto  +28.60%  ·  acciones  −1.65%
Correccion a la medicion de hoy: en ACCIONES, 2 de 11 bots SI superan
comprar-y-sostener (`s_rsi14_reg33` −0.22%, `s_boll_14` −0.67% contra
−1.65% del bench). El resumen previo de "los 11 negativos" era cierto en
nivel absoluto pero enganoso en nivel relativo. En CRIPTO se confirma:
0 de 11 superan el bench.

RESULTADO 2 — contrafactual de senales rechazadas (n=4,514 resueltas):
  cripto   ENTER      n=151   mediana −0.677%  media +0.688%  pos 41.1%
  cripto   SKIP-cap   n=2897  mediana −0.724%  media +2.423%  pos 41.6%
  cripto   SKIP-gate  n=230   mediana −0.547%  media −0.441%  pos 31.3%
  acciones ENTER      n=191   mediana −0.048%  media −0.194%  pos 44.0%
  acciones SKIP-cap   n=1245  mediana +0.000%  media +0.041%  pos 48.4%
Lectura: el GATE DE COSTE funciona — lo que filtra rinde peor que lo que
deja pasar (media −0.441%, solo 31.3% positivas). El TOPE DE POSICIONES
es otra historia: las bloqueadas tienen media +2.423% contra +0.688% de
las ejecutadas, pero MEDIANA casi identica. Media >> mediana significa
cola derecha gorda: el tope no bloquea senales mejores en promedio,
bloquea el acceso a unos pocos aciertos grandes.
NO SE ACTUA SOBRE ESTO. Es descriptivo sobre datos ya vistos, y mover el
tope por este numero es ajustar a la muestra observada. Queda como
insumo pre-registrado para la decision de topes, no como su respuesta.
955 filas PENDING; se resuelven solas en corridas futuras.

**2026-08-22 · HALLAZGO NO BUSCADO: los smoke tests llevan tiempo FALLANDO.**
Al verificar que los modulos nuevos no rompieran nada se ejecutaron los
tests existentes. Dos fallan, y NO por los cambios de hoy
(`git diff HEAD -- bot/` vacio — el motor no se toco):
  bot/test_squad_smoke.py:50        AssertionError: cap!
  bot/test_squad_stocks_smoke.py:43 AssertionError: cap breach
Ambos afirman `len(units) <= 2` — el valor del CHARTER. El codigo corre
con `seeds_crypto.MAX_POS = 3` y `seeds_stocks.MAX_POS = 4`. Estado
actual: `h_nearhi_168` tiene 3 posiciones; `s_macd_12_26`, `s_calm_7_33`,
`s_nearhi_33` y `s_rand_21` tienen 4 cada uno.
Los tests son un cable trampa que codifica el charter y lleva semanas
disparandose sin que nadie lo viera. Esto es exactamente el "hecho
consumado" que la entrada del 2026-08-11 dejo por escrito, ahora con
evidencia mecanica de que el sistema se sabe fuera de norma.
Ademas: `pytest` NO esta instalado en el `.venv`, asi que los tests solo
corren invocando cada archivo a mano. Eso explica que nadie los viera.
Accion propuesta (T3, higiene, sin efecto sobre veredictos): anadir la
ejecucion de los smoke tests al ciclo diario para que un fallo sea
visible el mismo dia, en vez de acumularse en silencio.

**2026-08-22 · CALENDARIO: decision de topes de posicion fijada al 2026-09-21 (30 dias).**
Las dos propuestas del 2026-08-11 (cripto 3→2, acciones 2→4) siguen sin
resolver. No se resuelven hoy: `ops/counterfactual.py` acaba de empezar a
producir el unico dato que las responde de verdad, y 955 filas siguen
PENDING. Decidir hoy es adivinar; decidir con el contrafactual maduro es
decidir. Insumo requerido en esa fecha: contrafactual con >=80% resuelto.
La direccion sigue siendo ratchet — el numero de acciones (4) esta por
encima del charter y la carga de la prueba la tiene quien quiera
mantenerlo, no quien quiera bajarlo.

**2026-08-22 · APLICADO: `ops/selfcheck.py` + cableado al ciclo diario.**
Los smoke tests ahora corren cada ciclo y dejan `logs/selfcheck.csv`.
Estado actual: 2/4 PASS — los dos fallos de tope siguen ahi, ahora
VISIBLES en cada corrida en vez de en silencio. NO es fatal por diseno:
un test que falla por una discrepancia de gobernanza ya documentada no
debe detener el registro forward, porque eso destruiria evidencia por un
problema que no es de datos. Cuando se resuelvan los topes, hacerlo
bloqueante es cambiar `fatal=False` a `True` en `bot/daily.py`.
`pytest 9.1.1` instalado en el `.venv` (antes ausente — esa era la razon
mecanica de que nadie viera los fallos).
Cableado tambien: `ops/bench_bh.py` y `ops/counterfactual.py`, ambos
`fatal=False`, junto a `bot/diversity.py`.
Bug corregido antes de cablear: `bench_bh` usaba modo APPEND y recalcula
la serie entera en cada corrida — al ejecutarse cada hora habria
duplicado filas indefinidamente. Ahora reescribe de forma idempotente por
pista. Verificado: 3 corridas seguidas -> 506 filas, 0 duplicados.
Ciclo completo `bot/daily.py` ejecutado end-to-end: salida 0, motor
intacto (`squad.py` y `squad_stocks.py` sin una linea modificada).

**2026-08-22 · OPERATIVO: el portal estaba muerto otra vez.**
`ps aux | grep portal/app.py` -> 0 procesos, curl sin respuesta.
Relanzado; HTTP 200 confirmado. Es la segunda vez documentada. Un
proceso que se muere en silencio y que ademas es la unica ventana del
propietario al sistema deberia tener supervision automatica, no una
comprobacion manual que depende de que alguien se acuerde. Pendiente.

**2026-08-22 · APLICADO: `docs/REVISION_INDEPENDIENTE.md`.**
Paquete para revisor NO-Claude, con 5 preguntas concretas ordenadas por
dano potencial, materiales, y una declaracion de conflicto de interes:
el documento lo redacto el sujeto de la revision. Sustituye y amplia la
peticion de `REVIEW.md`, sin respuesta desde el 2026-08-08.
Sigue SIN revisor asignado. Esto no cierra el hueco; solo lo documenta
mejor. Conseguir el revisor es una accion del propietario.

---

**2026-08-22 · PRE-REGISTRO H1: las salidas por señal destruyen valor.**
Escrito HOY, antes de cualquier cambio, precisamente porque es el
hallazgo más tentador de la medición del 2026-08-22 y el que más
fácilmente se convertiría en racionalización si se dejara para después.

**Hipótesis:** en la pista de CRIPTO, las salidas por `exit_kind=signal`
tienen esperanza negativa, y el P&L positivo del escuadrón proviene
sustancialmente de las salidas por `exit_kind=stop`.

**Evidencia que la origina (muestra ya vista, NO cuenta como prueba):**
131 cierres por señal → −102.26 neto. 25 cierres por stop → +2,435.94.
9 de 11 bots con P&L de salida-por-señal negativo. Ventana: 17 días.

**Predicción falsable, fijada AHORA:**
En la ventana 2026-08-23 → 2026-11-21 (90 días, evidencia estrictamente
posterior a esta entrada), sobre un mínimo de **150 cierres nuevos por
señal** en cripto, el P&L neto agregado de `exit_kind=signal` será
**negativo**, y el ratio
`P&L(stop) / (|P&L(signal)| + P&L(stop))` será **> 0.60**.

**Qué la falsifica:**
- Si el P&L de salidas por señal resulta ≥ 0 → H1 es FALSA. El resultado
  de 17 días fue ruido y no se toca el mecanismo de salida.
- Si se acumulan < 150 cierres en 90 días → INCONCLUSA. NO se extiende
  la ventana ni se baja el umbral para forzar un veredicto; se registra
  como inconclusa y se decide entonces si vale una segunda ventana.
- Si el ratio queda entre 0.40 y 0.60 → INCONCLUSA, misma regla.

**Compromisos que se aceptan por escrito, para que no se puedan
renegociar cuando llegue el resultado:**
1. Los umbrales (150 cierres, ratio 0.60, 90 días) quedan CONGELADOS.
   Cambiarlos después de ver el resultado invalida el pre-registro
   entero, y así debe registrarse si ocurre.
2. NO se modifica ningún mecanismo de salida durante la ventana. Un
   cambio a mitad de camino destruye la comparación.
3. Confirmar H1 **no autoriza** eliminar las salidas por señal. Autoriza
   proponer un experimento con nombre nuevo bajo §9.6 — sujeto a la
   declaración del propietario, todavía pendiente.
4. Este pre-registro es de CRIPTO. Acciones no tiene mecanismo de stop,
   así que la hipótesis no es comprobable allí y no se extiende.

**Por qué se pre-registra en vez de actuar:** quitar el mecanismo que
perdió dinero en la muestra observada es, procedimentalmente, idéntico
al camino que produjo el +354% falso. La diferencia entre ciencia y
ajuste no está en la hipótesis, está en si el criterio se fijó antes o
después de ver el resultado. Aquí se fija antes.

**Evaluación:** 2026-11-21. Insumo: `logs/squad_trades.csv` filtrado a
`utc > 2026-08-22`, agrupado por `exit_kind`.

**2026-08-22 · APLICADO: supervisión automática del portal (`ops/com.cryptobot.portal.plist`).**
LaunchAgent con `KeepAlive=true` y `ThrottleInterval=30`. Instalado y
cargado. Verificado empíricamente, no solo por configuración: se mató el
proceso con `pkill -9` y launchd lo relanzó solo (PID 44525 → 44622,
HTTP 200 restaurado en <40s).
Why: el portal se murió en silencio al menos dos veces documentadas, y
es la única ventana del propietario al sistema. Su muerte no produce
ninguna señal — los bots siguen operando y los logs siguen creciendo,
solo que nadie puede verlo. Depender de que alguien se acuerde de hacer
curl no es supervisión.
DELIBERADO: no toca el motor. Si el portal cae, el registro forward
continúa. El portal es observación, no ejecución.

**2026-08-22 · MEDICIÓN: cuánto de los −965.74 de ACCIONES era ficción contable.**
Cálculo hipotético sobre las 361 operaciones ya ejecutadas. NO aplica la
propuesta de fricción (efectiva 2026-08-23) ni adelanta su espera — solo
dimensiona el daño para que la decisión de mañana no sea a ciegas.
Notional total movido (ambas patas): $263,187.31.
   2 bps/pata → coste $52.64    → P&L ajustado  −1,018.38
   5 bps/pata → coste $131.59   → P&L ajustado  −1,097.33
  10 bps/pata → coste $263.19   → P&L ajustado  −1,228.93
  20 bps/pata → coste $526.37   → P&L ajustado  −1,492.11
Lectura: la fricción cero NO era el problema principal de la pista de
acciones. Aun a 20 bps por pata, el coste ($526) es la mitad de la
pérdida ya existente ($966). La pista pierde por la estrategia, no por
el modelo de costes. La corrección de mañana empeora el número entre un
5% y un 55%, pero no cambia el diagnóstico: 25.9% de aciertos con R:R
0.58 no se arregla con un parámetro de fricción.
NOTA: esto NO fija el valor del parámetro. El número concreto debe
elegirse por razonamiento sobre el broker real, escrito antes de
aplicarlo — no seleccionando de esta tabla el que produzca el resultado
más cómodo. Elegir de la tabla sería ajustar a la muestra.

---

**2026-08-22 · DECISIONES DEL PROPIETARIO (Jose Miguel).**

**D1 — Fricción en ACCIONES: APROBADA (opción a).** Parámetro declarado
AHORA, antes de aplicar: **10 bps por pata**. Elegido por razonamiento
(conservador para acciones líquidas de gran capitalización), NO
seleccionado de la tabla de reproceso del 2026-08-22 — elegir de esa
tabla habría sido ajustar a la muestra. Entra el 2026-08-23 según la
espera de §3.1. Dirección: tightening. Consecuencia aceptada:
discontinuidad en las curvas de acciones el día que entre.

**D2 — §9.6: un mecanismo nuevo de salida SÍ es mutación de parámetro
(opción a).** Lectura estricta. Consecuencias vinculantes:
  - `Bracket` y `TrailStop` NO pueden añadirse a bots existentes.
  - Cualquier bot con mecanismo de salida nuevo requiere NOMBRE NUEVO,
    pre-registro, y examen propio contra el contador K global.
  - Un nombre ya examinado no puede reexaminarse (charter).
Dirección: tightening. Justificación registrada: si esta lectura resulta
demasiado rígida, aflojarla después es un cambio deliberado con espera;
al revés no se puede deshacer.

**D3 — Pista de ACCIONES: REDISEÑO (opción c).** Queda DESBLOQUEADA por
D2 pero ESTRICTAMENTE CONSTREÑIDA por ella: todo bot del rediseño es un
nombre nuevo con pre-registro y examen propio. No se recicla ningún
nombre existente, no se "arregla" ningún bot actual.
REQUISITO PREVIO: especificación escrita antes de tocar código —
familias, número de bots por familia, universo, mecanismo de salida,
riesgo/beneficio, partición de datos. Sin spec no se escribe código;
esa es precisamente la falla que produjo 20 variantes de una sola idea.
Los 11 bots actuales de acciones siguen corriendo como línea base hasta
que el rediseño tenga veredicto propio. No se apagan.

**D4 — Revisor independiente: PENDIENTE.** El propietario propuso usar
Claude Fable como revisor. ADVERTENCIA REGISTRADA: Fable es un modelo de
Anthropic, del mismo linaje que la instancia que produjo todo el trabajo
del 2026-08-22. Usarlo NO resuelve la circularidad — es el mismo sistema
con más capacidad, y `REVIEW.md` ya rechazó exactamente esta sustitución
el 2026-08-08. Puede encontrar errores técnicos reales (lookahead, sesgo
en el contrafactual, bugs) y por eso se procede, pero se registra como
**segunda opinión**, NO como revisión independiente. El hueco de
gobernanza sigue ABIERTO. Cualquier veredicto que produzca Fable debe
anotarse en el ledger con la etiqueta `NO-INDEPENDIENTE`.

---

**2026-08-22 · PENDIENTES ABIERTOS AL CERRAR LA SESIÓN. No se pierden por esperar.**

**PEND-1 — D1 NO ESTÁ IMPLEMENTADA. Requiere acción manual el 2026-08-23.**
Error de comunicación registrado: se le dijo al propietario que la
fricción "entra sola mañana si no la cancelas". **Es falso.**
`bot/squad_stocks.py:47` sigue diciendo `Q.FEE_TAKER = 0.0` y no existe
ningún mecanismo programado que lo cambie. Una decisión escrita no es
una implementación.
Acción requerida el 2026-08-23: `Q.FEE_TAKER = 0.0010` (10 bps/pata,
declarados en D1 antes de conocer su efecto). Y actualizar en paralelo
`FEE["stocks"]` en `ops/bench_bh.py`, o el benchmark queda con ventaja
sobre los bots — comparación inválida.
NO se aplica hoy: la espera de §3.1 vence mañana, y saltarla el mismo
día que se escribió es precisamente la P5 pre-registrada.

**PEND-2 — `MAX_CORR=0.70` vs `MAX_POS=6` sigue sin resolver.**
Cero carteras válidas de 6 activos existen bajo ambas reglas
simultáneamente. Arrastrado desde 2026-08-11, no se tocó hoy. No es
urgente en la práctica (`MAX_POS` real es 3 en cripto y 4 en acciones),
pero es una regla del charter que el sistema no puede satisfacer, y una
regla insatisfacible es una regla muerta.

**PEND-3 — La especificación del rediseño de acciones (D3) no existe.**
D3 aprobó el rediseño; no aprobó ningún diseño concreto. Falta: qué
familias, cuántos bots por familia, qué universo, qué mecanismo de
salida (constreñido por D2: nombre nuevo + examen propio), qué
riesgo/beneficio, qué partición de datos.
ORDEN RECOMENDADO: escribir la spec DESPUÉS de la auditoría de ChatGPT.
Si esa auditoría encuentra un problema estructural en el contrafactual o
en el lookahead, la spec cambia de forma. Diseñar 20 bots nuevos antes
de saberlo sería trabajo tirado.

**ESTADO OPERATIVO al cerrar:** bench, contrafactual, selfcheck y
diversity corriendo cada ciclo. Portal bajo `KeepAlive`, relanzamiento
verificado empíricamente. Selfcheck en 2/4 PASS — los dos fallos de tope
son reales y esperados, se resuelven el 2026-09-21. Árbol limpio.
Nada más requiere acción hasta que vuelva la auditoría externa.

---

**2026-08-30 · PEND-1 IMPLEMENTADA (con 7 días de retraso, documentado).**

D1 (fricción realista en acciones) quedó firmada el 2026-08-22 con
espera venciendo el 2026-08-23. No se implementó ese día: no hubo
sesión entre el 22 y el 30. Hoy se aplicó:

- `bot/squad_stocks.py`: `Q.FEE_TAKER` 0.0 → 0.0010 (10 bps/pata).
- `ops/bench_bh.py`: `FEE["stocks"]` 0.0 → 0.0015 (fee + slippage,
  en espejo con el bot, como exigía la propia nota del archivo).

REGISTRO DE HONESTIDAD: los datos de acciones del 2026-08-23 al
2026-08-30 corrieron con fee=0, en contra de la decisión ya firmada.
No se anulan (la comparación bot-vs-bench fue internamente coherente,
ambos a fee cero), pero cualquier lectura de ese tramo debe saber que
subestima costes. A partir de hoy la serie corre con D1 activa.

Verificación: ambos módulos importan sin error tras el cambio.


---

**2026-09-18 · HALLAZGO: la pista CRIPTO lleva ~17 días prácticamente apagada.**
9 de 11 bots fuera: 5 en halt->review (macd 08-11, tsmom 08-12, calm
08-13, donch 08-28, rand 08-31) y 4 BENCHED por −10% desde pico (volbrk
08-24, trend 08-31, nearhi 09-01, cross 09-05). Capital invertido: 89%
(08-09) → 35% (08-29) → 0-9% desde 09-02. Consecuencias:
- El "+4.9% vs +34.1% bench" desde septiembre compara efectivo contra
  mercado, no estrategias contra mercado. Debe leerse así.
- H1 (2026-11-21) se evaluará con muy pocas salidas nuevas si nada cambia.
- Que el control ALEATORIO haya sido detenido por −6%/7d indica que los
  interruptores disparan por ruido al tamaño actual (TV_DAY 2%, altcoins
  con 4-5% de vol diaria). Los interruptores son Tier 1 (solo más
  estrictos): NO se proponen cambios a sus números.
- Se deben 4 autopsias de retiro (charter s8). Ninguna escrita.
- No hubo revisión de sábado entre 08-30 y 09-18 (sin commits).

**2026-09-18 · REPARACIÓN (§3.2, sin entrada previa requerida): `ops/review.py`.**
`bot/squad.py` documenta "resumes at review" pero no existía ningún
camino de código que reanudara: un halt temporal era permanente. Se
añade la herramienta de revisión. No cambia ningún umbral. Guardas con
test de fallo (`ops/test_review.py`, §5.1): solo sábado America/Chicago;
nunca reanuda un BENCHED; todo resume queda en `logs/review_log.csv`.
Añadido a `ops/selfcheck.py`. La reanudación la ejecuta el propietario,
no un LLM. Qué cede Jose Miguel al aceptarla: nada en reglas; asume que
reanudar bots sin ventaja demostrada volverá a pagar comisiones.

**2026-09-18 · REGISTRO P5.** El propietario pidió "hacer todos los
cambios ya". Se aplicó solo lo que §3.2 permite el mismo día (reparación
+ documentos sin efecto). Todo lo demás queda como borrador o propuesta
con su espera. Predicción 5 del charter, funcionando como fue escrita.

**2026-09-18 · INSUMO para la decisión de topes del 2026-09-21.**
Contrafactual ≥98% resuelto (167 PENDING de 9,899). Cripto: ENTER media
+0.82% / mediana −0.68%; SKIP-cap media +3.16% / mediana −0.40%.
Acciones: ENTER −0.08% / SKIP-cap +0.02%. Lectura: el tope no selecciona
mejores señales y las medianas son negativas con o sin tope. No hay
evidencia que sostenga MAX_POS 3/4 por encima del valor del charter (2);
la carga de la prueba (entrada 08-22) no se cumple. Decide el propietario
el 09-21. Advertencia: es descriptivo sobre muestra ya vista.

**2026-09-18 · BORRADOR SIN FIRMAR: `docs/epoch2_prereg_BORRADOR.md`.**
Época 2: 4 candidatos + control, marco diario, tamaño reducido en vez de
interruptores aflojados. Incluye la hipótesis "Set and Forget" como
experimento de gemelos (salida bracket vs señal) y copia de
divulgaciones del Congreso con expectativa pre-registrada de NO batir a
SPY. Sin efecto hasta firma en revisión de sábado.


**2026-10-22 · DECISIÓN DEL PROPIETARIO: cierre de cripto y acciones; el proyecto pasa a futuros.**
Jose Miguel decide detener ambos escuadrones (cripto horario y acciones) y
reorientar el proyecto a futuros (NQ/MNQ, flujo de volumen). Motivo: los
datos y estrategias actuales no son relevantes para futuros. Nada se borra:
estado final congelado en git con la etiqueta `archivo-cripto-acciones-2026-10-22`
y copia de datos no versionados en `~/Projects/archivo/cryptobot-2026-10-22.tgz`.
El job `com.cryptobot.daily` se descarga de launchd (plist movido a
`ops/disabled/`). El portal sigue en pie. Se conserva la infraestructura de
gobernanza (charter, libro de exámenes, bóveda) para reutilizarla en futuros.
Estado al cierre: sin operaciones desde 2026-10-04; el bot aleatorio
lideraba el escuadrón cripto. Datos de futuros: Databento (GLBX.MDP3,
trades con lado agresor), probado el 2026-10-22 con un día de ES por ~$0.62.


**2026-10-22 · DECISIÓN DEL PROPIETARIO: reglas del laboratorio de futuros (v1).**
Jose Miguel fija, con las respuestas de Oscar, las reglas antes de cualquier
backtest. Fuente única: `futures/lab_rules.json` (se publica en la página).
- Instrumento: solo NQ; MNQ fuera.
- Estilo: scalping intradía (segundos a minutos); cierre obligatorio antes del
  fin de sesión; sin swing.
- Sesiones: prioridad Nueva York 9:30–16:00 ET; estudio separado de Asia,
  Londres y resto del overnight.
- Costos: comisiones publicadas por Topstep para NQ + 1 tick de deslizamiento
  por lado; prueba de estrés al doble de deslizamiento.
- Aprobación: reglas de la cuenta Topstep 50K ($3,000 meta, $2,000 pérdida
  máxima al cierre del día, $1,000 límite diario conservado aunque sea
  opcional, 5 NQ máx., consistencia 50%). Se simulan cuentas con arranques en
  fechas distintas; la estrategia debe pasar bastante más seguido que RAND con
  las mismas reglas. El umbral exacto se sella antes de la primera corrida.
- Big trades: umbral por investigación (fijo 70–80 vs relativo por sesión/hora,
  con agrupación de órdenes partidas), no por convención.
- Días de rollo: incluidos; se bajan ambos contratos.
- Noticias: sin entradas de −2 a +5 min en CPI, NFP y Fed (margen mayor en Fed).
Validación de datos previa: ATAS vs Databento TBBO en 2024-05-14 y 2026-09-14
(volumen 0.04% / 17 contratos; libro 99.8% / 100%). ATAS aceptado como base.
Pendientes: segundo contrato en días de rollo y marca de sesiones con huecos.
A partir de hoy, cada hallazgo o avance se agrega a `futures/updates.json` y
se publica en la página para Oscar.


**2026-10-22 · REGISTRO: examen final sellado con cifrado.**
132 sesiones NQ (2026-04-22 a 2026-10-22), el manifiesto completo y la referencia
Databento 2026-09-14 se cifraron en rt-oscar-lab:/srv/lab/data/sealed/
(AES-256-CBC, PBKDF2 200000). SHA-256 del archivo:
354e2b451c2d07664edfbe6756eff632aea0f0720d16c5b0d49489dca7b7f0b9.
Verificado: el archivo descifra y contiene los 134 elementos esperados antes de
borrar las copias planas. La llave vive fuera de la VM, en la Mac del propietario
(~/.radtak/lab-seal/), y se usa solo para el veredicto final. En raw/NQ quedan
595 sesiones de diseño (2024-01-02 a 2026-04-21), en solo lectura.
Nota: la laptop de descarga conserva los originales sin cifrar; el laboratorio
no tiene acceso a ella. La comparación ATAS-Databento del 2026-09-14 tocó un
día de la ventana sellada solo para validar datos (volumen), no para diseño.

## 2026-10-22 · Estrategias v1 registradas (BIG, ABS, POC)

Archivo `futures/strategies/v1.json`, SHA-256 `73abb571d6bab88af6775e65c925157e5fbafcaaa11c3921418767e2e2c3d229`. Congeladas antes de cualquier prueba: no se modifican; todo cambio es v2 y cuenta como otro intento. Se prueban solo en el periodo de diseño (2024-01-02 a 2026-04-21) contra RAND emparejado. El examen sellado solo se abre con una versión aprobada por Jose Miguel y Oscar.

## 2026-10-22 · Plan de investigación NQ v1 registrado

Archivo `futures/research_plan.json`, SHA-256 `5387f568a734f5eda8ac2f2d400a888486284ca89b8ccd067dd262c6cc26ac22`. Fase 1 mapa de 12 señales contra momentos al azar; Fase 2 estrategias de 3 en 3 (tanda 1 = BIG, ABS, POC v1); Fase 3 comité y examen sellado. Máximo 3 versiones por estrategia; toda prueba numerada y publicada. Registro de pruebas en `futures/tests.json`.

## 2026-10-22 · Infraestructura completa antes de la primera prueba (sesión Fable)

Jose Miguel aprobó construir toda la infraestructura del laboratorio antes de correr una sola prueba, para que ningún resultado llegue sin su receta, su registro y su hoja. Quedó así:

- **Costos fijados con cifra** (`futures/costs.json`): NQ $3.78 por ida y vuelta (verificado en el centro de ayuda de Topstep el 22/10/2026) + 1 tick por lado; estrés 2 ticks; curva 0–4.
- **Reglas Topstep verificadas** (`futures/topstep_rules.json`): MLL $2,000 trailing al cierre, vigilado en tiempo real con P&L no realizado, se congela al llegar al balance inicial; consistencia oficial 55% (el laboratorio mantiene 50%, más estricto); DLL $1,000; 5 contratos; $10 por liquidación.
- **Protocolo estadístico** (`futures/protocol.json`, SHA-256 `dad6c111…7b7a`): RAND emparejado con 1000 corridas y semilla por SHA-256; p ≤ 0.05; largo mínimo 100 operaciones / 120 sesiones; criterios de muerte declarados; registro de intentos de solo agregar; DSR con la cuenta total de intentos; Holm sobre las 48 pruebas del mapa; CPCV 6 grupos; placebos (desplazado, barajado) y curva de costos.
- **Lista congelada de sesiones** (`futures/sessions_manifest.json`, SHA-256 `2bd01ecb…c571`): 576 válidas de diseño, 19 excluidas (9 rollos sin segundo contrato, 7 huecos ≥ 120 s en Nueva York, 3 sin sesión de Nueva York). 0 fallos de horario de verano.
- **Bot con la "regla de Oscar"**: se retira definitivamente. Jose Miguel aclaró que fue contexto suyo al inicio de la conversación, no una regla de Oscar.
- **v1 es el intento ingenuo**: los números de BIG, ABS y POC v1 no salen de los datos; se corren igual porque ya están congelados, y se dice así en la página.
- **Sellos OpenTimestamps** sobre v1.json, research_plan.json, protocol.json, sessions_manifest.json, costs.json, topstep_rules.json, lab_rules.json y news.json (archivos .ots junto a cada uno).
- **Motor** `futures/lab/engine/` (versión 1.0.0), 9 pruebas unitarias; prueba de humo con 60 sesiones correcta.
- **Estudios registrados antes de correr**: `mapa_v1` (48 intentos declarados) y `tanda1` (51: 3 pruebas + 48 de sensibilidad).
- `docs/` de la época cripto pasa a `docs/archivo/`; nuevo `docs/README.md` del laboratorio NQ.

## 2026-10-23 · Red Team antes de publicar: primera corrida marcada como error

La primera corrida completa (mapa de señales + BIG v1 = P013) reveló dos fallas de programa, no de estrategia:
1. El percentil 99 de tamaño de orden se calculaba sobre **todas** las órdenes agresivas (casi todas de 1 contrato), así que "orden grande" quedó en 15 contratos.
2. El percentil agrupado guardaba solo las 200 órdenes mayores por sesión y, al pedir un rango fuera de lo guardado, devolvía el mínimo en vez de fallar: "absorción" quedó en 249 contratos por minuto (el p95 real ronda 1,300).
Además, en el mapa, iceberg y momentum no producían eventos y los niveles vecinos contaban el mismo momento varias veces.

Decisión: P013 y el mapa corrida 1 quedan en el registro como **error** (se agregan líneas de corrección; nada se borra ni se edita). La población de los percentiles queda aclarada en `futures/strategies/v1_aclaraciones.json` (órdenes de 10+ contratos; sellado con OTS, SHA-256 `7bfee375…77dc`). El programa ahora se detiene si el percentil pedido no cabe en lo guardado. El mapa reporta p de dos colas y el sentido (a favor / contraria), porque una señal que se comporta al revés de lo que dice su hipótesis es información útil. Todo se repite.

## 2026-10-23 · Protocolo v2 (motivo escrito) y primeros resultados reales

- **ABS v1 (P003)**: gana a RAND (p = 0.002), neto +$4,641 con costos base y +$2,505 con costos al doble, 6.4% de cuentas Topstep pasan (RAND 0.2%). Pero el placebo desplazado 5 min gana +$7,753: el valor está en el nivel y la dirección, no en el momento. Con el protocolo v1 habría sido "error" automático. **Protocolo v2** (SHA-256 `b4f30dc2…2a1e`, sellado; v1 guardado en `futures/protocol_v1.json`): sospecha → "revisar" hasta una revisión de código registrada. P003 queda en "revisar" con línea de corrección en el registro.
- **BIG v1 (P002)** con la población correcta (órdenes de 10+): no pasa.
- **Mapa corrida 2**: 0 significativas, y no por los datos sino por la resolución: con 1,000 sorteos el p mínimo de dos colas es 0.002 y Holm pide < 0.00125. Protocolo v2: 5,000 sorteos y z-score publicado. Se repite (corrida 3).
- Regla aprendida y anotada: una "prueba de fuga" que castiga señales de nivel no es prueba de fuga. La revisión de código del Red Team con IA se hace antes del comité y se registra aquí.

## 2026-10-23 · Revisión de código de ABS v1 (P003) · Red Team

Revisado `futures/lab/engine/strategies/v1.py::absorption` y `sim.py` línea por línea buscando fuga de futuro:
- La ventana de 60 s que detecta la absorción usa solo celdas hasta el instante e; el extremo y el precio inicial salen de esas mismas celdas.
- La ubicación compara contra niveles del día anterior y de la noche (ambos anteriores a las 09:30).
- La confirmación en la celda f usa el delta de la ventana que termina en f y el mínimo/máximo de f; la señal se fecha al FINAL de f.
- El simulador llena en la mejor oferta contraria del último llenado anterior a la señal, más 1 tick. No hay ningún índice que mire adelante.
**Conclusión: sin fuga de futuro.** El placebo desplazado gana más porque entra 5 min antes, más cerca del extremo absorbido, y la vuelta se da igual: el valor de ABS está en el nivel y la dirección.
Hallazgo menor: el parámetro `confirm_s` no estaba conectado en el código (siempre 60 s, que es el valor de la v1): el resultado principal es correcto; la fila `confirm_s` de la superficie de sensibilidad de P003 no vale. Código corregido para versiones futuras.

**Veredicto final de P003 (ABS v1): no pasa.** Gana a RAND (p = 0.002), sobrevive 2 ticks por lado, 12 de 15 caminos CPCV positivos, meseta en `near_ticks` y mejora con más objetivo (`rr`), pero pierde en 2025 (−$405) y solo 6.4% de las cuentas Topstep pasan con 1 contrato (ninguna rompe el MLL; 484 de 517 no llegan a la meta en 120 sesiones) porque hay solo 128 operaciones en 576 sesiones. Además el 67.7% de la ganancia viene de 5 días. Es la estrategia más prometedora de la tanda 1 y la única con ventaja real sobre el azar.
Ideas para una eventual v2 (NO se implementan hasta que Oscar y Jose Miguel lo aprueben): entrada más temprana (lo que sugiere el placebo), más horas de operación para tener más operaciones, objetivo más amplio (la sensibilidad muestra que 2.5–3× riesgo gana más), y revisar por qué `prev_vah` y `prev_low` no aportan.

## 2026-10-23 · Incidente de sincronización y regla nueva

El `push` Mac→VM copiaba también `tests.json`, `updates.json` y `signal_map.json`, y pisó dos veces las fichas y la bitácora que el motor había escrito en la VM. Nada se perdió: la fuente de verdad son `results/<id>/report.json` (ficha completa de cada prueba) y el registro (cadena de huellas, correcciones incluidas). Se agregó `engine/rebuild_tests.py`, que reconstruye `tests.json` y las entradas de bitácora desde esas fuentes aplicando la última corrección de cada prueba. Regla: la VM escribe `results/`, `registry/` y `signal_map.json`; la Mac es dueña de `tests.json` y `updates.json` y los reconstruye en cada `pull`. El `push` ya no manda archivos de estado.

## 2026-10-23 · Tanda 1 cerrada y mapa de señales v1 publicado

- P002 BIG v1: no pasa (−$2,120, p 0.41). P003 ABS v1: no pasa pero con ventaja real (ver revisión arriba). P004 POC v1: no pasa (−$3,934, p 0.58). P013: error (umbral). Las 3 estrategias v1 van al cementerio con causa escrita; ninguna va al comité.
- Mapa v1 (5,000 sorteos, Holm): 38 de 48 pruebas distintas del azar. Órdenes grandes: el precio va 6–7 ticks EN CONTRA de la orden a 5, 15 y 30 min (sentido contrario; 19,255 eventos). HVN del día anterior: rechazo de +9 ticks a 15 min y +17 a 30 min (2,561 eventos). Absorción: +3.7 / +6.1 ticks a favor en bruto a 15 y 30 min, pero por debajo de un momento al azar de la misma media hora con la misma dirección. Icebergs: 17 eventos con la definición actual (rarísimos). Momentum apertura→cierre: sin prueba válida con este diseño (el azar no tiene dispersión).
- Candidatas para la tanda 2 (se diseñan y congelan SOLO con Oscar y Jose Miguel): desvanecer órdenes grandes (hipótesis inversa de BIG), rechazo de HVN del día anterior, y ABS con entrada más temprana y más horas.
- Intentos registrados al cierre: 109 (mapa 48 declarados / 48 usados; tanda 1: 51 declarados / 52 usados → marcado "excedido" en la página, por la repetición de BIG tras el error de umbral).

## 2026-10-23 · Orquestador, backlog, LAB.md y Red Team ciego (propuesta de Jose Miguel)

Jose Miguel pidió: un MD del proyecto que se mantenga al día, una lista de pruebas futuras con arranque automático, y que cada prueba empiece "sin información" para que nada nos engañe. Quedó así:
- **`LAB.md`** en la raíz: estado completo en una página, generado por `portal/build_lab_md.py` en cada construcción de la página. Nadie lo edita a mano. `CLAUDE.md` apunta a él para cualquier sesión nueva.
- **`futures/backlog.json`**: cola de pruebas con estados `propuesta → aprobada → congelada → corrida`. Las candidatas de la tanda 2 (desvanecer órdenes grandes, rechazo HVN, ABS con entrada temprana / más horas, icebergs con mejor definición, mapa v2 con dirección aleatoria, SMT bloqueada por datos de ES) entran como **propuesta**: nadie las corre hasta que Oscar y Jose Miguel las aprueben y se congelen con sello.
- **Orquestador** (`engine/orchestrator.py`, cron cada 15 min en la VM): toma la primera prueba `congelada`, clona el commit exacto desde un espejo git local, verifica estudio/sello/lista de sesiones, y la corre en un **contenedor Docker efímero** (`--rm`, sin red, datos en solo lectura, sin acceso al registro ni a resultados previos). La corre **dos veces** y solo publica si `trades.csv` es idéntico bit a bit; el registro se escribe fuera del contenedor. Se eligió contenedor efímero en vez de recrear la VM: lo que puede engañarnos es el estado acumulado (cachés, parámetros tocados, código sin commit), no los datos, y el contenedor elimina exactamente eso en segundos sin volver a copiar 8 GB.
- **Red Team ciego** (`engine/redteam_pack.py`): paquete con la regla congelada, el código, el protocolo y los resultados, más un prompt para un Claude sin contexto cuyo único trabajo es encontrar cómo el resultado podría engañarnos. Los informes van a `docs/redteam/<id>.md`. Obligatorio para toda prueba que pase o quede en "revisar".
- La VM escribe `results/`, `registry/`, `signal_map.json` y `runs/state.json`; la Mac es dueña de `tests.json`, `updates.json` y `backlog.json` y los reconstruye en cada `pull`.

## 2026-10-23 · Mejoras de infraestructura (segunda ronda, aprobadas por Jose Miguel)

- **Prueba dorada** (`engine/golden.py`, `futures/lab/golden.json`): ABS v1 sobre 60 sesiones debe dar siempre la huella `119421551a85aad1` (15 operaciones). El orquestador la corre en contenedor antes de cada prueba; si difiere, no corre nada. Cambiar el motor a propósito = `--update "motivo"` + commit.
- **Régimen de mercado** (`engine/regime.py`, reglas fijas elegidas antes de mirar resultados): 275 sesiones de tendencia / 301 de balance; 278 alta / 278 baja volatilidad; 71 con noticias; 201 abren dentro del valor. Toda hoja de resultados reporta por régimen. Primer hallazgo: POC v1 pierde −$7,776 en tendencia y gana +$3,841 en balance; ABS v1 gana en ambos y más con volatilidad alta.
- **Manifiesto de datos canónicos** (`futures/canonical_manifest.json`): SHA-256 y tamaño de los 576 parquet. El contenedor verifica tamaños de todos y huella de 30 al azar antes de correr.
- **Los ojos de Oscar** (`engine/oscar_sample.py`): 30 operaciones por prueba (10 mejores, 10 peores, 10 al azar) en CSV y en la página con replay; Oscar marca "si/no" y el acuerdo se publica. Muestra de P003 lista.
- **Agenda del comité** (`docs/comite/agenda_actual.md`, generada en cada construcción): qué corrió, qué murió, qué está propuesto, qué falta de Oscar, lo más fuerte del mapa.
- **README del motor** (`futures/lab/engine/README.md`): cada decisión de diseño con su motivo.
- **Avisos** (`engine/notify.py`): correo por Resend al terminar cada prueba del orquestador; requiere `/srv/lab/notify.json` en la VM con llave, remitente y destinatarios (pendiente: Jose Miguel decide a qué correos).
- **Estabilidad del mapa** (2024 vs 2025 por señal) queda programada para la próxima corrida del mapa (mapa_v2).

## 2026-10-23 · Estudio de salidas (pedido de Oscar) · 159 intentos registrados

Oscar pidió explorar take profit fijo (20/30/40/50 puntos), distintos stops, y agregar contratos cuando la operación va a favor. Se corrió como estudio registrado `salidas_v1` sobre las mismas señales v1 (el simulador ahora sabe piramidar: `Rules.pyramid`, con prueba sintética). Resultados (superficie completa en la pestaña Pruebas):
- **ABS**: con el stop v1 (o 8 pts), el neto sube de forma monótona con el TP: +$4,641 → +$6,674 (30) → +$8,569 (40) → +$9,928 (50) con 15 min de tenencia. El TP casi no se toca: **trabaja la salida por tiempo**. Aguantar hasta las 11:45 empeora (+$7,058 con TP 50). Stops de 3–4 pts la matan. Piramidar pierde (−$1,116 a −$4,062): es reversión, no tendencia. Hay meseta TP 30–50 × stop v1/8 → candidata **T2-ABS-RUN** (propuesta, requiere protocolo completo; aciertos caen a 25–30%, vigilar concentración).
- **BIG**: solo TP 40 gana (+$835 a +$2,125); 30 y 50 pierden → pico aislado. Piramidar ayuda poco (+$676 / +$1,247).
- **POC**: negativa casi en todo; celdas positivas aisladas (TP 50 con stop 3–4; v1 hasta el cierre +$2,136).
Regla aplicada: nada de esto es un veredicto. Las celdas no tienen RAND, costos al doble, Topstep ni placebos. El DSR de cualquier v2 descontará estos 159 intentos.

## 2026-10-23 · "Adelante": mapa v2 y tanda 2 escrita y sellada

- **Mapa v2** (estudio `mapa_v2`, 72 intentos declarados, aprobado por Jose Miguel como cambio de método): azar con dirección aleatoria (¿la dirección es rentable por sí sola?), estabilidad 2024 vs 2025 por señal, partición por régimen (tendencia/balance, 24 pruebas con Holm aparte) y desglose descriptivo por media hora. El mapa v1 queda guardado en `futures/signal_map_v1.json`. Una corrida de humo (30 sesiones, 200 sorteos) registró 12 intentos por error; quedan marcados con línea de corrección y se agregó `--dry`.
- **Tanda 2 escrita y sellada** (`futures/strategies/v2.json`, SHA-256 `d2145d6d…44fd`, OTS; código `engine/strategies/v2.py`): FADE v1 (desvanecer órdenes grandes: stop 16 ticks, sin objetivo, 15 min), HVN v1 (rechazo de nodos ≥ p90 de ayer tras ≥ 20 ticks lejos: stop 12, objetivo 16, 30 min), ABS v2 (objetivo 40 puntos = salida por tiempo). Los números salen del mapa v1 y del estudio de salidas. En el backlog quedan como **propuesta**: el orquestador no las corre hasta que el comité las pase a congelada. Estudio `tanda2` registrado (51 intentos declarados).
- El motor ahora resuelve (estrategia, versión) → archivo y código; el orquestador busca la versión en cualquier `v*.json` sellado.
- **Humo de la tanda 2** (60 sesiones, `--dry`, sin registrar): FADE −$13,518 (194 op.), HVN −$2,288 (145 op.), ABS v2 +$1,639 (20 op.). FADE preocupa: el efecto promedio del mapa (6–7 ticks) no cubre stop + costos; se avisa al comité antes de aprobar. Cambiar sus números sería FADE v2.

## 2026-10-23 · Mapa v2 publicado (48 + 24 pruebas, 5,000 sorteos)

- **Dirección rentable por sí sola** (azar con dirección aleatoria, p bruto a 30 min): solo **desvanecer órdenes grandes** lo es (p 0.0016). HVN p 0.025 (sugestivo, no sobrevive Holm con 48). El resto: la dirección no gana sola; lo que hay es momento relativo a la media hora.
- **Estables 2024 vs 2025** (mismo signo a 15 min): órdenes grandes, divergencia de delta, ruptura del rango inicial, HVN, desequilibrio del libro. **No estables**: absorción, desequilibrios apilados, agotamiento, área de valor, ráfagas, momentum.
- **Por régimen (r30, Holm aparte)**: órdenes grandes revierten en balance (−13.5 ✓) y casi nada en tendencia (−0.1 ✓). HVN rechaza en balance (+53 ✓) y FALLA en tendencia (−22 ✓). Absorción: +24 en tendencia ✓, −12 en balance ✓ (al revés de lo esperado). Ruptura del rango inicial: +38 en tendencia ✓, nada en balance.
- **Advertencia registrada**: el régimen de un día se conoce al cierre. Partir resultados por régimen es diagnóstico; condicionar una estrategia a él en vivo sería fuga de futuro. Para eso hace falta un proxy conocido en tiempo real (rango de apertura, migración del valor), que sería una prueba aparte.
- Consecuencias para la tanda 2: FADE tiene la única dirección rentable en bruto pero el humo dice que stop 16 + sin objetivo no lo captura; HVN depende del régimen (bueno en balance, malo en tendencia) y en promedio sale +17 a 30 min. El comité decide con esto en la mano.

## 2026-10-23 · Hallazgo mayor del Red Team: el mapa medía desde un precio no operable

Al preparar FADE (desvanecer órdenes grandes) el simulador perdía (−$10k en 60 sesiones) mientras el mapa decía +6–7 ticks a favor. La discrepancia tenía dos causas, ambas de programa:
1. **Simulador**: una orden grande ejecuta todos sus llenados en el mismo instante y ATAS deja el libro "después" congelado en el valor previo al barrido; el simulador entraba con ese libro (hasta 19 ticks peor que el real) y luego "sufría" el propio barrido. Corregido: la entrada usa el libro **antes del primer llenado posterior** a la decisión; señales de FADE y BIG fechadas después de la orden. Golden actualizada con motivo (`885b6df1…`, 14 operaciones).
2. **Mapa**: medía desde el **último llenado** del barrido, que queda ~8 ticks atrás del libro real. Medición directa (1,254 eventos, 100 sesiones): desde el último llenado +2.2 ticks a 5 min "a favor de desvanecer"; desde el libro que uno pagaría **−6.6 ticks** (el precio sigue en la dirección del barrido); desde el mid −5.0. "Desvanecer órdenes grandes" era un artefacto. Corregido: el mapa mide desde el mid del libro operable (`mid_at`). Se repite como **mapa v3** (72 intentos declarados); el v2 queda en `signal_map_v2.json` como registro del error.
Decisiones: FADE v2 y FADEL v1 quedan **descartadas antes de correr** (cementerio con causa; no se gastan 34 intentos en una premisa falsa). HVN v1 y ABS v2 siguen congeladas y el orquestador las corre con el motor corregido; sus premisas se re-verifican con el mapa v3. T2-ABS-RUN había arrancado con el motor viejo y se detuvo a mano antes de publicar (anotado en orchestrator.log).

## 2026-10-23 · Proxy de régimen en tiempo real: resultado negativo

Estudio `proxy_v1` (1 intento): a las 09:45, con el rango y el cuerpo de los primeros 15 min, la apertura dentro/fuera del valor y la distancia al VWAP, no se anticipa el régimen del día. Base 48% de días de tendencia; el mejor proxy (distancia al VWAP) llega a 56.8% en su tercil extremo (criterio de muerte: < 15 puntos sobre la base); apertura fuera/dentro del valor 49.3% vs 45.6%. Conclusión: la partición por régimen sigue siendo diagnóstica, no operable; HVN se evalúa pura. Resultado completo en `futures/regime_proxy.json`.

## 2026-10-23 · Publicación automática y cierre del ciclo

`futures/lab/publish_vm.sh` (cron en la VM, minutos 5 y 35): trae registro, resultados y mapa al clon de GitHub, reconstruye fichas y página, y hace push; Vercel despliega. Requiere que Jose Miguel agregue la deploy key de la VM (con escritura) en GitHub › cryptobot › Settings › Deploy keys. Hasta entonces el push falla en silencio y se publica a mano. Regla nueva para la Mac: `git pull` antes de trabajar, porque la VM también hace commits.

## 2026-10-24 · Primeras pruebas corridas por el orquestador solo + mapa v3

El orquestador corrió ABS v2 y HVN v1 sin intervención: clon limpio del commit `90f148ae`, golden verificada, dos contenedores sin red cada una, `trades.csv` idéntico, registro fuera del contenedor. ~10 minutos por prueba.
- **P005 ABS v2**: +$8,869, p 0.003, estrés +$6,389 (p 0.0066), 14/15 CPCV, Topstep 43.5% (RAND 3.5%). Revisión de código (mismo código que P003 + objetivo fijo): sin fuga. **No pasa**: Topstep < 50%, 72% de la ganancia en 5 días, y la ganancia es de 2024 (+$8,888; 2025 +$140; 2026 −$159). El mapa v3 marca la absorción como no estable entre años: coherente. ABS tiene una versión más; no gastarla hasta entender 2025.
- **P006 HVN v1**: −$30,239, 1,460 operaciones, 0/15 CPCV, pierde los tres años. Cementerio. Causa de raíz: la premisa salía del mapa v2 medido desde el último llenado; en el mapa v3 (precios operables) los nodos de ayer no rechazan (−11.8 ticks a 15 min).
- **Mapa v3** (72 intentos): desde el mid del libro operable, las **órdenes grandes se siguen** (+11.7 / +12.4 / +12.2 ticks a 5/15/30 min; p bruto 0.0004; estable; +18.7 en tendencia y +5.4 en balance). Es la inversa exacta de lo que decía el v2, y explica por qué FADE perdía. Absorción: +8 a 30 min bruto pero "contraria" (peor que un momento al azar de la media hora) y no estable. Ruptura del rango inicial: +17.8 a 30 min (+38.6 en tendencia), estable, p bruto 0.21 (pocos eventos). Lo demás, cerca de cero.
- Nueva propuesta **T3-BIG2** (seguir la orden grande con entrada inmediata, objetivo 12, stop 16, 10 min). Pendiente del comité; sería BIG v2 de 3.
- Lección registrada: toda señal del mapa v1/v2 que se haya convertido en regla debe re-verificarse contra el v3 antes de gastar intentos. Las reglas de la tanda 2 se escribieron con el mapa viejo; solo ABS v2 sobrevivió porque su premisa no dependía del precio del último llenado.

## 2026-10-24 · Tanda 3 congelada (BIG v2 y ORB v1) · "apruebo que tomes los que puedas"

Jose Miguel delegó los pasos que Claude pueda tomar solo. Con esa aprobación (Oscar informado) quedan selladas en `futures/strategies/v4.json` (SHA-256 `edc0cd12…`, OTS) y congeladas en el backlog, estudio `tanda3` (34 intentos declarados):
- **BIG v2**: seguir a la orden grande, entrada inmediata, sin filtro de nivel ni confirmación, objetivo 12, stop 16, 10 min. Premisa del mapa v3 (+12 ticks, estable, p bruto 0.0004). Versión 2 de 3 de BIG.
- **ORB v1**: ruptura del rango de los primeros 15 min, 16/16, 30 min, una vez por lado y por día. Premisa del mapa v3 (+17.8 a 30 min, estable).
Humo (60 sesiones de 2024, `--dry`, sin registrar): BIG v2 −$1,916 (327 op., p 0.03), ORB −$401 (77 op.). El orquestador decide con las 576 sesiones.
Lo que Claude no puede hacer solo y queda en manos de Jose Miguel: deploy key de la VM en GitHub (publicación automática), correos de avisos, revisión ciega de P005 en una conversación nueva, datos de ES y segundos contratos de rollo, exportaciones semanales nuevas de ATAS (ventana viva), y pasarle a Oscar las muestras de P003 y P005.
