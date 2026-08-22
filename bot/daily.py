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


STATE = os.path.join(ROOT, "logs", "once_daily.json")


def once_daily(script, ok_codes=(0,), args=(), done_codes=None):
    """Run a step at most once per UTC day, no matter how often this driver
    fires.

    This exists because com.cryptobot.daily is NOT a 9am job - it is
    StartInterval 3600, i.e. every hour, and it has been live since
    2026-07-31. An hourly league cycle is intentional. An hourly 15-minute
    intraday refresh is not: it would be roughly six hours a day of Coinbase
    API calls to re-fetch bars already on disk, and it would hammer the
    OpenTimestamps calendars 24 times a day for no gain.

    Keyed on the UTC date of the last SUCCESSFUL run rather than a fixed
    clock time, deliberately. A fixed 9am job on a laptop that happens to be
    closed at 9am simply does not run, and for the 5m store a skipped day is
    unrecoverable - Coinbase serves only ~60 days at that granularity. This
    way the first fire after the machine wakes picks the day up.

    A failed run is not recorded, so it will be retried on the next hourly
    fire rather than waiting until tomorrow.

    done_codes separates "did not fail" from "finished the job". ops/stamp.py
    returns 1 while a receipt is still waiting on a Bitcoin block, which is
    not an error but is not done either. Marking that as done would park the
    upgrade until tomorrow; leaving it unrecorded retries every hour until
    the attestation actually lands, then stops."""
    import json
    from datetime import datetime, timezone
    today = f"{datetime.now(timezone.utc):%Y-%m-%d}"
    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE))
        except Exception:
            state = {}
    if state.get(script) == today:
        print(f"=== {script} === already ran today ({today} UTC); skipping.",
              flush=True)
        return 0
    rc = run(script, fatal=False, args=args, ok_codes=ok_codes)
    if rc in (done_codes if done_codes is not None else ok_codes):
        state[script] = today
        try:
            json.dump(state, open(STATE, "w"), indent=2)
        except Exception as e:
            print(f"WARNING: could not write {STATE}: {e}", flush=True)
    return rc


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
rc_intraday = once_daily("data/refresh_intraday.py", ok_codes=(0, 1))
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
rc_stamp = once_daily("ops/stamp.py", ok_codes=(0, 1), done_codes=(0,))
if rc_stamp == 2:
    print("\n!!! CRITERIA RECEIPT MISMATCH. A pre-registered document was "
          "edited after stamping. Under the ratchet this is legitimate only "
          "if the change makes the criteria STRICTER.\n", flush=True)

run("bot/league.py",         fatal=True)     # the forward record


def log_cycle_gap():
    """Record missed hourly cycles as first-class events.

    launchd's StartInterval does not fire while the Mac sleeps, so a
    gap leaves no trace anywhere except a hole in the equity log — the
    01:00 UTC 2026-08-03 gap was found by hand. A gap does NOT void a
    counted day (decisions read only completed bars, s4.5b), so this
    is deliberately not an execution_data event; it is an operational
    record for the weekly review, written before this cycle marks.
    """
    import csv as _csv
    from datetime import datetime as _dt, timezone as _tz
    eq = os.path.join(ROOT, "logs", "squad_equity.csv")
    if not os.path.exists(eq):
        return
    try:
        rows = list(_csv.DictReader(open(eq)))
        if not rows:
            return
        last = _dt.fromisoformat(rows[-1]["time"])
        now = _dt.now(_tz.utc)
        gap_h = (now - last).total_seconds() / 3600
        if gap_h < 1.75:                      # normal hourly cadence
            return
        missed = int(gap_h) - 1
        path = os.path.join(ROOT, "logs", "cycle_gaps.csv")
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = _csv.writer(f)
            if new:
                w.writerow(["detected_utc", "last_cycle_utc", "gap_h",
                            "cycles_missed", "note"])
            w.writerow([now.isoformat(), rows[-1]["time"],
                        f"{gap_h:.2f}", missed,
                        "launchd did not fire (likely system sleep)"])
        print(f"  !! CYCLE GAP: {gap_h:.1f}h since last mark "
              f"(~{missed} cycles missed) -> logs/cycle_gaps.csv")
    except Exception as e:
        print(f"  gap check failed (non-fatal): {e}")


log_cycle_gap()

# Intraday squad (charter: docs/intraday_success_criteria.md). Hourly by
# design — this is the cadence the whole plist exists for. While the seed
# roster in bot/seeds_crypto.py is unarmed this is a one-line no-op; once
# armed it is forward record, so it is fatal like the league.
run("bot/squad.py",          fatal=True)

# Stock squad. Same engine, market clock: outside 9:30-16:00 ET it
# marks and exits 0, so the hourly plist can fire it unconditionally.
run("bot/squad_stocks.py",   fatal=True)

# Diversity gauge (E2.6). Pure observation: reads state, writes its own
# log, gates nothing and cannot influence a decision - so it is safe
# inside a live epoch and is NOT fatal. Exists because on 2026-08-04
# eight of ten stock bots held identical books and nothing said so.
run("bot/diversity.py",      fatal=False, args=("--log",))

# Medicion T3 (docs/decisions.md 2026-08-22). Las tres son SOLO LECTURA:
# no importan el motor, no tocan estado, escriben a logs propios y no
# pueden influir en una decision. Por eso son seguras dentro de una
# epoca viva y NO son fatales.
run("ops/bench_bh.py",       fatal=False)   # comprar-y-sostener
run("ops/counterfactual.py", fatal=False)   # senales rechazadas
# Cable trampa. Existe porque el 2026-08-22 se descubrio que dos smoke
# tests llevaban semanas fallando en silencio (cap breach), y solo
# corrian invocandolos a mano. No fatal: ver cabecera de selfcheck.py.
run("ops/selfcheck.py",      fatal=False)

run("portal/build_site.py",  fatal=True)     # public page
run("ops/backup.py",         fatal=False)    # snapshot the record
run("bot/digest.py",         fatal=False)    # standings email/print
print("daily run complete.")
