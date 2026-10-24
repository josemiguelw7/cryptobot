"""Aplica el branding Oscar Lab (logo + paleta) a la página del laboratorio. Idempotente."""
import os, re
ROOT = "/Users/haroonrasheed/Projects/cryptobot"
P = lambda *a: os.path.join(ROOT, *a)
rd = lambda p: open(p, encoding="utf-8").read()
def wr(p, s): open(p, "w", encoding="utf-8").write(s)
def sub(s, old, new, path):
    if old not in s:
        if new in s: return s
        raise SystemExit(f"no encontrado en {path}: {old[:60]}")
    return s.replace(old, new)

LOGO = "data:image/png;base64," + rd(P("portal/brand/logo440.b64")).strip()

# 1) plantilla
p = P("portal/futures_template.html"); s = rd(p)
s = sub(s, "<title>Liga de Futuros · NQ</title>",
        '<title>Oscar Lab · Liga de Futuros NQ</title>\n<link rel="icon" type="image/png" href="__ICON__">\n'
        '<meta name="theme-color" content="#001830">', p)
s = sub(s, """:root{--bg:#000;--card:#121212;--line:#262626;--txt:#EDEDED;--dim:#9A9A9A;
--accent:#7FA4DB;--accent-bg:#1E2A3B;""", """:root{--bg:#000B17;--card:#06192B;--line:#12304A;--txt:#EDF2F4;--dim:#8FA3B3;
--accent:#00A968;--accent-bg:#013F4A;""", p)
s = sub(s, "html{background:#000}", "html{background:#000B17}", p)
s = sub(s, """@media (prefers-color-scheme:dark){:root{--bg:#111316;--card:#191C21;--line:#2A2E35;
--txt:#E8EAED;--dim:#8B919B;--accent:#7FA4DB;--accent-bg:#1E2A3B;""", """@media (prefers-color-scheme:dark){:root{--bg:#000B17;--card:#06192B;--line:#12304A;
--txt:#EDF2F4;--dim:#8FA3B3;--accent:#00A968;--accent-bg:#013F4A;""", p)
s = sub(s, "#tabbar{position:sticky;top:0;z-index:50;background:#000;border-bottom:1px solid #222;",
        "#tabbar{position:sticky;top:0;z-index:50;background:#001830;border-bottom:1px solid #013F4A;", p)
s = sub(s, "#tabbar a{color:#9a9a9a;", "#tabbar a{color:#9DB3C2;", p)
s = sub(s, "#tabbar a.on{background:#1f1f1f;color:#fff}", "#tabbar a.on{background:#01874E;color:#fff}", p)
s = sub(s, "#tabbar .brand{color:#fff;font-weight:700;padding:8px 14px 8px 4px;margin-right:6px}",
        "#tabbar .brand{display:flex;align-items:center;gap:8px;color:#fff;font-weight:800;font-size:17px;letter-spacing:-.01em;padding:4px 14px 4px 0;margin-right:6px;white-space:nowrap}\n"
        "#tabbar .brand img{width:30px;height:30px;border-radius:7px;display:block}\n#tabbar .brand b{color:#00A968;font-weight:800}", p)
s = sub(s, '<span class="brand">Laboratorio NQ</span>',
        '<span class="brand"><img src="__ICON__" alt="Oscar Lab"><span>Oscar <b>Lab</b></span></span>', p)
s = sub(s, " #tabbar .brand{display:none}", " #tabbar .brand{padding-right:6px;margin-right:2px}\n #tabbar .brand>span{display:none}", p)
wr(p, s)

# 2) fragmentos: botones y acento azul -> verdes de marca
for name, pairs in {"report_widget.html": [("#2563eb", "#01874E"), ("#38bdf8", "#3FC1B0")],
                    "trading_floor.html": [("#38bdf8", "#3FC1B0")],
                    "research_tabs.html": [("#38bdf8", "#3FC1B0")],
                    "explorer_tab.html": [("#38bdf8", "#3FC1B0")]}.items():
    p = P("portal", name); s = rd(p)
    for a, b in pairs: s = s.replace(a, b)
    wr(p, s)

# 3) build: inyecta el ícono
p = P("portal/build_futures_site.py"); s = rd(p)
if "__ICON__" not in s:
    s = sub(s, '.replace("__DATA__", json.dumps(data, ensure_ascii=False)))',
            '.replace("__DATA__", json.dumps(data, ensure_ascii=False))\n'
            '               .replace("__ICON__", "data:image/png;base64," + open(os.path.join(HERE, "brand", "tab64.b64")).read().strip()))', p)
    wr(p, s)

# 4) página de entrada (estática, fuera del candado: todo en línea)
p = P("site/entrar.html"); s = rd(p)
s = sub(s, "<title>Laboratorio NQ · entrar</title>",
        '<title>Oscar Lab · entrar</title>\n<meta name="theme-color" content="#001830">', p)
s = sub(s, "html,body{height:100%;margin:0;background:#000;color:#f2f2f2;",
        "html,body{height:100%;margin:0;background:#001830;color:#001830;", p)
s = sub(s, ".c{width:100%;max-width:360px;background:#121212;border:1px solid #262626;border-radius:18px;padding:26px}",
        ".c{width:100%;max-width:380px;background:#fff;border:0;border-radius:18px;padding:28px 26px;box-shadow:0 18px 50px rgba(0,0,0,.35)}\n"
        ".logo{display:block;width:100%;max-width:300px;height:auto;margin:0 auto 18px}", p)
s = sub(s, "h1{font-size:21px;margin:0 0 4px}p{color:#9a9a9a;font-size:14px;margin:0 0 18px}",
        "h1{font-size:0;margin:0}p{color:#4A5D6E;font-size:14px;margin:0 0 18px;text-align:center}", p)
s = sub(s, "input{width:100%;background:#0b0b0b;color:#fff;border:1px solid #333;",
        "input{width:100%;background:#F2F6F7;color:#001830;border:1px solid #C9D6DC;", p)
s = sub(s, "input:focus{outline:2px solid #2563eb;border-color:#2563eb}",
        "input:focus{outline:2px solid #00A968;border-color:#00A968}", p)
s = sub(s, "button{width:100%;margin-top:14px;background:#2563eb;", "button{width:100%;margin-top:14px;background:#01874E;", p)
s = sub(s, "small{display:block;color:#6f6f6f;", "small{display:block;color:#6B7D8B;", p)
s = re.sub(r'<h1>[^<]*</h1>', f'<h1><img class="logo" src="{LOGO}" alt="Oscar Lab · Estrategias que avanzan"></h1>', s, count=1)
s = s.replace("$('st').style.color='#9a9a9a'", "$('st').style.color='#4A5D6E'")
s = s.replace("#f87171", "#C2410C")
wr(p, s)
print("branding aplicado")
