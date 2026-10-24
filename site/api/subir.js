// Buzón de Oscar: recibe un .md (o texto) y lo guarda como commit en docs/oscar/inbox/ del repo.
// Sin base de datos: el repositorio es la memoria del laboratorio. Requiere GITHUB_TOKEN (fine-grained,
// solo "Contents: Read and write" sobre josemiguelw7/cryptobot) en las variables de entorno de Vercel.
const REPO = "josemiguelw7/cryptobot";
const MAX = 200 * 1024;

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  if (req.method !== "POST") return res.status(405).json({ error: "solo POST" });
  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: "falta GITHUB_TOKEN en Vercel" });
  let body = req.body;
  if (typeof body === "string") { try { body = JSON.parse(body); } catch { return res.status(400).json({ error: "JSON inválido" }); } }
  const { titulo = "", contenido = "", autor = "oscar", tipo = "hallazgo" } = body || {};
  if (!contenido || contenido.length < 10) return res.status(400).json({ error: "contenido vacío" });
  if (contenido.length > MAX) return res.status(413).json({ error: "máximo 200 KB" });
  const slug = (titulo || "nota").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "nota";
  const now = new Date(); const stamp = now.toISOString().slice(0, 16).replace("T", "_").replace(":", "");
  const path = `docs/oscar/inbox/${stamp}_${slug}.md`;
  const header = `---\nautor: ${autor}\ntipo: ${tipo}\nfecha: ${now.toISOString()}\ntitulo: ${(titulo || "").replace(/\n/g, " ")}\n---\n\n`;
  const content = Buffer.from(header + contenido, "utf8").toString("base64");
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "Content-Type": "application/json", "User-Agent": "nqlab-buzon" },
    body: JSON.stringify({ message: `buzon: ${autor} · ${tipo} · ${titulo || slug}`, content, committer: { name: "nqlab-buzon", email: "lab@radtak.com" } }),
  });
  const j = await r.json();
  if (!r.ok) return res.status(502).json({ error: "GitHub rechazó el commit", detalle: j.message || r.status });
  return res.status(200).json({ ok: true, path, url: j.content && j.content.html_url, nota: "Guardado. Aparece en la página y en LAB.md en la siguiente publicación automática (máximo 30 min)." });
};
