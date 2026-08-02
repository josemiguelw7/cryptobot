"""Offline smoke test for bot/squad_stocks.py: synthetic RTH series,
temp state, market clock forced open. Verifies the shared engine runs
on stock config (entries, position cap, day kill switch, rollover)."""
import json, os, random, sys, tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import squad as Q
import seeds_stocks as SS
import squad_stocks as S

TMP = tempfile.mkdtemp(prefix="squad_stk_")
for a in ("STATE", "EQLOG", "TRLOG", "DECLOG", "DAYLOG", "GATE"):
    setattr(Q, a, os.path.join(TMP, a.lower() + ".x"))
SS.ARMED = True

random.seed(11)
def synth():
    px, cl, ts = 100.0, [], []
    t0 = int(datetime.now(timezone.utc).timestamp()) - 3000 * 3600
    for i in range(3000):
        px *= 1 + random.gauss(0.0008, 0.006)
        cl.append(px); ts.append(t0 + i * 3600)
    return cl, ts

DATA = {t: synth() for t in SS.PAIRS}
CRASH = {"on": False}
Q.load_hourly = lambda t: DATA[t]
Q.topup = lambda ts_: []
Q.quote = lambda t: (lambda px: {"bid": px*0.9998, "ask": px*1.0002,
                                 "mid": px, "spread_pct": 0.0004})(
    DATA[t][0][-1] * (0.94 if CRASH["on"] else 1.0))
NOW = {"t": datetime.now(timezone.utc)}
Q.utc_now = lambda: NOW["t"]
S.session_open = lambda now=None: True     # force the clock open

print("--- cycle 1 ---"); S.cycle()
st = json.load(open(Q.STATE))
n = sum(len(b["units"]) for b in st["bots"].values())
print("open positions:", n)
assert n > 0, "no entries on the stock squad"
assert all(len(b["units"]) <= 2 for b in st["bots"].values()), "cap breach"
assert all(k.startswith("s_") for k in st["bots"]), "wrong seed module"

print("--- cycle 2: crash ---"); CRASH["on"] = True; S.cycle()
st = json.load(open(Q.STATE))
halted = [k for k, b in st["bots"].items() if b["halt_day"]]
left = sum(len(st["bots"][k]["units"]) for k in halted)
print("day-halted:", len(halted), "| positions left on halted:", left)
assert halted and left == 0

print("--- cycle 3: next day rollover ---")
NOW["t"] += timedelta(days=1); S.cycle()
rows = open(Q.DAYLOG).read().strip().splitlines()
assert len(rows) >= 11, "missing counted-day rows"
print("daylog rows:", len(rows), "|", rows[1])

print("--- clock gate (real function) ---")
import importlib; importlib.reload(S)
SS.ARMED = True
closed = S.session_open(datetime(2026, 8, 2, 16, 0, tzinfo=timezone.utc))
assert not closed, "Sunday should be closed"
print("ALL STOCK SMOKE CHECKS PASS")
