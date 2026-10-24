"""Avisos del laboratorio por correo (Resend). Lee /srv/lab/notify.json en la VM:
  {"resend_api_key": "re_...", "from": "Oscar Lab <lab@radtak.com>", "to": ["..."], "reply_to": "jose@radtak.com"}
Si no existe, solo escribe en el log (nunca falla por esto).
Todos los correos llevan: aviso de informe automático, enlaces útiles con iconos al final y el botón
"Pregunta, problema o datos" que abre el buzón en la página.
  python -m engine.notify "asunto" "cuerpo"                 # texto
  python -m engine.notify "asunto" --html informe.html       # informe largo en HTML (se envuelve igual)
"""
import html as H
import json, os, sys, time, urllib.request

CFG = "/srv/lab/notify.json"; LOG = "/srv/lab/logs/notify.log"
SITE = "https://cryptobot-liga.vercel.app"           # dominio público (el alias *-radtak-projects pide login de Vercel)
REPO = "https://github.com/josemiguelw7/cryptobot"
ASK = "https://claude.ai/artifact/Cg4KvpvZ4gCEgVu2QZKmd7"


def links(test_id=None, extra=None):
    L = []
    if test_id:
        L += [("🧪", f"Ver la prueba {test_id} en la página", f"{SITE}/#prueba-{test_id}"),
              ("📁", f"Archivos de {test_id} (operaciones, recibo)", f"{REPO}/tree/main/futures/lab/results/{test_id}")]
    L += list(extra or [])
    L += [("🏠", "Página del laboratorio", SITE),
          ("📋", "Agenda del comité", f"{REPO}/blob/main/docs/comite/agenda_actual.md"),
          ("📄", "Estado completo del laboratorio (LAB.md)", f"{REPO}/blob/main/LAB.md"),
          ("💬", "Pregúntale al Laboratorio (Claude)", ASK)]
    return L


def wrap(subject, inner_html, L):
    rows = "".join(f'<tr><td style="padding:6px 10px 6px 0;font-size:18px;width:28px;vertical-align:top">{i}</td>'
                   f'<td style="padding:6px 0"><a href="{u}" style="color:#01874E;text-decoration:none;font-weight:600">{H.escape(t)}</a></td></tr>' for i, t, u in L)
    return f"""<!doctype html><html><body style="margin:0;background:#f4f5f7;padding:24px 12px;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#14181f">
<div style="max-width:640px;margin:0 auto;background:#fff;border:1px solid #e3e6eb;border-radius:12px;overflow:hidden">
<div style="background:#001830;color:#fff;padding:14px 20px;font-weight:700">Oscar <span style="color:#00A968">Lab</span> <span style="color:#9DB3C2;font-weight:400">· {H.escape(subject)}</span></div>
<div style="padding:18px 20px">{inner_html}</div>
<div style="border-top:1px solid #e3e6eb;padding:16px 20px">
 <div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#69707d;margin-bottom:6px">Enlaces</div>
 <table role="presentation" style="border-collapse:collapse">{rows}</table>
 <p style="margin:12px 0 0;font-size:13px;color:#69707d">La página se actualiza cada 30 minutos; si un enlace todavía no muestra lo último, espera la siguiente publicación.</p>
</div>
<div style="padding:18px 20px;text-align:center;background:#f8fafc;border-top:1px solid #e3e6eb">
 <a href="{SITE}/#reportar" style="display:inline-block;background:#01874E;color:#fff;text-decoration:none;font-weight:700;padding:12px 20px;border-radius:10px">❓ Pregunta, problema o datos para agregar</a>
 <p style="margin:10px 0 0;font-size:13px;color:#69707d">Abre el buzón en la página: escribe la pregunta y pega una captura de pantalla.</p>
</div>
<div style="padding:12px 20px;font-size:12px;color:#8a909b;border-top:1px solid #e3e6eb">🤖 Este es un informe automático de Oscar Lab, generado por el servidor del laboratorio. Nadie lo escribió a mano. Si respondes a este correo, la respuesta le llega a Jose Miguel.</div>
</div></body></html>"""


def text_footer(L):
    return ("\n\n— Enlaces —\n" + "\n".join(f"{i} {t}: {u}" for i, t, u in L) +
            f"\n\n❓ Pregunta, problema o datos para agregar: {SITE}/#reportar\n\n"
            "🤖 Informe automático de Oscar Lab, generado por el servidor del laboratorio. Si respondes, le llega a Jose Miguel.")


def body_html(body):
    return "".join(f'<p style="margin:0 0 10px">{H.escape(p).replace(chr(10), "<br>")}</p>' for p in body.strip().split("\n\n"))


def send(subject, body="", test_id=None, html_body=None, extra_links=None):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {subject}\n")
    if not os.path.exists(CFG):
        return False
    c = json.load(open(CFG)); L = links(test_id, extra_links)
    msg = {"from": c["from"].replace("Laboratorio NQ", "Oscar Lab"), "to": c["to"], "subject": f"[Oscar Lab] {subject}",
           "html": wrap(subject, html_body or body_html(body), L), "text": (body or subject) + text_footer(L),
           "reply_to": c.get("reply_to", "jose@radtak.com")}
    req = urllib.request.Request("https://api.resend.com/emails", method="POST", data=json.dumps(msg).encode(),
                                 headers={"Authorization": "Bearer " + c["resend_api_key"], "Content-Type": "application/json",
                                          "User-Agent": "nqlab-notify/1.0"})   # Cloudflare bloquea el User-Agent de urllib (error 1010)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status < 300
    except Exception as e:
        with open(LOG, "a") as f:
            f.write(f"  error: {e}\n")
        return False


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[1] == "--html":
        print(send(a[0], "", html_body=open(a[2], encoding="utf-8").read()))
    else:
        print(send(a[0], a[1] if len(a) > 1 else ""))
