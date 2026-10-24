"""Informe en el Formato Estándar de Oscar (Trading Floor · Oscar Lab) para una prueba ya corrida.
Resumen ejecutivo de 9 secciones, legible en menos de un minuto, misma estructura siempre.
Las cifras de las secciones 5-8 salen de reporte_floor.py (Topstep $50K con y sin DLL de $1,000).
  python -m engine.informe_floor P012            # imprime el texto
  python -m engine.informe_floor P012 --enviar   # lo manda por correo (notify)
"""
import glob, html as H, json, os, sys
from datetime import date

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUT = os.path.dirname(LAB)
sys.path.insert(0, LAB)

UMBRAL_TOPSTEP = 50.0
CLARO = {  # causas del laboratorio en palabras simples
    "placebo desplazado sospechoso: revisión de código pendiente":
        "la misma señal movida 5 minutos (placebo) también gana, y hay que revisar el código para descartar una fuga de información",
}
def _claro(t):
    for k, v in CLARO.items():
        t = t.replace(k, v)
    return t   # % de cuentas simuladas que deben pasar (regla del laboratorio)


def _f(d):  # 'YYYY-MM-DD' -> MM/DD/YYYY
    return date.fromisoformat(d).strftime("%m/%d/%Y")


def _usd(x):
    return ("−" if x < 0 else "+") + f"${abs(x):,.0f}"


def _periodo(k, v):
    if k == "dia":
        return _f(v)
    if k == "mes":
        y, m = v.split("-"); return date(int(y), int(m), 1).strftime("%m/%Y")
    y, w = v.split("-W"); return "semana del " + date.fromisocalendar(int(y), int(w), 1).strftime("%m/%d/%Y")


def _estrategia(eid, ver):
    for f in sorted(glob.glob(os.path.join(FUT, "strategies", "v*.json")), reverse=True):
        if "aclaraciones" in f:
            continue
        d = json.load(open(f, encoding="utf-8"))
        S = d.get("estrategias") or d.get("strategies") or []
        if isinstance(S, dict):
            S = list(S.values())
        for s in S:
            if isinstance(s, dict) and s.get("id") == eid and int(s.get("version", 0)) == int(ver):
                return s
    return {}


