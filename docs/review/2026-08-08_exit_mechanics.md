# Review item — exit mechanics (take-profit hypothesis)
**Prepared:** 2026-08-03 · **For:** Saturday review 2026-08-08 09:00 CT
**Origin:** owner observation ("bots were up and gave it back — add a
10% stop / 30% take-profit?")

## What was built today (all non-governance instrumentation)
1. **MFE/MAE tape** in `bot/squad.py` — every closed trade now logs
   `mfe_pct`/`mae_pct` (peak/trough mid sampled each cycle). Both
   squads inherit; open positions were backfilled from candles.
2. **`bot/exit_autopsy.py`** — counterfactual replay of closed trades
   under TP/stop/trailing grids at charter costs. Zero exam-ledger
   cost. First report: `docs/review/exit_study_2026-08-03.md`.
3. **Portal fee-drag + BTC-HOLD strip** — `/api/squad_costs`, shown
   under each squad's capital strip. Derived from logs; no new bot.
4. **`Bracket` + `TrailStop` classes** in `bot/strategies.py` —
   written and unit-sanity-checked, deliberately NOT registered.

## Finding (12 closed trades, 2026-08-03)
- Actual net −$345.34; gross −$169.00; **fees/spread −$176.34 (51%)**.
- **Max MFE across all trades: +1.27%. Median ≈ +0.1%.**
- TP counterfactuals at 2/3/5/10/20/30%: **zero would ever have
  fired.** Stops at 3% fire once, −$2 worse. Trailing: same.
- Conclusion so far: the observed "gains" were sub-1% marks, smaller
  than the ~1.2% round-trip cost. Nothing existed for a TP to lock.
  This is consistent with move_scale (1h median |move| 0.31%) and the
  exam's 0/10 PASS prediction — it is the cost wall, not the exits.

## Decisions requested Saturday
1. **Name + exam bracket/trail variants now?** Recommendation: **no —
   defer.** Each name is a one-shot exam and raises K for everyone.
   Trigger to revisit: any week's MFE distribution showing p75 above
   ~2× round-trip cost. Re-run `exit_autopsy` at each review (free).
2. **§2.5 interpretation to record if/when bred:** is a new exit
   mechanism (TP) a legal "one parameter mutation" (§9.6), or does it
   require the strict reading (new mechanism ≠ parameter)? Strictest
   defensible reading governs until resolved.
3. **Optional ratchet amendment** (needs 24h cooling-off via the
   intervention log BEFORE Saturday if wanted): none proposed —
   existing §8 kill switches + P1 already cover the fee-drag concern.

## Standing instruction
Run before every review:
`.venv/bin/python bot/exit_autopsy.py --md docs/review/exit_study_$(date +%F).md`
