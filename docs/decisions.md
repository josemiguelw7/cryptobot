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
