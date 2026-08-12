# Roadmap — stolen shamelessly, adapted deliberately

**Status:** PROPOSAL backlog. Nothing here is scheduled until it gets a
`docs/decisions.md` entry (charter v2 §3.1). Items marked **T1-guard**
touch money-adjacent machinery and get the §3.3 treatment.
**Written:** 2026-08-08, from a survey of pysystemtrade, freqtrade,
vectorbt, nautilus_trader, purged-cross-validation, Allocate Smartly,
Riskfolio-Lib/OptimalPortfolios, quantstats, and microsoft/qlib, plus
the external-review recommendations of the same date.

Every item states: what we steal, from whom, the exact change, why it
matters *for this project specifically*, effort, and the acceptance
test that proves it works (§5.1: every guard ships able to fail).

Legend — effort: S (< half a day), M (a weekend), L (a wave).
Tier: per charter v2 (T2 = science, adjustable with a logged decision).

---

## Phase 0 — Foundations (do before any new wave)

### 0.1 Continuous integration: the test suite runs on every commit
**Stolen from:** every serious open-source project; freqtrade runs
~2,000 tests per PR.
**Change:** add `.github/workflows/ci.yml` running on every push:
`bot/test_slowclock.py`, `bot/test_stats.py`, `backtest/test_engine.py`,
`backtest/exam_1h.py --selftest`, `ops/lookahead_audit.py --days 7`,
plus a new `bot/test_guards_bite.py` (see 1.4). Red CI blocks merges to
main.
**Why here:** the smoke tests were red on main for days and nobody knew.
The SlowClock freeze shipped inside a bug fix. CI is the cheapest
guard-that-bites in existence.
**Effort:** S. **Tier:** T2 (repair-adjacent, §3.2).
**Acceptance:** push a commit that deliberately breaks SlowClock; CI
must go red. Push the fix; CI must go green.

### 0.2 Move the clock off the sleeping Mac
**Stolen from:** pysystemtrade's production discipline (Carver's runs
on a dedicated machine, 20h/day, with crontab + monitoring).
**Change:** either (a) a ~$5/mo VPS running the launchd jobs as
systemd timers, or (b) GitHub Actions scheduled workflows for the
hourly cycle (free, but minute-level jitter). State syncs via the repo
or a small object store. The Mac becomes a *viewer*, not the engine.
**Why:** missed cycles are already documented (ops findings #1); a
counted-day experiment whose clock stops when a laptop sleeps has a
silent data-quality hole.
**Effort:** M. **Tier:** T2.
**Acceptance:** `/api/meta` shows ciclos 24/24 for 14 consecutive days.

### 0.3 SQLite for state and ledger (CSV/JSON retired from write paths)
**Stolen from:** freqtrade (SQLite trade DB), nautilus (Postgres/
Redis), and our own defect #5 / H-4 (a 21-field row against a 23-field
header).
**Change:** one file `state.db`: tables `ledger`, `void_log`,
`exam_metrics`, `squad_state`, `decisions_log`. Writers use
transactions; schema is versioned with a `schema_version` table.
CSV exports remain for humans (`ops/export_csv.py`) — read-only.
**Why:** rectangularity enforced by the engine instead of by hope;
atomic writes end the torn-row class of bug forever.
**Effort:** M. **Tier:** T2, needs a decisions.md entry (ledger format
is charter-adjacent).
**Acceptance:** kill -9 the process mid-write in a test; the DB must
contain either the whole row or none of it.

### 0.4 quantstats tearsheets in the portal and the Saturday report
**Stolen from:** quantstats (ranaroussi).
**Change:** `ops/tearsheet.py`: feed each bot's counted-day net return
series to `qs.reports.html()`; link the HTML per bot from the portal;
attach the squad-level sheet to the weekly report (M3.2).
**Why:** monthly-return heatmaps and drawdown-period tables answer in
one glance what the current equity CSVs answer only with effort. Zero
methodology risk — reporting only, gates untouched.
**Effort:** S. **Tier:** T2 (report, not gate).
**Acceptance:** tearsheet's Sharpe matches `bot/stats.py` within
rounding on the same series (a free cross-check of our own math).

