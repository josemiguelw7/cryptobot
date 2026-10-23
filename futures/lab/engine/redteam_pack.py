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
- `codigo_estrategia.py`, `codigo_simulador.py`, `codigo_niveles.py`: el programa exacto que produjo el resultado.
- `protocol.json`: cómo se midió (RAND, costos, placebos, criterios).
- `report.json`: la hoja de resultados completa. `trades.csv`: cada operación.
- `receta.json`: commit, huellas, costos, semilla.

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
    shutil.copy(os.path.join(E, "strategies", f"v{v}.py"), os.path.join(out, "codigo_estrategia.py"))
    shutil.copy(os.path.join(E, "sim.py"), os.path.join(out, "codigo_simulador.py"))
    shutil.copy(os.path.join(E, "levels.py"), os.path.join(out, "codigo_niveles.py"))
    shutil.copy(os.path.join(config.FUT, "protocol.json"), os.path.join(out, "protocol.json"))
    for f in ("report.json", "trades.csv"):
        shutil.copy(os.path.join(rd, f), os.path.join(out, f))
    json.dump(rep.get("receta", {}), open(os.path.join(out, "receta.json"), "w"), indent=1)
    open(os.path.join(out, "PROMPT.md"), "w", encoding="utf-8").write(PROMPT.format(id=tid, version=v))
    print(f"paquete listo: {out} · sube la carpeta a una conversación nueva de Claude sin contexto y pega PROMPT.md")


if __name__ == "__main__":
    main()
