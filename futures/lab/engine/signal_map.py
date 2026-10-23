"""Fase 1 · Mapa de señales. Para cada señal: cada vez que aparece, movimiento del precio a 1, 5, 15 y 30 min
en la dirección que la señal predice (ticks), comparado con 1000 sorteos de momentos al azar en la misma
sesión y la misma media hora (misma dirección). Sin stops ni objetivos. p de dos colas: una señal puede ser
mejor que el azar (sentido "a favor") o peor (sentido "contraria", que es la hipótesis opuesta). Holm sobre 48 pruebas.
Un evento por celda de 10 s y dirección para no contar varias veces el mismo momento.

  python -m engine.signal_map --study mapa_v1 [--limit N]
Salida: futures/signal_map.json + un intento por señal en el registro.
"""
import argparse, json, os, time
import numpy as np
from . import config, registry
from .data import load, NY_OPEN, NY_CLOSE
from .levels import Levels, precompute_stats
from .strategies.v1 import _bins, BIN

H = {"r1": 60, "r5": 300, "r15": 900, "r30": 1800}
NAMES = {
    "big": "Órdenes grandes (tamaño y niveles barridos)", "abs": "Absorción", "stack": "Desequilibrios apilados",
    "ddiv": "Divergencia de delta", "orb": "Ruptura del rango inicial", "exh": "Agotamiento", "va": "Rechazo del área de valor",
    "hvn": "Zonas HVN (estilo Profit Pro)", "qimb": "Desequilibrio de la mejor compra/venta", "ice": "Icebergs (orden que se repone)",
    "burst": "Ráfagas de intensidad", "mom": "Momentum primera → última media hora",
}
HYP = {"big": "continuación en la dirección de la orden", "abs": "reversión contra el volumen absorbido",
       "stack": "continuación del lado dominante", "ddiv": "reversión contra el precio", "orb": "continuación de la ruptura",
       "exh": "reversión", "va": "vuelta hacia el POC", "hvn": "rechazo (vuelve por donde vino)",
       "qimb": "sube si la mejor compra domina (Gould & Bonart)", "ice": "reversión contra el lado que choca con el iceberg",
       "burst": "continuación del delta de la ráfaga", "mom": "la última media hora sigue a la primera"}


