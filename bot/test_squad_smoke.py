"""Offline smoke test for bot/squad.py — synthetic data, fake quotes,
temp state. Exercises: arming, signal->entry through the s4.3 gate,
the -3% day kill switch, and the counted-day rollover. Run:
    python bot/test_squad_smoke.py
"""
import json, os, sys, tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "data"))
import seeds_crypto as SEEDS
import squad

TMP = tempfile.mkdtemp(prefix="squad_smoke_")
for attr in ("STATE", "EQLOG", "TRLOG", "DECLOG", "DAYLOG", "GATE"):
    setattr(squad, attr, os.path.join(TMP, attr.lower() + ".x"))
SEEDS.ARMED = True                     # in-memory only

import random
random.seed(4)
def synth(pair):
    px, closes, ts = 100.0, [], []
    t0 = int(datetime.now(timezone.utc).timestamp()) - 4000 * 3600
    for i in range(4000):
        px *= 1 + random.gauss(0.0006, 0.007)   # drifty + wild: gate opens
        closes.append(px); ts.append(t0 + i * 3600)
    return closes, ts

DATA = {p: synth(p) for p in SEEDS.PAIRS}
CRASH = {"on": False}

squad.load_hourly = lambda p: DATA[p]
squad.topup = lambda pairs: []
def fake_quote(pair):
    px = DATA[pair][0][-1] * (0.95 if CRASH["on"] else 1.0)
    return {"bid": px * 0.9998, "ask": px * 1.0002, "mid": px,
            "spread_pct": 0.0004}
squad.quote = fake_quote

NOW = {"t": datetime.now(timezone.utc)}
squad.utc_now = lambda: NOW["t"]

print("--- cycle 1: entries expected ---")
squad.cycle()
st = json.load(open(squad.STATE))
n_pos = sum(len(b["units"]) for b in st["bots"].values())
print(f"open positions across squad: {n_pos}")
assert n_pos > 0, "no bot entered; gate or signals broken"
assert all(len(b["units"]) <= 2 for b in st["bots"].values()), "cap!"

print("--- cycle 2: -5% crash -> day kill switches ---")
CRASH["on"] = True
squad.cycle()
st = json.load(open(squad.STATE))
halted = [n for n, b in st["bots"].items() if b["halt_day"]]
still = sum(len(b["units"]) for n, b in st["bots"].items()
            if n in halted)
print(f"bots day-halted: {len(halted)}; positions left on halted: {still}")
assert halted, "crash did not trip the -3% day switch"
assert still == 0, "halted bot still holds!"

print("--- cycle 3: next day -> rollover writes counted rows ---")
NOW["t"] = NOW["t"] + timedelta(days=1)
squad.cycle()
rows = open(squad.DAYLOG).read().strip().splitlines()
print(f"daylog rows (incl header): {len(rows)}")
print(rows[0]); print(rows[1])
assert len(rows) >= len(SEEDS.SEEDS) + 1, "missing counted-day rows"
assert ",yes," in rows[1], "day not marked counted"

dec = open(squad.DECLOG).read().strip().splitlines()
assert any(",pass" in r for r in dec), "no gate-pass decision logged"
assert "snapshot_sha" in dec[0], "decision log missing s4.5 fields"
print(f"decision rows: {len(dec) - 1} (s4.5 fields present)")
print("ALL SMOKE CHECKS PASS")
