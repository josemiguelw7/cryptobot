# Intraday (hourly) entrance standard — PRE-COMMITMENT

Written 2026-07-31, BEFORE any hourly backtest has been run and before
backtest/exam_1h.py exists. That ordering is the entire point: this bar
is set while we are still ignorant of the results, so it cannot be
drawn around a number we have already seen.

Same standing rule as entrance_exam.md: **this document may only be
made STRICTER, never looser.** Loosening requires a written amendment
with evidence of a specification bug, as in exam_amendment_001.md.

## Why this document is deliberately hostile to intraday

The owner's stated interest is day trading: many trades, short holds.
Everything measured so far argues the opposite:

  - corr(trades per window, edge vs buy-and-hold) = -0.783
    across 12 strategies x 20 crypto pairs
  - round trip cost at current fees = 1.30%; only ~8 round trips/year
    are affordable before friction alone eats 10% of capital
  - at 1 trade/day, friction alone consumes 99.1% of capital per year
    at 0.60%/side, and still 66.6% at 0.10%/side
  - in a 20-strategy x 12-stock screen at NEAR-ZERO fees, buy-and-hold
    still beat all 20 timing strategies

So the prior is strongly against intraday. This standard exists to give
intraday a fair chance to overturn that prior with evidence, not to
give it an easier door because the daily door was unwelcoming. If a
strategy cannot clear a bar this high, deploying it would lose money
slowly and confidently.

## Data

  - Source: data/candles/{PAIR}_3600s.csv (25 pairs available).
    NOTE: an earlier draft of this document cited a non-existent
    data/candles_1h/ directory. Corrected 2026-07-31 after verifying
    on disk. The data does exist; the path was wrong.
  - VERIFIED COVERAGE (2026-07-31): all eight universe pairs have
    8,750 hourly bars = ~364 days, spanning 2025-07-24 to 2026-07-24.
    The feed is currently ~1 week stale and MUST be refreshed before
    any exam run.
  - Universe (FIXED, chosen now, before any results):
        BTC-USD, ETH-USD, SOL-USD, XRP-USD, ADA-USD, DOGE-USD,
        LINK-USD, LTC-USD
    Same eight as the daily exam, so daily and hourly results are
    directly comparable on identical assets.
  - Bars must be COMPLETED (drop the in-progress hour), mirroring
    W1.3 so exam and live signals see identical data.
  - Gap policy: any window containing a gap of >6 consecutive missing
    hours is DISCARDED, not interpolated. Exchange outages must not be
    silently converted into fake price continuity.

## THE BINDING LIMITATION: one year, one regime

Only ~364 days of hourly history exist. After reserving the 120-day
holdout, ~244 days remain for the main windows. At 90-day windows
stepping 45 days that yields ~4 windows per pair, ~32 across eight
pairs — which clears criterion 1 only barely, and every one of those
windows comes from the SAME twelve-month market regime.

The daily exam spans multiple years and several regimes. The hourly
exam cannot. This means:

  - A PASS on this standard is much weaker evidence than a daily pass.
    It says "worked in one particular year," not "works."
  - Therefore a passing hourly strategy enters the league as a
    CANDIDATE ONLY and, regardless of forward performance, may not be
    proposed for real money until hourly history covers at least two
    distinct regimes (a sustained drawdown AND a sustained rally).
  - Strategy lookbacks must be hourly-appropriate. Porting a 200-DAY
    lookback to hourly bars would consume 200 days of warmup and leave
    almost no window budget. Lookbacks are measured in BARS here.

This limitation is recorded now, before results, so that a lucky pass
cannot later be presented as stronger evidence than it is.

## Windows

  - Window = 90 calendar days (2160 hourly bars).
  - Step = 45 days (50% overlap), matching the daily exam's structure.
  - Warmup precedes the window, as in simulate_window().
  - HOLDOUT: the most recent 120 days of hourly data are RESERVED and
    must not be touched during development. They are graded once, at
    the end, and reported separately. If a strategy passes the main
    windows and fails the holdout, it FAILS.

## Costs

  - Base: FEE 0.60%/side, SLIP 0.05%/side (current Coinbase taker).
  - Intraday slippage is worse than daily, not equal. If the exchange
    moves to maker-only limit orders, the fee may be reduced ONLY if
    the simulation also models non-fill risk. A maker order that is
    not filled is not a free discount; unmodelled, it is a lie.

## Pass criteria (ALL must hold)

  1. SAMPLE      >= 24 windows across >= 4 pairs.
  2. SAFETY      drawdown never worse than buy-and-hold in the same
                 window (relative test, per amendment 001).
  3. RISK EDGE   shallower drawdown than buy-and-hold in >= 60% of
                 windows.
  4. RETURN      stitched return >= buy-and-hold charged the SAME
                 fees (net-to-net, per amendment 001 fix 4a).
  5. ACTIVITY    >= 4 trades total.
  6. FEE STRESS  must ALSO pass criteria 2-4 at 1.5x fees and slip.
                 (Reported-only in the daily exam; BINDING here,
                 because intraday's whole risk is cost sensitivity.)
  7. BEATS DAILY stitched return >= the best DAILY strategy that has
                 passed its own exam on the same pairs and period.
                 If no daily strategy has passed, the comparison is
                 against buy-and-hold net of fees, i.e. criterion 4.
                 Rationale: hourly adds complexity, cost, latency, and
                 failure modes. It must EARN that by beating the
                 simpler thing, not merely by beating nothing.
  8. HOLDOUT     passes criteria 2-4 on the reserved 120-day holdout.
  9. NOT LUCK    permutation p-value < 0.05 (validation.py), AND
                 observed Sharpe > the luck hurdle from
                 expected_max_sharpe(n_trials) where n_trials is the
                 cumulative count in exam_ledger.csv plus every
                 hourly variant screened. As of writing that count is
                 10 recorded + ~30 screened.

## Governance

  - One exam per candidate name, EVER — same as the daily ledger.
  - Hourly candidates are recorded in the same exam_ledger.csv with an
    added `timeframe` column, so the multiple-testing count is global.
    Testing the same idea at a new timeframe is still another trial.
  - A pass admits the strategy to the LEAGUE only. It does not admit
    it to real money; success_criteria.md still governs that, and its
    90-day forward requirement is unchanged.
  - Research screening on hourly bars is unlimited and unrecorded via
    research.py, exactly as with daily. Screening is free; examining
    is once.

## Statistical warning that must accompany any hourly result

Hourly bars are NOT independent observations. 24 hourly bars carry far
less than 24x the information of one daily bar, because returns are
autocorrelated and volatility clusters. Any hourly result will LOOK
more statistically impressive than it is, purely from sample-size
inflation. Criterion 9 exists because of this. Do not quote hourly
t-statistics without it.

## Predicted outcome, recorded in advance

Recorded so it can be checked against reality rather than remembered
selectively: I expect ZERO strategies to pass this standard at 0.60%
fees, and expect criterion 4 (return net of fees) and criterion 6 (fee
stress) to be the binding failures. I expect a handful to pass
criteria 2 and 3, because trading less time in the market genuinely
does reduce drawdown — while costing more than it saves.

If that prediction is wrong, that is the most valuable finding this
project could produce, and the pre-commitment above is what will make
it believable.
