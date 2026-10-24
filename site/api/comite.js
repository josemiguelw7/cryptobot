// Comité y PIN del laboratorio. Cada persona tiene su propio PIN (variables de Vercel PIN_JOSE y PIN_OSCAR).
// POST {accion:"quien", pin}                         -> {ok, persona}
// POST {accion:"votar", pin, id, voto, comentario}   -> guarda docs/comite/votos/<id>__<persona>.json (commit) y avisa por correo
// Decide Oscar: su voto cambia el estado de la idea (lo aplica la publicación automática, máx. 30 min). Jose Miguel no vota.
const crypto = require("crypto");
const REPO = "josemiguelw7/cryptobot";
const SITE = "https://cryptobot-liga.vercel.app";
const TO = ["jose@radtak.com", "oscontreras84@gmail.com"];
const NOMBRE = { jose: "Jose Miguel", oscar: "Oscar" };
const VOTOS = { aprobar: "Aprobar", descartar: "Descartar", mas_datos: "Pedir más datos" };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function eq(a, b) {
  const x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}

async function persona(pin) {
  const p = String(pin || "").trim().toUpperCase().replace(/[\s-]/g, "");
  let who = null;
  for (const k of ["jose", "oscar"]) {
    const v = (process.env["PIN_" + k.toUpperCase()] || "").toUpperCase().replace(/[\s-]/g, "");
    if (v && p && eq(p, v)) who = k;
  }
  if (!who) await sleep(1200);           // frena intentos de adivinar
  return who;
}

async function gh(method, path, body) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method, headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json",
      "Content-Type": "application/json", "User-Agent": "nqlab-comite" }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, j };
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ error: "solo POST" });
  let b = req.body;
  if (typeof b === "string") { try { b = JSON.parse(b); } catch { return res.status(400).json({ error: "JSON inválido" }); } }
  b = b || {};
  const who = await persona(b.pin);
  if (!who) return res.status(401).json({ error: "PIN incorrecto." });
  if (b.accion === "quien") return res.status(200).json({ ok: true, persona: who, nombre: NOMBRE[who] });
  if (b.accion !== "votar") return res.status(400).json({ error: "acción desconocida" });
  if (who !== "oscar") return res.status(403).json({ error: "En el comité decide Oscar; tu PIN sirve para entrar y mandar notas." });

  const id = String(b.id || "");
  const voto = String(b.voto || "");
  const comentario = String(b.comentario || "").slice(0, 2000);
  if (!/^[A-Za-z0-9-]{2,40}$/.test(id)) return res.status(400).json({ error: "idea inválida" });
  if (!VOTOS[voto]) return res.status(400).json({ error: "voto inválido" });
  if (!process.env.GITHUB_TOKEN) return res.status(503).json({ error: "Falta GITHUB_TOKEN en Vercel: el voto no se puede guardar todavía." });

  // La idea tiene que existir y seguir propuesta.
  const bl = await gh("GET", "futures/backlog.json");
  if (!bl.ok) return res.status(502).json({ error: "No pude leer el backlog del repositorio." });
  const items = JSON.parse(Buffer.from(bl.j.content, "base64").toString("utf8")).pruebas || [];
  const it = items.find((x) => x.id === id);
  if (!it) return res.status(404).json({ error: `No existe la idea ${id}.` });
  if (it.estado !== "propuesta") return res.status(409).json({ error: `${id} ya no está esperando decisión (estado: ${it.estado}).` });

  const path = `docs/comite/votos/${id}__${who}.json`;
  const prev = await gh("GET", path);
  const fecha = new Date().toISOString();
  const doc = { id, persona: who, nombre: NOMBRE[who], voto, comentario, fecha };
  const put = await gh("PUT", path, { message: `comite: ${NOMBRE[who]} vota ${VOTOS[voto]} en ${id}`,
    content: Buffer.from(JSON.stringify(doc, null, 1) + "\n").toString("base64"), sha: prev.ok ? prev.j.sha : undefined,
    committer: { name: "nqlab-comite", email: "lab@radtak.com" } });
  if (!put.ok) return res.status(502).json({ error: "GitHub rechazó el voto", detalle: put.j.message || put.status });

  const estado = voto === "mas_datos" ? "Queda propuesta con tu petición anotada; se ve en la página en la siguiente publicación (máx. 30 min)."
    : `Decidido: la idea queda ${voto === "aprobar" ? "aprobada" : "descartada"} en la siguiente publicación (máx. 30 min).` + (voto === "aprobar" ? " Después Claude escribe y congela las reglas, y el orquestador la corre." : "");

  if (process.env.RESEND_API_KEY) {
    const html = `<div style="font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#14181f;max-width:640px">
<p style="margin:0 0 6px;color:#69707d;font-size:13px">Comité · voto registrado</p>
<h2 style="margin:0 0 10px;font-size:18px">${esc(NOMBRE[who])} votó <b>${esc(VOTOS[voto])}</b> en ${esc(id)}</h2>
<p><b>${esc(it.nombre)}</b><br>${esc(it.hipotesis || "")}</p>
${comentario ? `<div style="white-space:pre-wrap;background:#f6f7f9;border:1px solid #e3e6eb;border-radius:10px;padding:12px">${esc(comentario)}</div>` : ""}
<p>${esc(estado)}</p>
<p style="font-size:13px">🏛️ <a href="${SITE}/#comite">Votar o ver el comité</a> · 📋 <a href="https://github.com/${REPO}/blob/main/docs/comite/agenda_actual.md">Agenda</a></p>
<p style="font-size:12px;color:#8a909b">🤖 Aviso automático del comité del Laboratorio NQ.</p></div>`;
    await fetch("https://api.resend.com/emails", { method: "POST",
      headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, "Content-Type": "application/json", "User-Agent": "nqlab-comite/1.0" },
      body: JSON.stringify({ from: "Laboratorio NQ <lab@radtak.com>", to: TO, reply_to: TO,
        subject: `[Laboratorio NQ] Comité · ${NOMBRE[who]}: ${VOTOS[voto]} en ${id}`, html,
        text: `${NOMBRE[who]} votó ${VOTOS[voto]} en ${id} (${it.nombre}).\n${comentario}\n\n${estado}\n\n${SITE}/#comite\n\n🤖 Aviso automático del comité del Laboratorio NQ.` }) }).catch(() => {});
  }
  return res.status(200).json({ ok: true, persona: who, voto, estado });
};
