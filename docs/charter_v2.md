# Charter v2 — two tiers, one owner

**Status:** PROPOSAL — takes effect when Jose signs at the bottom.
**Replaces:** the governance sections (§2) of `docs/intraday_success_criteria.md`.
Everything v1.0 says that this document does not contradict stays in force.
**Written:** 2026-08-08, after the external review found that the one-way
ratchet was blocking legitimate bug fixes while missing the failures that
mattered (six guards that appeared to constrain and did not).

**The one-sentence version:** money rules are locked; science rules are
adjustable in daylight; nothing is adjustable in the dark.

---

## 1. Why v2 exists

v1.0's ratchet ("rules only get stricter") assumed the rules were correct
and the only threat was future-Jose loosening them under stress. Three
months of operation showed a second threat the ratchet cannot handle:
**rules that were wrong when written** — a luck hurdle calibrated to no
actual sample size, a coverage metric with the hole it was built to patch,
a "gate" that duplicated another gate, names permanently burned by code
bugs rather than verdicts. Fixing any of these was technically forbidden,
because a fix is not always a tightening.

v2 keeps the ratchet exactly where it earns its keep — between Jose and
his money — and replaces it everywhere else with something better suited
to rules that might simply be mistaken: **changes allowed, in either
direction, but only in writing, in advance, in public.**

## 2. Tier 1 — MONEY RULES (one-way, unchanged from v1.0)

These may only ever move in the direction indicated. No exceptions, no
interpretations, no "just this once." They bind all automated or
semi-automated trading with real capital by the owner, in any repo, any
account, any tooling (v1.0 §7.9 carries forward whole).

| Rule | Direction |
|---|---|
| Live capital ceiling: **$3,000** total, all bots, both asset classes | down only |
| Pilot: one champion, **$500**, 30 counted days before any rung move | stricter only |
| Ladder $500 → $1,500 → $3,000, one rung per 30 clean counted days | stricter only |
| Kill switches (v1.0 §8 numbers) | tighter only |
| Live drawdown ≥15% of ever-deployed capital → full stop + post-mortem | tighter only |
| **Paper before live, always.** No strategy touches real capital without a recorded PASS + confirmation window | never waived |
| Shadow twin runs for the entire live period; tracking failure halts live | never waived |
| Stock same-day round trips forbidden (FINRA PDT at this capital level) | never waived |
| **No LLM makes or modifies any live trade decision** | never waived |
| Stopping is always fast; starting is always slow (halt anytime; resume only at review) | never waived |
| Withdraw-anytime clause (v1.0 §7.8) | never waived |

**2.1** If this tier ever conflicts with anything — including Tier 2, a
signed plan, or Jose's explicit instruction in a session — Tier 1 wins,
and the conflict is recorded in the decision log.

## 3. Tier 2 — SCIENCE RULES (adjustable, with a paper trail)

Everything about how strategies are tested, measured, and compared:
exam criteria and their statistics, thresholds, window geometry, sample
periods, coverage definitions, K accounting, seed rosters, paper-engine
parameters (position caps, correlation caps, sizing — while unarmed or
paper-only).

**3.1 The change rule.** A Tier 2 change requires, before it takes effect:

1. a written entry in `docs/decisions.md` stating *what* changes, *why*,
   and *what would prove the change wrong*;
2. the direction stated honestly (tightening / loosening / recalibration);
3. one night. Changes land no sooner than the calendar day after they are
   written. (Replaces the 24h + Saturday machinery: one sleep, not one
   week — enough distance to kill impulse edits, short enough not to
   block bug fixes.)

**3.2 What needs no entry at all:** fixing code so it does what its own
documentation already claims. A frozen clock, a swallowed exception, a
missing column — these are repairs, not rule changes. They need a commit
message and, where behaviour changed, a regression test.

**3.3 The bright line.** If a change makes it *more likely that a
strategy reaches real money*, it is not Tier 2 — it is Tier 1-adjacent
and needs the full treatment: written entry, one week (not one night),
and an explicit statement of who benefits if the change is wrong.
Loosening an exam gate the week a favourite seed is examined is the
canonical example — and is why exam gates may never be changed while any
exam is in flight or pre-registered.

