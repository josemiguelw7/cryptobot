# Autopsias de retiro — Época 1 (cripto)

Generado por `ops/autopsy.py` desde los logs. Descriptivo: no hay
aquí ninguna propuesta de cambio. Regla aplicada: −10% desde el pico
(charter s8). `h_rand_72` se incluye como referencia de ruido.

## h_trend_168
- Equity final $3,370.93 (+12.4% vida) · pico $3,753.53 el 2026-08-22 · caída desde pico -10.2%
- 32 operaciones cerradas · aciertos 12% · mediana de duración 18h
- Bruto $+676.82 · comisiones $250.05 · neto $+370.92
- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: 6
- Salidas: {'signal': 23, 'stop': 9} · causas de pérdida: {'signal_reversal': 17, 'fees_spread': 6, 'stop_hit': 5}
- Últimas 10 antes del cierre: neto $-166.05, 1/10 ganadoras

## h_cross_24_168
- Equity final $3,472.90 (+15.8% vida) · pico $3,876.93 el 2026-08-22 · caída desde pico -10.4%
- 21 operaciones cerradas · aciertos 24% · mediana de duración 81h
- Bruto $+681.66 · comisiones $172.95 · neto $+472.89
- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: 2
- Salidas: {'signal': 12, 'stop': 9} · causas de pérdida: {'signal_reversal': 11, 'fees_spread': 2, 'stop_hit': 3}
- Últimas 10 antes del cierre: neto $-99.31, 2/10 ganadoras

## h_volbrk_24_96
- Equity final $3,267.19 (+8.9% vida) · pico $3,659.51 el 2026-08-22 · caída desde pico -10.7%
- 23 operaciones cerradas · aciertos 35% · mediana de duración 26h
- Bruto $+488.42 · comisiones $184.56 · neto $+267.18
- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: 0
- Salidas: {'signal': 17, 'stop': 6} · causas de pérdida: {'signal_reversal': 12, 'stop_hit': 3}
- Últimas 10 antes del cierre: neto $+274.34, 3/10 ganadoras

## h_nearhi_168
- Equity final $3,392.58 (+13.1% vida) · pico $3,790.11 el 2026-08-22 · caída desde pico -10.5%
- 29 operaciones cerradas · aciertos 24% · mediana de duración 4h
- Bruto $+708.74 · comisiones $256.18 · neto $+392.58
- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: 6
- Salidas: {'signal': 23, 'stop': 6} · causas de pérdida: {'signal_reversal': 15, 'fees_spread': 6, 'stop_hit': 1}
- Últimas 10 antes del cierre: neto $-141.17, 2/10 ganadoras

## h_rand_72  (control, NO retirado)
- Equity final $3,506.99 (+16.9% vida) · pico $3,828.51 el 2026-08-25 · caída desde pico -8.4%
- 19 operaciones cerradas · aciertos 37% · mediana de duración 74h
- Bruto $+713.45 · comisiones $167.76 · neto $+506.98
- Operaciones ganadoras en bruto que las comisiones volvieron pérdida: 2
- Salidas: {'signal': 14, 'stop': 5} · causas de pérdida: {'signal_reversal': 6, 'fees_spread': 2, 'stop_hit': 4}
- Últimas 10 antes del cierre: neto $+364.66, 3/10 ganadoras

## Lectura conjunta (escrita 2026-09-18)
1. Los cuatro retirados hicieron pico EL MISMO DÍA (2026-08-22) y cayeron
   juntos. No eran cuatro estrategias: eran una sola apuesta (largo en el
   rally de agosto) con cuatro nombres. Confirma el hallazgo de diversidad.
2. Aciertos del 12-35%. Todo el beneficio viene de un puñado de
   operaciones grandes en un solo tramo alcista; fuera de él, 1-3 de cada
   10 ganan. Eso es exposición al mercado, no señal.
3. Las comisiones se llevaron el 25-37% del bruto de cada uno; 14
   operaciones ganadoras en bruto terminaron en pérdida neta.
4. 'signal_reversal' es la primera causa de pérdida en los cuatro: la
   salida por señal devuelve la ganancia. Es coherente con H1 y es el
   motivo del experimento de gemelos E2-SF. NO es aún evidencia: es la
   misma muestra que sugirió la hipótesis.
5. El control aleatorio tiene mejor neto, mejor tasa de acierto y menos
   comisiones que los cuatro. Esa frase queda literal.
Veredicto: retiro correcto bajo s8. Ninguno se reanuda ni se renombra.
