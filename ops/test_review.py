"""Guards of ops/review.py must be shown to FIRE (charter_v2 s5.1)."""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review

SAT = datetime(2026, 9, 19, 9, 0, tzinfo=review.CT)
FRI = datetime(2026, 9, 18, 9, 0, tzinfo=review.CT)

def st():
    return {"bots": {"a": {"halt_review": True, "benched": False},
                     "b": {"halt_review": False, "benched": True}}}

# 1. not Saturday -> refused, state untouched
s = st()
try:
    review.resume(s, ["a"], FRI); raise SystemExit("FAIL: resumed on Friday")
except PermissionError:
    assert s["bots"]["a"]["halt_review"] is True

# 2. benched bot -> refused even on Saturday
s = st()
try:
    review.resume(s, ["b"], SAT); raise SystemExit("FAIL: resumed a benched bot")
except PermissionError:
    assert s["bots"]["b"]["benched"] is True

# 3. happy path
s = st()
assert review.resume(s, ["a"], SAT) == ["a"]
assert s["bots"]["a"]["halt_review"] is False
print("test_review: PASS (3/3)")
