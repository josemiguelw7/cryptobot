"""Simulación de operaciones contra la cinta real (cada llenado, en orden).

Reglas de llenado (conservadoras, fijas):
  - Entrada a mercado: se llena en el PEOR entre (a) la mejor oferta contraria que ve el primer llenado posterior
    a la decisión (su bid/ask "antes") y (b) el precio de ese primer llenado; más `slip` ticks en contra. Las
    cotizaciones de ATAS pueden quedar congeladas durante segundos (hallazgo de la revisión ciega del 24/10/2026:
    libro en 71582 con operaciones en 71762), así que nunca se acepta una cotización mejor que el precio que
    realmente se operó. El llenado de entrada NO cuenta para el objetivo ni el stop: el recorrido empieza en el
    llenado siguiente. Se cuenta cuántas entradas tuvieron cotización anómala (> 20 ticks del precio operado).
  - Stop: se llena al PEOR entre el precio del stop y el precio real del llenado que lo disparó, menos `slip`:
    si el mercado salta más allá del stop, la pérdida es la del salto (hallazgo de la misma revisión).
  - Stop: es un stop de mercado; se llena al precio del stop más `slip` ticks en contra
    en cuanto la cinta opera en o más allá del stop.
  - Objetivo: es una orden límite; se da por llenada solo cuando la cinta opera MÁS ALLÁ
    del objetivo (regla 'through'); tocar el precio no basta. Sin deslizamiento.
  - Tiempo o cierre forzado: salida a mercado al último precio operado más `slip`.
  - Entrada límite (para estrategias pasivas): se modela la cola. La orden se pone detrás
    del tamaño que había en el libro a ese precio; se llena cuando se opera ese volumen
    en ese precio o cuando el precio pasa de largo. Si no se llena en `wait` segundos, se cancela.
Precios en ticks enteros. 1 tick = $5.
"""
from dataclasses import dataclass, field, asdict
import numpy as np

FORCED_CLOSE = 42300.0   # 11:45 ET
LAST_ENTRY = 41400.0     # 11:30 ET


@dataclass
class Signal:
    sec: float
    side: int
    stop_ticks: int
    target_ticks: int | None
    max_sec: float
    kind: str = ""
    level: str = ""
    order: str = "market"          # 'market' | 'limit'
    limit_px: int | None = None
    wait_sec: float = 60.0
    meta: dict = field(default_factory=dict)


@dataclass
class Rules:
    max_trades: int = 6
    max_consec_losses: int = 3
    first_entry: float = 34200.0
    last_entry: float = LAST_ENTRY
    forced_close: float = FORCED_CLOSE
    news: tuple = ()                # ((s0, s1), ...) ventanas sin entradas
    contracts: int = 1
    target_rule: str = "through"    # 'through' | 'touch'
    pyramid: dict | None = None     # {"add_ticks": X, "max_adds": n, "stop_breakeven": bool}: agrega 1 contrato cada X ticks a favor


def _in_news(sec, news):
    return any(a <= sec <= b for a, b in news)


def _best(s, i, side):
    """Mejor oferta contraria que ve una orden que llega justo antes del llenado i (libro 'antes' de i)."""
    k = min(i, s.n - 1)
    q = s.askb[k] if side > 0 else s.bidb[k]
    if q <= 0:
        q = s.px[k]
    return int(q)


def fill_limit(s, i, side, limit_px, wait_sec):
    """Llenado de una orden límite puesta en el índice i. Devuelve (índice, precio) o None."""
    k = i - 1 if i > 0 else 0
    # cola por delante: tamaño en el libro a ese precio en el momento de poner la orden
    if side > 0:
        queue = int(s.bsz[k]) if s.bid[k] == limit_px else 0
    else:
        queue = int(s.asz[k]) if s.ask[k] == limit_px else 0
    end_sec = s.sec[i] + wait_sec if i < s.n else None
    if end_sec is None:
        return None
    j = min(s.n, int(np.searchsorted(s.sec, end_sec, side="right")))
    px, vol, sd = s.px[i:j], s.vol[i:j], s.side[i:j]
    if side > 0:
        through = px < limit_px                      # alguien vendió más abajo: ya nos llenaron
        at = (px == limit_px) & (sd < 0)             # ventas agresivas pegando en nuestro precio
    else:
        through = px > limit_px
        at = (px == limit_px) & (sd > 0)
    cum = np.cumsum(np.where(at, vol, 0))
    done = (cum > queue) | through
    if not done.any():
        return None
    f = int(np.argmax(done))
    return i + f, int(limit_px)


