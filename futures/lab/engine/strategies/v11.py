"""Estrategias v11 (tanda 12), congeladas en futures/strategies/v13.json.
  ABK v1 : ABSORCIÓN MEDIDA CON EL LIBRO (la definición de footprint/Bookmap: el lado pasivo recibe mucho flujo agresivo y NO retrocede).
           Las ABS/ABI/ABV/HVF anteriores infieren la absorción por el precio ("no avanzó más de 2 ticks"). Aquí se exige que la
           MEJOR OFERTA (compra para ventas agresivas, venta para compras agresivas) se mantenga en el mismo precio durante toda la
           ventana y que, al final, siga con tamaño (se repuso). Eso es lo que distingue una pared pasiva que absorbe de un mercado
           que simplemente se frenó.
           Investigación y justificación: docs/investigacion/absorcion_libro.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "ABK": {"max_advance": 2, "refill_pct": 50, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32,
            "max_min": 15, "min_elapsed_s": 600, "cooldown_s": 300},
}
BIN = V1.BIN


def absorption_book(s, ref, thr, p=None):
    """Detector (todo con datos anteriores a la decisión):
      · Ventana de 60 s con ≥ p95 de volumen agresivo de UN lado (mismo umbral relativo que ABS v1: p95 de las 20 sesiones anteriores).
      · El precio no avanza más de `max_advance` ticks (igual que ABS).
      · LA MEJOR OFERTA AGUANTA: para venta agresiva, la mejor compra (bid) nunca baja del bid que había antes del primer llenado
        de la ventana; para compra agresiva, la mejor venta (ask) nunca sube del ask de antes del primer llenado.
      · SE REPONE: el tamaño de esa mejor oferta tras el último llenado de la ventana es ≥ `refill_pct`% del que había tras el primer llenado.
      · Confirmación (igual que ABS): en los `confirm_s` siguientes el delta de la ventana cambia de signo y el precio se aleja
        `away_ticks` del extremo. Entrada a mercado EN CONTRA del lado absorbido; stop `stop_beyond` ticks más allá del extremo
        (entre `stop_min` y `stop_max`); sin objetivo; salida por tiempo `max_min`.
      · Nada antes de `min_elapsed_s` (10 min); un disparo por lado cada `cooldown_s` (5 min). Sin filtro de nivel."""
    p = p or PARAMS["ABK"]
    if not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    sec = s.sec[i:j]
    bid = s.bid[i:j]; ask = s.ask[i:j]; bidb = s.bidb[i:j]; askb = s.askb[i:j]; bsz = s.bsz[i:j]; asz = s.asz[i:j]
    cell0 = np.searchsorted(sec, NY_OPEN + np.arange(nb + 1) * BIN, side="left")
    last_used = {}; out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if w0 * BIN < p["min_elapsed_s"]:
            continue
        a, z = int(cell0[w0]), int(cell0[e + 1])
        if z - a < 2:
            continue
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
            if volw < thr[thr_key]:
                continue
            start = int(first[w0])
            if side > 0:
                ext = int(hi[w0:e + 1].max())
                if ext > start + p["max_advance"]:
                    continue
                q0 = int(askb[a])
                if q0 <= 0 or int(ask[a:z].max()) > q0:      # la mejor venta no debe subir
                    continue
                sz0, sz1 = int(asz[a]), int(asz[z - 1])
            else:
                ext = int(lo[w0:e + 1].min())
                if ext < start - p["max_advance"]:
                    continue
                q0 = int(bidb[a])
                if q0 <= 0 or int(bid[a:z].min()) < q0:      # la mejor compra no debe bajar
                    continue
                sz0, sz1 = int(bsz[a]), int(bsz[z - 1])
            if sz0 <= 0 or sz1 < p["refill_pct"] / 100.0 * sz0:
                continue
            key = side
            t_sig = NY_OPEN + (e + 1) * BIN
            if key in last_used and t_sig - last_used[key] < p["cooldown_s"]:
                continue
            conf = None
            for f in range(e + 1, min(nb, e + 1 + p["confirm_s"] // BIN)):
                dw = bw[f - W + 1] - sw[f - W + 1] if f - W + 1 >= 0 else 0
                if side > 0 and dw < 0 and lo[f] <= ext - p["away_ticks"]:
                    conf = f; break
                if side < 0 and dw > 0 and hi[f] >= ext + p["away_ticks"]:
                    conf = f; break
            if conf is None:
                continue
            t_conf = NY_OPEN + (conf + 1) * BIN
            last_used[key] = t_conf
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                              kind="ABK", level="libro", meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side,
                                                                  "size_start": sz0, "size_end": sz1}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABK": absorption_book}
