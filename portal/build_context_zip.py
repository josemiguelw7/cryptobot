"""Contexto para Claude (descargable desde la página): un zip con todo lo que una conversación nueva de Claude
necesita para hablar del laboratorio con datos al día. Lo regenera cada publicación (build_futures_site.py).
Contenido: PROMPT_OSCAR.md, LAB.md, docs/decisions.md, agenda del comité, informes, backlog, glosario y preguntas,
resumen de cada prueba, mapa de señales, protocolo y reglas selladas, buzón de Oscar, revisiones del Red Team.
"""
import glob, json, os, zipfile
from datetime import datetime, timezone

PROMPT = """# Cómo usar este paquete con Claude (cuenta gratuita)

1. Abre https://claude.ai e inicia una conversación nueva.
2. Sube TODOS los archivos de este zip (o el zip entero si tu plan lo permite).
3. Pega este mensaje como primer mensaje:

---
Eres el asistente del Laboratorio NQ, un proyecto de investigación de estrategias de order flow en futuros NQ de
Jose Miguel y Oscar. Los archivos adjuntos son el estado completo del laboratorio al {fecha}: LAB.md (estado en una
página), decisions.md (todas las decisiones con fecha), backlog (cola de pruebas), resultados de cada prueba,
mapa de señales, protocolo estadístico, reglas selladas de cada estrategia, revisiones del Red Team, y el buzón
de Oscar (sus notas anteriores). Responde en español, con números y citando el archivo de donde sale cada dato.
No inventes resultados: si algo no está en los archivos, di que no está. Soy Oscar, trader de order flow; mi
trabajo aquí es revisar las estrategias con ojo de operador y proponer. Empieza con un resumen de 10 líneas
de dónde está el laboratorio hoy y qué está en cola.
---

4. Para dejar un hallazgo, una respuesta o una petición que el laboratorio deba tomar en cuenta, pégalo en el
   "Buzón de Oscar" de la página (pestaña Estrategias): queda guardado en el repositorio y entra a la agenda.
5. Este zip se regenera cada 30 minutos; descárgalo de nuevo para una conversación con datos frescos.
"""


def build(root, out_dir):
    fut = os.path.join(root, "futures"); fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    zp = os.path.join(out_dir, "contexto_claude.zip"); os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("PROMPT_OSCAR.md", PROMPT.format(fecha=fecha))
        for rel in ("LAB.md", "docs/decisions.md", "docs/README.md", "docs/comite/agenda_actual.md", "futures/backlog.json", "futures/glossary.json",
                    "futures/protocol.json", "futures/costs.json", "futures/topstep_rules.json", "futures/lab_rules.json", "futures/tests.json",
                    "futures/signal_map.json", "futures/regime_proxy.json", "futures/lab/engine/README.md"):
            p = os.path.join(root, rel)
            if os.path.exists(p): z.write(p, rel.replace("/", "_"))
        for pat in ("futures/strategies/v*.json", "docs/informes/*.md", "docs/redteam/*.md", "docs/oscar/inbox/*.md", "futures/lab/results/salidas_*/*.json"):
            for p in sorted(glob.glob(os.path.join(root, pat))):
                z.write(p, os.path.relpath(p, root).replace("/", "_"))
        # resumen de cada prueba (sin la hoja completa, que es pesada)
        tests = json.load(open(os.path.join(fut, "tests.json"), encoding="utf-8")).get("pruebas", []) if os.path.exists(os.path.join(fut, "tests.json")) else []
        lines = ["# Resumen de pruebas\n"]
        for t in tests:
            r = t.get("resultados", {})
            lines.append(f"## {t['id']} · {t['estrategia']} v{t['version']} · {t['veredicto']}\n- fecha {t.get('fecha')} · estudio {t.get('tanda')}\n- operaciones {r.get('operaciones')} · neto ${r.get('ganancia_neta')} · p vs RAND {r.get('vs_rand')} · Topstep {r.get('topstep')}% · aciertos {r.get('aciertos')}% · factor {r.get('factor')} · peor drawdown ${r.get('drawdown_max')}\n- causa: {t.get('muerte')}\n- notas: {t.get('notas','')}\n")
        z.writestr("pruebas_resumen.md", "\n".join(lines))
    return zp