---

## Phase 1 — Verification (the ledger's bodyguards)

### 1.1 Second engine: vectorbt as a disagreement detector
**Stolen from:** vectorbt; the aviation practice of dissimilar
redundancy.
**Change:** `backtest/xcheck_vbt.py`: for every exam candidate,
translate the seed into a vectorbt signal array (long/flat weights on
the same closes), run the same windows at the same costs, and compare
per-window `ret` and `trades` against our engine. Tolerance declared up
front (e.g. |Δret| < 5 bps/window from fee-timing differences).
Disagreement beyond tolerance **blocks the ledger write** — the exam
does not record until the two engines agree or the difference is
explained in the exam log.
**Why:** C-1 (the frozen SlowClock) would have been caught in the first
window: vectorbt's version would have traded, ours wouldn't, delta huge.
This converts an entire class of engine bugs from "burns a name" to
"blocks a run."
**Effort:** M–L (SlowClock/regime seeds need care to vectorize
honestly; where a seed can't be expressed vectorized, it's flagged
`xcheck: manual` in the ledger rather than silently skipped).
**Tier:** T2, tightening. **T1-guard when it blocks a write.**
**Acceptance:** re-introduce the old frozen SlowClock in a branch; the
cross-check must block the exam.

### 1.2 CPCV holdout: many splits instead of one
**Stolen from:** López de Prado via eslazarev/purged-cross-validation
(mlfinlab went closed-source; this is the maintained open drop-in).
**Change:** criterion 8 evolves from "one reserved 120-day slice"
(which M-2 showed is 1 window/pair — a coin flip) to **combinatorial
purged cross-validation**: partition the 10-year sample into N groups
(e.g. 8), evaluate on every combination of k test groups (e.g. 2) with
purging+embargo at the boundaries so no training window touches test
data. Gate on the DISTRIBUTION: median out-of-sample per-window return
> B&H in ≥60% of the C(8,2)=28 test paths.
**Why:** one holdout answers "did it work in late 2025-26?"; CPCV
answers "does it work in most eras it never saw?" — the question the
charter actually cares about. Also kills the "which 120 days happened
to be the holdout" luck factor in both directions.
**Effort:** M. **Tier:** T2, gate-statistic change → decisions.md entry
with the §3.3 week wait (it changes what PASS means).
**Acceptance:** a seed hard-coded to memorize one era must FAIL CPCV
while passing the old single holdout (build the fixture; keep it in
tests as the canonical overfit specimen).

### 1.3 Cross-check `bot/stats.py` against the reference implementation
**Stolen from:** eslazarev's deflated-Sharpe implementation.
**Change:** `bot/test_stats_xref.py`: on 1,000 random return series,
assert our PSR/DSR/expected-max-SR agree with the library's within
1e-6. Pin the library version.
**Why:** our DSR is now a gate (criterion 10). A gate's math should not
rest on a single implementation — that was C-2's lesson in another form.
**Effort:** S. **Tier:** T2.
**Acceptance:** mutate one constant in our `expected_max_sharpe`
(e.g. Euler–Mascheroni to 0.6); the xref test must fail.

### 1.4 Guard-bite suite + quarterly fault injection (charter v2 §5.5)
**Stolen from:** Netflix's chaos engineering, scaled to one laptop.
**Change:** `bot/test_guards_bite.py` with one deliberately bad input
per guard: a forming bar → loaders must drop it; a dirty tree → ledger
must refuse; a crashing seed → exam must raise (not FAIL); a burned
name → runner must refuse; a VOID without a bug doc → void tool must
refuse; `tail % k != 0` freeze → SlowClock suite must catch. Plus
`ops/inject_fault.py --arm` for the quarterly live drill.
**Why:** six of fifteen review findings were guards that couldn't fire.
This is the standing cure, not the one-time fix.
**Effort:** S–M. **Tier:** T2. **Acceptance:** the suite itself IS the
acceptance; CI runs it (0.1).

---

