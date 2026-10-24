"""Aplica los votos del comité (docs/comite/votos/<id>__<persona>.json, escritos por la página con PIN) al backlog.
Regla: una idea 'propuesta' cambia de estado solo cuando Jose Miguel y Oscar votan lo mismo:
  aprobar + aprobar     -> aprobada   (luego Claude escribe y congela las reglas; el orquestador solo corre 'congelada')
  descartar + descartar -> descartada
  mas_datos + mas_datos -> sigue propuesta, con la petición anotada
Votos distintos: sigue propuesta y va a la agenda. Cada voto queda guardado en el ítem (campo 'votos')."""
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
        if it["estado"] != "propuesta" or set(V) != {"jose", "oscar"}:
            continue
        a, o = V["jose"]["voto"], V["oscar"]["voto"]
        if a != o:
            continue
        fecha = max(V["jose"]["fecha"], V["oscar"]["fecha"])[:10]
        notas = "; ".join(f"{NOMBRE[p]}: {V[p]['comentario']}" for p in ("jose", "oscar") if V[p].get("comentario"))
        if a == "aprobar":
            it["estado"] = "aprobada"
            it["decision"] = f"aprobada por Jose Miguel y Oscar {fecha} (votos en la página)" + (f" · {notas}" if notas else "")
        elif a == "descartar":
            it["estado"] = "descartada"
            it["decision"] = f"descartada por Jose Miguel y Oscar {fecha} (votos en la página)" + (f" · {notas}" if notas else "")
        else:
            nueva = f"el comité pide más datos {fecha}" + (f" · {notas}" if notas else "")
            if it.get("decision") == nueva:
                continue
            it["decision"] = nueva
        changed += 1
    if changed:
        json.dump(b, open(BL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return changed


if __name__ == "__main__":
    print(apply())
