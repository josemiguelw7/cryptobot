"""
MFE / MAE POR OPERACION (Tanda A, 2026-08-07).

Para cada operacion cerrada del examen: cuanto llego a ir A FAVOR
(MFE, maximum favourable excursion) y cuanto EN CONTRA (MAE) antes de
cerrar. Responde una pregunta que el P&L solo no puede:

  - Si MFE es grande y el resultado chico -> el problema son las
    SALIDAS: la posicion gano y devolvio la ganancia. Un trailing stop
    lo arregla sin agregar operaciones.
  - Si MAE es grande antes de recuperar -> las entradas llegan
    temprano. Confirmacion (velas) ayudaria.
  - Si ambos son chicos -> el mercado no se movio lo suficiente para
    pagar el peaje. Es friccion, no timing.

Puro analisis: reusa el motor del examen, no escribe nada.
"""
import os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backtest"))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam_1h as X

FEE, SLIP = 0.0, 0.0042      # coste por lado, igual que el examen


def excursions(strat, closes, a, b):
    """Recorre la ventana replicando la logica del examen y anota, por
    cada posicion abierta, la excursion maxima a favor y en contra."""
    ctx = {"weight": 0.0, "entry_price": None}
    out, entry, mfe, mae = [], None, 0.0, 0.0
    tail = getattr(strat, "tail", None)
    for i in range(a, b):
        lo = max(0, i + 1 - tail) if tail else 0
        try:
            if getattr(strat, "wants_bars", False):
                sig = 1.0 if ctx["weight"] > 0 else 0.0
            else:
                sig = strat.step(closes[lo:i + 1], ctx)
        except Exception:
            sig = 0.0
        px = closes[i]
        if entry is not None:
            r = px / entry - 1
            mfe, mae = max(mfe, r), min(mae, r)
        if sig > 0 and entry is None:
            entry, mfe, mae = px, 0.0, 0.0
            ctx["weight"], ctx["entry_price"] = 1.0, px
        elif sig <= 0 and entry is not None:
            out.append((px / entry - 1, mfe, mae))
            entry, ctx["weight"], ctx["entry_price"] = None, 0.0, None
    return out


def main():
    names = sys.argv[1:] or list(X.SEEDS.SEEDS)
    data = {p: X.load_hourly(p) for p in X.PAIRS}
    print(f"{'semilla':16s} {'ops':>5s} {'result.':>8s} {'MFE med':>8s} "
          f"{'MAE med':>8s} {'devuelto':>9s}  diagnostico")
    print("-" * 82)
    for n in names:
        strat = X.SEEDS.get(n)
        if getattr(strat, "wants_bars", False):
            print(f"{n:16s}    (semilla de barras: omitida)")
            continue
        allt = []
        for p in X.PAIRS:
            cl, ts = data[p]
            if len(cl) < strat.warmup + 200:
                continue
            allt += excursions(strat, cl, strat.warmup, len(cl))
        if not allt:
            print(f"{n:16s}     0  (sin operaciones cerradas)")
            continue
        res = [t[0] for t in allt]
        mfe = [t[1] for t in allt]
        mae = [t[2] for t in allt]
        mres, mmfe, mmae = st.median(res), st.median(mfe), st.median(mae)
        giveback = (mmfe - mres)
        if mmfe > 0.02 and giveback > mmfe * 0.6:
            diag = "SALIDAS: gana y devuelve"
        elif mmae < -0.02:
            diag = "ENTRADAS: llega temprano"
        elif mmfe < 0.012:
            diag = "FRICCION: no se mueve lo suficiente"
        else:
            diag = "mixto"
        print(f"{n:16s} {len(allt):>5d} {mres:+8.2%} {mmfe:+8.2%} "
              f"{mmae:+8.2%} {giveback:+9.2%}  {diag}")
    print()
    print("Umbral de referencia: hace falta ~0.84% solo para empatar.")


if __name__ == "__main__":
    main()
