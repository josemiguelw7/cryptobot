"""Exporta los días de replay de una prueba: las 10 mejores y 10 peores operaciones y 20 al azar (semilla fija)
-> futures/lab/results/<id>/days/<fecha>.json (mismo formato que el Explorador).
  python -m engine.export_replays P001
"""
import hashlib, json, os, subprocess, sys
import numpy as np
from . import config

EXPORT = os.path.join(config.LAB, "export_day.py")


def main():
    test_id = sys.argv[1]
    d = os.path.join(config.RESULTS, test_id)
    tr = json.load(open(os.path.join(d, "trades.json")))
    if not tr:
        print("sin operaciones"); return
    order = sorted(range(len(tr)), key=lambda i: tr[i]["net_usd"])
    pick = set(order[:10] + order[-10:])
    rng = np.random.default_rng(int(hashlib.sha256(test_id.encode()).hexdigest()[:8], 16))
    pick |= set(rng.choice(len(tr), size=min(20, len(tr)), replace=False).tolist())
    dates = sorted({tr[i]["date"] for i in pick})
    out = os.path.join(d, "days"); os.makedirs(out, exist_ok=True)
    for date in dates:
        p = os.path.join(out, f"{date}.json")
        if os.path.exists(p):
            continue
        with open(p, "w") as f:
            subprocess.run([sys.executable, EXPORT, date, "ny"], stdout=f, check=True)
    print(f"{test_id}: {len(dates)} días de replay exportados")


if __name__ == "__main__":
    main()
