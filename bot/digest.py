"""
Daily digest + missed-day alarm (build plan W2.3).

digest : after the daily run, summarize standings, daily deltas, and
         each member's distance-to-circuit-breaker. Emails via Resend
         if RESEND_API_KEY + DIGEST_TO are set; otherwise prints.
alarm  : verify today's equity rows exist; if not, shout (email/print).

Usage:
    python bot/digest.py            # send/print the digest
    python bot/digest.py --alarm    # missed-day check only
"""
import argparse, csv, json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EQLOG = os.path.join(ROOT, "logs", "league_equity.csv")
STATE = os.path.join(HERE, "league_state.json")
MAXDD = 0.20


def rows():
    if not os.path.exists(EQLOG):
        return []
    with open(EQLOG) as f:
        return list(csv.DictReader(f))


def today_has_rows(rs):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return any(r["time"].startswith(today) for r in rs)


def send(subject, body):
    """Email via Resend if configured, else print. Never raises."""
    key = os.environ.get("RESEND_API_KEY")
    to = os.environ.get("DIGEST_TO")
    frm = os.environ.get("DIGEST_FROM", "onboarding@resend.dev")
    if not (key and to):
        print(f"[digest: email not configured, printing]\n"
              f"Subject: {subject}\n\n{body}")
        return
    try:
        import requests
        r = requests.post("https://api.resend.com/emails",
                          headers={"Authorization": f"Bearer {key}"},
                          json={"from": frm, "to": [to],
                                "subject": subject, "text": body},
                          timeout=20)
        print(f"digest emailed ({r.status_code}) to {to}")
    except Exception as e:
        print(f"[digest: email failed {e}, printing]\n{body}")


def build_digest():
    rs = rows()
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    # latest + previous equity per strategy
    latest, prev = {}, {}
    for r in rs:
        s = r["strategy"]
        if s in latest:
            prev[s] = latest[s]
        latest[s] = float(r["equity"])
    lines = []
    ranked = sorted(latest.items(), key=lambda kv: kv[1], reverse=True)
    for i, (s, eq) in enumerate(ranked, 1):
        ret = eq / 10000 - 1
        delta = (eq - prev[s]) / prev[s] if s in prev and prev[s] else 0
        peak = float(state.get(s, {}).get("peak_equity", eq))
        # breaker fires when equity < peak*(1-MAXDD). Room = fractional
        # drop from HERE to that level: 1 - (1-MAXDD)*peak/eq.
        to_breaker = 1 - (1 - MAXDD) * peak / eq if eq else 0
        halted = state.get(s, {}).get("halted")
        lines.append(
            f"{i}. {s:10} ${eq:>10,.2f}  {ret:+7.2%}  "
            f"today {delta:+.2%}  "
            f"{'HALTED' if halted else f'breaker room {to_breaker:.0%}'}")
    return "\n".join(lines) or "No equity data yet."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alarm", action="store_true")
    args = ap.parse_args()
    rs = rows()
    if args.alarm:
        if not today_has_rows(rs):
            send("⚠️ CRYPTOBOT: no league run today",
                 "The 9am league cycle did not log any equity rows for "
                 "today. Check the Mac was awake and logs/daily.log.")
        else:
            print("alarm check: today's rows present, all good.")
        return
    body = build_digest()
    stale = "" if today_has_rows(rs) else "\n\n(!) No rows for today yet."
    send(f"Cryptobot league — {datetime.now(timezone.utc):%Y-%m-%d}",
         body + stale)


if __name__ == "__main__":
    main()
