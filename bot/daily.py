"""Daily driver: refresh exam data, run one league cycle, rebuild the
public page, back up the record, send the digest. Single entry point
for automation. Data/backup/digest steps are non-fatal — only the
league cycle and site build can stop the run."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "bin", "python")


def run(script, fatal):
    print(f"=== {script} ===", flush=True)
    r = subprocess.run([PY, "-u", script], cwd=ROOT)
    if r.returncode != 0:
        if fatal:
            sys.exit(r.returncode)
        print(f"WARNING: {script} failed (non-fatal); continuing.",
              flush=True)


run("data/refresh_daily.py", fatal=False)   # keep exam data current
run("bot/league.py",         fatal=True)     # the forward record
run("portal/build_site.py",  fatal=True)     # public page
run("ops/backup.py",         fatal=False)    # snapshot the record
run("bot/digest.py",         fatal=False)    # standings email/print
print("daily run complete.")
