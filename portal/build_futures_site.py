"""
Página pública del Laboratorio NQ. Un solo HTML con pestañas (Floor, Pruebas, Estrategias,
Explorador, Bitácora) que se arma desde fragmentos de portal/ y publica los datos en site/data/.

Fuentes (todas en futures/):
  roster.json, data_status.json, lab_rules.json, updates.json           -> pestaña Bitácora
  research_plan.json, protocol.json, strategies/v*.json, tests.json,
  signal_map.json, sessions_manifest.json, costs.json, topstep_rules.json,
  glossary.json, lab/registry/*.jsonl, lab/results/<id>/                 -> Pruebas y Estrategias
Salida: site/index.html, site/data/research.json, site/data/tests/<id>/*, site/data/days/*.json
Despliegue: git push origin main (Vercel).
"""
import csv, glob, hashlib, json, os, re, shutil, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FUT = os.path.join(ROOT, "futures")
OUT = os.path.join(ROOT, "site")
sys.path.insert(0, HERE)

FROZEN = ["strategies/v1.json", "strategies/v1_aclaraciones.json", "research_plan.json", "protocol.json", "protocol_v1.json", "sessions_manifest.json",
          "costs.json", "topstep_rules.json", "lab_rules.json", "news.json"]


def load(rel, default):
    p = os.path.join(FUT, rel)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def integrity():
    out = []
    for rel in FROZEN:
        p = os.path.join(FUT, rel)
        if not os.path.exists(p):
            out.append({"archivo": "futures/" + rel, "sha256": None, "ots": False}); continue
        out.append({"archivo": "futures/" + rel, "sha256": sha(p), "ots": os.path.exists(p + ".ots"),
                    "modificado": datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).strftime("%Y-%m-%d")})
    return out


def registry_export():
    reg = os.path.join(FUT, "lab", "registry")
    studies = jsonl(os.path.join(reg, "studies.jsonl")); trials = jsonl(os.path.join(reg, "trials.jsonl"))
    chain_ok = True
    for name in ("studies.jsonl", "trials.jsonl"):
        p = os.path.join(reg, name)
        if not os.path.exists(p):
            continue
        prev = "0" * 64
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            if json.loads(line).get("prev_sha256") != prev:
                chain_ok = False; break
            prev = hashlib.sha256(line.encode()).hexdigest()
    by_study = {}
    for t in trials:
        s = by_study.setdefault(t["study_id"], {"usados": 0, "pruebas": 0, "sensibilidad": 0, "senales": 0})
        s["usados"] += 1; s[{"prueba": "pruebas", "sensibilidad": "sensibilidad", "senal": "senales"}.get(t["tipo"], "pruebas")] += 1
    for s in studies:
        s.update(by_study.get(s["study_id"], {"usados": 0, "pruebas": 0, "sensibilidad": 0, "senales": 0}))
        s["excedido"] = s["usados"] > s["n_declarado"]
    light = [{k: t.get(k) for k in ("test_id", "study_id", "estrategia", "version", "tipo", "registrado_utc", "veredicto", "config_hash", "error")}
             | {"neto": (t.get("resultado") or {}).get("ganancia_neta"), "p_rand": (t.get("resultado") or {}).get("p_rand"),
                "git": (t.get("receta") or {}).get("git_commit", "")[:8]} for t in trials]
    return {"estudios": studies, "intentos": light, "total_intentos": len(trials), "cadena_ok": chain_ok}


def graveyard(tests, trials):
    out = []
    for t in tests:
        if t.get("veredicto") in ("no_pasa", "error", "insuficiente"):
            out.append({"id": t["id"], "que": f"{t['estrategia']} v{t['version']}", "fecha": t.get("fecha"), "veredicto": t["veredicto"],
                        "causa": t.get("muerte") or "sin causa escrita", "neto": (t.get("resultados") or {}).get("ganancia_neta")})
    return out


def sessions_export():
    m = load("sessions_manifest.json", None)
    if not m:
        return None
    return {"resumen": m["resumen"], "criterios": m["criterios"], "generado": m["generado_utc"], "sha256_lista": m["sesiones_diseno_sha256"],
            "excluidas": [{"date": r["date"], "motivo": r["motivo"]} for r in m["detalle"] if r["clase"] == "excluida"],
            "avisos": [{"date": r["date"], "motivo": r["motivo"]} for r in m["detalle"] if r["clase"] == "aviso"],
            "por_anio": {y: sum(1 for r in m["detalle"] if r["clase"] != "excluida" and r["date"].startswith(y)) for y in ("2024", "2025", "2026")}}


