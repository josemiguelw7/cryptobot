"""Orquestador del laboratorio NQ. Corre en la VM (cron cada 15 min) y arranca la siguiente prueba del backlog
que esté en estado 'congelada', en un entorno que empieza SIEMPRE sin información previa:

  1. clona el commit exacto desde el espejo local (/srv/lab/git/cryptobot.git) a una carpeta nueva
  2. verifica: estudio registrado, estrategia congelada con huella, .ots presente, lista de sesiones con la
     huella esperada, backlog con la prueba en 'congelada'
  3. corre la prueba dentro de un contenedor Docker efímero: --rm, --network none, datos montados en
     SOLO LECTURA, sin acceso al registro ni a resultados anteriores
  4. la corre una SEGUNDA vez en otro contenedor y compara la huella de trades.csv: si no coincide, no publica
  5. copia resultados, agrega el intento al registro (fuera del contenedor), marca la prueba 'corrida'

  python -m engine.orchestrator --once        (lo que llama el cron)
  python -m engine.orchestrator --status
Estado por prueba en /srv/lab/runs/<id>/ (log, commit, huellas, receipt.json).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone

MIRROR = "/srv/lab/git/cryptobot.git"
RUNS = "/srv/lab/runs"
DATA = "/srv/lab/data"
REPO = "/srv/lab/repo"           # copia de trabajo sincronizada desde la Mac (backlog, registro, resultados)
IMAGE = "nqlab:1"
LOCK = os.path.join(RUNS, ".lock")


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), text=True, capture_output=True, **kw)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


STATE = os.path.join(RUNS, "state.json")   # la Mac es dueña de backlog.json; la VM solo escribe su estado aquí


def backlog():
    b = json.load(open(os.path.join(REPO, "futures", "backlog.json"), encoding="utf-8"))
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for it in b["pruebas"]:
        if it["id"] in st:
            it.update(st[it["id"]])
    return b


def save_backlog(b):
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for it in b["pruebas"]:
        if it["estado"] in ("corriendo", "corrida") or it.get("ultimo_error"):
            st[it["id"]] = {k: it[k] for k in ("estado", "inicio_utc", "fin_utc", "test_id", "veredicto", "ultimo_error") if k in it}
    os.makedirs(RUNS, exist_ok=True); json.dump(st, open(STATE, "w"), indent=1)


def ensure_image():
    if sh(f"sudo -n docker image inspect {IMAGE}").returncode == 0:
        return
    df = os.path.join(RUNS, "Dockerfile")
    open(df, "w").write("FROM python:3.12-slim\nRUN pip install --no-cache-dir polars==1.* numpy scipy pyarrow\nWORKDIR /lab\n")
    r = sh(f"sudo -n docker build -q -t {IMAGE} -f {df} {RUNS}")
    if r.returncode != 0:
        raise SystemExit("no se pudo construir la imagen: " + r.stderr[-800:])


def preflight(item, commit, wd):
    """Verificaciones antes de gastar cómputo. Devuelve lista de fallas (vacía = ok)."""
    fails = []
    fut = os.path.join(wd, "futures")
    v = item.get("version"); st = item.get("estudio"); sid = item.get("estrategia")
    if not (sid and v and st):
        fails.append("la prueba no tiene estrategia/version/estudio")
        return fails
    vf = os.path.join(fut, "strategies", f"v{v}.json")
    if not os.path.exists(vf):
        fails.append(f"falta strategies/v{v}.json en el commit {commit[:8]}")
    elif not os.path.exists(vf + ".ots"):
        fails.append(f"strategies/v{v}.json no tiene sello .ots")
    else:
        ids = [s["id"] for s in json.load(open(vf, encoding="utf-8"))["estrategias"]]
        if sid not in ids:
            fails.append(f"{sid} no está en v{v}.json")
    studies = os.path.join(REPO, "futures", "lab", "registry", "studies.jsonl")
    if not os.path.exists(studies) or not any(json.loads(l)["study_id"] == st for l in open(studies) if l.strip()):
        fails.append(f"estudio {st} no registrado")
    man = os.path.join(fut, "sessions_manifest.json")
    if not os.path.exists(man):
        fails.append("falta sessions_manifest.json")
    elif item.get("sesiones_sha256") and json.load(open(man))["sesiones_diseno_sha256"] != item["sesiones_sha256"]:
        fails.append("la lista de sesiones cambió respecto a la que aprobó el comité")
    return fails


def golden_in_container(wd, rd):
    """La prueba dorada corre en contenedor con el commit exacto; si difiere, no se corre nada."""
    out = os.path.join(rd, "golden"); os.makedirs(out, exist_ok=True)
    cmd = (f"sudo -n docker run --rm --network none -v {wd}:/lab:ro -v {DATA}:/srv/lab/data:ro -v {out}:/out "
           f"-e LAB_DATA=/srv/lab/data -e LAB_OUT=/out -e LAB_STATS=/out/lab_stats.jsonl -w /lab/futures/lab {IMAGE} python -m engine.golden")
    r = sh(cmd); return r.returncode == 0, (r.stdout + r.stderr)[-400:]


def run_in_container(wd, item, out, tag):
    """Corre la prueba en un contenedor efímero. Devuelve (ok, log)."""
    os.makedirs(out, exist_ok=True)
    cmd = (f"sudo -n docker run --rm --network none --name nqlab-{item['id']}-{tag} "
           f"-v {wd}:/lab:ro -v {DATA}:/srv/lab/data:ro -v {out}:/out -e LAB_DATA=/srv/lab/data -e LAB_OUT=/out -e LAB_RESULTS=/out/results -e LAB_STATS=/out/lab_stats.jsonl "
           f"-w /lab/futures/lab {IMAGE} python -m engine.run_test --strategy {item['estrategia']} --version {item['version']} "
           f"--study {item['estudio']} --sens --isolated --n-trials {item.get('_n_trials', 1)} --var-sr {item.get('_var_sr', 0.0)}")
    t0 = time.time(); r = sh(cmd)
    log = f"$ {cmd}\n{r.stdout}\n{r.stderr}\n[{time.time()-t0:.0f}s exit {r.returncode}]\n"
    return r.returncode == 0, log


def run_one(item):
    b = backlog(); it = next(x for x in b["pruebas"] if x["id"] == item["id"]); it["estado"] = "corriendo"; it["inicio_utc"] = now(); save_backlog(b)
    rd = os.path.join(RUNS, item["id"]); shutil.rmtree(rd, ignore_errors=True); os.makedirs(rd)
    logf = open(os.path.join(rd, "log.txt"), "a")
    commit = item.get("commit") or sh(f"git --git-dir={MIRROR} rev-parse main").stdout.strip()
    wd = os.path.join(rd, "src"); sh(f"git clone -q {MIRROR} {wd} && git -C {wd} checkout -q {commit}")
    logf.write(f"{now()} clon limpio de {commit}\n")
    fails = preflight(item, commit, wd)
    if fails:
        logf.write("PREFLIGHT FALLA: " + "; ".join(fails) + "\n"); logf.close()
        it["estado"] = "congelada"; it["ultimo_error"] = "; ".join(fails); save_backlog(b); return
    ensure_image()
    gok, glog = golden_in_container(wd, rd); logf.write(f"{now()} golden: {glog}\n")
    if not gok:
        logf.write("GOLDEN DIFIERE: el motor cambió sin actualizar golden.json; no se corre nada\n"); logf.close()
        it["estado"] = "congelada"; it["ultimo_error"] = "golden difiere: " + glog[-160:]; save_backlog(b); return
    sys.path.insert(0, os.path.join(REPO, "futures", "lab"))
    from engine import registry
    import statistics
    shs = registry.all_sharpes()
    item["_n_trials"] = len(registry.read(registry.TRIALS)) + 1
    item["_var_sr"] = statistics.pvariance(shs) if len(shs) > 1 else 0.0
    ok1, l1 = run_in_container(wd, item, os.path.join(rd, "out1"), "a"); logf.write(l1)
    ok2, l2 = run_in_container(wd, item, os.path.join(rd, "out2"), "b"); logf.write(l2)
    receipt = {"id": item["id"], "commit": commit, "inicio": it["inicio_utc"], "fin": now(), "corrida_1_ok": ok1, "corrida_2_ok": ok2}
    res1 = _result_dir(os.path.join(rd, "out1")); res2 = _result_dir(os.path.join(rd, "out2"))
    if ok1 and ok2 and res1 and res2:
        h1, h2 = sha(os.path.join(res1, "trades.csv")), sha(os.path.join(res2, "trades.csv"))
        receipt["trades_sha256"] = [h1, h2]; receipt["reproducible"] = h1 == h2
        if h1 == h2:
            test_id = registry.next_test_id()          # id secuencial al publicar; dentro del contenedor era X<huella>
            dst = os.path.join(REPO, "futures", "lab", "results", test_id)
            shutil.rmtree(dst, ignore_errors=True); shutil.copytree(res1, dst)
            rep = json.load(open(os.path.join(dst, "report.json"), encoding="utf-8"))
            rep["id_contenedor"] = rep["id"]; rep["id"] = test_id
            rep["archivos"] = {k: v.replace(rep["id_contenedor"], test_id) for k, v in rep["archivos"].items()}
            rep["receta"]["reproducible"] = True; rep["receta"]["commit"] = commit; rep["receta"]["contenedor"] = IMAGE
            json.dump(rep, open(os.path.join(dst, "report.json"), "w", encoding="utf-8"), ensure_ascii=False)
            # el registro se escribe FUERA del contenedor, con la receta que trae el reporte
            registry.record_trial(test_id, item["estudio"], item["estrategia"], item["version"], "prueba", rep["receta"].get("parametros", {}),
                                  rep["receta"].get("sesiones_sha256"), 0, rep["receta"].get("semilla"), rep["receta"].get("costos"),
                                  {**rep["resultados"], "reproducible": True, "commit": commit, "contenedor": IMAGE}, rep["veredicto"],
                                  f"orquestador: 2 corridas en contenedor efímero sin red, trades.csv idéntico ({h1[:12]})")
            it["estado"] = "corrida"; it["test_id"] = test_id; it["veredicto"] = rep["veredicto"]
            logf.write(f"{now()} PUBLICADA como {test_id} ({rep['veredicto']})\n")
        else:
            it["estado"] = "congelada"; it["ultimo_error"] = f"NO REPRODUCIBLE: {h1[:12]} vs {h2[:12]}"
            logf.write(f"{now()} NO REPRODUCIBLE, no se publica\n")
    else:
        it["estado"] = "congelada"; it["ultimo_error"] = "falló una corrida; ver log"
    it["fin_utc"] = now(); save_backlog(b)
    json.dump(receipt, open(os.path.join(rd, "receipt.json"), "w"), indent=1); logf.close()


def _result_dir(out):
    r = os.path.join(out, "results")
    if not os.path.isdir(r):
        return None
    ds = sorted(os.listdir(r))
    return os.path.join(r, ds[-1]) if ds else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--once", action="store_true"); ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry", default="", help="ESTRATEGIA:VERSION:ESTUDIO — corre las 2 corridas en contenedor sin registrar ni publicar")
    a = ap.parse_args()
    b = backlog()
    if a.dry:
        sid, v, st = a.dry.split(":")
        item = {"id": "DRY", "estrategia": sid, "version": int(v), "estudio": st}
        rd = os.path.join(RUNS, "DRY"); shutil.rmtree(rd, ignore_errors=True); os.makedirs(rd)
        commit = sh(f"git --git-dir={MIRROR} rev-parse main").stdout.strip(); wd = os.path.join(rd, "src")
        sh(f"git clone -q {MIRROR} {wd} && git -C {wd} checkout -q {commit}")
        print("preflight:", preflight(item, commit, wd) or "ok"); ensure_image()
        ok1, l1 = run_in_container(wd, item, os.path.join(rd, "out1"), "a"); print(l1[-600:])
        ok2, l2 = run_in_container(wd, item, os.path.join(rd, "out2"), "b"); print(l2[-300:])
        r1, r2 = _result_dir(os.path.join(rd, "out1")), _result_dir(os.path.join(rd, "out2"))
        if r1 and r2:
            h1, h2 = sha(os.path.join(r1, "trades.csv")), sha(os.path.join(r2, "trades.csv")); print("reproducible:", h1 == h2, h1[:12], h2[:12])
        return
    if a.status:
        for it in b["pruebas"]:
            print(f"{it['id']:14} {it['estado']:10} {it.get('test_id','')} {it.get('ultimo_error','')}")
        return
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 6 * 3600:
        return
    open(LOCK, "w").write(now())
    try:
        nxt = next((it for it in b["pruebas"] if it["estado"] == "congelada"), None)
        if nxt:
            print(f"{now()} arranca {nxt['id']}"); run_one(nxt)
    finally:
        os.remove(LOCK)


if __name__ == "__main__":
    main()
