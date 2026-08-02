"""Daily driver: refresh data, run one league cycle, rebuild the public
page, back up the record, send the digest. Single entry point for
automation. Data/backup/digest steps are non-fatal - only the league
cycle and site build can stop the run."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "bin", "python")


def run(script, fatal, args=(), ok_codes=(0,)):
    """ok_codes exists because not every non-zero exit is a failure.
    data/refresh_intraday.py returns 1 for 'warnings only', which is its
    normal steady state: the two permanent Coinbase holes of 2025-10-25 and
    2026-05-08 are WARNING-level audit findings on nearly every pair, so a
    clean 0 is unreachable and treating 1 as a fault would cry wolf daily."""
    print(f"=== {script} {' '.join(args)} ===", flush=True)
    r = subprocess.run([PY, "-u", script, *args], cwd=ROOT)
    if r.returncode not in ok_codes:
        if fatal:
            sys.exit(r.returncode)
        print(f"WARNING: {script} exited {r.returncode} (non-fatal); "
              f"continuing.", flush=True)
    return r.returncode


run("data/refresh_daily.py", fatal=False)    # keep exam data current

# Intraday stores, and the section 8 gate that guards them.
#
# This is non-fatal ON PURPOSE and the distinction matters. A blocking audit
# (exit 2) is an execution_data condition for the INTRADAY squad only - it
# means no counted intraday cycle today. The daily league below trades a
# different store and must keep running regardless, because charter 43
# counts a halted day as a counted day at 0.00% return, and skipping the
# cycle entirely would silently drop the day from the record instead.
#
# Runtime is ~15 min for 25 pairs at 5m. It comes first because Coinbase
# serves only ~60 days of 5m data and merges accumulate: a day this does not
# run is a day of 5m history that no later run can recover.
rc_intraday = run("data/refresh_intraday.py", fatal=False, ok_codes=(0, 1))
if rc_intraday == 2:
    print("\n!!! INTRADAY GATE: execution_data condition. No counted "
          "intraday cycle today. See logs/intraday_gate.json.\n", flush=True)

# Upgrade pending OpenTimestamps receipts and stamp any new criteria doc.
# A fresh stamp is PENDING, not proof: it becomes proof only once a Bitcoin
# block confirms it and the receipt is upgraded, hours later. A pending
# receipt nobody upgrades proves nothing, and remembering to do it by hand
# is exactly the step that gets skipped. Exit 1 means still pending, which
# is the normal state for the first hours. Exit 2 means a criteria document
# no longer matches its receipt - loud, but not a reason to stop the run.
rc_stamp = run("ops/stamp.py", fatal=False, ok_codes=(0, 1))
if rc_stamp == 2:
    print("\n!!! CRITERIA RECEIPT MISMATCH. A pre-registered document was "
          "edited after stamping. Under the ratchet this is legitimate only "
          "if the change makes the criteria STRICTER.\n", flush=True)

run("bot/league.py",         fatal=True)     # the forward record
run("portal/build_site.py",  fatal=True)     # public page
run("ops/backup.py",         fatal=False)    # snapshot the record
run("bot/digest.py",         fatal=False)    # standings email/print
print("daily run complete.")
