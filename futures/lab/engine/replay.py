"""Replay de cada operación para el Explorador: ventana de ±10 min alrededor de la operación.
Escribe futures/lab/results/<id>/replay/<k>.json (k = índice de la operación en trades.json).
Contenido (compacto): precio cada segundo (ticks), VWAP del día, delta acumulado del día,
órdenes agresivas >= 50 contratos de la ventana, niveles de referencia, y la operación
(entrada, salida, stop, objetivo) para dibujarla encima.
"""
import json, os
import numpy as np
from . import config
from .data import load, NY_OPEN


def build(test_id, trades, levels, pad_s=600, min_order=50):
    out_dir = os.path.join(config.RESULTS, test_id, "replay"); os.makedirs(out_dir, exist_ok=True)
    tr = sorted(trades, key=lambda t: (t["date"], t["entry_sec"]))
    by_date = {}
    for k, t in enumerate(tr):
        by_date.setdefault(t["date"], []).append((k, t))
    for d, items in by_date.items():
        s = load(d, ny_only=True)
        if s.n == 0:
            continue
        pv = np.cumsum(s.px.astype(float) * s.vol); cv = np.cumsum(s.vol.astype(float))
        cd = np.cumsum(s.vol.astype(np.int64) * s.side.astype(np.int64))
        ref = levels.reference(d) or {}
        starts = np.r_[0, np.flatnonzero(np.diff(s.tid)) + 1]; ends = np.r_[starts[1:], s.n] - 1
        osize = np.add.reduceat(s.vol, starts)
        for k, t in items:
            a, b = max(NY_OPEN, t["entry_sec"] - pad_s), t["exit_sec"] + pad_s
            i, j = s.idx_sec(a), s.idx_sec(b)
            if j <= i:
                continue
            secs = np.arange(int(a), int(b) + 1)
            idx = np.clip(np.searchsorted(s.sec, secs, side="right") - 1, 0, s.n - 1)
            valid = idx >= i
            big = [c for c in range(len(starts)) if osize[c] >= min_order and i <= starts[c] < j]
            rec = {"test": test_id, "k": k, "date": d, "t0": int(a),
                   "p": [int(s.px[x]) if v else None for x, v in zip(idx, valid)],
                   "vwap": [round(float(pv[x] / cv[x]), 2) if v and cv[x] else None for x, v in zip(idx, valid)],
                   "cd": [int(cd[x]) if v else None for x, v in zip(idx, valid)],
                   "big": [[int(s.sec[starts[c]] - a), int(s.px[starts[c]]), int(s.side[starts[c]]), int(osize[c])] for c in big],
                   "ref": {kk: int(vv) for kk, vv in ref.items() if vv is not None},
                   "trade": {"side": t["side"], "entry_sec": t["entry_sec"], "exit_sec": t["exit_sec"], "entry_px": t["entry_px"],
                             "exit_px": t["exit_px"], "stop_ticks": t["stop_ticks"], "target_ticks": t["target_ticks"],
                             "reason": t["reason"], "net_usd": t["net_usd"], "kind": t["kind"], "level": t["level"], "meta": t.get("meta", {})}}
            json.dump(rec, open(os.path.join(out_dir, f"{k}.json"), "w"), separators=(",", ":"))
    return len(tr)
