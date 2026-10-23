# Success criteria — written BEFORE the league started

Date committed: 2026-07-24
Rule: these criteria may only be made STRICTER after this date, never looser.

A strategy is declared SUCCESSFUL and eligible for a real-money
discussion only if, over at least 90 consecutive days of live forward
paper trading (no backtest counts):

1. Total return beats BTC-HOLD (buy-and-hold benchmark) over the
   same window, measured after all simulated fees and slippage.
2. Maximum drawdown is smaller than BTC-HOLD's over the same window.
3. It never tripped its -20% circuit breaker.
4. It made at least 4 decisions (rebalances/signals) in the window —
   so we know the result reflects the strategy, not one lucky entry.

A strategy is declared FAILED and retired if at any point:
- It trips the circuit breaker, or
- After 90 days it fails criterion 1 or 2.

League rules:
- Every strategy takes its backtest entrance exam ONCE. Tweaking a
  strategy creates a NEW candidate with a new name and a new exam.
- The website shows forward results only. Backtests never appear on
  the league table.

## Amendment 2026-07-24 (stricter): sustained confirmation

A strategy is funded only if it satisfies criteria 1–4 not merely
over one 90-day window, but continuously: at the moment of any
funding decision, the window from the strategy's league start date
to today must ALSO satisfy criteria 1 and 2. One qualifying 90-day
stretch is not enough; the strategy must be ahead of BTC-HOLD, with
a smaller drawdown, over its entire league life when funded.
