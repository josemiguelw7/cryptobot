# Amendment 001 to entrance_exam.md — PROPOSED, NOT ADOPTED

Status: **AWAITING APPROVAL**. Nothing in exam.py's verdict logic has
been changed. This document exists so the decision is deliberate and
on the record, per the standing rule in entrance_exam.md.

Proposed: 2026-07-30
Approved: ____________  (sign + date, or reject)

## Why an amendment is being proposed at all

entrance_exam.md says the exam may only be made STRICTER, never looser.
Amendment 001 makes criterion 4 EASIER to pass. That is exactly the kind
of change the standing rule exists to resist, so the burden of proof is
on this document.

The claim is NOT "the bar is too high." The claim is "the bar is
measuring something no one intended, and can prove it."

## Evidence: the benchmark fails its own exam

Run 2026-07-30, `python backtest/exam.py --selftest`:

    === ENTRANCE EXAM: hold ===
    windows 116 | pairs 8 | trades 116
    stitched +7996.5% vs buy-hold +17151.4%
    worst window DD -79.3% | shallower-DD windows 49%
      [FAIL] 2_safety   (no window DD <= -20%)
      [FAIL] 3_riskedge (shallower DD >= 60% windows)
      [FAIL] 4_return   (stitched >= buy-hold)
    VERDICT: FAIL

`hold` is buy-and-hold. It is the benchmark the entire league is built
to beat, and the reference asset of success_criteria.md. It fails the
entrance exam on three of five criteria.

Ledger record to date: 10 candidates examined, 10 FAIL. Every one
failed criteria 2 and 4. A test that fails every candidate AND its own
benchmark has no discriminating power: its output is a constant.

## Bug 1 — criterion 4 compares net-of-fees to gross-of-fees

exam.py builds the baseline as a raw price ratio:

    w  = closes[start:start+WIN]
    bh = [c / w[0] for c in w]          # <- no fee, no slippage

while every candidate is charged FEE + SLIP on each weight change in
simulate_window(). Measured directly on BTC-USD, window [300,483):

    hold, NET of fees   : 1.386424
    benchmark bh, GROSS : 1.395495
    drag per window     : 0.65 %

0.65% per window compounded over 116 windows = ~53% of terminal wealth.
That is the whole of `hold`'s criterion-4 shortfall. A strategy that is
*definitionally identical* to the benchmark loses by exactly its
transaction costs.

Criterion 4 as written cannot be passed by anything that pays fees.

### Proposed fix 4a
Charge the benchmark the same FEE + SLIP for its single entry that the
candidate pays. Comparison becomes net-vs-net. This does not lower the
standard "beat buy-and-hold"; it makes the sentence true for the first
time.

## Bug 2 — criterion 2 applies a live-equity rule to per-window paths

Criterion 2 ("no single window's max drawdown breaches -20%") was
written to mirror the league circuit breaker. But the breaker acts on
ONE live equity curve and halts it. Criterion 2 instead scans ~116
independent 183-day windows across 8 of the most volatile liquid assets
in existence and rejects the candidate if ANY window breaches.

Pure buy-and-hold's worst window is -79.3%. Crypto routinely draws down
50-80%. Criterion 2 therefore excludes any strategy with meaningful
crypto exposure -- while criterion 4 simultaneously demands the
candidate beat a fully-exposed asset. The two are close to logically
incompatible, which is what 10-for-10 failure looks like.

### Proposed fix 2a (choose ONE; 2a-ii is the stricter reading)
  i.  Judge criterion 2 on the STITCHED equity path, matching how the
      live circuit breaker actually acts, keeping the -20% line.
  ii. Keep per-window scanning but set the threshold RELATIVE to
      buy-and-hold in the same window (e.g. candidate DD must not be
      worse than buy-and-hold's DD in that window). This is strictly
      harder than (i) in trending markets and preserves the original
      risk-edge intent.

Recommendation: 2a-ii. It is the option that does not weaken the intent.

## What this amendment does NOT do

- Does not touch success_criteria.md or the 90-day forward requirement.
- Does not touch criteria 1, 3, or 5.
- Does not re-open any of the 10 recorded FAIL verdicts. Those were
  graded under the rules in force and stay in the ledger permanently.
  If re-examination is ever wanted, it happens under NEW candidate
  names, per "one exam per name, ever."
- Does not lower the money gate. Real capital still requires the full
  W5 sequence.

## Mandatory regression test (adopt regardless of the above)

backtest/test_exam_sanity.py asserts that `hold` passes criteria 1, 2
and 5. Rationale: if the benchmark cannot clear the exam's own floor,
the instrument is broken and must fail loudly rather than silently
emitting FAIL forever. This test is stricter-only and needs no approval.
