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
