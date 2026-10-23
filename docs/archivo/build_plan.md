# Build Plan — full backlog, ready to execute top-to-bottom

Date: 2026-07-24. Companion to docs/success_criteria.md and
docs/entrance_exam.md. Each item has a Done-when. Work the waves in
order; items inside a wave share context and are cheapest together.

## Wave 1 — Harness rebuild (one focused session)

### W1.1 Shared strategy module (improvement #1)
Create bot/strategies.py: one Strategy interface (name, warmup,
declared pairs/universe, per-bar step(history) -> target weight 0..1,
stateful allowed). exam.py and league.py BOTH import it; delete the
duplicated trend logic from each. The strategy that passes the exam
must be byte-for-byte the strategy that trades forward.
Done-when: BTC-TREND's live target and an exam trend signal for the
same date come from the same function call, verified by a small test.

### W1.2 Stateful + fractional exam simulation
Replace exam.py's precomputed 0/1 position arrays with a per-bar loop
driving Strategy.step(); support path-dependent logic (stop-losses
need entry price) and fractional weights (position sizing). Fees +
slippage charged on every weight change, per side, as in engine.py.
Done-when: a demo stop-loss candidate produces different trades than
plain trend on the same data, and --selftest still behaves correctly.

### W1.3 Exam↔live signal parity (#11)
league.py daily_closes() almost certainly receives today's PARTIAL
candle from Coinbase; the exam trades completed candles only. Fix:
drop the final candle when its date == today (UTC) before computing
signals, with a comment explaining why. 
Done-when: a same-day manual check shows league target and exam
signal agree for BTC-TREND on completed data.

### W1.4 Exam provenance (#2)
Ledger gains columns: git_hash (refuse or flag dirty tree), and a
per-pair data fingerprint (row count + last timestamp + checksum).
Zip the exact input CSVs to backtest/results/data_snapshots/<name>/.
Done-when: every new ledger row is reproducible from its snapshot.

### W1.5 Data linter (#13)
data/lint_candles.py: flag date gaps, duplicate timestamps, zero or
negative prices, absurd single-bar moves (likely bad data). exam.py
runs the linter first and aborts on hard errors.
Done-when: linter passes on the 8 exam pairs; a deliberately
corrupted copy trips it.

## Wave 2 — Protection & observability (quick wins)

### W2.1 Backups (#9)
Nightly zip of bot/*state*.json + logs/*.csv to backups/YYYY-MM-DD.zip
(keep ~60), added to daily.py as a non-fatal step. Code lives in git.
Done-when: first snapshot exists + one-line restore note here.

### W2.2 Crash-safe state (#12)
league.py: write state atomically (temp file + os.replace). On start,
reconcile the trade log against state and WARN on mismatch (a crash
mid-cycle currently leaves logged trades the state never saved).
Runbook: if a 9am run half-completes, read the warning, compare
logs/league_trades.csv tail vs league_state.json, fix state to match
the log (the log is ground truth), rerun bot/daily.py manually.

### W2.3 Morning digest + missed-day alarm (#8)
bot/digest.py: after the daily run, email standings, daily deltas,
and each member's distance-to-breaker via Resend. Second launchd job
at 18:00 checks logs/league_equity.csv has today's rows; if not,
send a loud alert email. Resend API key in macOS keychain or env —
NEVER in the repo.

### W2.4 Weekly universe top-up
data/refresh_all.py (like download_all_daily.py but WITHOUT the
skip-existing behavior) run weekly (Sun 10:00 launchd) so the
411-coin set stays current for future point-in-time rotation exams.

## Wave 3 — Exam & league upgrades

### W3.1 Fee stress (#3)
Verdict stays judged at base fees, but every exam report also prints
a 1.5x fees+slippage table. Before real money: verify actual
Coinbase tier pricing and re-check the passer at those rates.

### W3.2 Overlap honesty + multiple-testing counter (#4)
Windows overlap ~50% (183-day windows, 91-day step), which inflates
the apparent sample. Report a non-overlapping set (step=183)
alongside. Ledger also records candidates_examined_to_date on every
row — enough exams and something passes by luck; make that visible.

### W3.3 Regime tagging (#6)
Tag each window (and league day, in the digest) bull/bear/chop —
e.g. BTC vs its 200-day SMA plus a low-range chop flag. Exam report
gains a per-regime table: a candidate that only wins in one regime
is a bet on that regime repeating.

### W3.4 Real risk metrics everywhere (#7)
Use metrics.compute (Sharpe/Sortino/Calmar/CAGR) in exam reports AND
the portal league table. Add ETH-HOLD and a BTC/ETH 50-50 blend as
benchmark league members (benchmarks, not candidates; needs W3.5).

### W3.5 Late-joiner patch
league.load() currently initializes members only when no state file
exists. Patch: any STRATS member missing from state gets created
with a fresh created date. Required for admitting ANY new member.

### W3.6 Research journal (#15)
Notion journal, one entry per candidate: hypothesis, why it should
work, exam result, exactly which windows/pairs killed it. The ledger
stops name-recycling; the journal stops IDEA-recycling. First three
entries: tonight's trend_150/200/250 post-mortems.

## Wave 4 — Candidates (the point of all this)

### W4.1 Design & pre-register
In bot/strategies.py + a journal entry BEFORE any exam:
- Trend + hard stop (e.g. T200-S10: 200d trend, exit −10% from
  entry, re-enter on fresh signal).
- Volatility-targeted sizing (weight = target_vol / realized_vol,
  capped at 1) — attacks the −20% window rule directly.
- Optionally a BTC/ETH-only declared-universe variant. Declared in
  the definition up front = strategy design; adjusted after a fail
  = goalpost-moving. The rules hold: new name, one exam, ever.

### W4.2 Examine, then admit
Run exams (one shot each, ledger-recorded). Any passer: human
decision to admit via W3.5, own start date, own 90-day clock.

## Wave 5 — Toward real money (before late October)

### W5.1 Money gate amendment (#5) — DONE 2026-07-24
success_criteria.md amended (stricter): sustained confirmation over
the strategy's whole league life, not one lucky 90-day stretch.

### W5.2 Shadow execution layer (#10)
bot/execute.py places NO orders; it logs every order it WOULD place
(pair, side, size, price) while validating auth, balances, sizing
and error handling against the real Coinbase API read-only. Real
trading later becomes a reviewed switch-flip, not a rushed build.

### W5.3 Real-money rulebook (#14)
docs/money_rules.md, written BEFORE any funding, stricter-only:
- Security: Coinbase API keys trade-only, withdrawals disabled,
  stored in macOS keychain, never in the repo. Worst case of any
  bug or breach must be "bad trades", never "drained account".
- Capital policy: pre-committed starting size, scale-up rules, and
  de-funding triggers (what pulls a live strategy's money). Exit
  rules decided while losing money is how discipline dies.
- Tax: selling existing Coinbase holdings creates taxable events;
  confirm lot-tracking approach with a tax professional first.

## Sequencing summary

Wave 1 next session (W1.1–W1.5 together). Wave 2 same week (each
item is small). Wave 3 as exam upgrades before the next candidate
batch. Wave 4 is the recurring loop from then on. Wave 5 only
matters once something is 60+ days into a clean forward run.

Standing rules that govern all of it: success_criteria.md and
entrance_exam.md may only get stricter; one exam per name, ever;
backtests never appear on the league table; running members are
never edited; real money moves only through the W5 gates.
