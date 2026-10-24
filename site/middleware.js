// Candado de todo el sitio: sin la cookie firmada que da /api/entrar (con PIN personal), nada se ve.
// Protege también /data/* (los JSON y descargas). Quedan libres solo la página de entrada y las funciones /api/*
// (que piden PIN por su cuenta).
export const config = { matcher: "/((?!entrar\\.html|api/|favicon\\.ico).*)" };

const enc = new TextEncoder();
async function firma(txt, secret) {
  const k = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const s = await crypto.subtle.sign("HMAC", k, enc.encode(txt));
  return btoa(String.fromCharCode(...new Uint8Array(s))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export default async function middleware(request) {
  const secret = process.env.LAB_COOKIE_SECRET;
  const url = new URL(request.url);
  const m = /(?:^|;\s*)lab=([^;]+)/.exec(request.headers.get("cookie") || "");
  if (secret && m) {
    const [persona, exp, sig] = decodeURIComponent(m[1]).split(".");
    if (persona && exp && sig && Number(exp) > Date.now() / 1000 && sig === (await firma(`${persona}.${exp}`, secret))) {
      return new Response(null, { headers: { "x-middleware-next": "1" } });   // pasa
    }
  }
  if (url.pathname.startsWith("/data/")) return new Response("Requiere PIN", { status: 401 });
  const next = encodeURIComponent(url.pathname + url.search + url.hash);
  return Response.redirect(`${url.origin}/entrar.html?next=${next}`, 302);
}
