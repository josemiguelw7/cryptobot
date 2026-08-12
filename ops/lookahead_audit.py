"""
ops/lookahead_audit.py — the automated lookahead audit charter §4.5e
requires and (until 2026-08-08) did not exist.

§4.5e: "The weekly review runs an automated lookahead audit over the
week's decisions. The audit result is published whether it passes or
fails." squad.py has faithfully logged `snapshot_sha` and `last_closed`
on every decision since day one — this is the first code that READS
last_closed (external review 2026-08-08, M-6).

The invariant (§4.5b): no decision may use a bar that had not fully
closed at the decision timestamp:  last_closed + 3600 <= utc_ms.

Exit 0 = clean, 2 = violations found. Result is written to
logs/lookahead_audit.json for the portal to publish either way.

Usage:
    python ops/lookahead_audit.py            # audit everything
    python ops/lookahead_audit.py --days 7   # trailing week only
"""
import argparse, csv, json, os, statistics, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "logs")
DECLOGS = ["squad_decisions.csv", "squad_stocks_decisions.csv"]
OUT = os.path.join(LOGS, "lookahead_audit.json")
BAR_S = 3600


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def audit(path, since):
    checked = viol = 0
    lags, worst = [], None
    if not os.path.exists(path):
        return {"file": os.path.basename(path), "checked": 0,
                "violations": 0, "note": "missing"}
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                dt = parse(r["utc_ms"])
                lc = parse(r["last_closed"])
            except (KeyError, ValueError):
                continue
            if since and dt < since:
                continue
            checked += 1
            lag = (dt - lc).total_seconds() - BAR_S
            lags.append(lag)
            if lag < 0:
                viol += 1
                if worst is None or lag < worst["lag_s"]:
                    worst = {"lag_s": lag, "row": dict(r)}
    out = {"file": os.path.basename(path), "checked": checked,
           "violations": viol}
    if lags:
        out["lag_after_close_s"] = {
            "median": round(statistics.median(lags)),
            "min": round(min(lags)), "max": round(max(lags))}
    if worst:
        out["worst"] = worst
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0,
                    help="audit only the trailing N days (0 = all)")
    a = ap.parse_args()
    since = (datetime.now(timezone.utc) - timedelta(days=a.days)) \
        if a.days else None

    results = [audit(os.path.join(LOGS, f), since) for f in DECLOGS]
    total_viol = sum(r["violations"] for r in results)
    total_checked = sum(r["checked"] for r in results)
    report = {"utc": f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
              "window_days": a.days or "all",
              "invariant": "last_closed + 3600 <= utc_ms (charter 4.5b)",
              "checked": total_checked, "violations": total_viol,
              "verdict": "PASS" if total_viol == 0 else "FAIL",
              "detail": results}
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"LOOKAHEAD AUDIT ({report['window_days']} days): "
          f"{total_checked} decisions, {total_viol} violations "
          f"-> {report['verdict']}")
    for r in results:
        lag = r.get("lag_after_close_s", {})
        print(f"  {r['file']}: {r['checked']} checked, "
              f"{r['violations']} violations"
              + (f", median lag {lag.get('median')}s" if lag else ""))
    print(f"published -> {OUT}")
    sys.exit(0 if total_viol == 0 else 2)


if __name__ == "__main__":
    main()
