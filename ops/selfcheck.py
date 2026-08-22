#!/usr/bin/env python3
"""selfcheck.py -- cable trampa visible.

Propuesta docs/decisions.md 2026-08-22 (T3, higiene).

Los smoke tests codifican invariantes del charter (p.ej. el tope de
posiciones). El 2026-08-22 se descubrio que dos llevaban SEMANAS
fallando sin que nadie lo viera, porque solo corren invocandolos a mano.
Este modulo los ejecuta cada ciclo y deja el resultado en un log.

NO ES FATAL POR DISENO. Un test que hoy falla por una discrepancia
conocida y documentada (charter dice 2, seeds dicen 3 y 4) no debe
detener el registro forward -- eso destruiria evidencia por un problema
de gobernanza ya registrado. El objetivo es VISIBILIDAD, no bloqueo.
Si el propietario resuelve los topes y quiere que sea bloqueante,
cambiar `fatal=False` a True en bot/daily.py es una linea.

Uso:  .venv/bin/python ops/selfcheck.py
"""
import os
import sys
import csv
import subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOG = os.path.join(ROOT, "logs", "selfcheck.csv")

TESTS = ["bot/test_squad_smoke.py", "bot/test_squad_stocks_smoke.py",
         "bot/test_stats.py", "bot/test_slowclock.py"]


def last_line(txt):
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    return lines[-1][:180] if lines else ""


def main():
    now = datetime.now(timezone.utc).isoformat()
    rows, failed = [], []
    for t in TESTS:
        path = os.path.join(ROOT, t)
        if not os.path.exists(path):
            rows.append([now, t, "MISSING", ""])
            continue
        r = subprocess.run([PY, "-u", path], cwd=ROOT,
                           capture_output=True, text=True, timeout=600)
        ok = r.returncode == 0
        detail = "" if ok else last_line(r.stderr or r.stdout)
        rows.append([now, t, "PASS" if ok else "FAIL", detail])
        if not ok:
            failed.append((t, detail))

    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["utc", "test", "status", "detail"])
        w.writerows(rows)

    n_ok = sum(1 for r in rows if r[2] == "PASS")
    print(f"  selfcheck: {n_ok}/{len(rows)} PASS")
    for t, d in failed:
        print(f"  [FAIL] {t}: {d}")
    if failed:
        print("  ^ NO detiene el ciclo por diseno. Ver docs/decisions.md "
              "2026-08-22 (topes sin resolver).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
