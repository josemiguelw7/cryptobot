#!/bin/sh
# Chained: waits for the crypto exam batch AND the arming watcher to
# finish, then runs the 10 stock exams sequentially and pushes results.
# Does NOT arm stocks (engine pending; docs/stocks_standard.md delta 5).
cd /Users/haroonrasheed/Projects/cryptobot || exit 1
i=0; while [ $i -lt 720 ]; do
  grep -q "BATCH_COMPLETE" logs/exam_1h_batch.log && break
  sleep 120; i=$((i+1)); done
grep -q "BATCH_COMPLETE" logs/exam_1h_batch.log || { echo "TIMEOUT crypto batch"; exit 1; }
while pgrep -f "exam_1h.py --candidate" >/dev/null || pgrep -f "arm_watcher.sh" >/dev/null; do sleep 30; done
echo "crypto lane clear; starting stock exams $(date -u)"
for s in s_trend_33 s_cross_7_33 s_tsmom_21 s_macd_12_26 s_donch_14_7 s_volbrk_7_33 s_rsi14_reg33 s_boll_14 s_calm_7_33 s_nearhi_33; do
  echo "===== EXAM $s ====="
  ./.venv/bin/python backtest/exam_1h_stocks.py --candidate "$s"
  echo "exit=$? done-$s"
done
echo "STOCK_BATCH_COMPLETE"
git add backtest/results && git commit -q -m "Stock seed exams: 10 verdicts recorded (timeframe=1h-stk)

One exam per name forever; shared global K ledger. Verdicts label
candidate/control; ARMED waits for the market-hours engine." && git push -q origin main
echo "PUSHED rc=$?"