## 4. Verdicts (replaces "one exam per name, ever")

**4.1** One exam per name **per working implementation**. A recorded
verdict is permanent *unless voided*.

**4.2 VOID.** A verdict may be voided only when a documented code bug
affected the exam that produced it. Voiding is done exclusively through
`ops/void_verdict.py`, which refuses to act without a bug reference that
exists in the repo. The VOID row is appended — the ledger is never
rewritten — and the name returns to the pool for **one** re-exam on
fixed code.

**4.3** K counts every ledger row: PASS, FAIL, and VOID. A voided trial
still spent its compute; the luck hurdle never goes down. (This carries
forward the k_offset.json principle from 2026-08-04.)

**4.4** Disliking a FAIL is not a bug. A different sample is not a bug.
"The market changed" is not a bug. The void log (`results/void_log.csv`)
is reviewed at every weekly review; a pattern of voids is itself a
finding about the plumbing.

## 5. Standing verification (new — the lesson of 2026-08-08)

Fifteen findings in one external review shared one signature: guards
that appeared to constrain and did not. Therefore:

**5.1** Every gate, guard, or check added to exam or engine code ships
with a test proving it can **fail** — a deliberately bad input that the
guard rejects. A guard that cannot be shown to fire is presumed
decorative. (`bot/test_slowclock.py` demonstrates the pattern.)

**5.2** `ops/lookahead_audit.py` runs at every weekly review and its
JSON result is published, pass or fail (v1.0 §4.5e, now actually
implemented — its first run found the stocks track reading forming bars).

**5.3** The exam writes full statistics (`sharpe`, `p_value`,
`luck_hurdle`, `T_eff`, `dsr_prob`, provenance) to
`results/exam_metrics.jsonl` per run, so every threshold can be
recalibrated from evidence instead of argument.

**5.4** Provenance is captured at exam **start** (git hash + SHA-256 of
the loaded source files), never at write time.

**5.5** Once per quarter, or after any run of ≥3 all-green weeks, one
deliberate fault is injected (a forming bar, a broken seed, a dirty
tree) to confirm the guards still fire. Green dashboards are only
trustworthy if they are occasionally forced to turn red.

## 6. The owner's rule (new, at Jose's request — and binding on his AI)

**6.1** Jose commits to being able to explain, in his own words, any rule
that gates a real-money decision *before* that decision is taken. Not
the mathematics — the *purpose*. If he cannot say what a gate is for,
the weekly review pauses the decision and the explanation happens first.

**6.2** Claude (or any AI assisting this project) must, when proposing
any rule or code change, state in plain language: what it does, which
tier it touches, and **what Jose is giving up by accepting it**. A
suggestion Jose cannot evaluate is a decision Claude is making, not
advice — v1.0 §2.6 said this politely; v2 says it as an obligation on
the tool, not just the owner.

**6.3** External review recurs. Any wave that produces a PASS triggers
one before the result is believed; otherwise quarterly. The review brief
is REVIEW.md's standing question: *what defect is not yet on the list?*

## 7. What v2 deliberately does NOT change

- The $3,000 ceiling and the entire live ladder (Tier 1, untouched).
- The ledger's append-only nature. Nothing is ever deleted or rewritten.
- Pre-registration: expectations are still written before running.
- The luck-hurdle principle: K still only rises; DSR still gates (now
  computed correctly, per the 2026-08-08 rebuild).
- Benchmarks: if BTC-HOLD beats the whole squad, that sentence still
  appears verbatim in any writeup.
- The week-12 decision tree and Branch C's status as a designed success.

## 8. Decision log

`docs/decisions.md` is the single running record replacing v1.0's
amendment log for Tier 2. Format per entry: date · tier · what · why ·
direction · what would prove it wrong · effective date. Tier 1 changes
(all downward) continue to append to the v1.0 §14 amendment log as well.

---

## Signature

    Owner: ____________________            Date: ____________
    Signing adopts sections 1-8 above. Tier 1 is copied verbatim from
    v1.0 where indicated and remains one-way. This signature does not
    arm any squad, fund any bot, or alter any recorded verdict.
