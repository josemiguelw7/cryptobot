"""
REPORTE SABATINO (plan_v3 F3 / M3.2).

Una foto semanal del escuadrón EN VIVO, con las metricas que costaron
descubrir: friccion real, cobertura, diversidad, y comparacion contra
BTC-HOLD. Solo lee: no toca estado, no gasta K.

Correr: .venv/bin/python analysis/weekly.py [dias]
"""
import csv, json, os, sys, statistics as st
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))
import squad as Q
import seeds_crypto as SC


def parse(t):
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except Exception:
        return None


def main(days=7):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    px = {p: (Q.load_hourly(p)[0] or [0])[-1] for p in SC.PAIRS}
    st_j = json.load(open(os.path.join(ROOT, "bot", "squad_state.json")))

    trades = defaultdict(list)
    tp = os.path.join(ROOT, "logs", "squad_trades.csv")
    if os.path.exists(tp):
        for r in csv.DictReader(open(tp)):
            d = parse(r.get("utc", ""))
            if d and d >= since:
                trades[r.get("bot", "")].append(r)

    print(f"=== REPORTE SEMANAL · ultimos {days} dias · "
          f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC ===\n")

    # friccion real, desde px*units (notional verdadero, no estimado)
    tot_fee = tot_not = 0.0
    for rs in trades.values():
        for r in rs:
            try:
                tot_fee += float(r.get("fee") or 0)
                tot_not += float(r["px"]) * float(r["units"])
            except (KeyError, ValueError):
                pass
    print(f"{'bot':16s} {'equity':>10s} {'vs 3000':>8s} {'ops':>4s} "
          f"{'comision':>9s} {'posic':>6s}")
    print("-" * 60)
    tot_eq = 0.0
    for n in SC.SEEDS:
        b = st_j["bots"].get(n)
        if not b:
            continue
        eq = b.get("cash", 0) + sum(u * px.get(p, 0)
                                    for p, u in (b.get("units") or {}).items())
        tot_eq += eq
        fee = sum(float(r.get("fee") or 0) for r in trades.get(n, []))
        print(f"{n:16s} {eq:>10,.2f} {eq/3000-1:>+7.2%} "
              f"{len(trades.get(n, [])):>4d} {fee:>9,.2f} "
              f"{len(b.get('units') or {}):>5d}")
    n_bots = len(SC.SEEDS)
    print("-" * 60)
    print(f"{'TOTAL':16s} {tot_eq:>10,.2f} {tot_eq/(3000*n_bots)-1:>+7.2%}")

    # benchmark: BTC-HOLD sobre el mismo periodo
    cl, ts = Q.load_hourly("BTC-USD")
    idx = next((i for i, t in enumerate(ts)
                if datetime.fromtimestamp(t, timezone.utc) >= since), 0)
    if cl and idx < len(cl) - 1:
        bh = cl[-1] / cl[idx] - 1
        mine = tot_eq / (3000 * n_bots) - 1
        print(f"\nBTC-HOLD mismo periodo: {bh:+.2%}   escuadron: {mine:+.2%}"
              f"   diferencia: {mine-bh:+.2%}")

    if tot_not:
        print(f"\nFRICCION REAL (px x units, no estimada): "
              f"{tot_fee:,.2f} sobre {tot_not:,.2f} movidos "
              f"= {tot_fee/tot_not:.3%} por lado")

    # cobertura: cuantos bots operaron de verdad
    active = sum(1 for n in SC.SEEDS if trades.get(n))
    print(f"COBERTURA: {active}/{n_bots} bots operaron esta semana")

    # diversidad
    try:
        sys.path.insert(0, os.path.join(ROOT, "bot"))
        import diversity as D
        r = D.analyse(os.path.join(ROOT, "bot", "squad_state.json"))
        if r:
            print(f"DIVERSIDAD: solapamiento {r['overlap_invested']:.2f} · "
                  f"{r['distinct']} carteras distintas · "
                  f"efectiva {r['effective']:.0%}")
            for book, mem in r["clusters"]:
                if len(mem) > 1:
                    print(f"  CLON x{len(mem)}: {', '.join(sorted(mem))}")
    except Exception as e:
        print(f"diversidad no disponible: {e}")

    print("\nRecordatorio: todas las semillas armadas son CONTROL "
          "(0 PASS en 96 examenes). Esto es una linea base, no una "
          "estrategia con derecho a capital real.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
