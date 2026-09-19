"""Retirement autopsies (charter s8): descriptive only, from the logs.
Writes docs/autopsias_epoca1.md. Read-only on all state. No thresholds."""
import csv, os, json, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
st = json.load(open(os.path.join(ROOT, "bot", "squad_state.json")))
benched = [n for n, b in st["bots"].items() if b.get("benched")]

eq = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(ROOT, "logs", "squad_equity.csv"))):
    eq[r["bot"]].append((r["time"], float(r["equity"])))
tr = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(ROOT, "logs", "squad_trades.csv"))):
    tr[r["bot"]].append(r)

out = ["# Autopsias de retiro — Época 1 (cripto)", "",
       "Generado por `ops/autopsy.py` desde los logs. Descriptivo: no hay",
       "aquí ninguna propuesta de cambio. Regla aplicada: −10% desde el pico",
       "(charter s8). `h_rand_72` se incluye como referencia de ruido.", ""]
for n in benched + ["h_rand_72"]:
    e = eq[n]; peak = max(e, key=lambda x: x[1]); last = e[-1][1]
    sells = [t for t in tr[n] if t["action"] == "SELL" and t["net_pnl"]]
    net = [float(t["net_pnl"]) for t in sells]
    gross = sum(float(t["gross_pnl"] or 0) for t in sells)
    fees = sum(float(t["fee"] or 0) for t in tr[n])
    wins = [x for x in net if x > 0]
    kinds = collections.Counter(t["exit_kind"] for t in sells)
    causes = collections.Counter(t["loss_cause"] for t in sells if float(t["net_pnl"]) <= 0)
    hold = sorted(float(t["hold_h"] or 0) for t in sells)
    # last 10 closed trades before the bench
    tail = net[-10:]
    flat = sum(1 for t in sells if float(t["gross_pnl"] or 0) > 0 >= float(t["net_pnl"]))
    out += [f"## {n}" + ("  (control, NO retirado)" if n == "h_rand_72" else ""),
            f"- Equity final ${last:,.2f} ({(last/3000-1)*100:+.1f}% vida) · pico "
            f"${peak[1]:,.2f} el {peak[0][:10]} · caída desde pico {(last/peak[1]-1)*100:.1f}%",
            f"- {len(sells)} operaciones cerradas · aciertos {100*len(wins)/max(1,len(net)):.0f}% · "
            f"mediana de duración {hold[len(hold)//2] if hold else 0:.0f}h",
            f"- Bruto ${gross:+,.2f} · comisiones ${fees:,.2f} · neto ${sum(net):+,.2f}",
            f"- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: {flat}",
            f"- Salidas: {dict(kinds)} · causas de pérdida: {dict(causes)}",
            f"- Últimas 10 antes del cierre: neto ${sum(tail):+,.2f}, "
            f"{sum(1 for x in tail if x>0)}/10 ganadoras", ""]
open(os.path.join(ROOT, "docs", "autopsias_epoca1.md"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
