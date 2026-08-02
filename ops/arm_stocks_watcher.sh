#!/bin/sh
# Waits for the 10 stock exams, verifies every verdict is recorded,
# arms the stock squad, runs one cycle, commits and pushes.
cd /Users/haroonrasheed/Projects/cryptobot || exit 1
LOG=logs/stock_exam_watcher.log
i=0; while [ $i -lt 720 ]; do
  grep -q "STOCK_BATCH_COMPLETE" "$LOG" 2>/dev/null && break
  sleep 60; i=$((i+1)); done
grep -q "STOCK_BATCH_COMPLETE" "$LOG" 2>/dev/null || { echo "TIMEOUT"; exit 1; }
./.venv/bin/python - << 'PY' || exit 1
import csv, sys
need = {"s_trend_33","s_cross_7_33","s_tsmom_21","s_macd_12_26",
        "s_donch_14_7","s_volbrk_7_33","s_rsi14_reg33","s_boll_14",
        "s_calm_7_33","s_nearhi_33"}
have = {r["candidate"]: r["verdict"]
        for r in csv.DictReader(open("backtest/results/exam_ledger.csv"))
        if r.get("timeframe") == "1h-stk"}
missing = need - set(have)
if missing:
    sys.exit(f"ABORT: missing stock verdicts {sorted(missing)}")
print("all 10 stock verdicts:", dict(sorted(have.items())))
PY
n=$(grep -c "^ARMED = False" bot/seeds_stocks.py)
[ "$n" = "1" ] || { echo "ABORT: ARMED count=$n"; exit 1; }
sed -i '' 's/^ARMED = False/ARMED = True/' bot/seeds_stocks.py
./.venv/bin/python -m py_compile bot/seeds_stocks.py || {
  git checkout -- bot/seeds_stocks.py; echo "ABORT: compile"; exit 1; }
./.venv/bin/python bot/squad_stocks.py || {
  git checkout -- bot/seeds_stocks.py; echo "ABORT: first cycle"; exit 1; }
git add bot/seeds_stocks.py bot/squad_stocks_state.json logs/squad_stocks_*.csv backtest/results 2>/dev/null
git commit -m "ARM stock squad: 10/10 verdicts recorded, 20 bots live

Both tracks now forward: crypto 24/7, stocks on the RTH clock. First
cycle ran (or politely skipped if the market is closed). Counted-day
clock starts after 7 consecutive counted sessions per track." && git push origin main
echo "STOCKS_ARMED rc=$?"
