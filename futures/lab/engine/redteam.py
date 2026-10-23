"""Red Team automático (protocol.json › red_team): placebos y curva de costos.
Todas las funciones reciben las señales ya generadas por sesión y vuelven a simular.
Regla de rendimiento: la sesión se carga UNA vez y adentro se corren todas las variantes.
"""
import copy, hashlib
import numpy as np
from .sim import simulate
from .data import load


def _net(trades):
    return float(sum(t["net_usd"] for t in trades))


def resim(signals_by_date, rules, slip, commission_rt, mutate=None):
    tot, trades = 0.0, []
    for d, sigs in signals_by_date.items():
        if not sigs:
            continue
        s = load(d, ny_only=True)
        ss = [copy.copy(x) for x in sigs]
        if mutate:
            ss = mutate(ss, d)
        tr = simulate(s, ss, rules, slip, commission_rt)
        trades += tr; tot += _net(tr)
    return tot, trades


def placebo_shift(signals_by_date, rules, slip, commission_rt, shift_s=300):
    """La misma señal usada 5 min ANTES de ocurrir. Si gana parecido, hay fuga de futuro."""
    def mut(ss, d):
        for x in ss:
            x.sec = x.sec - shift_s
        return ss
    tot, _ = resim(signals_by_date, rules, slip, commission_rt, mut)
    return {"desplazamiento_s": shift_s, "neto": round(tot, 2)}


def placebo_flip(signals_by_date, rules, slip, commission_rt, real_net, n=200, test_id="x"):
    """Direcciones barajadas al azar n veces; la ganancia real debe quedar fuera del 95%."""
    tots = np.zeros(n)
    for d, sigs in signals_by_date.items():
        if not sigs:
            continue
        s = load(d, ny_only=True)
        for k in range(n):
            rng = np.random.default_rng(int(hashlib.sha256(f"flip:{test_id}:{d}:{k}".encode()).hexdigest()[:12], 16))
            ss = []
            for x in sigs:
                y = copy.copy(x)
                if rng.random() < 0.5:
                    y.side = -y.side
                ss.append(y)
            tots[k] += _net(simulate(s, ss, rules, slip, commission_rt))
    p = (1 + int((tots >= real_net).sum())) / (1 + n)
    return {"n": n, "p_valor": round(p, 4), "p95": round(float(np.percentile(tots, 95)), 2),
            "p5": round(float(np.percentile(tots, 5)), 2), "media": round(float(tots.mean()), 2), "real": round(real_net, 2)}


def cost_curve(signals_by_date, rules, commission_rt, slips=(0, 1, 2, 3, 4)):
    tot = {sl: 0.0 for sl in slips}; n = {sl: 0 for sl in slips}
    for d, sigs in signals_by_date.items():
        if not sigs:
            continue
        s = load(d, ny_only=True)
        for sl in slips:
            tr = simulate(s, [copy.copy(x) for x in sigs], rules, sl, commission_rt)
            tot[sl] += _net(tr); n[sl] += len(tr)
    return [{"slip_ticks": sl, "neto": round(tot[sl], 2), "operaciones": n[sl]} for sl in slips]


def sensitivity(gen, dates, levels, params, steps, rules, slip, commission_rt, open_in_value=None):
    """Superficie: cada parámetro numérico ±2 pasos, el resto fijo. gen(session, ref, thr, p[, open_in_value]) -> señales."""
    variants = []
    for name, step in steps.items():
        for m in (-2, -1, 0, 1, 2):
            p = dict(params); p[name] = params[name] + m * step
            variants.append((name, m, p))
    tot = [0.0] * len(variants); cnt = [0] * len(variants)
    for d in dates:
        ref, thr = levels.reference(d), levels.thresholds(d)
        if not ref or not thr:
            continue
        s = load(d, ny_only=True)
        kw = {"open_in_value": open_in_value(d)} if open_in_value else {}
        for i, (name, m, p) in enumerate(variants):
            if p[name] <= 0:
                continue
            tr = simulate(s, gen(s, ref, thr, p, **kw), rules, slip, commission_rt)
            tot[i] += _net(tr); cnt[i] += len(tr)
    surface = {}
    for i, (name, m, p) in enumerate(variants):
        surface.setdefault(name, []).append({"valor": p[name], "neto": None if p[name] <= 0 else round(tot[i], 2), "operaciones": cnt[i]})
    return surface
