"""RAND emparejado (protocol.json › rand_emparejado).

Copia la forma de la estrategia: por sesión, misma cantidad de operaciones y misma duración
de cada una; entrada en instante uniforme dentro del horario permitido, dirección 50/50,
sale por tiempo (sin stop ni objetivo), mismos costos y contratos.
La semilla de cada corrida = SHA-256(id_prueba:fecha:k) por sesión y corrida (protocolo v3).
RAND2 (with_exits=True) copia además stop, objetivo y tiempo máximo de cada operación real.
"""
import hashlib
import numpy as np
from .sim import Signal, Rules, simulate
from .data import load


def seed_for(test_id, k):
    return int(hashlib.sha256(f"{test_id}:{k}".encode()).hexdigest()[:12], 16)


def rand_signals(trades_by_date, rules: Rules, rng, with_exits=False):
    """trades_by_date: {date: [(dur, stop, target, max_sec)]} -> {date: [Signal]}
    with_exits=False: RAND clásico (sale por tiempo, copia la duración). with_exits=True: RAND2, copia stop,
    objetivo y tiempo máximo de cada operación real (misma estructura de salidas; solo cambian momento y dirección)."""
    out = {}
    span = rules.last_entry - rules.first_entry
    for d, items in trades_by_date.items():
        sigs = []
        for dur, stop, target, mx in items:
            sec = rules.first_entry + rng.random() * span
            side = 1 if rng.random() < 0.5 else -1
            if with_exits:
                sigs.append(Signal(sec=sec, side=side, stop_ticks=stop, target_ticks=target, max_sec=mx, kind="RAND2"))
            else:
                sigs.append(Signal(sec=sec, side=side, stop_ticks=10**6, target_ticks=None, max_sec=max(dur, 1.0), kind="RAND"))
        out[d] = sigs
    return out


def _rand_session(args):
    test_id, d, items, rules, slip, commission_rt, n_runs, with_exits = args
    s = load(d, ny_only=True)
    free = Rules(max_trades=10**6, max_consec_losses=10**6, first_entry=rules.first_entry,
                 last_entry=rules.last_entry, forced_close=rules.forced_close, news=rules.news, contracts=rules.contracts)
    col = np.zeros(n_runs)
    for k in range(n_runs):
        rng = np.random.default_rng(seed_for(f"{test_id}:{d}", k))
        sigs = rand_signals({d: items}, rules, rng, with_exits)[d]
        col[k] = sum(t["net_usd"] for t in simulate(s, sigs, free, slip, commission_rt))
    return col


def run_rand(test_id, trades, rules: Rules, slip, commission_rt, n_runs=1000, sessions=None, progress=None, workers=6, with_exits=False):
    """Devuelve matriz (n_runs x sesiones) de ganancia neta diaria, en el orden de `sessions`.
    Sesión afuera (en paralelo), corridas adentro: cada sesión se carga una sola vez."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    by_date = {}
    for t in trades:
        by_date.setdefault(t["date"], []).append((t["duration_s"], t.get("stop_ticks") or 10**6, t.get("target_ticks"), t.get("max_sec") or max(t["duration_s"], 1.0)))
    sessions = sessions or sorted(by_date)
    daily = np.zeros((n_runs, len(sessions)))
    jobs = [(j, (test_id, d, by_date[d], rules, slip, commission_rt, n_runs, with_exits)) for j, d in enumerate(sessions) if d in by_date]
    # spawn (no fork): polars deja hilos vivos en el padre y un fork se cuelga
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as ex:
        for i, (j, col) in enumerate(zip([j for j, _ in jobs], ex.map(_rand_session, [a for _, a in jobs], chunksize=4))):
            daily[:, j] = col
            if progress and (i + 1) % 50 == 0:
                progress(i + 1)
    return sessions, daily


def summarize(strategy_daily, rand_daily):
    """valor p y franja de la curva acumulada."""
    total = float(np.sum(strategy_daily))
    rand_tot = rand_daily.sum(axis=1)
    p = (1 + int((rand_tot >= total).sum())) / (1 + len(rand_tot))
    cum = np.cumsum(rand_daily, axis=1)
    return {"p_valor": round(p, 4), "n_rand": int(len(rand_tot)), "rand_media": round(float(rand_tot.mean()), 2),
            "rand_p5": np.percentile(cum, 5, axis=0).round(2).tolist(),
            "rand_p95": np.percentile(cum, 95, axis=0).round(2).tolist(),
            "rand_total_p5": round(float(np.percentile(rand_tot, 5)), 2),
            "rand_total_p95": round(float(np.percentile(rand_tot, 95)), 2)}
