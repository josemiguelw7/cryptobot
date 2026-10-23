"""Registro de estudios e intentos: solo agregar, nunca editar ni borrar.

futures/lab/registry/studies.jsonl  un estudio por línea: hipótesis, N declarado, criterios de muerte
futures/lab/registry/trials.jsonl   un intento por línea: receta completa + resultado + veredicto
Cada línea lleva la huella SHA-256 de la línea anterior (cadena): si alguien borra o edita
una línea, la cadena se rompe y `verify()` lo detecta.
"""
import hashlib, json, os
from datetime import datetime, timezone
from . import config, ENGINE_VERSION

STUDIES = os.path.join(config.REGISTRY, "studies.jsonl")
TRIALS = os.path.join(config.REGISTRY, "trials.jsonl")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _last_hash(path):
    if not os.path.exists(path):
        return "0" * 64
    last = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = line
    return hashlib.sha256(last.encode()).hexdigest() if last else "0" * 64


def _append(path, rec):
    os.makedirs(config.REGISTRY, exist_ok=True)
    rec["prev_sha256"] = _last_hash(path)
    line = json.dumps(rec, ensure_ascii=False, sort_keys=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return hashlib.sha256((line + "\n").encode()).hexdigest()


def read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def verify(path):
    """Devuelve (ok, línea_rota) revisando la cadena de huellas."""
    prev = "0" * 64
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("prev_sha256") != prev:
                return False, i + 1
            prev = hashlib.sha256(line.encode()).hexdigest()
    return True, None


def register_study(study_id, hypothesis, n_declared, kill_criteria, strategies, notes=""):
    if any(s["study_id"] == study_id for s in read(STUDIES)):
        return study_id
    _append(STUDIES, {"study_id": study_id, "registrado_utc": _now(), "hipotesis": hypothesis, "n_declarado": n_declared,
                      "criterios_de_muerte": kill_criteria, "estrategias": strategies, "notas": notes,
                      "git_commit": config.git_commit(), "protocol_sha256": config.protocol()[1]})
    return study_id


def study_counts(study_id):
    trials = [t for t in read(TRIALS) if t["study_id"] == study_id]
    st = next((s for s in read(STUDIES) if s["study_id"] == study_id), None)
    return {"usados": len(trials), "declarados": st["n_declarado"] if st else None,
            "excedido": bool(st and len(trials) > st["n_declarado"])}


def next_test_id():
    n = len(read(TRIALS)) + 1
    return f"P{n:03d}"


def record_trial(test_id, study_id, strategy, version, kind, params, sessions_sha, sessions_n, seed, costs, result, verdict, notes="", error=None):
    rec = {"test_id": test_id, "study_id": study_id, "registrado_utc": _now(), "estrategia": strategy, "version": version,
           "tipo": kind, "config_hash": config.config_hash({"s": strategy, "v": version, "k": kind, "p": params, "c": costs}),
           "parametros": params, "receta": {"git_commit": config.git_commit(), "git_sucio": config.git_dirty(),
                                            "motor": ENGINE_VERSION, "sesiones_sha256": sessions_sha, "sesiones_n": sessions_n,
                                            "semilla": seed, "costos": costs, "protocol_sha256": config.protocol()[1],
                                            "estrategias_sha256": config.strategies(version)[1] if kind != "senal" else None},
           "resultado": result, "veredicto": verdict, "notas": notes, "error": error}
    return _append(TRIALS, rec)


def all_sharpes():
    """Sharpe diario de cada intento registrado (para la varianza entre intentos del DSR)."""
    return [t["resultado"].get("sharpe_diario") for t in read(TRIALS)
            if t.get("resultado") and t["resultado"].get("sharpe_diario") is not None]
