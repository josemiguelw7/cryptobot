"""Estadística del laboratorio: PSR, DSR, largo mínimo, por año, concentración, drawdowns, CPCV.
Referencias: Bailey & López de Prado (2012, 2014); Bailey, Borwein, López de Prado & Zhu (2014); López de Prado (2018).
"""
import itertools, math
import numpy as np
from scipy.stats import norm, skew, kurtosis

EULER = 0.5772156649


def daily_series(trades, sessions):
    """Ganancia neta por sesión (0 en sesiones sin operaciones), en el orden de `sessions`."""
    by = {}
    for t in trades:
        by[t["date"]] = by.get(t["date"], 0.0) + t["net_usd"]
    return np.array([by.get(d, 0.0) for d in sessions])


def sharpe(x):
    x = np.asarray(x, dtype=float)
    return float(x.mean() / x.std(ddof=1)) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def psr(x, sr_bench=0.0):
    """Probabilistic Sharpe Ratio: P[SR verdadero > sr_bench] con T observaciones, asimetría y curtosis."""
    x = np.asarray(x, dtype=float); T = len(x)
    if T < 3:
        return 0.0
    sr = sharpe(x); g3 = float(skew(x)); g4 = float(kurtosis(x, fisher=False))
    den = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr * sr))
    z = (sr - sr_bench) * math.sqrt(T - 1) / den
    return float(norm.cdf(z))


def expected_max_sr(n_trials, var_sr):
    if n_trials <= 1:
        return 0.0
    return math.sqrt(var_sr) * ((1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * math.e)))


def dsr(x, n_trials, var_sr_trials):
    """Deflated Sharpe Ratio = PSR con el Sharpe esperado del mejor de n_trials intentos como vara."""
    return psr(x, expected_max_sr(n_trials, var_sr_trials))


def min_btl_years(n_trials, sr_target_annual=1.0):
    """Largo mínimo de backtest (años) para que un Sharpe anual sr_target no sea explicable por n_trials intentos."""
    if n_trials <= 1:
        return 0.0
    emax = (1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * math.e))
    return float((emax / sr_target_annual) ** 2)


def by_year(trades):
    out = {}
    for t in trades:
        y = t["date"][:4]
        o = out.setdefault(y, {"operaciones": 0, "neto": 0.0})
        o["operaciones"] += 1; o["neto"] += t["net_usd"]
    for o in out.values():
        o["neto"] = round(o["neto"], 2)
    return out


def concentration(trades, daily):
    net = np.array([t["net_usd"] for t in trades]); tot = net.sum()
    top5_tr = float(np.sort(net)[::-1][:5].sum())
    top5_days = float(np.sort(daily)[::-1][:5].sum())
    return {"total": round(float(tot), 2),
            "top5_operaciones_pct": round(100 * top5_tr / tot, 1) if tot > 0 else None,
            "top5_dias_pct": round(100 * top5_days / tot, 1) if tot > 0 else None,
            "depende_de_pocos_dias": bool(tot > 0 and top5_days / tot > 0.5)}


def drawdowns(daily, sessions, top=5):
    cum = np.cumsum(daily); peak = np.maximum.accumulate(cum); dd = cum - peak
    out, i = [], 0
    while i < len(dd):
        if dd[i] < 0:
            j = i
            while j < len(dd) and dd[j] < 0:
                j += 1
            k = int(i + np.argmin(dd[i:j]))
            out.append({"inicio": sessions[max(i - 1, 0)], "fondo": sessions[k], "fin": sessions[j - 1] if j - 1 < len(sessions) else None,
                        "recuperado": bool(j < len(dd)), "profundidad": round(float(dd[k]), 2), "sesiones": j - i})
            i = j
        else:
            i += 1
    out.sort(key=lambda x: x["profundidad"])
    return out[:top], round(float(dd.min()), 2) if len(dd) else 0.0


def rolling(daily, win=20):
    s = np.asarray(daily, float)
    if len(s) < win:
        return {"neto": [], "sharpe": []}
    neto = np.convolve(s, np.ones(win), "valid")
    sh = [sharpe(s[i:i + win]) * math.sqrt(252) for i in range(len(s) - win + 1)]
    return {"neto": neto.round(2).tolist(), "sharpe": np.round(sh, 2).tolist()}


def cpcv_paths(daily, groups=6, test_groups=2, purge=1):
    """Resultado neto fuera de muestra en cada combinación de grupos de prueba (C(6,2)=15 caminos)."""
    n = len(daily); edges = np.linspace(0, n, groups + 1).astype(int)
    paths = []
    for combo in itertools.combinations(range(groups), test_groups):
        tot = 0.0
        for g in combo:
            a, b = edges[g] + (purge if g > 0 else 0), edges[g + 1] - (purge if g < groups - 1 else 0)
            tot += float(np.sum(daily[a:b]))
        paths.append(round(tot, 2))
    return {"caminos": paths, "positivos": int(sum(p > 0 for p in paths)), "total": len(paths)}


def summary(trades, daily, sessions):
    net = [t["net_usd"] for t in trades]
    wins = [x for x in net if x > 0]; losses = [x for x in net if x < 0]
    gp, gl = sum(wins), -sum(losses)
    dd_top, dd_max = drawdowns(daily, sessions)
    return {"operaciones": len(net), "ganancia_neta": round(sum(net), 2),
            "aciertos_pct": round(100 * len(wins) / len(net), 1) if net else None,
            "factor": round(gp / gl, 2) if gl > 0 else None,
            "promedio_op": round(sum(net) / len(net), 2) if net else None,
            "promedio_gana": round(gp / len(wins), 2) if wins else None, "promedio_pierde": round(-gl / len(losses), 2) if losses else None,
            "sharpe_anual": round(sharpe(daily) * math.sqrt(252), 2), "psr": round(psr(daily), 3),
            "drawdown_max": dd_max, "drawdowns": dd_top, "por_anio": by_year(trades),
            "concentracion": concentration(trades, daily), "cpcv": cpcv_paths(daily),
            "sesiones_con_operacion": int(sum(1 for d in daily if d != 0)), "sesiones": len(sessions)}