def simulate(s, signals, rules: Rules, slip: int, commission_rt: float, tick_usd=5.0):
    """Corre las señales de una sesión en orden. Devuelve lista de operaciones (dict)."""
    trades, consec, busy_until = [], 0, -1.0
    for sig in sorted(signals, key=lambda x: x.sec):
        if len(trades) >= rules.max_trades or consec >= rules.max_consec_losses:
            break
        if sig.sec < rules.first_entry or sig.sec > rules.last_entry or sig.sec < busy_until:
            continue
        if _in_news(sig.sec, rules.news):
            continue
        i = s.idx_sec(sig.sec)
        if i >= s.n:
            continue
        side = 1 if sig.side > 0 else -1
        if sig.order == "limit" and sig.limit_px is not None:
            r = fill_limit(s, i, side, sig.limit_px, sig.wait_sec)
            if r is None:
                continue
            i, entry_px = r; anomal = False
            if i >= s.n:
                continue
        else:
            q = _best(s, i, side); first = int(s.px[i])
            anomal = abs(first - q) > 20                      # cotización congelada o rota
            entry_px = (max(q, first) if side > 0 else min(q, first)) + side * slip
        entry_sec = float(s.sec[i])   # el llenado ocurre en el primer evento posterior a la decisión
        i = i + 1                      # el recorrido empieza DESPUÉS del llenado de entrada
        if i >= s.n:
            continue
        stop_px = entry_px - side * sig.stop_ticks
        target_px = entry_px + side * sig.target_ticks if sig.target_ticks else None
        t_end = min(entry_sec + sig.max_sec, rules.forced_close)
        j = min(s.n, int(np.searchsorted(s.sec, t_end, side="right")))
        px = s.px[i:j]
        if len(px) == 0:
            continue
        hit_stop = (px <= stop_px) if side > 0 else (px >= stop_px)
        if target_px is not None:
            if rules.target_rule == "through":
                hit_tgt = (px > target_px) if side > 0 else (px < target_px)
            else:
                hit_tgt = (px >= target_px) if side > 0 else (px <= target_px)
        else:
            hit_tgt = np.zeros(len(px), dtype=bool)
        ks = int(np.argmax(hit_stop)) if hit_stop.any() else None
        kt = int(np.argmax(hit_tgt)) if hit_tgt.any() else None
        if ks is not None and (kt is None or ks <= kt):
            hit_px = int(px[ks])                                   # precio real que disparó el stop (puede saltar)
            k, exit_px, reason = ks, (min(stop_px, hit_px) if side > 0 else max(stop_px, hit_px)) - side * slip, "stop"
        elif kt is not None:
            k, exit_px, reason = kt, target_px, "objetivo"
        else:
            k = len(px) - 1
            exit_px = int(px[k]) - side * slip
            reason = "cierre" if t_end >= rules.forced_close else "tiempo"
        fills = [entry_px]; adds_idx = []
        if rules.pyramid and (target_px is not None or sig.target_ticks is None):
            # agrega 1 contrato cada add_ticks a favor (la cinta debe pasar de largo), hasta max_adds; el stop de TODO
            # puede subir al precio de la primera entrada (breakeven) al primer agregado. La salida se recalcula.
            P = rules.pyramid; stop_now = stop_px; k_lim = k
            for a in range(1, int(P.get("max_adds", 1)) + 1):
                add_px = entry_px + side * int(P["add_ticks"]) * a
                hit = (px > add_px) if side > 0 else (px < add_px)
                if not hit.any():
                    break
                ka = int(np.argmax(hit))
                if ka >= k_lim:
                    break
                fills.append(add_px + side * slip); adds_idx.append(ka)
                if P.get("stop_breakeven") and a == 1:
                    stop_now = entry_px
                    seg = px[ka:]; hs = (seg <= stop_now) if side > 0 else (seg >= stop_now)
                    ks2 = ka + int(np.argmax(hs)) if hs.any() else None
                    if ks2 is not None and (kt is None or ks2 <= kt) and ks2 < k_lim:
                        hp = int(px[ks2]); k_lim, exit_px, reason = ks2, (min(stop_now, hp) if side > 0 else max(stop_now, hp)) - side * slip, "stop_breakeven"
            k = k_lim
        exit_sec = float(s.sec[i + k])
        path = px[: k + 1]
        mfe = int(((path - entry_px) * side).max())
        mae = int(((entry_px - path) * side).max())
        pnl_ticks = int((exit_px - entry_px) * side)
        n_contr = rules.contracts * len(fills)
        gross = sum(int((exit_px - f) * side) for f in fills) * tick_usd * rules.contracts
        cost = commission_rt * n_contr
        net = gross - cost
        trades.append({
            "date": s.date, "kind": sig.kind, "level": sig.level, "side": side,
            "entry_sec": entry_sec, "entry_px": entry_px / 4, "exit_sec": exit_sec, "exit_px": exit_px / 4,
            "reason": reason, "pnl_ticks": pnl_ticks, "gross_usd": gross, "commission_usd": cost,
            "net_usd": net, "mae_ticks": mae, "mfe_ticks": mfe, "duration_s": exit_sec - entry_sec,
            "contracts": n_contr, "fills": [f / 4 for f in fills], "slip_ticks": slip, "stop_ticks": sig.stop_ticks,
            "target_ticks": sig.target_ticks, "max_sec": sig.max_sec, "cotizacion_anomala": bool(anomal), "meta": sig.meta,
        })
        busy_until = exit_sec
        consec = consec + 1 if net < 0 else 0
    return trades


def sec_to_hms(sec):
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"
