"""
SIMULACION DEL MOTOR v3 (plan_v3 F2, modo prueba).

Aplica las tres reglas propuestas sobre las señales REALES de los bots
armados y mide que habria cambiado. No arma nada, no toca estado, no
gasta K. Responde con datos, no con suposiciones:

  E3.1 MIN_HOLD_BARS  -> cuantas operaciones se evitarian
  E3.2 MAX_CORR 0.70  -> rompe los clones de verdad?
  E3.3 MAX_POS 6      -> mas diversificacion real?
"""
import itertools, json, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))
import squad as Q
import seeds_crypto as SC

MIN_HOLD, MAX_CORR, NEW_MAX_POS = 168, 0.70, 6


def corr(a, b):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((x - mb) ** 2 for x in b) ** 0.5
    return 0.0 if va * vb == 0 else sum(
        (a[i] - ma) * (b[i] - mb) for i in range(n)) / (va * vb)


def main():
    rets, closes = {}, {}
    for p in SC.PAIRS:
        cl, _ = Q.load_hourly(p)
        closes[p] = cl
        rets[p] = [cl[i] / cl[i - 24] - 1 for i in range(24, len(cl))][-1500:]

    C = {(a, b): corr(rets[a], rets[b])
         for a, b in itertools.combinations(SC.PAIRS, 2)}

    def cc(a, b):
        return C.get((a, b)) if (a, b) in C else C.get((b, a), 0.0)

    print("=== E3.2: tope de correlacion 0.70 ===")
    print(f"  correlacion mediana del universo: {st.median(C.values()):.2f}")
    over = [k for k, v in C.items() if v > MAX_CORR]
    print(f"  pares por encima de 0.70: {len(over)} de {len(C)}")

    # que carteras serian LEGALES bajo el tope
    legal = [c for c in itertools.combinations(SC.PAIRS, 3)
             if all(cc(a, b) <= MAX_CORR
                    for a, b in itertools.combinations(c, 2))]
    print(f"  carteras de 3 posibles: {len(list(itertools.combinations(SC.PAIRS,3)))}"
          f"  ·  LEGALES bajo el tope: {len(legal)}")
    legal6 = [c for c in itertools.combinations(SC.PAIRS, 6)
              if all(cc(a, b) <= MAX_CORR
                     for a, b in itertools.combinations(c, 2))]
    print(f"  carteras de 6 posibles: {len(list(itertools.combinations(SC.PAIRS,6)))}"
          f"  ·  LEGALES bajo el tope: {len(legal6)}")

    print("\n=== carteras actuales bajo la regla ===")
    stj = json.load(open(os.path.join(ROOT, "bot", "squad_state.json")))
    viol = 0
    for n, b in stj["bots"].items():
        held = sorted(b.get("units") or {})
        if len(held) < 2:
            continue
        bad = [(a, c, cc(a, c))
               for a, c in itertools.combinations(held, 2)
               if cc(a, c) > MAX_CORR]
        if bad:
            viol += 1
            worst = max(bad, key=lambda x: x[2])
            print(f"  {n:16s} {' '.join(x.split('-')[0] for x in held)}"
                  f"   VIOLA: {worst[0].split('-')[0]}/"
                  f"{worst[1].split('-')[0]} = {worst[2]:.2f}")
    print(f"  -> {viol} de {len(stj['bots'])} bots tendrian que cambiar cartera")

    print("\n=== E3.1: minimo de tenencia 168h ===")
    import csv
    tp = os.path.join(ROOT, "logs", "squad_trades.csv")
    kept = cut = 0
    if os.path.exists(tp):
        for r in csv.DictReader(open(tp)):
            if r.get("action") != "SELL":
                continue
            try:
                h = float(r.get("hold_h") or 0)
            except ValueError:
                continue
            if h < MIN_HOLD:
                cut += 1
            else:
                kept += 1
    tot = kept + cut
    if tot:
        print(f"  ventas cerradas: {tot}  ·  bajo 168h: {cut} ({cut/tot:.0%})")
        print(f"  -> el minimo de tenencia habria BLOQUEADO {cut/tot:.0%} "
              f"de las salidas, ahorrando ~{cut} pares de comisiones")
    else:
        print("  aun no hay ventas cerradas en el log")


if __name__ == "__main__":
    main()
