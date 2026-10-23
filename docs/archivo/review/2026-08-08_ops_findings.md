# Review item — 24h ops audit (2026-08-03)
Findings from the first full day of two-track forward trading, with
what was fixed immediately vs. what needs a Saturday decision.

## Fixed today (instrumentation / tooling only)
1. **Missed cycles were invisible.** launchd `StartInterval` skips
   while the Mac sleeps; 01:00 UTC on 2026-08-03 simply never ran and
   nothing recorded that. Now: `/api/meta` computes marked-vs-expected
   hours for the trailing 24 and the header shows `ciclos N/24`
   (amber + missing hours in tooltip when gapped).
2. **Portal `_armed()` read the docstring, not the flag** — reported
   the stocks squad UNARMED for ~3h while it was armed and trading.
   Fixed to require an `ARMED =` assignment. Class of bug: status by
   text-parsing source files. Optional hardening if it ever recurs:
   have /api/meta import the module in a subprocess instead.
3. **Book concentration was invisible.** Per-bot caps (s3) still let
   8/10 crypto bots hold ADA simultaneously — a fully correlated
   squad book. Both squad panels now show `concentración: ADA×8 ...`
   with an amber warning at ≥70% of bots in one symbol. Not a breach;
   now a visible fact for the weekly review + P-correlation work.

## Saturday decisions requested
4. **Dirty-tree exams.** Every exam-ledger row to date carries a
   `-dirty` git hash — pre-registration hashes that don't pin an
   exact tree. Proposal (stricter, ratchet-direction): `exam.py`
   refuses to record a verdict when `bot/` or `backtest/` have
   uncommitted changes. Cheap habit fix meanwhile: commit before
   exams; today's session is committed as of this audit.
5. **Sleep policy (owner action, needs sudo):** `sudo pmset -c sleep 0`
   keeps hourly cycles alive on AC power. Alternative: accept
   occasional gaps now that they're visible. Charter impact of a gap:
   none on counted-day integrity (decisions read completed bars), but
   entries/exits are delayed by the gap length.
6. **SKIP-cap volume** (294/day) is the position cap working as
   designed against correlated signals — no change proposed, noted so
   the number doesn't surprise anyone at week 12.