def datos(tid):
    import reporte_floor as RF
    rep, trades = RF.load(tid)
    sessions = rep["hoja"]["diario"]["x"]
    eq = peak = mdd = 0.0
    for t in sorted(trades, key=lambda x: (x["date"], x["entry_sec"])):
        eq += t["net_usd"]; peak = max(peak, eq); mdd = min(mdd, eq - peak)
    wins = sum(1 for t in trades if t["net_usd"] > 0)
    ts = {dll: RF.topstep_eval(trades, sessions, 0.50, dll) for dll in (True, False)}
    stops = [t["stop_ticks"] for t in trades if t["stop_ticks"] > 0]
    return {"rep": rep, "trades": trades, "sessions": sessions, "neto": eq, "mdd": mdd, "wins": wins,
            "extremos": RF.extremes(trades), "ts": ts,
            "stop_med": sorted(stops)[len(stops) // 2] / 4 if stops else None,
            "razones": {k: sum(1 for t in trades if t["reason"] == k) for k in {t["reason"] for t in trades}}}


def secciones(tid):
    D = datos(tid); rep = D["rep"]; S = _estrategia(rep["estrategia"], rep["version"])
    P = rep["receta"]["parametros"]; C = rep["receta"]["costos"]; n = len(D["trades"])
    nombre = f"{rep['estrategia']} v{rep['version']} · {S.get('nombre', '')}".strip(" ·")
    ent = S.get("entrada", "").rstrip(".")
    if ent and S.get("confirmacion"):
        ent = f"{ent}, cuando {S['confirmacion'].rstrip('.')}"
    expl = " ".join(x for x in [S.get("idea", ""), f"Entrada: {ent}." if ent else ""] if x)
    rango = f"{_f(D['sessions'][0])} a {_f(D['sessions'][-1])}"
    prueba = (f"Datos tick reales de NQ (ATAS/Rithmic), {rango}, {len(D['sessions'])} sesiones válidas de diseño, 1 contrato. "
              f"Incluye comisión de ${C['comision_rt']:.2f} ida y vuelta y {C['slip_ticks_por_lado']} tick de deslizamiento por lado. "
              "Sin validación fuera de muestra todavía: las reglas se eligieron con estos mismos datos y el examen final sellado (desde el 22/04/2026) sigue cerrado.")
    # TP / SL en puntos
    if P.get("stop_min") is not None and P.get("stop_max") is not None:
        sl = f"dinámico, {P['stop_min']/4:g} a {P['stop_max']/4:g} puntos (mediana {D['stop_med']:g})" if D["stop_med"] else f"{P['stop_min']/4:g} a {P['stop_max']/4:g} puntos"
    elif P.get("stop_ticks"):
        sl = f"{P['stop_ticks']/4:g} puntos fijo"
    else:
        sl = S.get("stop", "ver reglas")
    if P.get("target_fixed"):
        tp = f"{P['target_fixed']/4:g} puntos fijo"
    elif P.get("target_ticks"):
        tp = f"{P['target_ticks']/4:g} puntos fijo"
    elif P.get("rr"):
        tp = f"{P['rr']:g} veces el stop (dinámico)"
    else:
        tp = S.get("objetivo", "ver reglas")
    tmax = f"; salida por tiempo a los {P['max_min']} min" if P.get("max_min") else ""
    R_ = D["razones"]; sal = ", ".join(f"{v} por {'objetivo' if k=='objetivo' else 'stop' if k=='stop' else 'tiempo' if k=='tiempo' else k}" for k, v in sorted(R_.items(), key=lambda kv: -kv[1]))
    tpsl = f"Take profit: {tp}. Stop loss: {sl}{tmax}. 1 contrato. Salidas reales: {sal}."
    # Topstep
    ts = D["ts"]; c, s_ = ts[True], ts[False]
    def ln(x, et):
        return f"{et}: pasan {x['pct_pasan']:.1f}% de {x['cuentas']} cuentas simuladas (una por cada día de inicio posible)" + \
               (f", mediana {x['dias_mediana_pasa']:.0f} días para pasar" if x.get("dias_mediana_pasa") else "")
    pasa = c["pct_pasan"] >= UMBRAL_TOPSTEP
    peor_dia = min(v for v in [D["extremos"]["dia"]["peor"][1]])
    igual = "" if abs(c["pct_pasan"] - s_["pct_pasan"]) > 0.05 else f" Con y sin DLL da igual porque ningún día pierde más de $1,000 (el peor día pierde ${abs(peor_dia):,.0f})." if peor_dia > -1000 else " Con y sin DLL da igual."
    motivo = ""
    if not pasa:
        ns, nm = c.get("sin_resolver", 0), c.get("rompen_mll", 0)
        motivo = (f"No llega al {UMBRAL_TOPSTEP:.0f}% exigido: {ns} de {c['cuentas']} cuentas no alcanzan la meta de $3,000 antes de que se acaben los datos"
                  + (f" y {nm} rompen el límite de pérdida máxima (MLL) de $2,000." if nm else "."))
    topstep = {"veredicto": "SÍ" if pasa else "NO", "con": ln(c, "Con DLL de $1,000"), "sin": ln(s_, "Sin DLL") + "." + igual.rstrip("."),
               "motivo": motivo, "reglas": "Topstep $50K Trading Combine: meta $3,000, MLL $2,000 al cierre (trailing), regla de consistencia 50%, costos de Topstep incluidos."}
    # Conclusión (mecánica, desde el veredicto del laboratorio)
    v = rep["veredicto"]; causa = rep.get("muerte") or ""
    if v == "pasa":
        concl = "Seguir: pasó todas las pruebas del laboratorio y es candidata al examen final sellado; el comité decide si se abre."
    elif v == "revisar":
        vr = rep["resultados"].get("vs_rand")
        concl = (f"Seguir desarrollando con cuidado: gana al azar (p {vr})" if vr is not None and vr < 0.05 else "Seguir desarrollando con cuidado") + \
                f", pero queda en revisar porque {_claro(causa.split(';')[0]) if causa else 'el resultado es mixto'}. Pocas operaciones ({n}) y sin validación fuera de muestra."
    else:
        concl = f"Descartar esta versión: {causa.split(';')[0] if causa else 'no supera las pruebas'}."
    return {"tid": tid, "nombre": nombre, "expl": expl, "prueba": prueba, "tpsl": tpsl, "rango": rango, "n": n,
            "win": 100 * D["wins"] / n if n else 0, "neto": D["neto"], "mdd": D["mdd"],
            "tpd": n / len(D["sessions"]), "extremos": D["extremos"], "topstep": topstep, "concl": concl,
            "veredicto": v, "causa": causa, "vs_rand": rep["resultados"].get("vs_rand")}


def render(tid):
    X = secciones(tid); T = X["topstep"]; E = X["extremos"]
    V = {"pasa": "pasa", "revisar": "revisar", "no_pasa": "no pasa"}.get(X["veredicto"], X["veredicto"])
    subject = f"{X['tid']} · {X['nombre'].split(' · ')[0]} · {V}"
    sec = lambda n, t, body: (f'<tr><td style="padding:14px 0 4px;font:700 12px Arial,sans-serif;letter-spacing:1px;color:#01874E">{n} · {t.upper()}</td></tr>'
                              f'<tr><td style="font:15px/1.5 Arial,sans-serif;color:#14181f;padding-bottom:4px">{body}</td></tr>')
    rows = "".join(f'<tr><td style="padding:6px 8px;border-top:1px solid #e3e6eb">{lab}</td>'
                   f'<td style="padding:6px 8px;border-top:1px solid #e3e6eb">{_periodo(k, E[k]["mejor"][0])}<br><b style="color:#01874E">{_usd(E[k]["mejor"][1])}</b></td>'
                   f'<td style="padding:6px 8px;border-top:1px solid #e3e6eb">{_periodo(k, E[k]["peor"][0])}<br><b style="color:#b42318">{_usd(E[k]["peor"][1])}</b></td></tr>'
                   for k, lab in (("mes", "Mes"), ("semana", "Semana"), ("dia", "Día")))
    tabla = (f'<table role="presentation" style="border-collapse:collapse;width:100%;font:14px Arial,sans-serif">'
             f'<tr style="color:#69707d;font-size:12px"><td style="padding:4px 8px"></td><td style="padding:4px 8px">MEJOR</td><td style="padding:4px 8px">PEOR</td></tr>{rows}</table>'
             '<div style="color:#69707d;font-size:12px;margin-top:4px">Neto después de costos.</div>')
    kpi = lambda a, b, col="#001830": f'<td style="padding:8px;border:1px solid #e3e6eb;width:33%"><div style="font-size:11px;color:#69707d">{a}</div><div style="font:700 18px Arial,sans-serif;color:{col}">{b}</div></td>'
    tpd_s = f"{X['tpd']:.2f}"
    colv = "#01874E" if T["veredicto"] == "SÍ" else "#b42318"
    inner = (f'<div style="font:12px Arial,sans-serif;color:#69707d">Formato estándar · Trading Floor · resumen ejecutivo</div>'
             f'<table role="presentation" style="border-collapse:collapse;width:100%">'
             + sec(1, "Estrategia", f'<b style="font-size:17px;color:#001830">{H.escape(X["nombre"])}</b> <span style="color:#69707d">· prueba {X["tid"]} · veredicto del laboratorio: <b>{V}</b></span>')
             + sec(2, "Explicación de la estrategia", H.escape(X["expl"]))
             + sec(3, "Explicación de la prueba", H.escape(X["prueba"]))
             + sec(4, "Take profit / stop loss", H.escape(X["tpsl"]))
             + sec(5, "Rango testeado", f'Desde {X["rango"].replace(" a ", " hasta ")} · <b>{X["n"]:,}</b> operaciones · win rate <b>{X["win"]:.1f}%</b>')
             + sec(6, "Resultado global", f'<table role="presentation" style="border-collapse:collapse;width:100%"><tr>{kpi("P/L NETO", _usd(X["neto"]), "#01874E" if X["neto"] >= 0 else "#b42318")}{kpi("DRAWDOWN MÁXIMO", "−$" + format(abs(X["mdd"]), ",.0f"), "#b42318")}{kpi("OPERACIONES / DÍA", tpd_s)}</tr></table>')
             + sec(7, "Mejores y peores resultados", tabla)
             + sec(8, "¿Pasa las reglas de prop firms?", f'<b style="font-size:17px;color:{colv}">{T["veredicto"]}</b> · Topstep $50K Trading Combine<br>{H.escape(T["con"])}.<br>{H.escape(T["sin"])}.'
                   + (f'<br><span style="color:#b42318">{H.escape(T["motivo"])}</span>' if T["motivo"] else "")
                   + f'<div style="color:#69707d;font-size:12px;margin-top:4px">{H.escape(T["reglas"])}</div>')
             + sec(9, "Conclusión", f'<b>{H.escape(X["concl"])}</b>')
             + '</table><p style="color:#69707d;font-size:13px;margin:14px 0 0">El detalle completo (operaciones, Red Team, sensibilidad y metodología) está en la página, en la prueba.</p>')
    text = "\n".join([
        "Formato estándar · Trading Floor · resumen ejecutivo", "",
        f"1. ESTRATEGIA: {X['nombre']} (prueba {X['tid']}, veredicto: {V})",
        f"2. EXPLICACIÓN DE LA ESTRATEGIA: {X['expl']}",
        f"3. EXPLICACIÓN DE LA PRUEBA: {X['prueba']}",
        f"4. TAKE PROFIT / STOP LOSS: {X['tpsl']}",
        f"5. RANGO TESTEADO: desde {X['rango'].replace(' a ', ' hasta ')} · {X['n']:,} operaciones · win rate {X['win']:.1f}%",
        f"6. RESULTADO GLOBAL: P/L neto {_usd(X['neto'])} · drawdown máximo −${abs(X['mdd']):,.0f} · {X['tpd']:.2f} operaciones/día",
        "7. MEJORES Y PEORES (neto después de costos):",
        *[f"   {lab}: mejor {_periodo(k, E[k]['mejor'][0])} {_usd(E[k]['mejor'][1])} · peor {_periodo(k, E[k]['peor'][0])} {_usd(E[k]['peor'][1])}" for k, lab in (("mes", "Mes"), ("semana", "Semana"), ("dia", "Día"))],
        f"8. ¿PASA PROP FIRMS? {T['veredicto']} (Topstep $50K). {T['con']}. {T['sin']}." + (f" {T['motivo']}" if T["motivo"] else ""),
        f"9. CONCLUSIÓN: {X['concl']}"])
    return subject, inner, text


def enviar(tid):
    from engine import notify
    subject, inner, text = render(tid)
    return notify.send(subject, text, test_id=tid, html_body=inner)


if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else "P012"
    if "--enviar" in sys.argv:
        print(enviar(tid))
    else:
        print(render(tid)[2])
