"""
Página pública de la Liga de Futuros (NQ). Un solo HTML autocontenido
con los datos incrustados: funciona desde file://, desde el portal en
/public y se despliega en Vercel sin cambios.

Fuentes:
  futures/roster.json       -> los 10 bots (fuente única, también la usa el motor)
  futures/data_status.json  -> instantánea de la descarga de datos tick
  futures/lab_rules.json    -> reglas del laboratorio (instrumento, costos, criterio Topstep...)
  futures/updates.json      -> bitácora de hallazgos y avances (la más reciente arriba)
  backtest/results/futures_ledger.csv -> libro de exámenes de futuros (si existe)

La liga anterior (cripto y acciones, cerrada el 2026-10-22) queda
archivada sin cambios en site/archivo/cripto-acciones-2026-10-22.html.
"""
import csv, json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "site")
sys.path.insert(0, HERE)
from build_site import charter_integrity  # mismos documentos sellados


def load(rel, default):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def ledger_rows():
    p = os.path.join(ROOT, "backtest", "results", "futures_ledger.csv")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build():
    rows = ledger_rows()
    data = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "roster": load("futures/roster.json", {"bots": []}),
        "dataset": load("futures/data_status.json", {}),
        "rules": load("futures/lab_rules.json", {"rules": []}),
        "updates": load("futures/updates.json", {"entries": []}),
        "runs": len(rows),
        "runs_by_bot": {},
        "integrity": charter_integrity(),
    }
    for r in rows:
        b = r.get("bot", "?")
        data["runs_by_bot"][b] = data["runs_by_bot"].get(b, 0) + 1
    os.makedirs(OUT, exist_ok=True)
    _research_export()
    tpl = open(os.path.join(HERE, "futures_template.html"), encoding="utf-8").read()
    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site/index.html (futuros) · {len(data['roster']['bots'])} bots · "
          f"{data['runs']} corridas en el libro")


def _research_export():
    import glob, hashlib
    root = os.path.join(HERE, "..", "futures")
    def rd(p):
        raw = open(p, encoding="utf-8").read()
        return json.loads(raw), hashlib.sha256(raw.encode()).hexdigest()
    plan, ph = rd(os.path.join(root, "research_plan.json")); plan["sha256"] = ph
    vers = []
    for f in sorted(glob.glob(os.path.join(root, "strategies", "v*.json")), key=lambda x: int(os.path.basename(x)[1:-5])):
        d, h = rd(f); d["sha256"] = h; d["archivo"] = "futures/strategies/" + os.path.basename(f); vers.append(d)
    tests, _ = rd(os.path.join(root, "tests.json"))
    mp = os.path.join(root, "signal_map.json")
    mapa = rd(mp)[0].get("senales", []) if os.path.exists(mp) else []
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    json.dump({"plan": plan, "versiones": vers, "pruebas": tests.get("pruebas", []), "mapa": mapa},
              open(os.path.join(OUT, "data", "research.json"), "w", encoding="utf-8"), ensure_ascii=False)

if __name__ == "__main__":
    build()