## Phase 2 — The strategy layer (Carver's playbook, adapted)

### 2.1 Continuous forecasts instead of binary signals
**Stolen from:** pysystemtrade's core design: a forecast is a scaled
number in [-20, +20] (for us, long/flat: [0, +20]), position size is
proportional to forecast × vol target, and forecasts are AVERAGED
across rules rather than switched.
**Change:** add `conviction()` as a first-class exam concept: seeds
already expose it in the engine (E2.2); the exam currently grades only
the binary weight. New seed base class `ForecastSeed` returns a scaled
conviction; `simulate_window_bars` sizes positions by it (capped 1.0).
Wave 5 material — a NEW seed family, examined under the same rules,
never a retrofit of burned names.
**Why:** binary signals whipsaw at the threshold — enter at 1.001×SMA,
exit at 0.999× — and threshold-crossing churn is exactly what the cost
gate keeps rejecting. Proportional sizing turns the cliff into a slope;
Carver's data (and his whole second book) says the smoothing alone is
worth more than most signal improvements at retail cost levels.
**Effort:** M. **Tier:** T2 (new seed family through the front door).
**Acceptance:** turnover of the forecast version of trend_20 measured
at <50% of the binary version's on identical data, same window set.

### 2.2 Position buffering (the no-trade zone)
**Stolen from:** pysystemtrade's `buffered_positions` — Carver only
trades when the target position drifts >10% from the held position.
**Change:** engine-level: `if abs(target - held)/max(held, floor) <
BUFFER: hold`. BUFFER declared per roster, pre-registered, exam and
engine identical (W1.1). Applies to the forecast family (2.1) first.
**Why:** our cost curve says a round trip costs 0.84%; refusing to
trade a 4% position adjustment is free money at that toll. This is the
cheapest churn-killer in the entire survey.
**Effort:** S. **Tier:** T2.
**Acceptance:** on the exam's own recorded windows, buffered trend_20
must show strictly fewer trades AND ≥ the unbuffered median net return
(if it shows fewer trades but worse returns, the buffer is masking a
real signal and the size is wrong — that result is publishable too).

### 2.3 Per-instrument cost budget (speed limit)
**Stolen from:** Carver's "speed limit": max turnover per instrument
set so annual cost drag ≤ ⅓ of expected edge; instruments too costly
to trade at any speed are excluded *before* strategy design.
**Change:** formalize what C0.4 gestures at: `analysis/cost_curve.py`
output becomes a signed per-pair table in `docs/` — max round trips/yr
per pair at our fee tier. The admission pre-check enforces: declared
turnover × pair cost ≤ budget. Pairs whose budget is zero at retail
fees (the memecoins with 10 bps slippage) are struck from rosters
entirely, pre-registered.
**Why:** we keep discovering "the toll is the strategy" one exam at a
time, at K+1 per lesson. A signed cost budget discovers it once, for
free, for every future seed.
**Effort:** S (the analysis exists; this signs and enforces it).
**Tier:** T2, tightening.
**Acceptance:** h3_crossconf (breakeven "never at ≤0.32%/side") must be
rejected by the budget check without burning a name — we already know
the right answer for that fixture.

### 2.4 Walk-forward cadence for the weekly review
**Stolen from:** freqtrade community practice: re-fit nothing, but
treat each live month as the rolling out-of-sample test of the frozen
config, explicitly scored.
**Change:** `ops/oos_scorecard.py` in the Saturday report: for every
armed bot, this week's counted days scored against the exam-time
expectation (median window return, coverage, turnover). Three
consecutive weeks outside the exam's own distribution → automatic
review item (not automatic action — §10 owner rules apply).
**Why:** the squads currently run 90 days before anyone formally asks
"is live behaving like the exam said?" Weekly scoring catches drift —
and engine bugs like C-4 — in days instead of quarters.
**Effort:** S–M. **Tier:** T2 (report + review trigger, no gate).
**Acceptance:** replay the stock squad's forming-bar era through the
scorecard; it must flag the live-vs-exam turnover mismatch by week 2.

---

