"""Aplica los votos del comité (docs/comite/votos/<id>__oscar.json, escritos por la página con el PIN de Oscar) al backlog.
Regla (decisión de Jose Miguel, 24/10/2026): Oscar decide solo. Su voto sobre una idea 'propuesta':
  aprobar   -> aprobada   (luego Claude escribe y congela las reglas; el orquestador solo corre 'congelada')
  descartar -> descartada
  mas_datos -> sigue propuesta, con la petición anotada
Cada voto queda guardado en el ítem (campo 'votos')."""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BL = os.path.join(ROOT, "futures", "backlog.json")
NOMBRE = {"jose": "Jose Miguel", "oscar": "Oscar"}


def apply():
    if not os.path.exists(BL):
        return 0
    b = json.load(open(BL, encoding="utf-8")); votos = {}
    for f in glob.glob(os.path.join(ROOT, "docs", "comite", "votos", "*.json")):
        try:
            v = json.load(open(f, encoding="utf-8"))
            votos.setdefault(v["id"], {})[v["persona"]] = {k: v.get(k) for k in ("voto", "comentario", "fecha")}
        except Exception:
            continue
    changed = 0
    for it in b["pruebas"]:
        V = votos.get(it["id"])
        if not V:
            continue
        if it.get("votos") != V:
            it["votos"] = V; changed += 1
        if it["estado"] != "propuesta" or "oscar" not in V:
            continue
        v = V["oscar"]; fecha = (v.get("fecha") or "")[:10]; nota = f" · {v['comentario']}" if v.get("comentario") else ""
        if v["voto"] == "aprobar":
            it["estado"] = "aprobada"; it["decision"] = f"aprobada por Oscar {fecha} (voto en la página){nota}"
        elif v["voto"] == "descartar":
            it["estado"] = "descartada"; it["decision"] = f"descartada por Oscar {fecha} (voto en la página){nota}"
        else:
            nueva = f"Oscar pide más datos {fecha}{nota}"
            if it.get("decision") == nueva:
                continue
            it["decision"] = nueva
        changed += 1
    if changed:
        json.dump(b, open(BL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return changed


if __name__ == "__main__":
    print(apply())
