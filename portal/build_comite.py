"""Agenda del comité semanal (Jose Miguel + Oscar), generada desde el estado: qué corrió, qué murió y por qué,
qué está propuesto, qué respuestas faltan. Se escribe en docs/comite/agenda_actual.md en cada construcción
y se archiva una copia con fecha cuando se corre con --archivar (viernes)."""
import glob, json, os, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); FUT = os.path.join(ROOT, "futures")


def L(rel, d):
    p = os.path.join(FUT, rel); return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d


def build(archivar=False):
    tests = L("tests.json", {"pruebas": []})["pruebas"]; bl = L("backlog.json", {"pruebas": []})["pruebas"]
    ups = L("updates.json", {"entries": []})["entries"]; gl = L("glossary.json", {}); mapa = L("signal_map.json", {})
    week = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"); today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    o = [f"# Comité · agenda del {today}", "", "_Generada sola. 30 minutos. Un punto por línea; las decisiones se escriben en `docs/decisions.md`._", ""]
    o += ["## 1. Qué corrió esta semana"] + [f"- {t['id']} · {t['estrategia']} v{t['version']} · **{t['veredicto']}** · neto {t['resultados'].get('ganancia_neta')} · p {t['resultados'].get('vs_rand')} · Topstep {t['resultados'].get('topstep')}%" for t in tests if t.get("fecha", "") >= week] or ["- nada"]
    o += ["", "## 2. Qué murió y por qué"] + [f"- {t['id']} · {t['estrategia']} v{t['version']}: {t.get('muerte')}" for t in tests if t["veredicto"] in ("no_pasa", "error") and t.get("fecha", "") >= week] or ["- nada"]
    o += ["", "## 3. Qué está propuesto (decidir: aprobar / descartar / pedir más datos)"] + [f"- [ ] **{it['id']}** {it['nombre']} — {it['hipotesis'][:160]}" for it in bl if it["estado"] == "propuesta"] or ["- nada"]
    o += ["", "## 4. Qué está aprobado y falta congelar"] + [f"- {it['id']} {it['nombre']} · falta: {'; '.join(it.get('requisitos', []))}" for it in bl if it["estado"] == "aprobada"] or ["- nada"]
    o += ["", "## 5. Respuestas que faltan de Oscar"] + [f"- {q['id']}. {q['q']}" for q in gl.get("preguntas_oscar", []) if q.get("estado") != "respondida"][:5]
    pend = [t["id"] for t in tests if os.path.exists(os.path.join(FUT, "lab", "results", t["id"], "oscar", "muestra.csv")) and not os.path.exists(os.path.join(FUT, "lab", "results", t["id"], "oscar", "acuerdo.json"))]
    o += ["", "## 6. Muestras pendientes de marcar en ATAS (los ojos de Oscar)"] + ([f"- {t}: 30 operaciones en la pestaña Pruebas › hoja completa" for t in pend] or ["- ninguna"])
    if mapa.get("senales"):
        top = sorted([m for m in mapa["senales"] if m.get("significativa")], key=lambda m: -abs(m.get("r30_z") or 0))[:3]
        o += ["", "## 7. Lo más fuerte del mapa (para decidir la siguiente tanda)"] + [f"- {m['senal']}: {m.get('r30')} ticks a 30 min · {m.get('sentido')} · {m['n']:,} eventos" for m in top]
    inbox = sorted(glob.glob(os.path.join(ROOT, "docs", "oscar", "inbox", "*.md")), reverse=True)[:8]
    o += ["", "## 7b. Buzón de Oscar (notas nuevas)"] + ([f"- {os.path.basename(f)}" for f in inbox] or ["- ninguna"])
    o += ["", "## 8. Decisiones tomadas hoy", "- ", "", "_Al terminar: pasar lo decidido a `backlog.json` (estados) y a `docs/decisions.md`._"]
    d = os.path.join(ROOT, "docs", "comite"); os.makedirs(d, exist_ok=True)
    txt = "\n".join(o) + "\n"; open(os.path.join(d, "agenda_actual.md"), "w", encoding="utf-8").write(txt)
    if archivar:
        open(os.path.join(d, f"{today}.md"), "w", encoding="utf-8").write(txt)
    return len(o)


if __name__ == "__main__":
    build("--archivar" in sys.argv)
