"""
Nightly backup of the forward record (build plan W2.1). The league
state + logs ARE the project; a corrupted state file ends a streak
permanently. Zips them to backups/YYYY-MM-DD.zip, keeps the last ~60.
Non-fatal step in daily.py.

Restore: unzip backups/<date>.zip into the repo root, overwriting
bot/league_state.json and logs/*.csv with the snapshot's versions.

Usage: python ops/backup.py
"""
import os, zipfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEST = os.path.join(ROOT, "backups")
KEEP = 60

FILES = [
    "bot/league_state.json", "bot/state.json",
    "logs/league_equity.csv", "logs/league_trades.csv",
    "logs/paper_trades.csv", "logs/equity_history.csv",
]


def main():
    os.makedirs(DEST, exist_ok=True)
    out = os.path.join(DEST, f"{date.today().isoformat()}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            p = os.path.join(ROOT, rel)
            if os.path.exists(p):
                z.write(p, rel)
    snaps = sorted(f for f in os.listdir(DEST) if f.endswith(".zip"))
    for old in snaps[:-KEEP]:
        os.remove(os.path.join(DEST, old))
    print(f"backup -> {out} ({len(snaps)} snapshots kept)")


if __name__ == "__main__":
    main()