## Phase 3 — Wave 4: the allocation game (the winnable arithmetic)

### 3.1 Monthly-clock tactical allocation seeds, from published rules
**Stolen from:** Allocate Smartly's tracked-strategy model (40+
published TAA strategies with out-of-sample records), and the specific
public-domain rules they track (e.g. Faber's GTAA/Ivy timing model:
monthly close vs 10-month SMA, long or cash — published 2007, tracked
out-of-sample for 18 years).
**Change:** Wave 4 roster `m4_*` on a MONTHLY decision clock via
SlowClock(k=720-ish on hourly, or a true daily store): e.g.
`m4_faber` (asset > 10-mo SMA → hold, else cash, per asset),
`m4_dualmom` (Antonacci dual momentum: relative momentum picks the
asset, absolute momentum decides asset-vs-cash), `m4_rand` (turnover-
matched control, FAIL pre-registered). Universe: BTC, ETH + the stock
ETFs already stored (SPY/QQQ/IWM), long/cash only, same exam, same
costs, same one-shot names.
**Why:** this is the pivot the project's own arithmetic demands. At a
monthly clock the required accuracy is ~55% and costs are ~0.8%/YEAR.
Critically, these rules have SURVIVED PUBLICATION — Faber's model has
18 years of out-of-sample tracking by third parties. We are no longer
asking "can we invent an edge?" but "does a documented, tracked edge
survive OUR costs and OUR exam?" — a much better-posed question, and
one where a PASS would actually be believable.
**Effort:** M (seeds are ~10 lines each; the work is exam geometry for
monthly windows — WIN/STEP need a decisions.md entry).
**Tier:** T2, full pre-registration ritual: expectations written before
running, d3-style.
**Acceptance:** pre-registered per plan_v3 conventions. Prediction to
write down now: m4_faber beats B&H drawdown in >80% of windows and
still probably FAILS criterion 4 in crypto's up-regime — if so, THAT
result (defense ≠ alpha, formally, on the best-documented rule in the
genre) is the strongest publishable finding the project would have.

### 3.2 Portfolio-level exam (grade the BOOK, not just the bot)
**Stolen from:** Riskfolio-Lib / OptimalPortfolios (allocation math),
Carver (instrument weights as a first-class decision).
**Change:** a second exam track: candidate = a WEIGHTING RULE over
armed seeds (equal-weight, inverse-vol, HRP via riskfolio), examined on
the joint daily return series with the same gates + a correlation
criterion that's actually satisfiable (fixes the M-1/E3.2 impossibility
from the portfolio side instead of the position-cap side).
**Why:** the 0.77-correlation universe means single-seed verdicts
overstate diversification. The book is what actually compounds; it
deserves its own verdict. Also gives the E3.2 correlation cap a home
where it can bind coherently.
**Effort:** L. **Tier:** T2 + one T1-adjacent element (a portfolio
PASS would be the thing that eventually meets the $500 pilot, so gate
changes here get §3.3 treatment).
**Acceptance:** equal-weight over N pure-noise seeds must FAIL; the
same rule over N copies of one seed must be flagged by the correlation
criterion. Both fixtures in CI.

---

## Phase 4 — Agents (judgment jobs only; the ban on AI-in-the-loop stands)

