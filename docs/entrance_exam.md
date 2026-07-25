# Entrance exam — written BEFORE any candidate is examined

Date committed: 2026-07-24
Rule: this exam may only be made STRICTER after this date, never looser.
Companion to docs/success_criteria.md (the forward-league finish line).

## Purpose

The exam is how a strategy earns a league seat. It runs on historical
data and can run any time. Passing the exam admits a candidate to the
forward league; it never, by itself, qualifies anything for real money.

## Machinery

Runner: backtest/exam.py. Execution realism is inherited from
backtest/engine.py: signals are computed on a candle close and executed
at the NEXT candle's open; every side pays 0.6% fee + 0.05% slippage.

## Windows

Rolling walk-forward windows over daily candles (data/candles_daily):
window length 183 days, stepping forward 91 days, across every pair's
full available history. A window is valid only if the candidate's
indicator warmup is fully satisfied before the window starts.

Default exam pairs (fixed, liquid, long history):
BTC-USD, ETH-USD, SOL-USD, XRP-USD, ADA-USD, DOGE-USD, LINK-USD, LTC-USD.

Selection / rotation candidates (anything that picks WHICH coins to
hold) must be examined against point-in-time universes only — the
machinery in backtest/pit_rotation.py — never against today's
universe.json. This is the +354% vs −90% lesson, made law.

## Pass bar — all five required

1. Sample size: at least 8 valid windows spanning at least 2 pairs.
2. Safety: no single window's max drawdown breaches −20% (the same
   line as the league circuit breaker).
3. Risk edge: strategy max drawdown is shallower than buy-and-hold's
   in at least 60% of windows.
4. Return: stitched (compounded) return across all test windows is at
   least buy-and-hold's stitched return over the same windows.
5. Activity: at least 4 trades in total across all windows.

## League rules restated

- One exam per candidate name, EVER. Enforced in code by
  backtest/results/exam_ledger.csv: the runner refuses a name that
  already appears there. A tweak is a new candidate with a new name.
- The runner's --selftest mode exists only to validate the harness
  (it runs a hold benchmark and a known-bad control) and records
  nothing in the ledger.
- Existing league members (BTC-HOLD, BTC-TREND, MOM-ROT) were examined
  under the prior ad-hoc exam (backtest/trend_exam.py) and are
  grandfathered. The ledger starts fresh from today.
- Backtests never appear on the league table. Forward results only.
