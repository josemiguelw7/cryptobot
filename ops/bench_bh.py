#!/usr/bin/env python3
"""bench_bh.py -- benchmark de comprar-y-sostener equiponderado.

Propuesta docs/decisions.md 2026-08-22 (T3, medicion pura).

Compra el universo equiponderado en el primer ciclo registrado del
escuadron y NO vuelve a operar. Paga la friccion de entrada UNA vez,
para no darle al bench una ventaja que los bots no tienen.

DISENO DELIBERADO: este modulo NO importa ni modifica squad.py ni
squad_stocks.py, y escribe a su propio log. Un bench que puede romper
el motor de trading no es medicion, es riesgo. Solo lee.

Uso:  .venv/bin/python ops/bench_bh.py [--pista crypto|stocks|both]
"""
import os
import sys
import csv
import argparse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "logs", "bench_equity.csv")

# Friccion de entrada. Espeja squad.py s4.1 (FEE_TAKER 0.004 + slippage).
# Acciones: 0.0 hoy, coherente con squad_stocks.py. La propuesta de
# friccion realista (efectiva 2026-08-23) cambiara este numero; cuando
# lo haga, ESTE valor debe moverse con el, o el bench queda con ventaja.
FEE = {"crypto": 0.004 + 0.0010, "stocks": 0.0}

TRACKS = {
    "crypto": {
        "eqlog": "logs/squad_equity.csv",
        "seeds": "bot.seeds_crypto",
        "path": lambda s: f"data/candles/{s}_3600s.csv",
    },
    "stocks": {
        "eqlog": "logs/squad_stocks_equity.csv",
        "seeds": "bot.seeds_stocks",
        "path": lambda s: f"data/stocks/{s}_1h.csv",
    },
}


def load_series(rel):
    """Devuelve [(ts_utc, close)] ordenado. Tolera tz-aware y naive."""
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                ts = int(float(row["timestamp"]))
                out.append((ts, float(row["close"])))
            except (KeyError, ValueError, TypeError):
                continue
    out.sort()
    return out


def squad_anchor(rel):
    """(t0_epoch, equity_total_inicial) del primer ciclo del escuadron."""
    p = os.path.join(ROOT, rel)
    first_t, per_bot = None, {}
    with open(p) as f:
        for row in csv.DictReader(f):
            t = row["time"]
            if first_t is None:
                first_t = t
            if t != first_t:
                break
            per_bot[row["bot"]] = float(row["equity"])
    dt = datetime.fromisoformat(first_t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp()), sum(per_bot.values()), len(per_bot)


def px_at(series, ts):
    """Ultimo cierre en o antes de ts. Point-in-time: nunca mira adelante."""
    lo, hi, best = 0, len(series) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= ts:
            best = series[mid][1]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def run(track):
    cfg = TRACKS[track]
    mod = __import__(cfg["seeds"], fromlist=["PAIRS"])
    pairs = list(mod.PAIRS)
    t0, eq0, n_bots = squad_anchor(cfg["eqlog"])

    series = {p: load_series(cfg["path"](p)) for p in pairs}
    series = {p: s for p, s in series.items() if s and px_at(s, t0)}
    if not series:
        print(f"  {track}: sin datos utilizables, se omite")
        return

    # Equiponderado sobre el capital inicial agregado del escuadron,
    # pagando la comision de entrada una sola vez.
    slice_ = eq0 / len(series)
    units = {p: (slice_ * (1 - FEE[track])) / px_at(s, t0)
             for p, s in series.items()}

    grid = sorted({ts for s in series.values() for ts, _ in s if ts >= t0})
    rows = []
    for ts in grid:
        eq = 0.0
        for p, s in series.items():
            px = px_at(s, ts)
            if px is None:
                break
            eq += units[p] * px
        else:
            iso = datetime.fromtimestamp(ts, timezone.utc).isoformat()
            rows.append([iso, f"bench_bh_{track}", f"{eq:.2f}", "0.00",
                         " ".join(sorted(series))])

    # Reescritura idempotente por pista: la serie se recalcula entera
    # desde el ancla en cada corrida, asi que APPEND duplicaria filas al
    # correr cada hora. Se conservan las otras pistas del fichero.
    prev = []
    if os.path.exists(OUT):
        with open(OUT) as f:
            prev = [r for r in csv.reader(f)
                    if r and r[0] != "time" and r[1] != f"bench_bh_{track}"]
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "bot", "equity", "cash", "holdings"])
        w.writerows(sorted(prev + rows))

    ret = (rows[-1][2] and float(rows[-1][2]) / eq0 - 1) * 100
    print(f"  {track}: {len(series)} activos · {len(rows)} puntos · "
          f"desde ${eq0:,.0f} ({n_bots} bots) · retorno {ret:+.2f}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pista", default="both",
                    choices=["crypto", "stocks", "both"])
    a = ap.parse_args()
    sys.path.insert(0, ROOT)
    print("bench comprar-y-sostener (medicion, no opera)")
    for t in (["crypto", "stocks"] if a.pista == "both" else [a.pista]):
        run(t)