### 4.1 Weekly auditor agent
**Stolen from:** what happened on 2026-08-08, made a habit; qlib's
RD-Agent proves the orchestration is mainstream now.
**Change:** a scheduled Claude session (or Claude Code cron) every
Friday night: pull the repo, run the full test + audit suite, diff
state vs charter numbers, re-read the week's diffs adversarially, write
`docs/review/YYYY-MM-DD_auditor.md` in the established format, flag
anything that smells like a guard-that-doesn't-bite. It NEVER commits
code — it files findings.
**Why:** fifteen findings were sitting in plain sight because re-reading
is boring. Agents don't get bored.
**Effort:** S to stand up. **Tier:** T2 (charter v2 §6.3 already
commits to the cadence).
**Acceptance:** seed one planted defect (from 1.4's fixtures) into a
branch; the auditor's report must find it without being told.

### 4.2 Red-team ritual for every new guard
**Stolen from:** security practice; C-1's core lesson (author-reviewed
fixes miss author-shaped holes).
**Change:** process rule in decisions.md: any PR adding/changing a gate
or guard gets a fresh agent session — no context from the authoring
session — prompted only with the diff and "how does this fail to
constrain?" Its answer is attached to the PR before merge.
**Why:** two independent sessions demonstrably catch each other's bugs;
that's the one mechanism today that worked.
**Effort:** S (it's a ritual, not code). **Tier:** T2.
**Acceptance:** the ritual's paper trail exists on every gate PR after
adoption; spot-audit at weekly review.

### 4.3 Researcher agent for seed proposals
**Stolen from:** qlib RD-Agent's research loop, subordinated to our
governance instead of replacing it.
**Change:** an agent that reads coroner reports, `analysis/` outputs,
and the published-TAA literature, and produces PRE-REGISTRATION DRAFTS:
proposed seed, exact rule, declared hold, cost budget check, expected
failure modes, and the falsifier — in plan_v3's format. A human (Jose)
signs or discards; the deterministic seed goes through admission like
any other. The agent never touches live code or the exam.
**Why:** moves the creative labor to where creativity is safe, and
raises proposal quality — every draft arrives with its own kill
criteria attached.
**Effort:** S–M. **Tier:** T2.
**Acceptance:** first three drafts include at least one the owner
rejects — if everything gets signed, the drafts aren't honest enough.

---

## Phase 5 — The meta-product

### 5.1 Publish the exam as a standalone tool ("the honesty machine")
**Stolen from:** the gap the survey found — nothing on GitHub combines
a backtest engine with burned names, a public K counter, pre-registered
expectations, and bug-evidence-only voids. Nothing.
**Change:** extract `exam/` into its own repo: bring-your-own-seed
(a step function), bring-your-own-data (OHLCV CSVs), get: admission
pre-check, one-shot named exams, K-adjusted luck hurdle, DSR gate,
CPCV holdout, permutation p, append-only ledger, void protocol. Ship
with the guard-bite suite and the two fixture strategies (the
era-memorizer and the noise seed) as calibration proof.
**Why:** it's the project's actual invention. The week-12 writeup
(Branch C or not) becomes its launch documentation. And external users
hammering it is free red-teaming forever.
**Effort:** L. **Tier:** T2 (publication decision is the owner's).
**Acceptance:** a stranger runs a strategy through it from README alone,
and the ledger survives their attempt to cheat it.

---

## Explicitly considered and NOT stolen

- **freqtrade's hyperopt** (thousand-combo parameter search): it is an
  overfitting factory with no K accounting. Our plateau analysis +
  arithmetic-derived parameters already occupy this slot honestly.
- **nautilus_trader adoption now:** order-book realism matters at the
  $500 pilot, not at paper-vs-exam parity. Revisit as a shadow-twin
  fill auditor if anything ever reaches Stage 3 (T1 territory).
- **qlib's ML alpha pipeline / FreqAI:** ML-fitted signals at K=96 and
  retail costs is the exact trap the charter was built against. The
  luck hurdle would (correctly) be unpassable.
- **LLM anywhere in the decision loop:** ban stands (charter v2 Tier 1).

## Suggested order

0.1 CI → 1.4 guard-bite suite → 0.2 VPS → 1.3 stats xref → 0.4
tearsheets → 2.3 cost budget → 1.1 vectorbt xcheck → 3.1 Wave 4 TAA
(the first wave that plays a winnable game) → 2.1/2.2 forecasts +
buffering → 1.2 CPCV → 2.4 OOS scorecard → 4.1 auditor agent (can start
any time) → 0.3 SQLite → 3.2 portfolio exam → 5.1 publication.

Rationale for the head of the queue: everything before Wave 4 makes
verdicts trustworthy; Wave 4 is the first exam where a PASS is
arithmetically possible; everything after deepens it. The auditor agent
(4.1) is independent of the rest and can start this week.