def copy_results(tests):
    for t in tests:
        src = os.path.join(FUT, "lab", "results", t["id"]); dst = os.path.join(OUT, "data", "tests", t["id"])
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for f in ("trades.csv", "trades.json", "report.json", "oscar/muestra.csv", "oscar/muestra.json", "oscar/acuerdo.json"):
                if os.path.exists(os.path.join(src, f)):
                    os.makedirs(os.path.dirname(os.path.join(dst, f)), exist_ok=True); shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
            days = os.path.join(src, "days")
            if os.path.isdir(days):
                os.makedirs(os.path.join(OUT, "data", "days"), exist_ok=True)
                for f in os.listdir(days):
                    shutil.copy2(os.path.join(days, f), os.path.join(OUT, "data", "days", f))
    for study in ("salidas_v1",):
        src = os.path.join(FUT, "lab", "results", study)
        if os.path.isdir(src):
            dst = os.path.join(OUT, "data", study); os.makedirs(dst, exist_ok=True)
            for f in os.listdir(src):
                if f.endswith(".json"): shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    days_dir = os.path.join(OUT, "data", "days")
    idx = sorted(f[:-5] for f in os.listdir(days_dir) if f.endswith(".json") and f != "index.json") if os.path.isdir(days_dir) else []
    json.dump(idx, open(os.path.join(days_dir, "index.json"), "w")) if idx else None


def research_export():
    def rd(rel):
        p = os.path.join(FUT, rel); raw = open(p, encoding="utf-8").read()
        return json.loads(raw), hashlib.sha256(raw.encode()).hexdigest()
    plan, ph = rd("research_plan.json"); plan["sha256"] = ph
    proto, prh = rd("protocol.json"); proto["sha256"] = prh
    vers = []
    for f in sorted([x for x in glob.glob(os.path.join(FUT, "strategies", "v*.json")) if re.fullmatch(r"v\d+\.json", os.path.basename(x))], key=lambda x: int(os.path.basename(x)[1:-5])):
        d, h = rd("strategies/" + os.path.basename(f)); d["sha256"] = h; d["archivo"] = "futures/strategies/" + os.path.basename(f); vers.append(d)
    tests = load("tests.json", {"pruebas": []}).get("pruebas", [])
    mapa = load("signal_map.json", {})
    for r in mapa.get("senales", []):   # sin z (desviación cero del azar) no hay prueba válida
        if r.get("n") and any(r.get(h + "_z") is None for h in ("r1", "r5", "r15", "r30") if r.get(h) is not None):
            r["significativa"] = False; r["horizontes_significativos"] = []; r["sentido"] = "sin prueba válida (azar sin dispersión)"
        if r.get("n"):
            r["bruto"] = "gana" if (r.get("r30") or 0) > 0 and (r.get("r15") or 0) > 0 else "pierde" if (r.get("r30") or 0) < 0 and (r.get("r15") or 0) < 0 else "mixto"
    reg = registry_export()
    ups = load("updates.json", {"entries": []}).get("entries", [])
    week = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    sal = {sid: load(f"lab/results/salidas_v1/{sid}.json", None) for sid in ("BIG", "ABS", "POC")}
    data = {"plan": plan, "protocolo": proto, "versiones": vers, "pruebas": tests, "mapa": mapa, "registro": reg, "backlog": load("backlog.json", {"pruebas": []}), "salidas": {k: v for k, v in sal.items() if v},
            "cementerio": graveyard(tests, reg["intentos"]), "sesiones": sessions_export(), "costos": load("costs.json", {}),
            "topstep": load("topstep_rules.json", {}), "glosario": load("glossary.json", {}), "sellos": integrity(),
            "cambios_semana": [u for u in ups if u.get("date", "") >= week], "generado": datetime.now(timezone.utc).isoformat(timespec="minutes")}
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    json.dump(data, open(os.path.join(OUT, "data", "research.json"), "w", encoding="utf-8"), ensure_ascii=False)
    copy_results(tests)
    return data


def build():
    r = research_export()
    data = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "roster": load("roster.json", {"bots": []}), "dataset": load("data_status.json", {}),
            "rules": load("lab_rules.json", {"rules": []}), "updates": load("updates.json", {"entries": []}),
            "runs": len(r["pruebas"]), "runs_by_bot": {}, "integrity": {s["archivo"]: {"path": s["archivo"], "sha256": s["sha256"], "ots": s["ots"]} for s in r["sellos"]}}
    for t in r["pruebas"]:
        data["runs_by_bot"][t["estrategia"]] = data["runs_by_bot"].get(t["estrategia"], 0) + 1
    tpl = open(os.path.join(HERE, "futures_template.html"), encoding="utf-8").read()
    frag = lambda n: open(os.path.join(HERE, n), encoding="utf-8").read()
    html = (tpl.replace("<!--FLOOR-->", frag("trading_floor.html")).replace("<!--RESEARCH_TABS-->", frag("research_tabs.html"))
               .replace("<!--EXPLORER_TAB-->", frag("explorer_tab.html")).replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    import build_lab_md, build_comite; build_lab_md.build(r["sellos"]); build_comite.build()
    print(f"site/index.html · {len(r['pruebas'])} pruebas · {r['registro']['total_intentos']} intentos · cadena {'ok' if r['registro']['cadena_ok'] else 'ROTA'}")


if __name__ == "__main__":
    build()
