#!/usr/bin/env python3
"""counterfactual.py -- que habria pasado con las senales rechazadas.

Propuesta docs/decisions.md 2026-08-22 (T3, medicion pura).

squad_decisions.csv registra QUE se rechazo (SKIP-cap, SKIP-gate) pero
no QUE HABRIA PASADO. Este modulo calcula el retorno a horizonte fijo
(el hold_h declarado del bot) de cada senal rechazada, point-in-time.

Responde la pregunta que hoy no tiene evidencia: el tope de posiciones
y el gate de coste, .estan protegiendo o estorbando?

DISENO DELIBERADO: solo lee. No importa el motor, no toca estado, no
altera ninguna decision. Las filas cuyo horizonte aun no vence quedan
como PENDING y se recalculan en la siguiente corrida.

Uso:  .venv/bin/python ops/counterfactual.py [--pista crypto|stocks|both]
"""
import os
import sys
import csv
import argparse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "logs", "counterfactual.csv")

TRACKS = {
    "crypto": {"dec": "logs/squad_decisions.csv", "seeds": "bot.seeds_crypto",
               "path": lambda s: f"data/candles/{s}_3600s.csv", "rt": 0.0101},
    "stocks": {"dec": "logs/squad_stocks_decisions.csv",
               "seeds": "bot.seeds_stocks",
               "path": lambda s: f"data/stocks/{s}_1h.csv", "rt": 0.0},
}


def load_series(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                out.append((int(float(row["timestamp"])), float(row["close"])))
            except (KeyError, ValueError, TypeError):
                continue
    out.sort()
    return out


def px_at(series, ts):
    """Ultimo cierre en o antes de ts. Nunca mira adelante."""
    lo, hi, best = 0, len(series) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= ts:
            best, lo = series[mid][1], mid + 1
        else:
            hi = mid - 1
    return best


def run(track, rows_out):
    cfg = TRACKS[track]
    dec = os.path.join(ROOT, cfg["dec"])
    if not os.path.exists(dec):
        print(f"  {track}: sin log de decisiones, se omite")
        return
    mod = __import__(cfg["seeds"], fromlist=["SEEDS"])
    hold = {n: c.get("hold_h", 24) for n, c in mod.SEEDS.items()}
    series, now = {}, int(datetime.now(timezone.utc).timestamp())

    with open(dec) as f:
        decisions = list(csv.DictReader(f))
    print(f"  {track}: {len(decisions)} decisiones registradas")

    for d in decisions:
        act = d.get("action", "")
        if not act.startswith("SKIP") and act != "ENTER":
            continue
        pair, bot = d.get("pair", ""), d.get("bot", "")
        if pair not in series:
            series[pair] = load_series(cfg["path"](pair))
        s = series[pair]
        if not s:
            continue
        try:
            t = int(datetime.fromisoformat(
                d["utc_ms"].replace("Z", "+00:00")).timestamp())
        except (KeyError, ValueError):
            continue
        h = hold.get(bot, 24)
        t_exit = t + h * 3600
        p_in = px_at(s, t)
        if p_in is None:
            continue
        if t_exit > now or px_at(s, t_exit) is None:
            rows_out.append([d["utc_ms"], track, bot, pair, act, h,
                             "", "", "PENDING"])
            continue
        gross = px_at(s, t_exit) / p_in - 1
        net = gross - cfg["rt"]
        rows_out.append([d["utc_ms"], track, bot, pair, act, h,
                         f"{gross*100:.4f}", f"{net*100:.4f}", "RESOLVED"])


def summarize(rows):
    """Comparacion cruda: rechazadas vs ejecutadas. Sin interpretacion."""
    import statistics as stx
    print("\n  --- resumen (net %, horizonte = hold_h declarado) ---")
    for track in sorted({r[1] for r in rows}):
        sub = [r for r in rows if r[1] == track and r[8] == "RESOLVED"]
        if not sub:
            continue
        print(f"  {track}:")
        for act in ("ENTER", "SKIP-cap", "SKIP-gate"):
            v = [float(r[7]) for r in sub if r[4] == act]
            if not v:
                continue
            pos = sum(1 for x in v if x > 0) / len(v) * 100
            print(f"    {act:10s} n={len(v):5d}  mediana {stx.median(v):+7.3f}%"
                  f"  media {stx.mean(v):+7.3f}%  positivas {pos:5.1f}%")
    pend = sum(1 for r in rows if r[8] == "PENDING")
    print(f"\n  {pend} filas PENDING (horizonte sin vencer); "
          f"se recalculan en la proxima corrida.")
    print("  NOTA: esto es descriptivo sobre datos ya vistos. NO es "
          "autorizacion para\n  mover el tope ni el gate -- eso seria "
          "ajustar a la muestra observada.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pista", default="both",
                    choices=["crypto", "stocks", "both"])
    a = ap.parse_args()
    print("contrafactual de senales rechazadas (medicion, no opera)")
    rows = []
    for t in (["crypto", "stocks"] if a.pista == "both" else [a.pista]):
        run(t, rows)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["utc", "track", "bot", "pair", "action", "hold_h",
                    "gross_pct", "net_pct", "status"])
        w.writerows(rows)
    summarize(rows)
