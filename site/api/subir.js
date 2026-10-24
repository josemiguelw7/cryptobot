// Buzón del laboratorio: preguntas, problemas, datos para agregar e ideas, con captura de pantalla opcional.
// Cada nota (1) llega por correo a Jose Miguel y Oscar con la captura adjunta (RESEND_API_KEY) y
// (2) se guarda como commit en docs/oscar/inbox/ del repo, captura incluida (GITHUB_TOKEN, fine-grained,
// solo "Contents: Read and write" sobre josemiguelw7/cryptobot). Basta con que una de las dos funcione.
const REPO = "josemiguelw7/cryptobot";
const SITE = "https://cryptobot-liga.vercel.app";
const TO = ["jose@radtak.com", "oscontreras84@gmail.com"];
const FROM = "Oscar Lab <lab@radtak.com>";
const MAX_TXT = 200 * 1024;
const MAX_IMG = 3 * 1024 * 1024;
const TIPOS = { pregunta: "Pregunta", problema: "Problema a corregir", datos: "Datos para agregar", idea: "Idea o petición de prueba",
  hallazgo: "Hallazgo", respuesta: "Respuesta a preguntas", peticion: "Petición de prueba", ojos: "Los ojos de Oscar" };

const crypto = require("crypto");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function eq(a, b) { const x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest(); return crypto.timingSafeEqual(x, y); }
async function persona(pin) {   // mismo PIN personal que el comité (PIN_JOSE, PIN_OSCAR en Vercel)
  const p = String(pin || "").trim().toUpperCase().replace(/[\s-]/g, ""); let who = null;
  for (const k of ["jose", "oscar"]) { const v = (process.env["PIN_" + k.toUpperCase()] || "").toUpperCase().replace(/[\s-]/g, ""); if (v && p && eq(p, v)) who = k; }
  if (!who) await sleep(1200); return who;
}
const NOMBRE = { jose: "Jose Miguel", oscar: "Oscar" };
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function gh(path, b64, message, token) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "Content-Type": "application/json", "User-Agent": "nqlab-buzon" },
    body: JSON.stringify({ message, content: b64, committer: { name: "nqlab-buzon", email: "lab@radtak.com" } }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.message || `GitHub ${r.status}`);
  return j.content && j.content.html_url;
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  if (req.method !== "POST") return res.status(405).json({ error: "solo POST" });
  let body = req.body;
  if (typeof body === "string") { try { body = JSON.parse(body); } catch { return res.status(400).json({ error: "JSON inválido" }); } }
  body = body || {};
  const texto = String(body.texto ?? body.contenido ?? "").trim();
  const titulo = String(body.titulo || "").replace(/\n/g, " ").slice(0, 140);
  const quien = await persona(body.pin);
  if (!quien) return res.status(401).json({ error: "PIN incorrecto." });
  const autor = NOMBRE[quien];
  const tipo = TIPOS[body.tipo] ? body.tipo : "pregunta";
  const pagina = String(body.pagina || "").slice(0, 300);
  if (texto.length < 5) return res.status(400).json({ error: "Escribe la pregunta o el problema." });
  if (texto.length > MAX_TXT) return res.status(413).json({ error: "Máximo 200 KB de texto." });

  let img = null;
  if (body.imagen) {
    const m = /^data:(image\/(png|jpeg|webp));base64,([A-Za-z0-9+/=]+)$/.exec(body.imagen);
    if (!m) return res.status(400).json({ error: "La captura debe ser PNG, JPG o WebP." });
    const bytes = Math.floor(m[3].length * 3 / 4);
    if (bytes > MAX_IMG) return res.status(413).json({ error: "La captura pesa más de 3 MB." });
    img = { mime: m[1], ext: m[2] === "jpeg" ? "jpg" : m[2], b64: m[3] };
  }

  const now = new Date();
  const stamp = now.toISOString().slice(0, 16).replace("T", "_").replace(":", "");
  const slug = (titulo || texto.slice(0, 50)).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "nota";
  const base = `${stamp}_${slug}`;
  const imgName = img ? `${base}.${img.ext}` : null;
  const out = { ok: false, correo: false, repo: false };

  // 1) Repositorio (memoria del laboratorio): imagen primero, luego la nota que la enlaza.
  const token = process.env.GITHUB_TOKEN;
  if (token) {
    try {
      if (img) await gh(`docs/oscar/inbox/img/${imgName}`, img.b64, `buzon: captura ${imgName}`, token);
      const header = `---\nautor: ${autor}\ntipo: ${tipo}\nfecha: ${now.toISOString()}\ntitulo: ${titulo}\npagina: ${pagina}\n` +
        (img ? `captura: img/${imgName}\n` : "") + `---\n\n`;
      const md = header + texto + (img ? `\n\n![captura](img/${imgName})\n` : "\n");
      out.url = await gh(`docs/oscar/inbox/${base}.md`, Buffer.from(md, "utf8").toString("base64"),
        `buzon: ${autor} · ${TIPOS[tipo]} · ${titulo || slug}`, token);
      out.repo = true;
    } catch (e) { out.repo_error = String(e.message || e); }
  }

  // 2) Correo a los dos, con la captura adjunta.
  const key = process.env.RESEND_API_KEY;
  if (key) {
    const html = `<div style="font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#14181f;max-width:640px">
<p style="margin:0 0 6px;color:#69707d;font-size:13px">${esc(TIPOS[tipo])} · de ${esc(autor)} · ${esc(now.toISOString().slice(0, 16).replace("T", " "))} UTC</p>
${titulo ? `<h2 style="margin:0 0 10px;font-size:18px">${esc(titulo)}</h2>` : ""}
<div style="white-space:pre-wrap;background:#f6f7f9;border:1px solid #e3e6eb;border-radius:10px;padding:12px">${esc(texto)}</div>
${img ? `<p style="color:#69707d;font-size:13px">📎 Captura adjunta.</p>` : ""}
${pagina ? `<p style="font-size:13px">📍 Enviado desde: <a href="${esc(pagina)}">${esc(pagina)}</a></p>` : ""}
${out.url ? `<p style="font-size:13px">📁 Guardado en el laboratorio: <a href="${esc(out.url)}">${esc(base)}.md</a> (entra a la agenda del comité)</p>` : ""}
<p style="font-size:13px">🏠 <a href="${SITE}">Página del laboratorio</a> · ❓ <a href="${SITE}/#reportar">Enviar otra</a></p>
<p style="font-size:12px;color:#8a909b">🤖 Aviso automático del buzón de Oscar Lab. Si respondes a este correo, la respuesta le llega a quien escribió la nota y a Jose Miguel.</p></div>`;
    const msg = { from: FROM, to: TO, reply_to: TO, subject: `[Oscar Lab] Buzón · ${TIPOS[tipo]} · ${titulo || texto.slice(0, 60)}`, html,
      text: `${TIPOS[tipo]} de ${autor}\n\n${titulo}\n\n${texto}\n\nEnviado desde: ${pagina}\n${out.url ? "Guardado: " + out.url + "\n" : ""}\n🤖 Aviso automático del buzón de Oscar Lab.` };
    if (img) msg.attachments = [{ filename: imgName, content: img.b64 }];
    try {
      const r = await fetch("https://api.resend.com/emails", { method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", "User-Agent": "nqlab-buzon/1.0" }, body: JSON.stringify(msg) });
      if (r.ok) out.correo = true; else out.correo_error = `Resend ${r.status}: ${(await r.text()).slice(0, 200)}`;
    } catch (e) { out.correo_error = String(e.message || e); }
  }

  out.ok = out.correo || out.repo;
  if (!out.ok) {
    const why = !token && !key ? "El buzón no tiene configurado ni el correo ni el repositorio." : (out.correo_error || out.repo_error || "error desconocido");
    return res.status(502).json({ ...out, error: why });
  }
  out.nota = [out.correo && "Les llegó por correo a Jose Miguel y Oscar", out.repo && "quedó guardado en el laboratorio (entra a la agenda del comité)"]
    .filter(Boolean).join(" y ") + ".";
  return res.status(200).json(out);
};
