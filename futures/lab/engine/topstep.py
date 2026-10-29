"""Cuentas Topstep $50K Trading Combine que arrancan en fechas distintas (futures/topstep_rules.json).

Entrada: operaciones de la estrategia (con fecha, net_usd y mae_ticks) y la lista de sesiones.
Por cada arranque se corre una cuenta nueva:
  - balance 50,000; MLL = 48,000; sube con el balance al cierre, nunca baja; se congela en 50,000
  - MLL y DLL se revisan contra el PEOR momento de cada operación (MAE), no solo contra su cierre
  - DLL −1,000: al tocarlo se liquida la posición (con costo de liquidación) y se cierra el día
  - orden dentro de una operación (motor 1.2.0): el límite que la excursión adversa toca PRIMERO es el que manda.
    Si el DLL queda más cerca que el MLL, la posición se liquida en el DLL y el MLL no puede romperse con una
    excursión posterior que ya no ocurrió; antes se revisaba el MLL con la MAE completa aunque el DLL hubiera
    cerrado el día antes (revisión externa 29/10/2026).
  - meta 3,000 con consistencia: mejor día ≤ pct × ganancia total (0.50 laboratorio, 0.55 oficial Topstep)
  - resultado: pasa / rompe_mll / sin_resolver, con días usados y peor drawdown
Decisiones de modelado (no son reglas de Topstep, son elecciones del laboratorio): el DLL se aplica siempre
(Topstep lo ofrece como opción configurable), la cuenta se abandona a los 120 días de sesión (`max_days`) y las
cuentas se arrancan en todas las sesiones con al menos 60 por delante (arranques solapados, no independientes).
"""
import numpy as np

START, MLL, DLL, TARGET = 50000.0, 2000.0, 1000.0, 3000.0


def _daily_paths(trades, contracts_mult=1, tick_usd=5.0):
    """{date: [(net, worst_unrealized)...]} en orden de entrada."""
    by = {}
    for t in sorted(trades, key=lambda x: (x["date"], x["entry_sec"])):
        net = t["net_usd"] * contracts_mult
        worst = -t["mae_ticks"] * tick_usd * t.get("contracts", 1) * contracts_mult - t["commission_usd"] * contracts_mult
        by.setdefault(t["date"], []).append((net, min(worst, net)))
    return by


def run_account(dates, paths, consistency=0.50, max_days=120, liq_fee=10.0):
    bal, mll, best_day, day_pnls = START, START - MLL, 0.0, []
    for n, d in enumerate(dates[:max_days]):
        day = 0.0
        for net, worst in paths.get(d, []):
            # excursión (negativa) a la que cada límite se toca; el más cercano a cero ocurre primero
            x_mll = mll - bal - day                            # MLL intradía con P&L no realizado
            x_dll = -DLL - day                                 # DLL del día
            if worst <= x_mll and x_mll >= x_dll:              # el MLL se toca antes (o a la vez) que el DLL
                return {"resultado": "rompe_mll", "dias": n + 1, "balance": bal + day + worst - liq_fee,
                        "mejor_dia": best_day, "fecha_fin": d}
            if worst <= x_dll:                                 # DLL: se liquida (con costo) y se cierra el día
                day = -DLL - liq_fee
                break
            day += net
            if day <= -DLL:
                day = -DLL - liq_fee
                break
        bal += day
        if bal <= mll:                                         # la liquidación del DLL también puede romper el MLL
            return {"resultado": "rompe_mll", "dias": n + 1, "balance": bal, "mejor_dia": best_day, "fecha_fin": d}
        day_pnls.append(day)
        best_day = max(best_day, day)
        mll = min(START, max(mll, bal - MLL))                  # trailing al cierre, se congela en START
        profit = bal - START
        if profit >= TARGET and best_day <= consistency * profit:
            return {"resultado": "pasa", "dias": n + 1, "balance": bal, "mejor_dia": best_day, "fecha_fin": d}
    return {"resultado": "sin_resolver", "dias": len(dates[:max_days]), "balance": bal, "mejor_dia": best_day,
            "fecha_fin": dates[min(len(dates), max_days) - 1] if dates else None}


def run_all(trades, sessions, consistency=0.50, contracts_mult=1, min_ahead=60, max_days=120, step=1):
    paths = _daily_paths(trades, contracts_mult)
    out = []
    for i in range(0, len(sessions) - min_ahead + 1, step):
        r = run_account(sessions[i:], paths, consistency, max_days)
        r["arranque"] = sessions[i]
        out.append(r)
    return out


def summarize(accounts):
    n = len(accounts) or 1
    res = [a["resultado"] for a in accounts]
    dias_pasa = [a["dias"] for a in accounts if a["resultado"] == "pasa"]
    return {"cuentas": len(accounts), "pasan": res.count("pasa"), "rompen_mll": res.count("rompe_mll"),
            "sin_resolver": res.count("sin_resolver"), "pct_pasan": round(100 * res.count("pasa") / n, 1),
            "dias_mediana_pasa": float(np.median(dias_pasa)) if dias_pasa else None,
            "hist_dias_pasa": np.histogram(dias_pasa, bins=[0, 10, 20, 30, 45, 60, 90, 120])[0].tolist() if dias_pasa else [],
            "hist_balance": np.histogram([a["balance"] for a in accounts], bins=12)[0].tolist() if accounts else [],
            "hist_balance_bins": np.histogram([a["balance"] for a in accounts], bins=12)[1].round(0).tolist() if accounts else []}
