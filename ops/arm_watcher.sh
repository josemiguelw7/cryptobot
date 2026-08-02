#!/bin/sh
# One-shot: waits for the exam batch, verifies all 10 verdicts, arms the
# squad, runs the first cycle, commits. Owner approval recorded in
# docs/seed_proposals_crypto.md (2026-08-02). Aborts loudly otherwise.
cd /Users/haroonrasheed/Projects/cryptobot || exit 1
LOG=logs/exam_1h_batch.log
i=0; while [ $i -lt 240 ]; do
  grep -q "BATCH_COMPLETE" "$LOG" && break; sleep 60; i=$((i+1)); done
grep -q "BATCH_COMPLETE" "$LOG" || { echo "TIMEOUT waiting for batch"; exit 1; }
./.venv/bin/python - << 'PY' || exit 1
import csv, sys
need = {"h_trend_168","h_cross_24_168","h_tsmom_72","h_macd_12_26",
        "h_donch_48_24","h_volbrk_24_96","h_rsi14_reg168","h_boll_48",
        "h_calm_24_168","h_nearhi_168"}
rows = [r for r in csv.DictReader(open("backtest/results/exam_ledger.csv"))
        if r.get("timeframe") == "1h"]
have = {r["candidate"]: r["verdict"] for r in rows}
missing = need - set(have)
if missing:
    sys.exit(f"ABORT: missing verdicts for {sorted(missing)}")
print("all 10 verdicts:", dict(sorted(have.items())))
PY
n=$(grep -c "^ARMED = False" bot/seeds_crypto.py)
[ "$n" = "1" ] || { echo "ABORT: ARMED flag count=$n"; exit 1; }
sed -i '' 's/^ARMED = False/ARMED = True/' bot/seeds_crypto.py
./.venv/bin/python -m py_compile bot/seeds_crypto.py || {
  echo "ABORT: compile"; git checkout -- bot/seeds_crypto.py; exit 1; }
./.venv/bin/python bot/squad.py || {
  echo "ABORT: first armed cycle failed"; git checkout -- bot/seeds_crypto.py; exit 1; }
git add bot/seeds_crypto.py backtest/results bot/squad_state.json logs/squad_*.csv 2>/dev/null
git commit -m "ARM intraday squad: 10/10 exam verdicts recorded, shakedown begins

Exams per docs/intraday_standard.md, one per name forever. Verdicts in
exam_ledger.csv (timeframe=1h) + per-window CSVs. Owner adoption and
pre-registered predictions: docs/seed_proposals_crypto.md. First armed
cycle ran; hourly launchd fires continue via bot/daily.py. Counted-day
clock starts after 7 consecutive counted days (charter s3)." && git push origin main
echo "ARMED_AND_PUSHED rc=$?"
