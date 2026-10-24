"""Arma el paquete para la revisión ciega del Red Team: un Claude SIN contexto recibe solo la regla congelada,
el código, el protocolo y los archivos de resultado, y su único trabajo es encontrar cómo el resultado podría
engañarnos. Salida: futures/lab/results/<id>/redteam/ (PROMPT.md + archivos). El informe se guarda como
docs/redteam/<id>.md y se enlaza desde decisions.md.
  python -m engine.redteam_pack P003
"""
import json, os, shutil, sys
from . import config

PROMPT = """# Red Team ciego · prueba {id}

Eres un revisor adversarial sin ningún contexto previo de este laboratorio. No sabes quién diseñó la estrategia
ni qué resultado esperaban. Tu único trabajo es **encontrar cómo este resultado podría ser falso o engañoso**.
No propongas mejoras a la estrategia. No seas amable. Si no encuentras nada, dilo con las pruebas que hiciste.

Archivos en esta carpeta:
- `regla.json`: la regla congelada de la estrategia (versión {version}) y las reglas comunes.
- `engine/`: TODO el motor (simulador, niveles, estrategias v1/v2, RAND, Topstep, estadística, Red Team, registro, orquestador).
- `protocol.json` (y v1): cómo se midió. `sessions_manifest.json`: sesiones válidas y excluidas con motivo. `canonical_manifest.json`: huellas de los datos.
- `registry/trials.jsonl` y `studies.jsonl`: todos los intentos y estudios declarados (cadena de huellas).
- `report.json` (con `veredicto_original` y `correccion` si la hubo), `trades.csv`, `receta.json`, `receipt_*.json` (huellas de las dos corridas en contenedor), `golden.json`, `Dockerfile`, `LIMITES.md`.

Revisa, en este orden, y responde con una lista numerada de hallazgos (gravedad: crítica / media / baja):
1. **Fuga de futuro**: ¿algún índice, ventana, percentil, nivel o precio usa información posterior al instante de la señal o del llenado?
2. **Llenados**: ¿los precios de entrada y salida son alcanzables? ¿el objetivo se da por llenado sin que la cinta pase de largo? ¿el stop se llena mejor de lo real?
3. **Selección de datos**: ¿la lista de sesiones, el periodo o los umbrales favorecen el resultado?
4. **Pruebas múltiples**: ¿cuántas cosas se probaron antes de esta? ¿el valor p o el DSR lo reflejan?
5. **Concentración**: ¿la ganancia depende de pocos días u operaciones? ¿se sostiene sin ellos?
6. **Costos y capacidad**: ¿los costos son realistas para 1 contrato? ¿y para 5?
7. **Reproducibilidad**: ¿con la receta se puede repetir el resultado bit a bit?
8. **Cualquier otra cosa** que un auditor desconfiado miraría.

Termina con un veredicto en una línea: "Confío / No confío / Confío con reservas", y por qué.
"""


def main():
    tid = sys.argv[1]
    rd = os.path.join(config.RESULTS, tid); rep = json.load(open(os.path.join(rd, "report.json"), encoding="utf-8"))
    out = os.path.join(rd, "redteam"); os.makedirs(out, exist_ok=True)
    v = rep["version"]; vj = json.load(open(os.path.join(config.FUT, "strategies", f"v{v}.json"), encoding="utf-8"))
    regla = {"comun": vj["comun"], "estrategia": next(s for s in vj["estrategias"] if s["id"] == rep["estrategia"])}
    json.dump(regla, open(os.path.join(out, "regla.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    E = os.path.join(config.LAB, "engine")
    # TODO el motor (la revisión ciega del 24/10/2026 no pudo auditar porque faltaban módulos)
    shutil.rmtree(os.path.join(out, "engine"), ignore_errors=True)
    shutil.copytree(E, os.path.join(out, "engine"), ignore=shutil.ignore_patterns("__pycache__"))
    for f in ("protocol.json", "protocol_v1.json", "sessions_manifest.json", "canonical_manifest.json", "costs.json", "topstep_rules.json", "news.json"):
        if os.path.exists(os.path.join(config.FUT, f)): shutil.copy(os.path.join(config.FUT, f), os.path.join(out, f))
    os.makedirs(os.path.join(out, "registry"), exist_ok=True)
    for f in ("trials.jsonl", "studies.jsonl"):
        if os.path.exists(os.path.join(config.REGISTRY, f)): shutil.copy(os.path.join(config.REGISTRY, f), os.path.join(out, "registry", f))
    for f in ("golden.json", "regimes.json"):
        if os.path.exists(os.path.join(config.LAB, f)): shutil.copy(os.path.join(config.LAB, f), os.path.join(out, f))
    runs = os.path.join(config.LAB, "runs")
    if os.path.isdir(runs):
        for rdir in os.listdir(runs):
            rc = os.path.join(runs, rdir, "receipt.json")
            if os.path.exists(rc) and json.load(open(rc)).get("id"):
                shutil.copy(rc, os.path.join(out, f"receipt_{rdir}.json"))
    open(os.path.join(out, "Dockerfile"), "w").write("FROM python:3.12-slim\nRUN pip install --no-cache-dir polars==1.* numpy scipy pyarrow\nWORKDIR /lab\n")
    open(os.path.join(out, "LIMITES.md"), "w", encoding="utf-8").write(
        "# Qué NO contiene este paquete y por qué\n\n- La cinta (3.3 GB de parquet por sesión) no viaja en el paquete; sus huellas SHA-256 y tamaños están en canonical_manifest.json, "
        "y la lista congelada de sesiones con cada exclusión y su motivo en sessions_manifest.json.\n- Para reproducir bit a bit: clonar el commit de receta.json, construir la imagen del Dockerfile, "
        "montar los datos en /srv/lab/data en solo lectura y correr `python -m engine.run_test --strategy <id> --version <v> --study <estudio> --sens --isolated --n-trials <N>`. "
        "Los recibos receipt_*.json traen las huellas de trades.csv de las dos corridas del orquestador.\n- lab_stats_NQ.jsonl (percentiles) se regenera desde la cinta dentro del contenedor.\n")
    for f in ("report.json", "trades.csv"):
        shutil.copy(os.path.join(rd, f), os.path.join(out, f))
    json.dump(rep.get("receta", {}), open(os.path.join(out, "receta.json"), "w"), indent=1)
    open(os.path.join(out, "PROMPT.md"), "w", encoding="utf-8").write(PROMPT.format(id=tid, version=v))
    print(f"paquete listo: {out} · sube la carpeta a una conversación nueva de Claude sin contexto y pega PROMPT.md")


if __name__ == "__main__":
    main()