def events(s, L, d, thr, ref, prof):
    """Devuelve {señal: [(sec, dir)]} para la sesión s (ventana NY completa)."""
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_CLOSE)
    out = {k: [] for k in NAMES}
    if j - i < 1000 or not thr:
        return out
    tid = s.tid[i:j]; px = s.px[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]; sec = s.sec[i:j]
    starts = np.r_[0, np.flatnonzero(np.diff(tid)) + 1]; ends = np.r_[starts[1:], len(tid)] - 1
    size = np.add.reduceat(vol, starts); hi = np.maximum.reduceat(px, starts); lo = np.minimum.reduceat(px, starts)
    big = np.flatnonzero((size >= thr["order_p99"]) & (hi - lo + 1 >= 2))
    out["big"] = [(float(sec[ends[c]]), int(sd[starts[c]])) for c in big if sd[starts[c]] != 0]
    buy, sell, bh, bl, first, last = _bins(s, i, j); nb = len(buy); W = 6
    k = np.ones(W); bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    for e in range(W - 1, nb):
        w0 = e - W + 1; t = NY_OPEN + (e + 1) * BIN
        if bw[w0] >= thr["buy60_p95"] and bh[w0:e + 1].max() <= first[w0] + 2:
            out["abs"].append((t, -1))
        if sw[w0] >= thr["sell60_p95"] and bl[w0:e + 1].min() >= first[w0] - 2:
            out["abs"].append((t, 1))
    tot = buy + sell
    for e in range(1, nb):
        b2, s2 = buy[e - 1:e + 1], sell[e - 1:e + 1]
        if (b2 >= 2 * np.maximum(s2, 1)).all() and tot[e - 1:e + 1].min() >= 50:
            out["stack"].append((NY_OPEN + (e + 1) * BIN, 1))
        elif (s2 >= 2 * np.maximum(b2, 1)).all() and tot[e - 1:e + 1].min() >= 50:
            out["stack"].append((NY_OPEN + (e + 1) * BIN, -1))
    # divergencia de delta: 5 min vs 5 min anteriores
    M = 30
    delta = buy - sell
    for e in range(2 * M, nb, M // 2):
        h1, h0 = bh[e - M:e].max(), bh[e - 2 * M:e - M].max(); l1, l0 = bl[e - M:e].min(), bl[e - 2 * M:e - M].min()
        d1, d0 = delta[e - M:e].sum(), delta[e - 2 * M:e - M].sum()
        if h1 > h0 and d1 < d0:
            out["ddiv"].append((NY_OPEN + e * BIN, -1))
        elif l1 < l0 and d1 > d0:
            out["ddiv"].append((NY_OPEN + e * BIN, 1))
    # ruptura del rango inicial (15 min)
    orh, orl = bh[:90].max(), bl[:90].min()
    up = np.flatnonzero(bh[90:] > orh); dn = np.flatnonzero(bl[90:] < orl)
    if len(up) and (not len(dn) or up[0] < dn[0]):
        out["orb"].append((NY_OPEN + (90 + up[0] + 1) * BIN, 1))
    elif len(dn):
        out["orb"].append((NY_OPEN + (90 + dn[0] + 1) * BIN, -1))
    # agotamiento: >=20 ticks en 5 min con volumen cayendo en los últimos 2 min
    for e in range(M, nb, 6):
        mv = last[e] - first[e - M]
        v_late, v_early = tot[e - 12:e].sum(), tot[e - M:e - 12].sum() * 12 / (M - 12)
        if abs(mv) >= 20 and v_late < 0.6 * v_early:
            out["exh"].append((NY_OPEN + (e + 1) * BIN, -1 if mv > 0 else 1))
    # rechazo del área de valor (solo si abre dentro)
    if ref and L.open_in_value(d):
        for edge, lvl, dirn in (("prev_vah", ref["prev_vah"], -1), ("prev_val", ref["prev_val"], 1)):
            hit = np.flatnonzero((bh >= lvl - 2) if dirn < 0 else (bl <= lvl + 2))
            if len(hit):
                out["va"].append((NY_OPEN + (hit[0] + 1) * BIN, dirn))
    # HVN del día anterior: niveles con volumen >= p90 del perfil; llegada desde >= 20 ticks
    if prof is not None and len(prof):
        pxs, vs = prof[:, 0], prof[:, 1]; hv = pxs[vs >= np.percentile(vs, 90)]
        for lvl in hv:
            far_above = np.flatnonzero(bl >= lvl + 20); far_below = np.flatnonzero(bh <= lvl - 20)
            touch = np.flatnonzero((bl <= lvl) & (bh >= lvl))
            if len(touch) and len(far_above) and far_above[0] < touch[0] and (touch[0] - far_above[0]) < 360:
                out["hvn"].append((NY_OPEN + (touch[0] + 1) * BIN, 1))
            elif len(touch) and len(far_below) and far_below[0] < touch[0] and (touch[0] - far_below[0]) < 360:
                out["hvn"].append((NY_OPEN + (touch[0] + 1) * BIN, -1))
    # desequilibrio de la mejor compra/venta, muestreado cada 10 s
    for e in range(0, nb, 1):
        kk = int(np.searchsorted(sec, NY_OPEN + (e + 1) * BIN, side="right")) - 1
        if kk < 0:
            continue
        b, a_ = int(s.bsz[i + kk]), int(s.asz[i + kk])
        if b + a_ >= 20:
            q = b / (b + a_)
            if q >= 0.8: out["qimb"].append((NY_OPEN + (e + 1) * BIN, 1))
            elif q <= 0.2: out["qimb"].append((NY_OPEN + (e + 1) * BIN, -1))
    # icebergs: racha de llenados consecutivos en el MISMO precio y del mismo lado agresor, con >= 5 órdenes distintas
    # y >= 100 contratos, y la cotización en ese precio sigue viva al final (se repone). Dirección: contra el agresor.
    chg = (px[1:] != px[:-1]) | (sd[1:] != sd[:-1])
    rs_ = np.r_[0, np.flatnonzero(chg) + 1]; re_ = np.r_[rs_[1:], len(px)]
    runvol = np.add.reduceat(vol, rs_)
    tchg = np.r_[0, (tid[1:] != tid[:-1]).astype(int)]; cum = np.cumsum(tchg)
    norders = cum[re_ - 1] - cum[rs_] + 1
    quote_after = np.where(sd[rs_] > 0, s.asz[i + re_ - 1], s.bsz[i + re_ - 1])
    cand = np.flatnonzero((runvol >= 100) & (norders >= 5) & (quote_after >= 20) & (sd[rs_] != 0))
    out["ice"] = [(float(sec[re_[c] - 1]), -int(sd[rs_[c]])) for c in cand]
    # ráfagas: celda de 10 s con volumen >= p99 de las celdas de la sesión
    p99 = np.percentile(tot, 99)
    for e in np.flatnonzero(tot >= p99):
        dl = buy[e] - sell[e]
        if dl != 0:
            out["burst"].append((NY_OPEN + (e + 1) * BIN, 1 if dl > 0 else -1))
    # un evento por celda de 10 s y dirección: niveles o celdas vecinas que disparan a la vez no se cuentan varias veces
    for k, lst in out.items():
        seen, uniq = set(), []
        for t, dd in lst:
            key = (int((t - NY_OPEN) // BIN), dd)
            if key not in seen:
                seen.add(key); uniq.append((t, dd))
        out[k] = uniq
    # momentum: primera media hora -> última media hora
    p930, p1000 = int(s.px[0]), s.price_at(NY_OPEN + 1800)
    if p930 and p1000 and p1000 != p930:
        out["mom"].append((NY_CLOSE - 1800, 1 if p1000 > p930 else -1))
    return out


def forward(s, secs, dirs):
    base = np.array([s.price_at(t) or 0 for t in secs], dtype=float)
    res = {}
    for k, h in H.items():
        fut = np.array([s.price_at(t + h) or 0 for t in secs], dtype=float)
        res[k] = (fut - base) * dirs
    return res


def baseline(s, secs, dirs, n=1000, rng=None, groups=None, ngroups=0):
    """n sorteos: cada evento se mueve a un momento al azar dentro de su misma media hora.
    Devuelve (misma dirección, dirección aleatoria, por grupo [misma dirección])."""
    secs = np.asarray(secs); slot = np.floor((secs - NY_OPEN) / 1800) * 1800 + NY_OPEN
    out = {k: np.zeros(n) for k in H}; out_rd = {k: np.zeros(n) for k in H}
    out_g = {k: np.zeros((n, ngroups)) for k in H} if ngroups else None
    for r in range(n):
        rs = slot + rng.random(len(secs)) * 1800
        rs = np.minimum(rs, NY_CLOSE - 1801)
        rdir = rng.choice([-1.0, 1.0], size=len(secs))
        idx0 = np.searchsorted(s.sec, rs, side="right") - 1
        base = s.px[np.clip(idx0, 0, s.n - 1)].astype(float)
        for k, h in H.items():
            idx1 = np.searchsorted(s.sec, rs + h, side="right") - 1
            mv = (s.px[np.clip(idx1, 0, s.n - 1)] - base)
            out[k][r] = float(np.sum(mv * dirs)); out_rd[k][r] = float(np.sum(mv * rdir))
            if ngroups:
                out_g[k][r] = np.bincount(groups, weights=mv * dirs, minlength=ngroups)
    return out, out_rd, out_g


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--study", required=True); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--draws", type=int, default=5000); ap.add_argument("--only", default="")
    a = ap.parse_args(); only = set(a.only.split(",")) - {""}
    if not any(s["study_id"] == a.study for s in registry.read(registry.STUDIES)):
        raise SystemExit("estudio no registrado")
    dates, sess_sha = config.design_sessions()
    if a.limit: dates = dates[:a.limit]
    precompute_stats(dates); L = Levels(dates); t0 = time.time()
    import polars as pl
    from . import regime as _regime
    REG = _regime.load() or (_regime.build(dates) and _regime.load())
    SLOTS = 13; GROUPS = ["tendencia", "balance"]           # grupos del condicional: régimen × media hora
    NG = len(GROUPS) * SLOTS
    gsum = {k: {h: np.zeros(NG) for h in H} for k in NAMES}; gcnt = {k: np.zeros(NG, dtype=int) for k in NAMES}
    gbase = {k: {h: np.zeros((a.draws, NG)) for h in ("r15", "r30")} for k in NAMES}
    rdsum = {k: {h: np.zeros(a.draws) for h in H} for k in NAMES}
    sums = {k: {h: 0.0 for h in H} for k in NAMES}; cnt = {k: 0 for k in NAMES}
    bsum = {k: {h: np.zeros(a.draws) for h in H} for k in NAMES}
    rng = np.random.default_rng(20261022)
    hist = {k: {h: [] for h in H} for k in NAMES}
    ysum = {k: {h: {} for h in H} for k in NAMES}; ycnt = {k: {} for k in NAMES}   # estabilidad: por año
    for n, d in enumerate(dates):
        ref, thr = L.reference(d), L.thresholds(d)
        if not thr: continue
        s = load(d, ny_only=True)
        prev = L.prev_date(d); prof = None
        pp = os.path.join(config.FEAT, "profile", "NQ", f"{prev}.parquet") if prev else None
        if pp and os.path.exists(pp):
            pr = pl.read_parquet(pp).filter(pl.col("seg") == "ny"); prof = np.c_[pr["price_t"].to_numpy(), pr["vol"].to_numpy()]
        ev = events(s, L, d, thr, ref, prof)
        for k, lst in ev.items():
            if not lst or (only and k not in only): continue
            secs = np.array([x[0] for x in lst]); dirs = np.array([x[1] for x in lst], dtype=float)
            keep = secs <= NY_CLOSE - 1800
            secs, dirs = secs[keep], dirs[keep]
            if not len(secs): continue
            gidx = (0 if REG.get(d, {}).get("tendencia") == "tendencia" else 1) * SLOTS + np.clip(((secs - NY_OPEN) // 1800).astype(int), 0, SLOTS - 1)
            fw = forward(s, secs, dirs); bl, bl_rd, bl_g = baseline(s, secs, dirs, a.draws, rng, gidx, NG)
            y = d[:4]
            for h in H:
                sums[k][h] += float(fw[h].sum()); bsum[k][h] += bl[h]; rdsum[k][h] += bl_rd[h]
                gsum[k][h] += np.bincount(gidx, weights=fw[h], minlength=NG)
                if h in ("r15", "r30"): gbase[k][h] += bl_g[h]
            gcnt[k] += np.bincount(gidx, minlength=NG)
                hist[k][h] += fw[h][:50].tolist()
                ysum[k][h][y] = ysum[k][h].get(y, 0.0) + float(fw[h].sum())
            cnt[k] += len(secs); ycnt[k][y] = ycnt[k].get(y, 0) + len(secs)
        if (n + 1) % 25 == 0: print(f"  {n+1}/{len(dates)} sesiones · {time.time()-t0:.0f}s", flush=True)
    rows, pv = [], []
    prev_map = {}
    mp = os.path.join(config.FUT, "signal_map.json")
    if only and os.path.exists(mp):
        prev_map = {r["id"]: r for r in json.load(open(mp, encoding="utf-8"))["senales"]}
    for k in NAMES:
        if only and k not in only and k in prev_map:
            r = prev_map[k]; rows.append(r)
            for h in H:
                if r.get(h + "_p") is not None: pv.append((k, h, r[h + "_p"]))
            continue
        r = {"id": k, "senal": NAMES[k], "hipotesis": HYP[k], "n": cnt[k]}
        for h in H:
            if cnt[k]:
                obs = sums[k][h] / cnt[k]; bm = bsum[k][h] / cnt[k]
                p_up = (1 + int((bm >= obs).sum())) / (1 + a.draws); p_dn = (1 + int((bm <= obs).sum())) / (1 + a.draws)
                p = min(1.0, 2 * min(p_up, p_dn))   # dos colas: la señal puede ser mejor O peor que el azar
                r[h] = round(obs, 2); r[h + "_azar"] = round(float(bm.mean()), 2); r[h + "_p"] = round(p, 4)
                r[h + "_dir"] = "a favor" if obs > float(bm.mean()) else "contraria"; pv.append((k, h, p))
                r[h + "_z"] = round(float((obs - bm.mean()) / bm.std()), 2) if bm.std() > 0 else None
                rd = rdsum[k][h] / cnt[k]   # azar con dirección aleatoria: ¿la DIRECCIÓN es rentable por sí sola?
                pu = (1 + int((rd >= obs).sum())) / (1 + a.draws); pd_ = (1 + int((rd <= obs).sum())) / (1 + a.draws)
                r[h + "_p_bruto"] = round(min(1.0, 2 * min(pu, pd_)), 4)
            else:
                r[h] = None; r[h + "_p"] = None
        r["por_anio"] = {y: {h: round(ysum[k][h].get(y, 0.0) / n, 2) for h in H} for y, n in ycnt[k].items() if n} if cnt[k] else {}
        yrs = [y for y in ("2024", "2025") if y in r["por_anio"]]
        r["estable_r15"] = (len(yrs) == 2 and np.sign(r["por_anio"]["2024"]["r15"]) == np.sign(r["por_anio"]["2025"]["r15"]) and r["por_anio"]["2024"]["r15"] != 0) if cnt[k] else None
        # condicional: régimen × media hora (descriptivo, con z contra el azar de la misma dirección por celda)
        cond = {}
        for gi, gname in enumerate(GROUPS):
            cond[gname] = []
            for sl in range(SLOTS):
                g = gi * SLOTS + sl; n_ = int(gcnt[k][g])
                c = {"slot": f"{9 + (sl + 1) // 2}:{'30' if sl % 2 == 0 else '00'}", "n": n_}
                for h in ("r15", "r30"):
                    if n_:
                        obs_ = gsum[k][h][g] / n_; b_ = gbase[k][h][:, g] / n_
                        c[h] = round(float(obs_), 2); c[h + "_z"] = round(float((obs_ - b_.mean()) / b_.std()), 2) if b_.std() > 0 else None
                cond[gname].append(c)
        r["condicional"] = cond
        # por régimen (r30): obs y p de dos colas contra el azar de la misma dirección, 24 pruebas con Holm aparte
        r["por_regimen"] = {}
        for gi, gname in enumerate(GROUPS):
            sel = slice(gi * SLOTS, (gi + 1) * SLOTS); n_ = int(gcnt[k][sel].sum())
            if n_:
                obs_ = gsum[k]["r30"][sel].sum() / n_; b_ = gbase[k]["r30"][:, sel].sum(axis=1) / n_
                pu = (1 + int((b_ >= obs_).sum())) / (1 + a.draws); pd_ = (1 + int((b_ <= obs_).sum())) / (1 + a.draws)
                r["por_regimen"][gname] = {"n": n_, "r30": round(float(obs_), 2), "azar": round(float(b_.mean()), 2), "p": round(min(1.0, 2 * min(pu, pd_)), 4)}
        r["hist_r15"] = np.histogram(hist[k]["r15"], bins=[-80, -40, -20, -10, -5, 0, 5, 10, 20, 40, 80])[0].tolist() if hist[k]["r15"] else []
        rows.append(r)
    # Holm al 5% sobre las 48 pruebas
    m = len(pv); pv.sort(key=lambda x: x[2]); sig = set()
    for rank, (k, h, p) in enumerate(pv):
        if p <= 0.05 / (m - rank): sig.add((k, h))
        else: break
    for r in rows:
        r["horizontes_significativos"] = [h for h in H if (r["id"], h) in sig]
        r["significativa"] = bool(r["horizontes_significativos"])
        r["sentido"] = ("a favor" if all(r.get(h + "_dir") == "a favor" for h in r["horizontes_significativos"]) else
                        "contraria" if all(r.get(h + "_dir") == "contraria" for h in r["horizontes_significativos"]) else "mixto") if r["significativa"] else "—"
    prv = [(r["id"], g, v["p"]) for r in rows for g, v in r.get("por_regimen", {}).items()]
    prv.sort(key=lambda x: x[2]); sigr = set(); mr = len(prv)
    for rank, (k, g, p) in enumerate(prv):
        if p <= 0.05 / (mr - rank): sigr.add((k, g))
        else: break
    for r in rows:
        for g, v in r.get("por_regimen", {}).items():
            v["significativa"] = (r["id"], g) in sigr
    out = {"titulo": "Mapa de señales v2 (azar misma dirección + dirección aleatoria + régimen + media hora + estabilidad 2024/2025)", "fecha": time.strftime("%Y-%m-%d"), "sesiones": len(dates), "sorteos": a.draws,
           "pruebas": m, "pruebas_regimen": mr, "correccion": "Holm 5% (48 principales; 24 de régimen aparte)", "sesiones_sha256": sess_sha, "senales": rows}
    json.dump(out, open(os.path.join(config.FUT, "signal_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in rows:
        if only and r["id"] not in only: continue
        registry.record_trial(f"S-{r['id']}", a.study, r["id"], 1, "senal", {"horizontes": list(H)}, sess_sha, len(dates), "20261022",
                              config.Costs().as_dict(), {"n": r["n"], **{h: r[h] for h in H}, **{h + "_p": r[h + "_p"] for h in H}},
                              "significativa" if r["significativa"] else "no_significativa")
    print(f"mapa listo: {m} pruebas, {len(sig)} significativas · {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
