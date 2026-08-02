# Intraday Squad — Success Criteria & Pre-Commitments

**Version:** 1.0 · **Status:** LOCKED at commit · **Committed:** 2026-08-01
**Governs:** the intraday trading squad, crypto and stock tracks. The daily Strategy League remains governed by `docs/success_criteria.md`. The intraday backtest entrance bar remains governed by `docs/intraday_standard.md`.
**Lock rule:** this file must be committed to the repo *before* the first counted squad cycle runs. The commit hash and timestamp are the pre-registration record.
**Nature of this document:** a self-governance charter for the owner's own project and capital, written before results exist so that decisions under stress are already made. It is not financial advice. All dollar figures are the owner's, confirmed once at commit; thereafter the ratchet (§2) applies.

The one-sentence version: **calm-Jose wrote these rules; stressed-Jose doesn't get a vote.**

---

## 1. Purpose — what this experiment is actually for

1.1 **The deliverable is the finding, not the money.** At the §7.1 ceiling of $3,000, a total, unambiguous success returns a few hundred dollars a year against hundreds of hours of work. That is a bad trade if the goal is income. It is a good trade if the goal is a defensible answer to the question *"does short-horizon systematic trading survive retail costs?"* — an answer the owner will otherwise pay for in real money, slowly, over years.

1.2 Therefore: **Branch C (§11) is a delivered result, not a consolation prize.** An experiment that prices the intraday hypothesis at $0 of real capital and produces an honest public writeup has succeeded at its stated purpose. This sentence exists so that week-12 disappointment cannot reframe a working experiment as a failed one.

1.3 The secondary deliverable is machinery that outlives the hypothesis: the tape recorder, the trade autopsy, the coroner's report, the intervention log. These have value regardless of which branch fires.

1.4 The financial goal is explicitly *not* "make money." It is: **do not lose money discovering that this does not work.**

## 2. The Ratchet (governance)

2.1 This document may only be edited in the **stricter** direction. Stricter means, per parameter type: thresholds (Sharpe, DSR, LCB, trade counts) may only increase; evaluation windows may only lengthen; drawdown and kill-switch limits may only tighten (numbers decrease); modeled costs may only get harsher; live capital ceilings may only decrease.

2.2 Edits may only be executed during the weekly review (§10), and only after a **24-hour cooling-off**: the proposed edit must be written into the intervention log at least 24 hours before it may be committed.

2.3 Every edit appends a row to the Amendment Log (§14) with date, change, and reason.

2.4 If this document ever conflicts with another project document, the stricter reading wins.

2.5 **Ambiguity clause.** Where this document is ambiguous, the **strictest defensible reading governs** until the ambiguity is resolved at a weekly review. Resolutions are recorded in §14 as interpretation rows and bind thereafter. Interpreting is not editing and does not require the 24-hour cooling-off — but choosing the *looser* of two readings is editing, and is forbidden.

2.6 **Understanding clause.** Some parameters here were adopted on the recommendation of an advisor rather than from the owner's own derivation. §14 records which. This is permitted, but such parameters are always set to the conservative side, and the owner commits to being able to explain any parameter before it gates a live-capital decision.

## 3. Definitions

- **Slice:** $3,000 paper capital per bot, reset to $3,000 at each breeding boundary. Lifetime stats are tracked separately from slice equity.
- **Closed trade:** a fully exited position with a complete autopsy record.
- **Net P&L:** profit and loss after the full cost model (§4). No other P&L number appears on leaderboards or in criteria checks.
- **Sharpe:** annualized Sharpe of daily net returns — √365 for crypto bots, √252 for stock bots.
- **LCB:** mean daily net return − 1.28 × standard error (≈90% lower confidence bound). Unless a section names another window, LCB is computed over the bot's trailing 90 counted days.
- **Counted day:** a day with clean data for that bot (no `execution_data` halt). Performance halts (§8) do not stop the clock; data failures do. **A day on which a bot is halted or flat counts as a counted day with a net return of 0.00%** and enters the return series as such.
- **Week 1 of the clock:** begins after all crypto seed bots complete 7 consecutive counted days. Shakedown days before that are excluded. The stock track runs its own clock under the same rule.
- **Position cap:** max 2 concurrent positions per bot, vol-targeted sizing, long/flat only, no leverage.
- **K (trial count):** the running number of distinct configurations that have ever begun accumulating counted days in an asset class — seeds plus every bred descendant. K never decreases; benching a bot does not decrement it. K is published on the portal weekly and is an input to the DSR (§5.7).
- **Crypto track = intraday.** Holds shorter than one day are permitted.
- **Stock track = swing.** Every stock position must be held across **at least one overnight session**. Same-day round trips are forbidden — paper and live, always. See §4.6 for why this is structural rather than stylistic.

