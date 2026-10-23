# Agenda — revisión del sábado 2026-10-04, 09:00 America/Chicago

Preparada 2026-10-01. Nada de esto se ejecuta entre semana (P5 del charter).
Pasaron dos sábados sin revisión (09-20 y 09-27).

## Estado al 2026-10-01
- Cripto: $34,706 (+5.2%) vs B&H +44.9%. 2/11 activos. Lidera el aleatorio h_rand_72.
- Acciones: $32,414 (-1.8%) vs B&H +2.7%. 11/11 activos. s_rand_21 es 2.o.
- Época 1 sigue como línea base hasta H1 (2026-11-21).

## Decisiones (en orden; cada una necesita firma escrita en decisions.md)
1. D4 / auditoría no-Claude: hacerla (audit_chatgpt.zip + docs/AUDITORIA_CHATGPT.txt)
   o retirarla formalmente como bloqueo. Sin esto, Época 2 no se firma (§4 del borrador).
2. PEND-2: MAX_CORR=0.70 vs MAX_POS=6 son incompatibles. Elegir la interpretación
   menos estricta, cuantificar el coste, y dejar el trinquete para apretar después.
3. Época 2: firmar o rechazar docs/epoch2_prereg_BORRADOR.md
   (SF + INS + RISK + RAND). Pendientes del §4:
   [ ] Jose Miguel explica con sus palabras cada candidato (§6.1)
   [ ] Horizonte y nº mínimo de operaciones por candidato
   [ ] Descargador EDGAR Form 4 — hecho en 43ac61b, verificar guarda de lookahead
4. PEND-3 (rediseño acciones): solo si 1 queda resuelto.

## Operativo (no requiere firma)
- Liga pública desplegada en Vercel (proyecto cryptobot-liga, raíz site/).
  Se actualiza solo cuando se hace commit+push de site/index.html.
  Decidir si daily.py debe hacer commit automático de site/index.html cada hora.
