"""Asistente de Oscar Lab: Claude en el servidor contesta las notas del buzón.
Cada 5 min (cron): trae el repo, busca notas nuevas en docs/oscar/inbox/, y por cada una
  1) le pasa a Claude la nota (y su captura) con el estado real del laboratorio (LAB.md, cola, resultados),
  2) manda la respuesta por correo a Oscar y Jose Miguel (formato Oscar Lab),
  3) guarda la respuesta en docs/oscar/respuestas/ y, si Oscar pidió trabajo nuevo, lo deja en la cola
     como 'aprobada' (lo pidió él; decide Oscar). NUNCA cambia reglas congeladas, código ni corre pruebas.
Config: /srv/lab/asistente.json  {"activo": true}  (Claude Code con la suscripción de Jose; sin API key)
  python -m engine.asistente            # una vuelta
  python -m engine.asistente --seco     # no manda correo ni hace push; imprime la respuesta
  python -m engine.asistente --marcar   # marca todas las notas actuales como ya atendidas (arranque)
"""
import base64, glob, json, os, re, subprocess, sys, time, urllib.request

CFG = "/srv/lab/asistente.json"; STATE = "/srv/lab/asistente_state.json"; LOG = "/srv/lab/logs/asistente.log"
R = "/srv/lab/asistente-repo"; REMOTE = "git@github.com:josemiguelw7/cryptobot.git"
GIT_ENV = dict(os.environ, GIT_SSH_COMMAND="ssh -i %s/.ssh/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" % os.path.expanduser("~"))
MAX_NOTAS_POR_VUELTA = 3          # freno: nunca más de 3 respuestas cada 5 min
MAX_POR_DIA = 40

SISTEMA = """Eres el asistente del laboratorio de trading "Oscar Lab" (investigación de order flow en futuros NQ con datos tick reales).
Contestas notas que Oscar (trader, el que decide en el comité) o Jose Miguel (dueño) mandan desde el buzón de la página.
Escribes en español, claro y directo, como un colega analista. Sin jerga innecesaria; si usas un término técnico, explícalo en pocas palabras.

REGLAS QUE NO SE ROMPEN
- Solo afirmas cifras que estén en el CONTEXTO (LAB.md, cola, resultados). Si un dato no está, lo dices ("eso no está medido todavía") y no lo inventas.
- Cita la prueba o el estudio de donde sale cada cifra (p. ej. P012, mapa de señales).
- Nunca prometas ganancias ni digas que algo "funciona" si el laboratorio no lo validó. Ninguna estrategia ha pasado todo todavía; el examen final sellado (desde 22/04/2026) sigue cerrado y nadie lo mira.
- No puedes cambiar reglas congeladas, código, ni correr pruebas. Si la nota pide trabajo (un estudio, una prueba, un indicador, una corrección), explica en pocas líneas cómo se haría con el método del laboratorio (estudio registrado antes de correr, definición congelada con huella y sello, comparación contra el azar) y di que queda en la cola: el investigador autónomo del servidor lo toma primero, antes que sus propias ideas, y el resultado le llega por correo.
- Si es un problema de la página o del servidor, describe qué entendiste y di que queda anotado para Jose Miguel.
- En el comité decide Oscar. Nunca reveles PINs, llaves ni datos privados.
- Respuestas cortas: lo que se lee en un minuto. Si la pregunta es amplia, contesta lo esencial y ofrece profundizar.

FORMATO DE SALIDA: solo un objeto JSON, sin texto antes ni después, sin ```:
{"asunto": "máx 70 caracteres",
 "respuesta": "texto para el correo; párrafos separados por línea en blanco; listas con '- '",
 "accion": "respondida" | "en_cola" | "para_jose",
 "trabajo": null | {"id": "E-... o T-... corto, MAYÚSCULAS y guiones", "nombre": "...", "hipotesis": "qué se mide o se construye, 1-3 frases"}}
'accion' = "en_cola" solo si la nota pide trabajo nuevo (entonces 'trabajo' no es null); "para_jose" si es un problema técnico o algo que solo Jose puede resolver."""


def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {m}\n")


def git(*a, check=True):
    return subprocess.run(["git", "-C", R, *a], env=GIT_ENV, capture_output=True, text=True, check=check)


def sync():
    if not os.path.isdir(os.path.join(R, ".git")):
        subprocess.run(["git", "clone", "-q", REMOTE, R], env=GIT_ENV, check=True)
    git("fetch", "-q", "origin"); git("reset", "-q", "--hard", "origin/main")


def front(raw):
    meta = {}
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1); meta[k.strip()] = v.strip()
        raw = raw[m.end():]
    return meta, re.sub(r"\n*!\[captura\]\([^)]*\)\s*$", "", raw.strip())


