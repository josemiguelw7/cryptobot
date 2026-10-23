"""Los ojos de Oscar: muestra de 30 operaciones por prueba (10 mejores, 10 peores, 10 al azar con semilla fija)
para que Oscar marque en ATAS si él la habría tomado. El porcentaje de acuerdo mide si el código dice lo que
él quiere decir: la verificación que ningún estadístico puede hacer.

  python -m engine.oscar_sample P003               -> results/P003/oscar/muestra.csv (+ muestra.json para la página)
  python -m engine.oscar_sample P003 --respuestas results/P003/oscar/respuestas.csv
       respuestas.csv: mismas filas con columnas oscar (si/no) y comentario -> calcula acuerdo y lo publica en la hoja
"""
import argparse, csv, hashlib, json, os
import numpy as np
from . import config
from .sim import sec_to_hms


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("test_id"); ap.add_argument("--respuestas", default=""); a = ap.parse_args()
    rd = os.path.join(config.RESULTS, a.test_id); out = os.path.join(rd, "oscar"); os.makedirs(out, exist_ok=True)
    tr = json.load(open(os.path.join(rd, "trades.json"), encoding="utf-8"))
    if a.respuestas:
        rows = list(csv.DictReader(open(a.respuestas, encoding="utf-8")))
        ans = [r for r in rows if (r.get("oscar") or "").strip().lower() in ("si", "sí", "no")]
        si = sum(1 for r in ans if r["oscar"].strip().lower() in ("si", "sí"))
        res = {"respondidas": len(ans), "tomaria": si, "acuerdo_pct": round(100 * si / len(ans), 1) if ans else None,
               "por_grupo": {g: {"n": sum(1 for r in ans if r["grupo"] == g), "tomaria": sum(1 for r in ans if r["grupo"] == g and r["oscar"].strip().lower() in ("si", "sí"))} for g in ("mejores", "peores", "azar")},
               "comentarios": [{"n": r["n"], "fecha": r["fecha"], "oscar": r["oscar"], "comentario": r.get("comentario", "")} for r in ans if r.get("comentario")]}
        json.dump(res, open(os.path.join(out, "acuerdo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rep_p = os.path.join(rd, "report.json"); rep = json.load(open(rep_p, encoding="utf-8")); rep.setdefault("hoja", {})["ojos_de_oscar"] = res
        json.dump(rep, open(rep_p, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"acuerdo {res['acuerdo_pct']}% en {len(ans)} operaciones"); return
    order = sorted(range(len(tr)), key=lambda i: tr[i]["net_usd"])
    rng = np.random.default_rng(int(hashlib.sha256(("oscar:" + a.test_id).encode()).hexdigest()[:8], 16))
    rest = [i for i in range(len(tr)) if i not in set(order[:10] + order[-10:])]
    groups = [("peores", i) for i in order[:10]] + [("mejores", i) for i in order[-10:][::-1]] + [("azar", int(i)) for i in rng.choice(rest, size=min(10, len(rest)), replace=False)]
    rows = []
    for n, (g, i) in enumerate(groups, 1):
        t = tr[i]
        rows.append({"n": n, "grupo": g, "fecha": t["date"], "lado": "compra" if t["side"] > 0 else "venta", "senal": t["kind"], "nivel": t["level"],
                     "entrada_hora_et": t["entry_hms"], "entrada_precio": t["entry_px"], "stop_ticks": t["stop_ticks"], "objetivo_ticks": t["target_ticks"],
                     "salida_hora_et": t["exit_hms"], "salida_precio": t["exit_px"], "motivo": t["reason"], "neto_usd": t["net_usd"], "oscar": "", "comentario": ""})
    with open(os.path.join(out, "muestra.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(os.path.join(out, "muestra.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"muestra de {len(rows)} operaciones en {out}/muestra.csv · Oscar llena 'oscar' (si/no) y 'comentario'")


if __name__ == "__main__":
    main()
