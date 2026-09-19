"""SEC EDGAR Form 4 downloader — open-market insider PURCHASES (code P).

Measurement infrastructure for draft candidate E2-INS. It trades nothing,
reads no bot state, and has no effect until Epoch 2 is signed.

LOOKAHEAD RULE (the whole point): every row is keyed by `filed` = the date
the filing appears in EDGAR's *daily index*, i.e. the day it became public.
`tx_date` (when the insider actually bought) is stored for reference ONLY
and must never be used as an entry date. Earliest honest entry: next
session open after `filed`.

  EDGAR_UA="name contact" .venv/bin/python data/edgar_form4.py 2026-09-17
  ... --limit 100      # smoke test

SEC fair-access: <=10 req/s and a descriptive User-Agent. We run ~5/s.
"""
import csv, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "insiders")
UA = os.environ.get("EDGAR_UA", "")
BASE = "https://www.sec.gov/Archives/"
COLS = ["filed", "accession", "issuer_cik", "ticker", "issuer", "owner_cik",
        "owner", "officer", "director", "ten_pct", "title", "tx_date", "code",
        "shares", "price", "plan_10b5_1"]


def get(url):
    if not UA:
        raise SystemExit("EDGAR_UA no definido (la SEC exige User-Agent con contacto)")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    time.sleep(0.2)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("latin-1")


def index_files(d):
    q = (d.month - 1) // 3 + 1
    txt = get(f"{BASE}edgar/daily-index/{d.year}/QTR{q}/form.{d:%Y%m%d}.idx")
    seen = []
    for line in txt.splitlines():
        if line.startswith("4 ") and line.rstrip().endswith(".txt"):
            f = line.split()[-1]
            if f not in seen:                  # issuer + owner rows share a file
                seen.append(f)
    return seen


def t(node, path):
    x = node.find(path) if node is not None else None
    return (x.text or "").strip() if x is not None and x.text else ""


def parse(raw, filed, fname):
    m = re.search(r"<ownershipDocument>.*?</ownershipDocument>", raw, re.S)
    if not m:
        return []
    doc = ET.fromstring(m.group(0))
    plan = t(doc, "aff10b5One")
    rows = []
    for o in doc.findall("reportingOwner"):
        rel = o.find("reportingOwnerRelationship")
        for tx in doc.findall("nonDerivativeTable/nonDerivativeTransaction"):
            if t(tx, "transactionCoding/transactionCode") != "P":
                continue
            rows.append([filed, fname.split("/")[-1][:-4],
                         t(doc, "issuer/issuerCik"), t(doc, "issuer/issuerTradingSymbol"),
                         t(doc, "issuer/issuerName"),
                         t(o, "reportingOwnerId/rptOwnerCik"), t(o, "reportingOwnerId/rptOwnerName"),
                         t(rel, "isOfficer"), t(rel, "isDirector"), t(rel, "isTenPercentOwner"),
                         t(rel, "officerTitle"),
                         t(tx, "transactionDate/value"), "P",
                         t(tx, "transactionAmounts/transactionShares/value"),
                         t(tx, "transactionAmounts/transactionPricePerShare/value"), plan])
    return rows


def run(d, limit=None):
    os.makedirs(OUT, exist_ok=True)
    files = index_files(d)[:limit]
    filed, rows, bad = d.isoformat(), [], 0
    for i, f in enumerate(files):
        try:
            rows += parse(get(BASE + f), filed, f)
        except Exception:
            bad += 1
    # guard (charter_v2 s5.1): a purchase cannot be dated AFTER it was published
    for r in rows:
        assert r[11] <= filed, f"tx_date {r[11]} > filed {filed}: indice o parser roto"
    path = os.path.join(OUT, f"form4_P_{d:%Y%m%d}.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(COLS); w.writerows(rows)
    print(f"{filed}: {len(files)} Form 4 leidos, {bad} ilegibles, "
          f"{len(rows)} compras P -> {os.path.relpath(path, ROOT)}")
    return rows


if __name__ == "__main__":
    a = sys.argv[1:]
    lim = int(a[a.index("--limit") + 1]) if "--limit" in a else None
    run(date.fromisoformat(a[0]), lim)