def contexto():
    rd = lambda p, n: open(os.path.join(R, p), encoding="utf-8").read()[:n] if os.path.exists(os.path.join(R, p)) else ""
    B = json.load(open(os.path.join(R, "futures/backlog.json"), encoding="utf-8"))["pruebas"]
    cola = "\n".join(f"- {i['id']} [{i['estado']}] {i['nombre']}: {i.get('hipotesis','')[:220]}" + (f" (decisión: {i['decision'][:120]})" if i.get("decision") else "") for i in B)
    T = json.load(open(os.path.join(R, "futures/tests.json"), encoding="utf-8"))["pruebas"]
    res = "\n".join(f"- {t['id']} {t['estrategia']} v{t['version']} [{t['veredicto']}] neto ${t['resultados'].get('ganancia_neta',0):,.0f}, "
                    f"p vs azar {t['resultados'].get('vs_rand')}, Topstep {t['resultados'].get('topstep')}%, {t['resultados'].get('operaciones')} ops. "
                    f"Causa: {(t.get('muerte') or '')[:200]}" for t in T)
    resp = sorted(glob.glob(os.path.join(R, "docs/oscar/respuestas/*.md")))[-3:]
    prev = "\n\n".join(open(f, encoding="utf-8").read()[:1500] for f in resp)
    return (f"=== LAB.md (estado completo) ===\n{rd('LAB.md', 30000)}\n\n=== COLA DE PRUEBAS ===\n{cola}\n\n"
            f"=== RESULTADOS PUBLICADOS ===\n{res}\n\n=== ÚLTIMAS RESPUESTAS DEL ASISTENTE ===\n{prev or '(ninguna)'}")


