"""RAND emparejado (protocol.json › rand_emparejado).

Copia la forma de la estrategia: por sesión, misma cantidad de operaciones y misma duración
de cada una; entrada en instante uniforme dentro del horario permitido, dirección 50/50,
sale por tiempo (sin stop ni objetivo), mismos costos y contratos.
La semilla de cada corrida = SHA-256(id_prueba:fecha:k) por sesión y corrida (protocolo v3).
RAND2 (with_exits=True) copia además stop, objetivo y tiempo máximo de cada operación real.
Motor 1.2.0: RAND recibe las MISMAS reglas que la estrategia, incluidas las ventanas de noticias por fecha
(`news_by_date`); el instante aleatorio se sortea fuera de esas ventanas, así la cantidad de operaciones
no se pierde por la regla de noticias. `run_rand(..., return_counts=True)` devuelve además cuántas
operaciones se llenaron en cada corrida, para publicar si coinciden con las de la estrategia (pueden no
coincidir: dos sorteos solapados en la misma sesión se suprimen, igual que en la estrategia).
"""
import hashlib
import numpy as np
from .sim import Signal, Rules, simulate
from .data import load


def seed_for(test_id, k):
    return int(hashlib.sha256(f"{test_id}:{k}".encode()).hexdigest()[:12], 16)


def _in_news(sec, news):
    return any(a <= sec <= b for a, b in news)


def rand_signals(trades_by_date, rules: Rules, rng, with_exits=False, news_by_date=None):
    """trades_by_date: {date: [(dur, stop, target, max_sec)]} -> {date: [Signal]}
    with_exits=False: RAND clásico (sale por tiempo, copia la duración). with_exits=True: RAND2, copia stop,
    objetivo y tiempo máximo de cada operación real (misma estructura de salidas; solo cambian momento y dirección).
    news_by_date: {date: ((s0, s1), ...)}; el instante se sortea FUERA de las ventanas de noticias de esa fecha."""
    out = {}
    span = rules.last_entry - rules.first_entry
    for d, items in trades_by_date.items():
        sigs = []
        news = (news_by_date or {}).get(d, ()) or rules.news
        for dur, stop, target, mx in items:
            sec = rules.first_entry + rng.random() * span
            tries = 0
            while news and _in_news(sec, news) and tries < 200:
                sec = rules.first_entry + rng.random() * span; tries += 1
            side = 1 if rng.random() < 0.5 else -1
            if with_exits:
                sigs.append(Signal(sec=sec, side=side, stop_ticks=stop, target_ticks=target, max_sec=mx, kind="RAND2"))
            else:
                sigs.append(Signal(sec=sec, side=side, stop_ticks=10**6, target_ticks=None, max_sec=max(dur, 1.0), kind="RAND"))
        out[d] = sigs
    return out


def _rand_session(args):
    test_id, d, items, rules, slip, commission_rt, n_runs, with_exits, news = args
    s = load(d, ny_only=True)
    free = Rules(max_trades=10**6, max_consec_losses=10**6, first_entry=rules.first_entry,
                 last_entry=rules.last_entry, forced_close=rules.forced_close, news=news, contracts=rules.contracts)
    col = np.zeros(n_runs); cnt = np.zeros(n_runs, dtype=int)
    for k in range(n_runs):
        rng = np.random.default_rng(seed_for(f"{test_id}:{d}", k))
        sigs = rand_signals({d: items}, rules, rng, with_exits, {d: news})[d]
        tr = simulate(s, sigs, free, slip, commission_rt)
        col[k] = sum(t["net_usd"] for t in tr); cnt[k] = len(tr)
    return col, cnt


def run_rand(test_id, trades, rules: Rules, slip, commission_rt, n_runs=1000, sessions=None, progress=None, workers=6, with_exits=False,
             news_by_date=None, return_counts=False):
    """Devuelve matriz (n_runs x sesiones) de ganancia neta diaria, en el orden de `sessions`
    (y, con return_counts=True, también la matriz de operaciones llenadas por corrida y sesión).
    Sesión afuera (en paralelo), corridas adentro: cada sesión se carga una sola vez."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    by_date = {}
    for t in trades:
        by_date.setdefault(t["date"], []).append((t["duration_s"], t.get("stop_ticks") or 10**6, t.get("target_ticks"), t.get("max_sec") or max(t["duration_s"], 1.0)))
    sessions = sessions or sorted(by_date)
    daily = np.zeros((n_runs, len(sessions))); counts = np.zeros((n_runs, len(sessions)), dtype=int)
    nb = news_by_date or {}
    jobs = [(j, (test_id, d, by_date[d], rules, slip, commission_rt, n_runs, with_exits, tuple(nb.get(d, ()) or rules.news))) for j, d in enumerate(sessions) if d in by_date]
    # spawn (no fork): polars deja hilos vivos en el padre y un fork se cuelga
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as ex:
        for i, (j, (col, cnt)) in enumerate(zip([j for j, _ in jobs], ex.map(_rand_session, [a for _, a in jobs], chunksize=4))):
            daily[:, j] = col; counts[:, j] = cnt
            if progress and (i + 1) % 50 == 0:
                progress(i + 1)
    if return_counts:
        return sessions, daily, counts
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
