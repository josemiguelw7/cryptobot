"""Huellas de los datos canónicos y verificación dentro del contenedor.

  python -m engine.data_manifest build      -> futures/canonical_manifest.json (SHA-256 y tamaño de cada parquet de diseño)
  python -m engine.data_manifest verify     -> tamaños de todos + SHA-256 de una muestra de 30 (semilla fija); sale con 1 si algo difiere
El motor llama a verify al arrancar en modo aislado: si alguien reprocesó los datos, la prueba no corre.
"""
import hashlib, json, os, sys, time
import numpy as np
from . import config

MAN = os.path.join(config.FUT, "canonical_manifest.json")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build():
    dates, sess_sha = config.design_sessions(); out = {}
    for d in dates:
        p = os.path.join(config.CAN, f"{d}.parquet"); out[d] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    json.dump({"generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sesiones_sha256": sess_sha, "archivos": out}, open(MAN, "w"), indent=1)
    print(f"manifiesto: {len(out)} archivos")


def verify(sample=30):
    m = json.load(open(MAN)); bad = []
    for d, r in m["archivos"].items():
        p = os.path.join(config.CAN, f"{d}.parquet")
        if not os.path.exists(p) or os.path.getsize(p) != r["bytes"]:
            bad.append(f"{d}: tamaño o archivo distinto")
    rng = np.random.default_rng(20261023); keys = sorted(m["archivos"])
    for d in rng.choice(keys, size=min(sample, len(keys)), replace=False):
        if sha(os.path.join(config.CAN, f"{d}.parquet")) != m["archivos"][d]["sha256"]:
            bad.append(f"{d}: SHA-256 distinto")
    return bad, m["sesiones_sha256"]


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    else:
        bad, _ = verify(); print("datos OK" if not bad else "DATOS DIFIEREN: " + "; ".join(bad[:5])); sys.exit(1 if bad else 0)
