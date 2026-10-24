"""Genera LAB.md (raíz del repo): el estado del laboratorio en una página, SIEMPRE derivado de los archivos
(registro, tests.json, backlog, mapa, sellos, bitácora). Nadie lo edita a mano. Lo llama build_futures_site.py.
"""
import json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); FUT = os.path.join(ROOT, "futures")


def L(rel, d):
    p = os.path.join(FUT, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d


def jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def money(n):
    return "—" if n is None else ("−$" if n < 0 else "$") + f"{abs(n):,.0f}"


def build(sellos):
    tests = L("tests.json", {"pruebas": []})["pruebas"]; bl = L("backlog.json", {"pruebas": []}); mapa = L("signal_map.json", {})
    man = L("sessions_manifest.json", {}); ups = L("updates.json", {"entries": []})["entries"]; gl = L("glossary.json", {})
    reg = os.path.join(FUT, "lab", "registry"); studies = jsonl(os.path.join(reg, "studies.jsonl")); trials = jsonl(os.path.join(reg, "trials.jsonl"))
    by = {}
    for t in trials:
        by[t["study_id"]] = by.get(t["study_id"], 0) + 1
    vcount = {}
    for t in tests:
        vcount[t["veredicto"]] = vcount.get(t["veredicto"], 0) + 1
    o = []
    o.append("# Laboratorio NQ · estado actual\n")
    o.append(f"_Generado automáticamente el {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} desde el registro, tests.json, backlog.json y signal_map.json. No editar a mano: cambia los archivos fuente._\n")
    o.append("Página: https://cryptobot-liga-radtak-projects.vercel.app · Guía del repo: `docs/README.md` · Decisiones: `docs/decisions.md`\n")
    o.append("## En una línea\n")
    o.append(f"- Sesiones válidas de diseño: **{man.get('resumen', {}).get('diseno_validas', '—')}** (examen sellado desde 2026-04-22, cerrado).")
    o.append(f"- Intentos registrados: **{len(trials)}** · pruebas publicadas: **{len(tests)}** ({', '.join(f'{k} {v}' for k, v in vcount.items()) or 'ninguna'}).")
    o.append(f"- Estrategias aprobadas por el comité: **0**. Nada toca dinero real.\n")
    o.append("## Pruebas corridas\n")
    o.append("| Id | Qué | Veredicto | Neto | p vs RAND | Topstep | Causa |\n|---|---|---|---|---|---|---|")
    for t in tests:
        r = t.get("resultados", {})
        o.append(f"| {t['id']} | {t['estrategia']} v{t['version']} | **{t['veredicto']}** | {money(r.get('ganancia_neta'))} | {r.get('vs_rand', '—')} | {r.get('topstep', '—')}% | {(t.get('muerte') or '')[:110]} |")
    o.append("\n## Cola de pruebas (backlog)\n")
    o.append("Estados: propuesta → aprobada (Oscar + Jose Miguel) → congelada (reglas con huella y sello, estudio registrado) → en cola → corrida. El orquestador solo arranca las **congeladas**.\n")
    o.append("| Id | Prueba | Estado | Origen | Falta |\n|---|---|---|---|---|")
    for it in bl.get("pruebas", []):
        o.append(f"| {it['id']} | {it['nombre']} | **{it['estado']}**{(' → ' + it['test_id']) if it.get('test_id') else ''} | {it.get('origen', '')} | {'; '.join(it.get('requisitos', []))[:120]}{(' · ERROR: ' + it['ultimo_error']) if it.get('ultimo_error') else ''} |")
    o.append("\n## Estudios y cuenta de intentos\n")
    for s in studies:
        u = by.get(s["study_id"], 0)
        o.append(f"- **{s['study_id']}**: {s['hipotesis'][:140]} · declarados {s['n_declarado']}, usados {u}{' ⚠ excedido' if u > s['n_declarado'] else ''}")
    if mapa.get("senales"):
        o.append("\n## Mapa de señales (resumen)\n")
        o.append(f"{mapa.get('sesiones')} sesiones · {mapa.get('sorteos')} sorteos · {mapa.get('pruebas')} pruebas · Holm 5%. Ticks promedio en la dirección predicha a 15 y 30 min; sentido = contra el azar de la misma media hora.\n")
        o.append("| Señal | Eventos | 15 min | 30 min | Veredicto |\n|---|---|---|---|---|")
        for m in mapa["senales"]:
            o.append(f"| {m['senal']} | {m['n']:,} | {m.get('r15', '—')} | {m.get('r30', '—')} | {('distinta del azar · ' + str(m.get('sentido'))) if m.get('significativa') else 'no distinta'} |")
    o.append("\n## Documentos congelados\n")
    for s in sellos:
        o.append(f"- `{s['archivo']}` · {(s['sha256'] or 'falta')[:16]}… · {'OTS ✓' if s['ots'] else 'sin OTS'}")
    import glob
    inbox = sorted(glob.glob(os.path.join(ROOT, "docs", "oscar", "inbox", "*.md")), reverse=True)
    o.append("\n## Buzón de Oscar\n")
    o += [f"- `docs/oscar/inbox/{os.path.basename(f)}`" for f in inbox[:10]] or ["- sin notas todavía (se suben desde la página › Estrategias › Buzón de Oscar)"]
    o.append("\n## Preguntas abiertas para Oscar\n")
    for q in gl.get("preguntas_oscar", []):
        if q.get("estado") != "respondida":
            o.append(f"{q['id']}. {q['q']}")
    o.append("\n## Últimos movimientos (bitácora)\n")
    for e in ups[:8]:
        o.append(f"- {e.get('date')} · {e.get('kind')} · {e.get('title')}")
    o.append("\n## Cómo se corre una prueba nueva\n")
    o.append("1. Escribir la regla en `futures/strategies/v<N>.json`, sellar (`ots stamp`), registrar el estudio (`engine/register_study.py`).")
    o.append("2. Poner la prueba en `futures/backlog.json` con estado `congelada` y `./futures/lab/sync_vm.sh push`.")
    o.append("3. El orquestador (cron en la VM, cada 15 min) la corre dos veces en contenedores efímeros sin red con datos en solo lectura; publica solo si `trades.csv` es idéntico.")
    o.append("4. `./futures/lab/sync_vm.sh pull && .venv/bin/python portal/build_futures_site.py && git push origin main`.")
    o.append("5. Si pasa o queda en revisar: `engine/redteam_pack.py <id>` → revisión ciega → `docs/redteam/<id>.md`.\n")
    open(os.path.join(ROOT, "LAB.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
    return len(o)
