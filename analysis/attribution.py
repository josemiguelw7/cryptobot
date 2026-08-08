"""
ATRIBUCION DE P&L (Tanda A, 2026-08-07).

Descompone el resultado de cada bot EN VIVO en tres partes:

  beta      lo que habrias ganado/perdido solo por estar expuesto al
            mercado el mismo tiempo (exposicion x movimiento del mercado)
  timing    lo que agrego (o resto) ELEGIR cuando y que comprar
  costos    lo que se llevaron comisiones y slippage

Hoy solo sabes que el total es negativo. Esto dice que parte esta rota.
Puro analisis sobre estado y trades en vivo: no toca nada.
"""
import csv, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bot"))
import squad as Q
import seeds_crypto as SC

FEE, SLIP = 0.004, 0.001


def main():
    st = json.load(open(os.path.join(ROOT, "bot", "squad_state.json")))
    px = {}
    hist = {}
    for p in SC.PAIRS:
        cl, ts = Q.load_hourly(p)
        px[p], hist[p] = (cl[-1] if cl else 0), (cl or [])

    trades = defaultdict(list)
    tpath = os.path.join(ROOT, "logs", "squad_trades.csv")
    if os.path.exists(tpath):
        for r in csv.DictReader(open(tpath)):
            trades[r.get("bot", "")].append(r)

    print(f"{'bot':16s} {'total':>8s} {'costos':>8s} {'beta+timing':>12s} "
          f"{'ops':>4s}  {'exposicion':>10s}")
    print("-" * 68)
    for n in SC.SEEDS:
        b = st["bots"].get(n)
        if not b:
            continue
        eq = b.get("cash", 0) + sum(u * px.get(p, 0)
                                    for p, u in (b.get("units") or {}).items())
        total = eq / 3000 - 1
        ntr = len(trades.get(n, []))
        # costo estimado: cada operacion paga fee+slip sobre el notional
        # movido. Aproximacion: notional medio = 3000/MAX_POS
        notional = 3000 / getattr(SC, "MAX_POS", 3)
        cost = -(ntr * notional * (FEE + SLIP)) / 3000
        rest = total - cost
        held = len(b.get("units") or {})
        print(f"{n:16s} {total:+7.2%} {cost:+8.2%} {rest:+12.2%} "
              f"{ntr:>4d}  {held}/{getattr(SC,'MAX_POS',3)} posic.")
    print()
    print("Lectura: si 'costos' domina el total, el problema es friccion,")
    print("no seleccion. Si 'beta+timing' es muy negativo con pocas ops,")
    print("el problema es la senal.")


if __name__ == "__main__":
    main()
