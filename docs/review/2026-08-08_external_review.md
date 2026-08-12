# External review — 2026-08-08

**Reviewer:** Claude (Opus), independent session, no prior context on this repo
**Scope:** full repo at commit `01aa018`, in response to `REVIEW.md`
**Status:** findings enter as **proposals** for the Saturday review, per REVIEW.md §7
**Written for:** the owner, who is not a programmer. Concepts are explained inline.

---

## 0. Verdict in one paragraph

The governance machinery in this project is better than most professional
quant shops. The pre-registration is real and dated, the ledger discipline
is real, the point-in-time decision logging works and I verified it
independently. But **Wave 3 examined nothing.** A bug introduced on
2026-08-08 — in the very commit that fixed the SlowClock defect listed as
#4 in REVIEW.md §5 — froze all four slow-clock seeds so they make exactly
one decision per 90-day window and then hold it. `d3_trend` and `d3_calm`
were graded on that frozen behaviour, failed, and their names are now
permanently burned. Separately, the new criterion 10 ("DSR as an explicit
gate", C0.3) adds **zero** constraint: it is character-for-character the
second half of criterion 9. And `stitched()`, which C0.1 formally retired
as uninterpretable, still decides criteria 4, 6, 7, 8 and 9. The
retirement changed what gets printed, not what gates.

The good news buried in this: **the answer to REVIEW.md §6 Q10 is "yes,
there were more, and here they are."** The system's own prediction about
itself was correct.

---

## 1. What I verified as working

Stated first, because the rest of this document is critical and that would
otherwise give a false impression.

| Claim | Verified how | Result |
|---|---|---|
| No exchange connection, no secrets | Scanned all of git history for keys, `.env`, `.pem`, tokens | **Clean.** `.gitignore` pre-emptively covers credentials before any exist |
| §4.5b — no decision uses an unclosed bar | Ran the audit §4.5e requires, over all 1,157 logged decisions | **0 violations.** Median decision lag 2,041s (34 min) after bar close |
| Bar-close rule in the exam | Read `load_hourly`, `load_bars_exam` | Correct: `t + 3600 <= now` |
| Warmup doesn't leak into graded span | Read `windows_for` | Correct: history visible, graded span restricted |
| Cross-sectional slicing by timestamp | Read `simulate_window_bars`, `bisect_right` usage | Correct — no pair can see another pair's future |
| Ledger-first write ordering (defect #2) | Read `run()` | Correctly fixed |
| `bot/stats.py` DSR | Read against Bailey & López de Prado | **Correctly implemented**, unit-tested, estimates dispersion empirically |
| `data/audit.py` | Read | A real gate with documented real catches |

**No classical lookahead bias found** in `exam_1h.py` or `exam.py`. That
was Q1 and it is the question that mattered most. The answer is clean.

---

## 2. Critical findings

### C-1 · The SlowClock fix froze every slow seed. Wave 3 measured nothing.

**Severity: critical. This invalidates the only two verdicts in Wave 3.**

`SlowClock` is the wrapper that makes an hourly strategy think in daily
bars. Defect #4 in REVIEW.md §5 was that it didn't actually slow the
*decision* clock. The 2026-08-08 fix (commit `727ed1f`) added this:

```python
def step_bars(self, bars, ctx):
    n = len(bars)
    if n < self.k:
        return ctx.get("slow_sig", 0.0)
    boundary = (n % self.k == 0)          # <-- the bug
    if boundary or "slow_sig" not in ctx:
        ctx["slow_sig"] = self._inner_call("step_bars", bars, ctx) or 0.0
    return ctx["slow_sig"]
```

The intent: "recompute the signal once per slow bar." The mechanism:
"recompute when the number of bars I was handed is divisible by 24."

The problem is that the number of bars handed to a seed is **capped**. Every
`BarStrategy` declares a `tail` — the maximum history it may see:

```python
tail = max(200, self.warmup * 3 + 10)
```

Once the exam is past warmup, the slice is always exactly `tail` bars long.
So `n` stops growing and becomes a constant. And:

```
SlowClock.warmup = inner.warmup * k + k   ->  always divisible by k
tail             = warmup * 3 + 10        ->  tail % k  ==  10 % k
```

For `k = 24`, `tail % 24 == 10`, **always, for every possible slow seed.**
Never zero. The boundary never fires again. The signal freezes at whatever
it was on the first bar of the window.

Measured, all four:

```
d3_trend     warmup=  504  tail= 1522  k=24  tail%k=10  FROZEN
d3_nearhi    warmup= 1464  tail= 4402  k=24  tail%k=10  FROZEN
d3_calm      warmup=  528  tail= 1594  k=24  tail%k=10  FROZEN
d3_cash      warmup= 4872  tail=14626  k=24  tail%k=10  FROZEN
```

**Direct proof.** Same seed, same synthetic data containing a deliberate
up→down regime flip, same window. The only change is `tail`:

| `tail` | `tail % 24` | distinct decisions in 2,160 bars | trades | final equity |
|---|---|---|---|---|
| 1522 (actual) | 10 | **1** (`1.0` × 2160) | 1 | **0.5676** |
| 1512 (control) | 0 | 2 (`1.0` × 1134, `0.0` × 1026) | 2 | **3.2546** |

The working version exits when the trend breaks. The shipped version rides
it down. Same code, same data — an 83% difference in outcome, caused
entirely by `tail` not being a multiple of `k`.

**This is visible in the recorded verdicts.** From
`backtest/results/exam1h_d3_trend_2026-08-08.csv` (430 windows):

```
never traded    : 208 (48.4%)   ret == 0, dd == 0
exactly 1 trade : 216 (50.2%)   entered, never exited -> a buy-and-hold clone
more than 1     :   6 ( 1.4%)   <- the only windows containing a round trip
```

`d3_calm`: 34.2% cash, 64.2% buy-and-hold clone, **1.6%** actually trading.

So Wave 3 did not grade two trend strategies. It graded a coin that lands
on "cash" or "buy and hold" and then sits still for three months.

**Consequences that need a Saturday decision:**

1. `d3_trend`'s Sharpe 0.66 and permutation `p = 0.0100` — the result
   REVIEW.md Q9 asks about — are **not interpretable**. They measure a
   frozen position, i.e. mostly the market itself.
2. Two names are permanently burned on a plumbing failure. This is the
   2026-08-04 situation again, and §5.7 has a clause that fires here:
   *"If the implementation is ever found to be wrong, the correction is
   applied and every affected evaluation is redone."*
3. `d3_nearhi`, `d3_cash` were rejected at admission — but the admission
   pre-check ran through the same frozen code, so those rejections are
   also artifacts. **Their names are still free**, so this is recoverable.

**Proposed fix** (correctness, not a rule change — no ratchet implication):
decide on an absolute clock, not on slice length.

```python
def step_bars(self, bars, ctx):
    if not bars:
        return ctx.get("slow_sig", 0.0)
    slot = bars[-1][TS] // (self.k * 3600)      # which slow bar are we in
    if slot != ctx.get("slow_slot"):
        ctx["slow_slot"] = slot
        ctx["slow_sig"] = self._inner_call("step_bars", bars, ctx) or 0.0
    return ctx["slow_sig"]
```

This also fixes a second, quieter problem: `n % k` was aligned to the
*first row of the CSV file*, so "daily" bars began at whatever hour the
data happened to start, and the 229 known gaps shifted the alignment
further. A timestamp-derived slot is anchored to real UTC days.

**Add a regression test** (this class of bug is invisible without one):
assert that a slow seed emits more than one distinct signal across a
window containing a regime change.

---

### C-2 · Criterion 10 (C0.3, "DSR as an explicit gate") constrains nothing

**Severity: critical — a signed tightening that has no effect.**

C0.3 was adopted as a §2.1 hardening. Here is what shipped:

```python
# criterion 9
checks["9_notluck"]  = (p_val < 0.05 and sr > hurdle)
#                                        ^^^^^^^^^^^^
# criterion 10
checks["10_dsr"]     = bool(validation.deflated_check(sr, K, var_sharpe=0.25)["clears"])
```

And `deflated_check` is:

```python
def deflated_check(observed_sharpe, n_trials, var_sharpe=0.25):
    hurdle = expected_max_sharpe(n_trials, var_sharpe)
    return {..., "clears": observed_sharpe > hurdle}
```

`hurdle` in criterion 9 is computed by the *same call with the same
arguments*. So criterion 10 evaluates to `sr > hurdle` — already required
by criterion 9. Since the verdict is `all(checks.values())`, adding
criterion 10 cannot change any verdict, ever. Verified numerically at
K=95: both return `False` from the identical expression.

This is the same class as defect #3 (`bool(dict)`). The code comment above
it specifically warns about the `bool(dict)` trap and correctly avoids it —
while missing that the gate it is carefully unwrapping was redundant to
begin with.

**Worse: it is not the DSR.** The Deflated Sharpe Ratio is a *probability*,
adjusted for skewness, kurtosis and series length, compared against 0.95.
`deflated_check` does none of that — it is a bare threshold comparison.

The real DSR **already exists, correctly, in `bot/stats.py`** — which is
the file charter §5.7 names as the implementation:

```python
def deflated_sharpe(returns, trial_sharpes):
    sr0 = expected_max_sharpe(_std(trial_sharpes, ddof=1), len(trial_sharpes))
    return probabilistic_sharpe(returns, sr0)   # a probability, with skew/kurtosis
```

`exam_1h.py` imports `validation`, not `stats`. Two implementations of the
same concept exist; the exam uses the wrong one; the charter names the
right one.

**Proposed:** point criterion 10 at `bot/stats.deflated_sharpe(...) >= 0.95`
over the per-period return series, using the empirical dispersion of trial
Sharpes. That makes it a genuine additional constraint and matches §5.7 as
written. Delete `validation.deflated_check` or make it call `stats`.

---

### C-3 · `stitched()` was retired as a metric but still decides five criteria

**Severity: critical — C0.1 was cosmetic.**

C0.1 retired `stitched()` because it compounds 50%-overlapping windows, so
the same calendar week enters the product twice. The code says so itself:

> *"Las magnitudes del ledger hasta 2026-08-07 no son interpretables por
> eso. stitched() se conserva solo para reproducir filas viejas."*

But `stitched()` is still the deciding statistic in:

- **criterion 4** — `stitched(rows) >= stitched(rows, "bh_net")`
- **criterion 6** — fee stress re-runs criteria 2–4
- **criterion 7** — resolves to criterion 4 by definition
- **criterion 8** — holdout re-runs criteria 2–4
- **criterion 9** — the permutation test statistic is `stitched(main_rows)`

The replacements (`median_win_net`, `beat_bh_pct`, `pct_traded`,
`median_traded`) are printed and written to the ledger but gate nothing,
except criterion 5b.

What this looks like in the actual ledger row for `d3_trend`:

```
stitched = 9,494,617,811.7155        (949 billion percent)
stitched_bh = 1,189,649,412,235.83   (119 trillion percent)
```

Criterion 4 — a gate — is a comparison between two numbers of order 10¹²
that the project has formally declared meaningless. `slip2x_net` records
`8,401,408,672.21` for the same reason.

**Proposed:** replace the criterion-4 family with the C0.1 metrics that
were designed for exactly this purpose (`median_win_net` vs `bh_net`
median, plus `beat_bh_pct`), and use a per-window statistic for the
permutation test. Keep `stitched()` only for reproducing pre-2026-08-08
rows. Note that changing a gate's *statistic* is neither a tightening nor a
loosening, so §2.1 needs an explicit interpretation ruling under §2.5.

---

## 3. High-severity findings

### H-1 · W1.1 is broken: `tail` is enforced in the exam, not in the live engine

`BarStrategy.tail` exists specifically to make a seed a fixed function of
recent data. Its own docstring:

> *"Declared, bounded, and identical in the exam and in forward trading —
> that identity is the point (W1.1) ... their value would silently depend
> on how much history happened to be on disk that day."*

- Exam (`exam.py:435`): `strat.step_bars(bars[lo:i + 1], ctx)` where
  `lo = max(0, i + 1 - tail)` — **bounded**
- Live (`squad.py:525`): `sigs[p] = strat.step_bars(bars[p], ctx)` — **the
  full array from disk**

The string `tail` does not appear anywhere in `squad.py`. The exact failure
the docstring warns about is running in production. And it just got much
worse: on 2026-08-08 the on-disk history went from ~8,700 bars to 87,550 —
**a 10× change to the live engine's inputs, with no change to the exam's.**

For cumulative seeds (OBV) and any resampled seed this changes the signal
outright. W1.1 — "the seed examined is byte-for-byte the one that
operates" — is true of the *function* and false of its *inputs*.

**Proposed:** apply the tail slice in `squad.py` at the single call site.
One line. Then add a parity test that runs both paths on the same bars and
asserts identical signals.

### H-2 · `pct_windows_traded` (C0.1b) has the same hole it was built to patch

This is REVIEW.md Q2, and the answer is **yes — measurably.**

C0.1b counts a window as "traded" if `trades > 0`. But `trades` counts
**weight changes**, and a round trip is two of them. So `trades == 1` means
*entered and never exited* — which is a buy-and-hold clone, not activity.

Measured on `d3_trend`, the seed C0.1b admitted at 51% coverage:

```
never traded    208 (48.4%)  ->  cash
exactly 1 trade 216 (50.2%)  ->  buy-and-hold clone, counted as "traded"
>1 trade          6 ( 1.4%)  ->  contains an actual round trip
```

`pct_traded = 0.51` therefore means "was passively long half the time,"
not "played half the time." The metric distinguishes *cash* from
*not-cash*; it does not distinguish *trading* from *holding*. That third
case is the dominant one, and it is the one that matters.

The knock-on effect is worse. Criterion 3 requires shallower drawdown than
buy-and-hold in ≥60% of windows. For `d3_trend`:

```
DD shallower : 216 windows (50.2%)
  ... of which never traded: 208  (96%)
DD exactly equal to B&H: 214 windows (49.8%)  <- the buy-and-hold clones
```

**96% of the credit toward criterion 3 comes from windows where the seed
did nothing at all.** The remaining half are mathematically identical to
buy-and-hold (drawdown is scale-invariant, so a one-time entry fee leaves
it unchanged — exactly as the `DD_EPS` comment in `exam.py` explains).

**Proposed:** count **round trips**, not weight changes, and require a
minimum per window — e.g. `round_trips >= 2` in ≥50% of windows.
Additionally split the drawdown criteria to exclude flat windows, so
"shallower DD" cannot be earned by abstention. Both are tightenings and
therefore ratchet-legal.

### H-3 · The luck hurdle is not calibrated to anything

This is Q4, and it feeds Q9.

`var_sharpe=0.25` is hardcoded at both call sites, meaning "the spread of
Sharpe across trials has standard deviation 0.5." That number was not
measured. It should be, and Bailey & López de Prado require it to be.

The dispersion of an *annualized* Sharpe estimated over T daily
observations is `sqrt(365/T)`. So:

| assumed T | implied σ(Sharpe) | resulting hurdle at K=95 |
|---|---|---|
| 90 days (the figure in charter §5.7) | 2.014 | **5.05** |
| 37,962 (the exam's nominal T) | 0.098 | **0.25** |
| ~2,965 (T after removing 50% window overlap and ρ=0.77 cross-pair correlation) | 0.351 | **0.88** |
| — *(hardcoded 0.25)* | 0.500 | **1.25** ← actually applied |

The applied hurdle of 1.25 corresponds to no sample size the exam
actually uses. It sits above the defensible range.

There is also a **units error**. `bot/stats.py` warns explicitly:

> *"PSR and DSR operate on the PER-PERIOD (daily) Sharpe, never the
> annualized one. Mixing these up silently inflates DSR."*

`exam_1h.py` passes `sharpe_annualized_from_rows(...)` — the annualized
figure — into the other implementation, which has no such guard.

**On Q9 specifically:** `d3_trend`'s Sharpe 0.66 clears a correctly
calibrated hurdle (0.25–0.88) and fails the hardcoded one (1.25). But it
does not matter, because C-1 means the seed was frozen — 0.66 is the
Sharpe of a stuck position. **The honest answer to Q9 is that the question
cannot be answered from this run, and the threshold it failed was not
defensible either way.**

**Proposed:** estimate `var_sharpe` from the empirical spread of trial
Sharpes, as `bot/stats.py` already does. This requires a change you should
make regardless: **the ledger has no `sharpe` column**, so the dispersion
cannot be estimated retrospectively from 24 rows of history. Add
`sharpe`, `p_value`, `luck_hurdle`, and `K` as columns.

### H-4 · `git_hash()` is evaluated at write time, so provenance can be wrong — and is

The ledger's whole claim is that `git_hash` pins the code that produced the
verdict. It does not, because `git_hash()` runs when the row is *written*,
minutes after the run *started*. A long exam that straddles a commit gets
attributed to code that did not produce it.

**This already happened, and it is provable from the repo:**

- `d3_calm`'s row carries hash `f0229fd` — the commit that fixed defect #5
  (the missing `pct_traded` / `median_traded` columns)
- but `d3_calm`'s row has **21 fields**, not 23 — i.e. it was written by
  the **pre-fix** code
- commit times: fix at 06:21:41, `d3_calm` verdict committed 06:35:45

The exam was already running, with the old module loaded in memory, when
the fix was committed. The row records the new hash and the old behaviour.

So **defect #5 is not fully fixed**: `d3_calm` is still missing both
coverage columns. `d3_trend`'s row was repaired by hand from its log (a
reasonable call — re-running would have been a second exam on a burned
name), but `d3_calm`'s was not.

Related: **all 24 ledger rows still carry `-dirty`**, including the
newest. `require_clean_tree()` watches only `bot/` and `backtest/`, while
`git_hash()` calls `git diff --quiet` across the *whole* repo — so data and
log churn marks every row dirty. The 2026-08-03 fix works, but its evidence
is invisible: a reader cannot distinguish "code was dirty" from "logs
were dirty." The audit finding it was meant to close still appears open.

**Proposed:** capture the hash and the clean-tree check **once at process
start**, before any simulation, and record that. Additionally record a hash
of the loaded source files (`exam_1h.py`, `strategies.py`, the roster) so
provenance is pinned to what was executed, not to what HEAD said later.
Scope `git_hash`'s dirty flag to the same paths `dirty_paths()` watches.

### H-5 · `d3_rand` — the pre-registered luck control — was never examined

`plan_v3.md` F1 admitted three names and declared:

> *"Si d3_rand PASA, el resultado invalida la ola completa y se investiga
> la plomeria antes de celebrar nada."*

`d3_rand` does not appear in the ledger. Only `d3_trend` and `d3_calm` were
recorded. So the control that was supposed to validate the wave was never
run — **and, given C-1, it is the one seed that would have caught the bug**,
because `RandomEntry` is not a `SlowClock` and would not have frozen. A
random entry trading normally against two frozen seeds would have looked
anomalous immediately.

The arithmetic confirms it: `K = 24 ledger rows + 38 carried + 33 screened
= 95`, not the 96 cited in REVIEW.md §4 and `plan_v3`. 93 + 2 names = 95.

**Proposed:** run `d3_rand` before interpreting anything from Wave 3, and
correct the K figure in REVIEW.md.

---

## 4. Medium-severity findings

### M-1 · `MAX_POS = 6` violates the ratchet

Charter §3: *"**Position cap:** max 2 concurrent positions per bot."*
`plan_v3` E3.3 and `seeds_crypto_v3.py` set `MAX_POS = 6`. Going 2 → 6 is a
**loosening**, which §2.1 forbids. It was signed on 2026-08-08.

The armed engine still has `MAX_POS = 2` (`squad.py:53`), so nothing live is
in breach — but the signed plan is.

**This reframes Q7.** The question asks how to resolve "0.70 correlation cap
with MAX_POS=6 is impossible — zero of 28 six-coin portfolios are legal."
The answer is that the incompatibility is not a design puzzle: **MAX_POS=6
was never charter-legal.** Revert to 2 and the conflict dissolves. At
MAX_POS=2 you need only one pair below 0.70 correlation with one other,
which is achievable. The correlation cap is the newer, stricter rule and
under §2.4 the stricter reading wins.

### M-2 · The holdout gate is decided by one window per pair

Criterion 8 is the out-of-sample check — arguably the most important gate.
Its geometry:

```
holdout span = 120 days = 2,880 bars
WIN = 2,160, STEP = 1,080
=> windows that fit: 1 per pair  x 8 pairs = 8
```

Confirmed against the recorded results: 430 rows = 422 main + **8 holdout**.

So criterion 3 inside the holdout ("shallower drawdown in ≥60% of windows")
is evaluated on a *single observation per pair*. That is a coin flip, not a
gate. Given that ~50% of `d3_trend`'s windows are buy-and-hold clones with
drawdown exactly equal to the benchmark, it is a coin flip weighted by a
tie-break.

**Proposed:** either lengthen the holdout (a §2.1 tightening — "evaluation
windows may only lengthen") to at least 300 days so ≥4 windows fit per
pair, or reduce `STEP` inside the holdout only, or judge the holdout on a
pooled statistic rather than a per-window fraction.

### M-3 · Expanding the sample silently tightened criterion 2

Criterion 2 ("drawdown never worse than buy-and-hold") is a **universally
quantified** constraint: it must hold in *every* window. Windows per pair
went from ~4 to ~80 on 2026-08-08. Total graded windows went from 32 to
430. That multiplies the opportunities to violate by ~13×.

Tightening is legal under §2.1, but this one was not declared, and the
addendum records only the regime-mix change. It is a second reason old and
new verdicts are not comparable — additional to the one already noted.

Note also that per-pair window counts are now very unequal (BTC 75, ETH 77,
LTC 73 vs XRP 35, SOL 38, DOGE 38). BTC+ETH+LTC contribute 52% of all
windows, so pooled medians are effectively majority-BTC/ETH/LTC. Combined
with ρ=0.77, the effective independent sample is far below 430.

### M-4 · A strategy that throws an exception is recorded as a strategy with no edge

`simulate_window_bars`, cross-sectional path:

```python
try:
    w = strat.step_all(sl, pctx)
except Exception:
    return 0.0
```

Any error — a typo, an index error, a missing key — silently becomes "go
flat." The seed then trades zero times, fails criterion 5b, and is recorded
as a FAIL. **Under "one exam per name, ever," a plumbing bug permanently
burns a name and is indistinguishable in the ledger from a real verdict.**

Given that five bugs were found in one week, this is not hypothetical.

**Proposed:** let it raise. An exam that crashes costs one commit; an exam
that silently returns 0.0 costs a name forever. If a fallback is wanted,
log the exception and mark the verdict `VOID`, not `FAIL`.

### M-5 · `permute_bars` does not preserve candle geometry

This is Q3. The docstring claims *"a hammer is still a hammer."* It is not.

Shapes are stored as ratios to the *previous close*, then replayed against a
*different* previous close. The rebuilt bar is then clamped:

```python
out.append((bars[i][0], o, max(h, o, c), min(l, o, c), c, v))
```

When the shuffled ratios land `o` or `c` outside the original high/low
range relative to the new base, `h` and `l` are overwritten. Wick length —
the entire signal in a pin bar or engulfing pattern — is systematically
altered. So for any candle-pattern seed the null does not test "was the
order informative"; it tests order *and* a distorted shape distribution.

`h3_crossconf` was retired, so nothing currently examined depends on this.
But the docstring's claim should not be relied on by the next candle seed.

Two smaller notes on the same function:

- **Two different nulls.** The close-based path preserves the holdout
  (`shuf += closes[hi:]`), while the bar-based path permutes the entire
  series including the holdout, mixing holdout shapes into the main region.
- **Mismatched benchmark in bar mode.** The strategy's returns come from
  `bmap[p]` (one shuffle) while `bh`, `bh_net` and `bh_dd` come from `shuf`
  (an independent shuffle of the same pair). The current p-value only uses
  `stitched(rows)` on `ret`, so it is unaffected today — but the moment the
  test statistic becomes benchmark-relative (which C-3 recommends), this
  breaks silently.

**Good news on Q5:** window overlap does **not** bias the permutation
p-value. Both the real and permuted grading travel identical geometry, so
the null distribution inherits the same overlap. Overlap's damage is to
`stitched()` (C-3) and to nominal sample size (H-3), not to the p-value.

### M-6 · §4.5e's automated lookahead audit does not exist

The charter requires: *"The weekly review runs an automated lookahead audit
over the week's decisions. The audit result is published whether it passes
or fails."*

`squad.py` faithfully logs `snapshot_sha` and `last_closed` on every
decision — but **nothing in the repo reads `last_closed`**. Grep returns
exactly one hit: the line that writes the header.

I ran the audit manually. **It passes cleanly**: 1,157 decisions, 0
violations, median lag 2,041s after bar close, minimum 414s. That is a
genuinely good result — the field is worth having. It just isn't audited,
so it is unaudited good news, and §4.5e is unmet.

**Proposed:** ~20 lines in `ops/` that read `logs/squad_decisions.csv`,
assert `last_closed + 3600 <= utc_ms` for every row, and publish the count.

### M-7 · The reproduction data is not in the repo

`.gitignore` excludes `data/candles/` and `data/candles_daily/`. Only
`data/candles.bak_1y/` (the *superseded* 1-year sample) is tracked.

So the `data_fingerprint` recorded in every ledger row points at files a
reviewer cannot obtain, and REVIEW.md §4 cites `data/candles/` as the
location of the 10-year sample that isn't there. **No verdict in this repo
is externally reproducible.** For a project whose central value is
defensibility, that is a meaningful gap.

**Proposed:** commit the fingerprints and a fetch script pinned to exact
date ranges, or publish the candle store as a release artifact. Not the raw
CSVs in git — 115MB and growing.

### M-8 · "Daily" aggregation in the Sharpe crosses pair and window boundaries

```python
daily = [prod(1 + x for x in hourly[i:i+24]) - 1
         for i in range(0, len(hourly) - 23, 24)]
```

`hourly` is built by concatenating per-window curves, pair after pair. Each
window contributes 2,159 points, which is not divisible by 24. So every
window boundary shifts the phase, and blocks straddle both window and
**pair** boundaries — some "days" are 14 hours of BTC plus 10 of ETH.

It does not invalidate the point estimate, but "annualized Sharpe of daily
returns" is not what is being computed, and it interacts with H-3's
sample-size question.

---

## 5. Direct answers to REVIEW.md §6

| # | Question | Answer |
|---|---|---|
| 1 | Lookahead in `exam_1h.py` / `exam.py`? | **No.** Bar-close rule, warmup/graded-span separation, holdout cut and cross-sectional timestamp slicing are all correct. This is the cleanest part of the codebase. |
| 2 | Does `pct_windows_traded` have the hole it patches? | **Yes, measurably.** It counts weight changes, so a buy-and-hold clone (`trades == 1`) reads as "traded." 50% of `d3_trend`'s windows are exactly that. See **H-2**. |
| 3 | Is `permute_bars` a valid null? | Valid as an order-destroying null for close-based logic (and terminal price is invariant, which is elegant). **Invalid for candle-shape seeds** — clamping distorts wicks. Two different nulls exist across the two code paths. See **M-5**. |
| 4 | Is the Sharpe ≈1.25 hurdle calibrated? | **No.** `var_sharpe=0.25` is hardcoded and corresponds to no sample size the exam uses; defensible range is 0.25–0.88. Plus an annualized-vs-per-period units error. See **H-3**. |
| 5 | Does 50% window overlap bias Sharpe / counts / p-value? | **p-value: no** — both sides share geometry. **`stitched()`: catastrophically yes** (C-3). **Sample size: yes** — nominal T is ~13× the effective T (H-3). Window *count* is inflated, which silently tightened criterion 2 (M-3). |
| 6 | Should the ledger formally separate the 1yr and 10yr populations? | **Yes**, add an `epoch`/`sample_id` column — but it is secondary. The 2026-08-08 rows are bug artifacts (C-1), so the more urgent question is whether they should stand at all. |
| 7 | 0.70 correlation cap vs MAX_POS=6 — what is the way out? | **MAX_POS=6 was never legal.** Charter §3 caps it at 2; 2→6 is a loosening forbidden by §2.1. Revert to 2 and the impossibility dissolves. See **M-1**. |
| 8 | Long-only seeds are defensive, not alpha — reward that, or self-deception? | Worse than defensive: for Wave 3, 98.6% of windows contain no round trip. You are measuring cash and buy-and-hold. Fix C-1 first, then re-ask — the question is currently unanswerable. If it survives, require round trips per window (H-2) so "defence" must be an active choice, not abstention. |
| 9 | `d3_trend`: Sharpe 0.66, p=0.0100 — real signal or artifact? | **Artifact, but not for the reason you suspected.** The seed was frozen (C-1), so 0.66 is the Sharpe of a stuck position. Separately, the hurdle it failed is miscalibrated (H-3) — 0.66 clears a correct hurdle. Both numbers need to be discarded and the name is already burned. |
| 10 | What defect is *not* in §5? | **C-1** (SlowClock freeze — introduced by the fix for §5 #4), **C-2** (criterion 10 is a no-op), **C-3** (`stitched()` still gates), **H-1** (`tail` not applied live), **H-4** (`git_hash` misattribution — and §5 #5 is still unfixed for `d3_calm`), **H-5** (control never run), **M-4** (exceptions become FAILs), **M-5**, **M-6**, **M-8**. |

---

## 6. Proposed ordering for Saturday

**Before anything else — decide the status of Wave 3.** C-1 means
`d3_trend` and `d3_calm` were graded on frozen seeds. Precedent exists
(2026-08-04) and §5.7 has a clause that fires ("the correction is applied
and every affected evaluation is redone"). This is a governance decision,
not a technical one, and it should be made before any fix lands so the fix
cannot be accused of being reverse-engineered to a preferred outcome.

Then, in dependency order:

1. **C-1** — fix `SlowClock` on an absolute clock; add the regression test.
2. **H-5** — run `d3_rand`. It is the control, and it is the one seed that
   would have caught C-1.
3. **H-1** — apply `tail` in `squad.py`; add the exam↔engine parity test.
4. **M-4** — stop swallowing exceptions; introduce a `VOID` verdict.
5. **H-4** — capture provenance at process start; repair `d3_calm`'s row or
   mark it incomplete.
6. **C-2, C-3, H-3** — the statistics block. These change what "PASS" means
   and need an explicit §2.5 interpretation ruling, so they belong together
   in one signed amendment rather than as separate patches.
7. **M-1** — revert `MAX_POS` to 2 and record the ratchet breach in §14.
8. **M-2, M-6, M-7** — holdout geometry, the §4.5e audit, reproducibility.

**One meta-observation.** Four of the five defects in REVIEW.md §5, and
five of the ten here, share a single signature: **a guard that appears to
constrain and does not.** `bool(dict)`; a header without a row; a resample
that didn't slow the clock; a gate identical to another gate; a `tail` that
is declared and not applied; a retirement that changed only the printout.
The project's instinct — add a check — is right. The missing habit is a
test that the check can *fail*. Every new gate should ship with a
deliberately-failing input proving it bites. That single practice would
have caught six of the fifteen findings in this document, including all
three critical ones.

---

## 7. Reviewer's caveats

Stated so this document can be weighed rather than trusted.

- I read the code and ran targeted experiments; I did **not** re-run any
  exam end-to-end. The 10-year candle store is not in the repo (M-7), so I
  could not reproduce a verdict even if I wanted to. C-1's proof uses
  synthetic data with a deliberately planted regime flip — the mechanism is
  established by construction (`tail % k == 10` is arithmetic), and the
  recorded `d3_trend` / `d3_calm` result files corroborate it, but the exact
  equity numbers in a real re-run will differ.
- My effective-sample estimate in H-3 (~2,965) is a back-of-envelope
  correction for 50% overlap and ρ=0.77. It is an order-of-magnitude
  argument, not a derivation. The correct fix is to estimate dispersion
  empirically rather than to argue about which constant is right.
- I did not review `portal/`, `bot/league.py`, the stock track beyond
  `exam_1h_stocks.py`'s ledger writer, or `analysis/` in depth. `analysis/`
  matters more than it looks: `admission.py` gates entry to the exam and
  ran through the same frozen `SlowClock` code, so the Wave 3 admission
  table in `plan_v3.md` is also suspect.
- I am the same model that wrote this codebase, which is precisely the blind
  spot REVIEW.md's preamble warns about. I found bugs in code written by a
  model that shares my priors — which is weak evidence that I share its
  remaining blind spots too. A reviewer with a different architecture, or a
  human quant reading `exam_1h.py` cold, would be a genuinely independent
  third check and is worth getting.

---

*Findings enter as proposals per REVIEW.md §7. No verdict is reopened by
this document. Any rule change arising from it must be a tightening (§2.1),
and any statistic change needs an explicit §2.5 interpretation recorded in
§14.*

---

## ADDENDUM (same day) — C-4, found by implementing M-6

### C-4 · The stocks track has been trading on forming bars since it armed

The first run of the new `ops/lookahead_audit.py` (the §4.5e audit that
M-6 noted was missing) immediately found:

```
squad_decisions.csv        : 1,157 checked,   0 violations  (crypto: clean)
squad_stocks_decisions.csv :   541 checked, 534 violations  (median -2515s)
```

Root cause: `data/fetch_stocks.py` saves whatever yfinance returns, and
yfinance includes the **current, still-forming bar** as its last row.
Crypto's loader filters it (`t + 3600 <= now`); the stock loaders —
`load_stk`, `load_bars_stk` in `bot/squad_stocks.py`, and both loaders
in `backtest/exam_1h_stocks.py` — had **no completeness filter at all**.
A decision logged at 13:33 read the bar that opened at 13:30, three
minutes into its life. `quote_stk()` also priced fills off that partial
close. The median decision was **42 minutes into a forming bar.**

Consequences: this is precisely the §4.5 failure mode the charter calls
"subtler and therefore more dangerous." Under §4.5f, the affected counted
days of the entire armed stock squad are void, and the 11 stock-track
ledger rows (`1h-stk`, examined through the same unfiltered loaders) are
compromised in the *optimistic* direction — forming-bar closes leak
same-hour information into signals.

Fixed same day: completeness filter added to all four loaders
(conservative for the short 15:30 ET half-bar — visible late, never
early). The audit now runs as `ops/lookahead_audit.py` and publishes
`logs/lookahead_audit.json` either way.

Worth stating plainly: **the crypto track passed the same audit with
zero violations across 1,157 decisions.** The discipline was real; it
just was never wired up on the stocks side. This is also a clean answer
to why M-6 mattered — the audit found a critical bug within seconds of
existing.
