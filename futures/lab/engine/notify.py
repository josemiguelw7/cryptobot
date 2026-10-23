"""Avisos del laboratorio. Lee /srv/lab/notify.json en la VM:
  {"resend_api_key": "re_...", "from": "lab@radtak.com", "to": ["jose@..."]}
Si no existe, solo escribe en el log (nunca falla por esto).
  python -m engine.notify "asunto" "cuerpo"
"""
import json, os, sys, time, urllib.request

CFG = "/srv/lab/notify.json"; LOG = "/srv/lab/logs/notify.log"


def send(subject, body):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {subject}\n")
    if not os.path.exists(CFG):
        return False
    c = json.load(open(CFG))
    req = urllib.request.Request("https://api.resend.com/emails", method="POST",
                                 data=json.dumps({"from": c["from"], "to": c["to"], "subject": f"[Laboratorio NQ] {subject}", "text": body}).encode(),
                                 headers={"Authorization": "Bearer " + c["resend_api_key"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status < 300
    except Exception as e:
        with open(LOG, "a") as f:
            f.write(f"  error: {e}\n")
        return False


if __name__ == "__main__":
    print(send(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
