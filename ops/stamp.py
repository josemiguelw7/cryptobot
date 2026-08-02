"""
ops/stamp.py - keep OpenTimestamps receipts current for the criteria docs.

WHY

A private GitHub repo gives the pre-registration a backup and a date, but
not immutability: force-push works on a repo the author controls, and there
are no third parties watching. The .ots receipts are what actually make a
loosened charter detectable, because they commit each document's sha256 to
the Bitcoin blockchain and nobody can revise that.

A fresh stamp is PENDING, not proof. It becomes proof only after a Bitcoin
block confirms it and the receipt is upgraded to carry the attestation,
typically a few hours later. A pending receipt that is never upgraded
proves nothing. That is precisely the kind of step a human forgets, so it
runs from the daily driver instead.

WHAT IT COVERS

Only the ratchet surface: the documents that define what counts as success.
Session notes and build plans are deliberately excluded - stamping those
adds noise without adding a constraint on future behaviour.

Adding a document here is safe. Removing one, or letting its receipt go
permanently unupgraded, quietly weakens the pre-registration.

Exit 0 = all receipts present and confirmed
       1 = receipts present, one or more still pending (normal for hours)
       2 = a document changed and its receipt no longer matches, or the
           ots client is unavailable
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

# The ratchet surface. See docstring before editing.
COVERED = [
    "intraday_success_criteria.md",
    "intraday_standard.md",
    "success_criteria.md",
    "entrance_exam.md",
    "exam_amendment_001.md",
]


def ots():
    exe = shutil.which("ots") or os.path.join(ROOT, ".venv", "bin", "ots")
    return exe if os.path.exists(exe) else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(exe, *args):
    r = subprocess.run([exe, *args], capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def receipt_hash(exe, ots_path):
    """The sha256 the receipt actually commits to. If this stops matching
    the file on disk, the document was edited after stamping and the
    receipt now attests to a version that no longer exists."""
    _, out = run(exe, "info", ots_path)
    for line in out.splitlines():
        if "sha256 hash:" in line:
            return line.split(":")[-1].strip()
    return None


def main():
    exe = ots()
    if not exe:
        print("ots client not found. pip install opentimestamps-client")
        return 2

    pending, confirmed, drifted, missing = [], [], [], []

    for name in COVERED:
        doc = os.path.join(DOCS, name)
        if not os.path.exists(doc):
            continue
        rec = doc + ".ots"

        if not os.path.exists(rec):
            print(f"stamping {name} (no receipt yet)")
            rc, out = run(exe, "stamp", doc)
            print("  " + out.strip().replace("\n", "\n  ")[:400])
            missing.append(name)
            continue

        committed = receipt_hash(exe, rec)
        actual = sha256(doc)
        if committed and committed != actual:
            drifted.append((name, committed, actual))
            continue

        rc, out = run(exe, "upgrade", rec)
        if "Success" in out or "up to date" in out.lower():
            confirmed.append(name)
        elif "Pending" in out:
            pending.append(name)
        else:
            # upgrade is idempotent; an already-complete receipt says so
            _, vout = run(exe, "verify", rec)
            (confirmed if "Success" in vout else pending).append(name)

    print()
    if confirmed:
        print(f"confirmed on Bitcoin ..... {len(confirmed)}: {', '.join(confirmed)}")
    if pending:
        print(f"pending confirmation ..... {len(pending)}: {', '.join(pending)}")
        print("  Normal for the first hours after stamping. Re-run later;")
        print("  the daily driver does this automatically.")
    if missing:
        print(f"newly stamped ............ {len(missing)}: {', '.join(missing)}")
        print("  Commit the new .ots files.")
    if drifted:
        print(f"\n!!! RECEIPT MISMATCH on {len(drifted)} document(s):")
        for name, committed, actual in drifted:
            print(f"  {name}")
            print(f"    receipt commits to {committed}")
            print(f"    file on disk is    {actual}")
        print("  The document was edited after it was stamped. Under the")
        print("  ratchet this is only legitimate if the change makes the")
        print("  criteria STRICTER. Record which, then re-stamp.")
        return 2

    return 1 if (pending or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
