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
