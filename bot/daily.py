"""Daily driver: refresh exam data (non-fatal), run one league cycle,
then rebuild the public page. Single entry point for automation."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "bin", "python")

# Data refresh keeps backtest/exam CSVs current. The league fetches
# live prices itself, so a refresh failure must never block the cycle.
print("=== data/refresh_daily.py ===", flush=True)
r = subprocess.run([PY, "-u", "data/refresh_daily.py"], cwd=ROOT)
if r.returncode != 0:
    print("WARNING: data refresh failed; continuing with league cycle.",
          flush=True)

for script in ("bot/league.py", "portal/build_site.py"):
    print(f"=== {script} ===", flush=True)
    r = subprocess.run([PY, "-u", script], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(r.returncode)
print("daily run complete.")