## 4. Cost model (binding — part of the criteria)

4.1 **Crypto:** taker 0.40% / maker 0.25% per side (paper assumption regardless of the account's actual live tier at any time); spread crossing taken from live best bid/ask at decision time; slippage 2 bps BTC/ETH, 5–10 bps other coins; stop-outs fill at 2× slippage.

4.2 **Stocks:** $0 commission; spread from the live quote; slippage 1–3 bps; stop-outs at 2× slippage; overnight gap risk is borne in full, never smoothed.

4.3 **Cost gate:** no bot enters a trade unless its modeled expected edge ≥ 2× the modeled round-trip cost. Zero-trade days that result from this gate are correct behavior, not failure.

4.4 These parameters are covered by the ratchet: they may only be made harsher.

4.5 **Point-in-time execution integrity (binding).** The single largest known failure mode in this project's history was lookahead bias: a naive backtest showed $3K → ~$13.6K while the honest point-in-time version showed $3K → ~$303. The intraday equivalent is subtler and therefore more dangerous. Accordingly:

  a. Every decision logs: decision timestamp (UTC, millisecond), the SHA-256 hash of the exact data snapshot used, and the timestamp of the last **fully closed** bar in that snapshot.
  b. No signal may reference a bar that had not closed at or before the decision timestamp. Partial or forming bars are invisible to strategy code.
  c. No signal may reference a quote timestamped after the decision timestamp.
  d. Fills are priced from quotes at or after the decision timestamp — never before.
  e. The weekly review runs an automated lookahead audit over the week's decisions. The audit result is published whether it passes or fails.
  f. **Any violation voids the affected counted days**, which are struck from that bot's evaluation window. A voided window cannot graduate.

4.6 **Stock swing constraint (structural).** Under FINRA's pattern-day-trader rule, four or more same-day round trips in five business days in a margin account requires $25,000 minimum equity. The §7.1 ceiling is $3,000. An intraday stock bot is therefore **permanently undeployable** at this capital level. Rather than build a champion that cannot be funded, the stock track is swing by construction: entries decided at or after a bar close, exits no earlier than the next session's open. Any stock bot whose realized trade log contains a same-day round trip is disqualified from live deployment regardless of performance.

## 5. Stage 1 — Graduation (per bot, per asset class)

Over a rolling window of counted days, **all** of:

1. **Sample size** — either path, whichever the bot satisfies first:
   - **Path A:** 90 counted days with ≥ 100 closed trades, or
   - **Path B:** 180 counted days with ≥ 50 closed trades.

   Path B exists because §4.3's cost gate deliberately produces selective bots, and a flat ≥100-trade requirement would structurally exclude exactly the strategies most likely to survive a 0.40% taker fee. Path B is not a lower bar: the window is twice as long, which under §2.1 is the stricter direction.
2. Net P&L > 0
3. Sharpe ≥ 1.0 *(floor, not the real test — see 4 and §5.7)*
4. **LCB > 0**
5. Max drawdown ≤ 10% of slice
6. Net-profitable in at least 2 of the 3 consecutive **30-counted-day blocks** measured backward from the window end (Path B: 2 of the 6 blocks must be profitable *and* no 3 consecutive blocks may all be negative). Blocks, not calendar months — calendar months are undefined on a rolling window.
7. Zero kill-switch breaches (§8)

**DSR is computed and published at every stage but does not gate at v1.0** (§5.7). Promoting it to a gate later is a tightening and is permitted under §2.1; demoting it again is not.

No regime excuses: the window is whatever the market served. A bot correctly flat in hostile conditions is not penalized — but the clock does not pause for it either. Crypto and stock bots graduate only against their own asset class; the two leaderboards never merge.

### 5.7 The multiplicity problem, the LCB gate, and the DSR metric

Sharpe measured over 90 days is extremely noisy. The standard error of the annualized estimate is roughly √365/√90 ≈ 2.0. A strategy with **exactly zero edge** clears Sharpe ≥ 1.0 about **30.6%** of the time by luck alone (20,000-run simulation, `bot/test_stats.py`). With 10 seeds per asset class plus bred descendants, Sharpe alone is not a bar — it is a coin flip with extra steps.

- **LCB > 0** requires the *lower* confidence bound on mean daily net return to be positive, not the point estimate. Zero-edge false-pass rate: **10.0%** standalone.
- **DSR (Deflated Sharpe Ratio, Bailey & López de Prado)** computes the Sharpe you would expect the *luckiest of N random strategies* to show under the null of zero edge, then asks whether the observed Sharpe beats that benchmark with 95% confidence, adjusted for skewness and kurtosis. It is the only statistic here that gets harder as the squad breeds — which is correct, since breeding is what manufactures false positives.

**Why DSR is a metric and not a gate at v1.0.** Under §2.1 a gate can be added later but never removed, so the conservative commit is the looser one. The simulated cost of that choice, measured over the *full* Stage 1 + Stage 2 stack with 20 bots of pure noise:

| | reaches Stage 2 | becomes champion |
|---|---|---|
| LCB gate only (v1.0) | 1.96 of 20 bots | 0.21 of 20 bots |
| DSR as hard gate | 0.01 of 20 bots | 0.00 of 20 bots |

The fresh confirmation window (§6.2) does most of the work; the residual exposure is roughly one false champion per five full squad runs, and that one meets the $500 pilot and the shadow twin (§7.3–7.4) before it meets real size. **The predictable consequence is that ~2 noise bots per squad will reach Stage 2 and feel like success for 60–120 days.** When that happens, DSR is the number that says whether to believe it. Recording this here so week-12 Jose cannot claim he was not warned.

**DSR computation (binding even though it does not gate):** computed over the **combined Stage 1 + Stage 2 return series**, not Stage 1 alone — a longer series makes the estimate more reliable, and the champion decision is made on both windows anyway. The trial count is **K as defined in §3**: every variant ever evaluated in that asset class, seeds plus bred descendants, growing over time, never reset and never frozen at its starting value. (Where the Bailey & López de Prado literature writes *N*, this document writes *K*; they are the same quantity.) The DSR appears in every champion writeup regardless of what it says, and on the portal weekly alongside K.

Implementation lives in `bot/stats.py`, formula documented inline and unit-tested. **If the implementation is ever found to be wrong, the correction is applied and every affected evaluation is redone.**

## 6. Stage 2 — Confirmation

6.1 Parameters are frozen at the moment Stage 1 is met; the frozen config hash is logged.

6.2 A **fresh confirmation window** must then independently show: net P&L > 0; Sharpe ≥ 1.0; LCB > 0; max drawdown ≤ 10%; zero kill-switch breaches. The window scales with the graduation path — a slow bot does not get a fast confirmation:

  - **Path A graduate** (90d / ≥100 trades) → **60 fresh counted days, ≥ 60 closed trades**
  - **Path B graduate** (180d / ≥50 trades) → **120 fresh counted days, ≥ 30 closed trades**

  DSR is recomputed over the combined Stage 1 + Stage 2 series at the then-current N and published (§5.7), but does not gate.

6.3 Any parameter change during confirmation resets the confirmation window to zero.

6.4 **Occam clause:** a bred descendant must also beat its ancestral seed's LCB over the same confirmation window (60 or 120 days per §6.2). If it cannot, the simpler seed becomes the champion candidate instead. (Vacuous if the graduate is itself a seed.)

6.5 At most the top 3 bots by trailing-90-counted-day LCB may hold champion status at any time.

## 7. Stage 3 — Live deployment ladder

7.1 **Absolute ceiling: $3,000 total live capital across all bots and both asset classes.** Under the ratchet, this number may only be lowered.

7.2 Funding comes from existing Coinbase funds (crypto). A stock champion would require opening and funding a brokerage account; that decision is itself a weekly-review item and does not raise the ceiling. No stock bot may be funded unless §4.6 is satisfied over its entire qualifying window.

7.3 **Pilot:** exactly one Stage-2 champion begins live at **$500 for 30 counted days**.

7.4 **Shadow twin:** the champion's paper twin runs on identical signals for the entire live period. Live results count only while tracking holds: average fill deviation ≤ 2× modeled slippage, and 30-day live-vs-twin net gap ≤ 2% of deployed capital. A tracking failure halts live trading; restarting the pilot requires the weekly review.

7.5 **Ladder (single champion):** $500 → $1,500 → $3,000. Each rung requires 30 counted days at the prior rung with zero live breaches, tracking intact, and net P&L ≥ 0 at that rung. Rung moves happen only at the weekly review.

7.6 **Multiple champions:** at most 3 may be funded, and only if every funded pair shows daily-P&L correlation < 0.5 over ≥ 60 shared days. Otherwise only the top-LCB champion is funded. Per-bot ladders under the shared ceiling: two champions → $500 → $1,500 each; three → $500 → $1,000 each.

7.7 **Demotions:** any live kill-switch breach drops that bot one rung and restarts its 30-day clock (a breach at $500 → back to paper for 30 counted days). If live lifetime drawdown reaches 15% of total ever-deployed capital: full stop — all capital back to holdings, a public post-mortem is written, and redeployment requires a brand-new Stage 2 confirmation.

7.8 **Withdraw-anytime clause:** the owner may reduce or remove live capital immediately at any time, no review required. Increasing or resuming always requires the review and the rules above. *Stopping is always fast; starting is always slow.*

7.9 **No side door.** A charter binds only what it covers, so this clause covers the rest: for as long as this document is in force, the §7.1 ceiling binds **all automated or semi-automated trading with real capital by the owner** — any repo, any account, any asset class, any tooling, including manual execution of signals produced by any bot in this project. Starting a parallel effort under looser rules is a breach of this charter and is recorded as such in §14. The ratchet is worthless if it can be walked around by opening a new folder.

## 8. Kill switches (binding numbers — paper and live, scaled to slice/deployed capital)

- **Per bot:** −3% in a day → flatten and halt until next day. −6% over a rolling 7 days → halt until weekly review. −10% lifetime drawdown → bench with retirement autopsy.
- **Squad:** −5% aggregate in a day → halt everything; resume only at weekly review.
- **Data:** 3 `execution_data`-tagged events in one day → halt that bot until the plumbing fix is logged.
- Halting is always permitted, by anyone or anything, at any time. Resuming happens only at the weekly review.

## 9. Selection-integrity rules (guarding the bar)

9.1 Breeding eligibility requires ≥ 30 closed trades. Under 30, a bot's verdict is "insufficient data" — it cannot be retired for performance.

9.2 Max 1 replacement per week. Bots are **benched, never deleted**; benched bots keep paper trading at zero breeding weight.

9.3 The 10 original seed strategies per asset class are **immortal and immutable** — the frozen controls every generation must beat.

9.4 Slice equity resets to $3,000 at each breeding boundary.

9.5 Fitness for ranking and breeding is LCB with a drawdown penalty — never raw return.

9.6 One parameter mutation per child, on coarse grids; every mutation records a `mutation_reason` citing a coroner's-report pattern. Each new child increments K (§3).

9.7 No bot's parameters change within a generation. **No LLM makes or modifies any trade decision.** LLMs may draft narratives and propose mutations for the weekly review only.

## 10. Human rules — the intervention log

10.1 **Weekly review:** **Saturdays 09:00 America/Chicago** — confirmed at commit, fixed thereafter. All changes — resumes, rung moves, breeding approvals, criteria edits, ambiguity resolutions — happen only here.

10.2 **Emergency powers:** halt anything, anytime. Nothing else.

10.3 **Intervention log:** every manual action records timestamp, action, stated reason, and a one-word feeling field. Thirty counted days later, the review computes the counterfactual — what the halted or overridden bot did on paper in the meantime — and tags the intervention `helped | hurt | neutral`. Interventions get autopsied exactly like trades.

10.4 Combined with §2.2, the minimum distance between any impulse and any executed change is 24 hours, and usually the gap to the next Saturday.

## 11. Week-12 decision tree (pre-committed)

Evaluated at the first weekly review after week 12 of each track's clock:

- **Branch A** — ≥ 1 bot meets Stage 1 → proceed to Stage 2. Squad continues.
- **Branch B** — no graduations, but the family × regime matrix shows at least one cell with positive net expectancy over ≥ 30 trades → one targeted iteration, maximum 6 weeks, scoped only to those cells; then this tree is re-run **exactly once**. Two consecutive Branch Bs are not permitted — the second pass resolves to A or C. Every configuration touched in a Branch B iteration increments K.

  **Path B carve-out.** Week 12 is 84 counted days; a Path B candidate needs 180. Without this clause the tree would kill every slow bot before it could possibly qualify, which would make Path B decorative. Therefore: a Path B candidate holding **≥ 30 closed trades, LCB > 0, and zero kill-switch breaches** at week 12 may run its 180-day window to completion as a targeted iteration, exempt from the 6-week cap. The exemption covers **that bot's unchanged, frozen parameters only** — it is permission to finish counting, not permission to keep tinkering. A bot on this carve-out that trips any kill switch or falls to LCB ≤ 0 at any weekly review loses the exemption immediately and resolves under the ordinary tree.
- **Branch C** — neither → conclude the experiment: publish the public findings post; the squad drops to seeds-only maintenance or full stop (owner's choice at that review); the tape recorder and the daily league continue. **Branch C is a designed outcome, not a failure** (§1.2) — it prices the intraday hypothesis at $0 of real capital and produces the writeup.

## 12. Pre-registered predictions (checked publicly at week 12)

Each prediction has a pre-specified test. A verdict without a test specified in advance is post-hoc rationalization, which is the thing this whole document exists to prevent.

**12.1 Frozen loss-cause taxonomy.** Every closed losing trade is assigned exactly one cause, by deterministic rule, no LLM involvement. The labels are frozen at commit: `fees_spread` · `stop_hit` · `signal_reversal` · `timeout_exit` · `regime_shift` · `execution_data` · `position_cap`. Adding a label is an amendment; the tie-break order is the order listed.

- **P1:** `fees_spread` will be a top-2 loss cause squad-wide. *Test:* rank labels by count of losing trades attributed, squad-wide, at week 12.
- **P2:** frozen seeds will be statistically indistinguishable from bred descendants at week 8. *Test:* Welch two-sample t-test on pooled daily net returns, seeds vs. descendants, two-sided, α = 0.05. "Indistinguishable" = fail to reject.
- **P3:** zero or one bot will meet Stage 1 by week 12. *Test:* count of bots satisfying all of §5.
- **P4:** the stock squad will show better raw equity curves than the crypto squad, for cost-structure reasons rather than skill. *Test:* median across bots of cumulative **pre-cost** return, stock vs. crypto, over the shared window; plus the same comparison post-cost to isolate the cost channel.
- **P5:** the intervention log will contain at least one entry whose stated reason is discomfort rather than data. *Test:* at least one entry whose stated reason references no logged metric.

Each prediction receives a one-paragraph verdict in the week-12 writeup regardless of outcome.

## 13. Reporting and benchmarks (context, never gates)

BTC-HOLD, cash, and per-asset-class benchmarks are reported on the portal and in every writeup. The intraday track is judged on absolute return; the benchmarks exist for honesty. If BTC-HOLD beats the entire squad at week 12, that sentence appears verbatim in the public post.

## 14. Amendment log

| Date | Version | Change | Direction | Reason |
|---|---|---|---|---|
| 2026-08-01 | 1.0 | Initial commit | n/a | Pre-registration |

**Integrity record for v1.0.** The SHA-256 of this file at commit is published on the public site and recomputed on every build. A mismatch between the published hash and the committed file is itself a finding and is disclosed.

**Owner-derived:** all dollar figures, kill-switch numbers, the ratchet, the ladder, the intervention log, the week-12 tree, the §6.2 path-scaled confirmation windows, the §11 Path B carve-out, and the decision to hold DSR as a metric rather than a gate.

**Adopted on advisor recommendation** (§2.6), reviewed and accepted by the owner with the tradeoff quantified in §5.7:
- §3 / §4.6 stock-track swing constraint (FINRA PDT rule at sub-$25,000 equity)
- §5.4 LCB > 0 promoted from ranking input to hard gate
- §4.5 point-in-time execution integrity requirements

**Governing rule applied at commit:** where two readings were defensible, the *less strict* was committed, because §2.1 permits tightening later and forbids loosening. This means v1.0 is deliberately the loosest version this charter will ever have.

*End of charter. Everything below this line in future versions must be stricter than what stands above it.*
