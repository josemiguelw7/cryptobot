// Entrada al sitio con PIN personal: si es correcto, deja una cookie firmada por 30 días (HttpOnly).
// POST {pin} -> {ok, nombre}.   POST {salir:true} -> borra la cookie.
const crypto = require("crypto");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const NOMBRE = { jose: "Jose Miguel", oscar: "Oscar" };
const DIAS = 30;

function eq(a, b) { const x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest(); return crypto.timingSafeEqual(x, y); }
const norm = (s) => String(s || "").trim().toUpperCase().replace(/[\s-]/g, "");

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ error: "solo POST" });
  let b = req.body;
  if (typeof b === "string") { try { b = JSON.parse(b); } catch { b = {}; } }
  b = b || {};
  if (b.salir) {
    res.setHeader("Set-Cookie", "lab=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax");
    return res.status(200).json({ ok: true });
  }
  const secret = process.env.LAB_COOKIE_SECRET;
  if (!secret) return res.status(500).json({ error: "Falta LAB_COOKIE_SECRET en Vercel." });
  const p = norm(b.pin); let who = null;
  for (const k of ["jose", "oscar"]) { const v = norm(process.env["PIN_" + k.toUpperCase()]); if (v && p && eq(p, v)) who = k; }
  if (!who) { await sleep(1500); return res.status(401).json({ error: "PIN incorrecto." }); }
  const exp = Math.floor(Date.now() / 1000) + DIAS * 86400;
  const sig = crypto.createHmac("sha256", secret).update(`${who}.${exp}`).digest("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  res.setHeader("Set-Cookie", `lab=${encodeURIComponent(`${who}.${exp}.${sig}`)}; Path=/; Max-Age=${DIAS * 86400}; HttpOnly; Secure; SameSite=Lax`);
  return res.status(200).json({ ok: true, persona: who, nombre: NOMBRE[who] });
};
