"""Forward-test intake ledger (pre-registration docs/prerregistro_forward_ABU_v2.md, approved 2026-10-29).

Records NEW raw NQ session files (dated after the last sealed day) in an append-only, hash-chained ledger,
so that nobody has to look at them to know they arrived. It never reads prices, never builds features, never
simulates. The only thing it prints is a count.

  python -m engine.forward_intake            append any new raw files to the ledger and print the count
  python -m engine.forward_intake --status   print the count only

Ledger: futures/lab/registry/forward_sessions.jsonl  (one line per raw file: date, sha256, bytes, ingested_utc, prev_sha256)
Scoring happens once, by a separate step, when the ledger reaches SCORE_AT_SESSIONS valid sessions (see the pre-registration).
"""
import argparse, glob, hashlib, json, os
from datetime import datetime, timezone
from . import config

FIRST_ELIGIBLE = "2026-10-23"          # first day after the sealed exam (2026-04-22 .. 2026-10-22)
SCORE_AT_SESSIONS = 320                # pre-registered trigger (~100 ABU v2 trades at the design rate)
LEDGER = os.path.join(config.REGISTRY, "forward_sessions.jsonl")
RAW_DIR = os.path.join(config.DATA, "raw", "NQ")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _last_hash():
    rows = _read()
    if not rows:
        return "0" * 64
    with open(LEDGER, encoding="utf-8") as f:
        last = [l for l in f if l.strip()][-1]
    return hashlib.sha256(last.encode()).hexdigest()


def _append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rec["prev_sha256"] = _last_hash()
    line = json.dumps(rec, ensure_ascii=False, sort_keys=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def new_raw_files():
    """Raw session files dated after FIRST_ELIGIBLE - 1 that are not yet in the ledger."""
    seen = {r["date"] for r in _read()}
    out = []
    for p in sorted(glob.glob(os.path.join(RAW_DIR, "????-??-??.csv.gz"))):
        d = os.path.basename(p)[:10]
        if d >= FIRST_ELIGIBLE and d not in seen:
            out.append((d, p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="print the count only; do not append")
    a = ap.parse_args()
    if not a.status:
        for d, p in new_raw_files():
            _append({"date": d, "file": os.path.basename(p), "sha256": _sha256(p), "bytes": os.path.getsize(p),
                     "ingested_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "audit": "pending"})
    rows = _read()
    n = len(rows)
    print(f"forward ledger: {n} raw sessions recorded (first eligible {FIRST_ELIGIBLE}; scoring trigger {SCORE_AT_SESSIONS} valid sessions; "
          f"last recorded {rows[-1]['date'] if rows else 'none'}). No prices were read.")


if __name__ == "__main__":
    main()
