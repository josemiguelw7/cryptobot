"""Reconstruye futures/tests.json y las entradas de bitácora de pruebas desde results/<id>/report.json,
aplicando las correcciones del registro (la última corrección de cada prueba manda).
Sirve si tests.json se pierde o se pisa: la fuente de verdad son los reports y el registro.
  python -m engine.rebuild_tests
"""
import json, os
from . import config, registry
from .report import publish


NOTES = {  # notas de contexto por prueba (se escriben aquí para que sobrevivan a cualquier reconstrucción)
    "P013": "Corrida con la interpretación literal de la v1 (p99 de todas las órdenes = 15 contratos) y percentil truncado. No cuenta ni a favor ni en contra.",
    "P003": "Única estrategia de la tanda 1 con ventaja real sobre el azar (p 0.002, sobrevive 2 ticks por lado, 12/15 caminos CPCV positivos). Revisión de código del Red Team: sin fuga de futuro; el placebo desplazado gana más porque el valor está en el nivel y la dirección, no en el momento. La fila confirm_s de la sensibilidad no vale (parámetro no conectado en el código v1). No pasa: pierde en 2025 y solo 6.4% de las cuentas Topstep llegan a la meta con 128 operaciones en 576 sesiones.",
    "P002": "Población corregida (órdenes de 10+ contratos, p99 ≈ 100). Seguir a la orden grande pierde: el mapa de señales muestra que esas órdenes marcan el peor momento de su media hora.",
    "P004": "Rechazo del área de valor hacia el POC en días que abren dentro del valor. El mapa confirma que el precio sale del valor más de lo que rebota.",
}


MUERTE = {"P003": "pierde en 2025 (−$405); pasa Topstep solo 6.4% (128 operaciones en 576 sesiones no alcanzan la meta); 67.7% de la ganancia viene de 5 días"}


def main():
    corr = {}
    for t in registry.read(registry.TRIALS):
        if t.get("tipo") == "correccion":
            corr[t["test_id"]] = t
    p = os.path.join(config.FUT, "tests.json")
    json.dump({"pruebas": []}, open(p, "w", encoding="utf-8"))
    ups_p = os.path.join(config.FUT, "updates.json"); ups = json.load(open(ups_p, encoding="utf-8"))
    have = {e.get("test_id") for e in ups["entries"]}
    tids = [t for t in os.listdir(config.RESULTS) if os.path.exists(os.path.join(config.RESULTS, t, "report.json"))]
    tids.sort(key=lambda t: json.load(open(os.path.join(config.RESULTS, t, "report.json"), encoding="utf-8")).get("receta", {}).get("registrado", "") or os.path.getmtime(os.path.join(config.RESULTS, t, "report.json")))
    for tid in tids:
        rp = os.path.join(config.RESULTS, tid, "report.json")
        f = json.load(open(rp, encoding="utf-8"))
        if tid in corr:
            c = corr[tid]; f["veredicto"] = c["veredicto"]; f["correccion"] = c["motivo"]; f["corregido_utc"] = c["registrado_utc"]
            f["muerte"] = c["motivo"] if c["veredicto"] in ("error", "no_pasa", "insuficiente") else f.get("muerte")
        if tid in NOTES:
            f["notas"] = NOTES[tid]
        if tid in MUERTE:
            f["muerte"] = MUERTE[tid]
        publish(f)
        if tid not in have:
            r = f["resultados"]; lbl = {"pasa": "pasa", "no_pasa": "no pasa", "insuficiente": "insuficiente", "error": "error", "revisar": "revisar"}.get(f["veredicto"], f["veredicto"])
            ts = (f.get("hoja", {}).get("topstep") or {})
            body = (f"{f['estrategia']} v{f['version']}: {r['operaciones']} operaciones, ganancia neta ${r['ganancia_neta']:,.0f} con costos base, "
                    f"p contra RAND {r['vs_rand']}, estrés ${f.get('estres', {}).get('neto', 0):,.0f}, Topstep {ts.get('pct_pasan')}% de las cuentas (RAND {ts.get('rand_pct_pasan')}%). "
                    f"Veredicto: {lbl}." + (f" Causa: {f.get('muerte')}." if f["veredicto"] != "pasa" and f.get("muerte") else ""))
            ups["entries"].append({"date": f["fecha"], "kind": "prueba", "title": f"Prueba {tid} · {f['estrategia']} v{f['version']} · {lbl}", "body": body, "test_id": tid})
    ups["entries"].sort(key=lambda e: e.get("date", ""), reverse=True)
    json.dump(ups, open(ups_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # estado del orquestador (VM) -> backlog.json (Mac)
    stp = os.path.join(config.LAB, "runs_state.json"); bp = os.path.join(config.FUT, "backlog.json")
    if os.path.exists(stp) and os.path.exists(bp):
        st = json.load(open(stp)); b = json.load(open(bp, encoding="utf-8"))
        for it in b["pruebas"]:
            if it["id"] in st:
                it.update(st[it["id"]])
        json.dump(b, open(bp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("tests.json reconstruido:", [t["id"] + ":" + t["veredicto"] for t in json.load(open(p, encoding="utf-8"))["pruebas"]])


if __name__ == "__main__":
    main()