def claude(cfg, meta, texto, img_path):
    """Usa Claude Code con la suscripción de Jose (token OAuth en ~/.config/oscar-lab/claude.env), no API key."""
    img = img_path if img_path and os.path.exists(img_path) else None
    prompt = (f"{contexto()}\n\n=== NOTA DEL BUZÓN ===\nDe: {meta.get('autor')}\nTipo: {meta.get('tipo')}\nFecha: {meta.get('fecha')}\n"
              f"Título: {meta.get('titulo')}\nEnviada desde: {meta.get('pagina')}\n"
              + (f"Trae captura de pantalla: léela con la herramienta Read en {img}\n" if img else "")
              + f"\n{texto}\n\nContesta según las reglas. Solo el JSON.")
    env = dict(os.environ, PATH=os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", ""))
    for line in open(os.path.expanduser("~/.config/oscar-lab/claude.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); env[k] = v
    r = subprocess.run(["claude", "-p", prompt, "--append-system-prompt", SISTEMA, "--allowedTools", "Read",
                        "--max-turns", "6", "--output-format", "text"], env=env, capture_output=True, text=True, timeout=600, cwd="/tmp")
    out = r.stdout.strip()
    if r.returncode != 0 or "{" not in out:
        raise RuntimeError(f"claude -p falló ({r.returncode}): {(r.stderr or out)[-300:]}")
    out = re.sub(r"^```(?:json)?\s*|\s*```$", "", out)
    j = json.loads(out[out.index("{"): out.rindex("}") + 1])
    assert j.get("respuesta") and j.get("asunto")
    return j


def correo(meta, j, nota_rel, seco):
    sys.path.insert(0, "/srv/lab/repo/futures/lab")
    from engine import notify
    import html as H
    cuerpo = "".join(f'<p style="margin:0 0 10px">{H.escape(p).replace(chr(10), "<br>")}</p>' for p in j["respuesta"].strip().split("\n\n"))
    estado = {"respondida": "✅ Respondida", "en_cola": f"📋 Queda en la cola como {j['trabajo']['id']}" if j.get("trabajo") else "📋 En la cola",
              "para_jose": "🛠️ Anotado para Jose Miguel"}.get(j["accion"], "")
    cita = H.escape((meta.get("titulo") or "")[:120])
    inner = (f'<div style="font-size:12px;color:#69707d;margin-bottom:10px">Respuesta a la nota de {H.escape(meta.get("autor",""))}'
             + (f' · «{cita}»' if cita else "") + f' · {estado}</div>{cuerpo}'
             + '<p style="font-size:12px;color:#8a909b;margin-top:14px">Escrito por Claude en el servidor del laboratorio con los datos publicados. '
               'Si algo no cuadra, responde con otra nota o escríbele a Jose Miguel.</p>')
    texto = f"Respuesta a la nota de {meta.get('autor','')}: {meta.get('titulo','')}\n{estado}\n\n{j['respuesta']}\n\n(Escrito por Claude en el servidor del laboratorio.)"
    if seco:
        print("ASUNTO:", j["asunto"]); print(texto); return True
    return notify.send(j["asunto"], texto, html_body=inner,
                       extra_links=[("📨", "La nota original", f"https://github.com/josemiguelw7/cryptobot/blob/main/{nota_rel}")])


def registrar(base, meta, j):
    os.makedirs(os.path.join(R, "docs/oscar/respuestas"), exist_ok=True)
    with open(os.path.join(R, "docs/oscar/respuestas", base + ".md"), "w", encoding="utf-8") as f:
        f.write(f"---\nnota: {base}.md\nautor_nota: {meta.get('autor')}\naccion: {j['accion']}\nfecha: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
                f"asunto: {j['asunto']}\n---\n\n{j['respuesta']}\n")
    w = j.get("trabajo")
    if j["accion"] == "en_cola" and w and re.fullmatch(r"[A-Z0-9-]{3,30}", w.get("id", "")):
        p = os.path.join(R, "futures/backlog.json"); b = json.load(open(p, encoding="utf-8"))
        if not any(i["id"] == w["id"] for i in b["pruebas"]):
            quien = (meta.get("autor") or "").lower()
            b["pruebas"].append({"id": w["id"], "nombre": w["nombre"], "hipotesis": w["hipotesis"],
                                 "origen": f"nota del buzón de {meta.get('autor')} ({(meta.get('fecha') or '')[:10]}), resumida por el asistente",
                                 "estado": "aprobada" if "oscar" in quien else "propuesta",
                                 "decision": f"pedida por Oscar en el buzón {(meta.get('fecha') or '')[:10]}" if "oscar" in quien else ""})
            json.dump(b, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            live = "/srv/lab/repo/futures/backlog.json"
            if os.path.exists(live):
                bl = json.load(open(live, encoding="utf-8"))
                if not any(i["id"] == w["id"] for i in bl["pruebas"]):
                    bl["pruebas"].append(b["pruebas"][-1]); json.dump(bl, open(live, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def push(msg):
    git("add", "-A")
    if not git("status", "--porcelain").stdout.strip():
        return
    git("-c", "user.name=oscarlab-asistente", "-c", "user.email=lab@radtak.com", "commit", "-qm", msg)
    for _ in range(3):
        if git("pull", "-q", "--rebase", "origin", "main", check=False).returncode == 0 and git("push", "-q", "origin", "main", check=False).returncode == 0:
            return
        time.sleep(5)
    log("push falló")


def main():
    seco = "--seco" in sys.argv
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"hechas": [], "dia": "", "n_dia": 0}
    sync()
    notas = sorted(glob.glob(os.path.join(R, "docs/oscar/inbox/*.md")))
    if "--marcar" in sys.argv:
        st["hechas"] = sorted(set(st["hechas"]) | {os.path.basename(n) for n in notas})
        json.dump(st, open(STATE, "w"), indent=1); print("marcadas", len(notas)); return
    if not os.path.exists(CFG):
        return
    cfg = json.load(open(CFG))
    if not cfg.get("activo", True):
        return
    hoy = time.strftime("%Y-%m-%d")
    if st.get("dia") != hoy:
        st["dia"], st["n_dia"] = hoy, 0
    nuevas = [n for n in notas if os.path.basename(n) not in st["hechas"]][:MAX_NOTAS_POR_VUELTA]
    if seco and "--nota" in sys.argv:
        nuevas = [os.path.join(R, "docs/oscar/inbox", sys.argv[sys.argv.index("--nota") + 1])]
    hechas = []
    for n in nuevas:
        if st["n_dia"] >= MAX_POR_DIA:
            log("tope diario alcanzado"); break
        base = os.path.basename(n)[:-3]
        meta, texto = front(open(n, encoding="utf-8").read())
        img = os.path.join(R, "docs/oscar/inbox", meta["captura"]) if meta.get("captura") else None
        try:
            j = claude(cfg, meta, texto, img)
        except Exception as e:
            log(f"{base}: error de Claude: {e}"); continue
        if correo(meta, j, f"docs/oscar/inbox/{base}.md", seco) and not seco:
            registrar(base, meta, j); st["hechas"].append(base + ".md"); st["n_dia"] += 1; hechas.append(base)
            log(f"{base}: {j['accion']} · {j['asunto']}")
    if hechas and not seco:
        push("asistente: responde " + ", ".join(hechas))
    if not seco:
        json.dump(st, open(STATE, "w"), indent=1)


if __name__ == "__main__":
    main()
