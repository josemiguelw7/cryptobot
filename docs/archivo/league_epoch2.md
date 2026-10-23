# Liga diaria — época 2 ($3,000)

**2026-08-02.** Por decisión del owner, las slices de paper de la liga
se alinean con la asignación real planificada: $3,000 iniciales por
bot (antes $10,000). Los $3,000 son asignación inicial, no techo.

- La época 1 ($10K, 2026-07-24 → 2026-08-02, 9 días forward) queda
  **archivada íntegra** en `archive/league_epoch1_10k/` y en el
  historial git. No se borra ni se reescribe.
- El reloj de 90 días de `docs/success_criteria.md` **reinicia hoy**
  para la época 2. Mezclar épocas con capital distinto ensuciaría los
  retornos; reiniciar es la lectura honesta.
- Los criterios NO cambian (son relativos: batir BTC-HOLD, drawdown
  menor, después de fees, sin circuit breaker). El ratchet sigue.
- El import legacy de MOM-ROT se retiró de `league.py`: en época 2
  todos los miembros nacen frescos e iguales.
