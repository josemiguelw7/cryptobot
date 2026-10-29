# Prerregistro · Prueba hacia adelante de ABU v2 (BORRADOR para aprobación de Jose y Oscar)

Fecha del borrador: 2026-10-29 · Estado: **BORRADOR, sin firmar, sin sello**. Nada de lo que dice aquí tiene efecto hasta que Jose y Oscar lo aprueben; entonces se sella con OpenTimestamps y se registra en `futures/lab/registry/studies.jsonl` como estudio `forward_abu_v2` con **1 intento declarado**.

## 1. Qué es y qué no es

Esto es la única prueba que todavía puede sorprender: la misma regla, juzgada en días que **nadie** ha visto al elegirla. Los 576 días de diseño ya fueron estudiados 1,224 veces; otra prueba sobre ellos solo mueve el pasado. El examen sellado (132 sesiones, 2026-04-22 → 2026-10-22) **sigue cerrado y no es parte de esto**: se guarda para una sola apertura futura, si alguna vez hay una candidata que la merezca.

No es una búsqueda. No hay variantes, no hay vecinos, no hay "segunda oportunidad". Es un solo examen, con la regla y la línea de aprobación escritas antes de mirar.

## 2. La regla, congelada (no se toca)

- **Estrategia:** ABU v2, exactamente como está sellada en `futures/strategies/v20.json` (SHA-256 `ba767e39c96e4b6bb3696bc9ee54fb14378e06166322e75193bffeb3d53be7a6`, con su `.ots`). Código: `engine/strategies/v17.py` (señales) + `v18.py` (2 contratos).
- **Parámetros:** los de P031/P050: near_ticks 4, max_advance 2, confirm_s 60, away_ticks 4, stop_beyond 4, stop 12–32, rr 2.0, max_min 15, min_elapsed_s 0, dev_min_elapsed_s 600, dev_cooldown_s 600, rel_pct 90, rel_lookback_s 3600, floor_frac 0.5, last_sec 55800, data_end_sec 56700.
- **Ventana y reglas comunes:** `run_test.py::RULES_WINDOW[("ABU", 2)]`: entradas 09:30–15:30 ET, cierre forzado 15:45, 2 contratos, máximo 6 operaciones al día, parada tras 3 pérdidas seguidas, sin entradas en ventanas de noticias (`futures/news.json`, actualizado con las fechas nuevas **antes** de puntuar, con el mismo criterio de siempre: Fed, CPI, NFP).
- **Motor:** 1.2.0 (commit `561152b3` o posterior **sin cambios de comportamiento**: la dorada de ABS v1 `82db41a8…` y la del perfil `c8a33787…` deben seguir idénticas el día de la puntuación). Si el motor cambia por la revisión de llenados y rollos (`sim.py`), la versión que puntúa es la que esté vigente, y **se declara aquí antes de puntuar**; nunca se puntúa con dos motores y se elige.
- **Costos:** `futures/costs.json` base: $3.78 ida y vuelta + 1 tick por lado ($13.78 por operación); estrés con 2 ticks por lado.

## 3. Los datos nuevos: cómo entran y quién los mira (nadie)

- **Fuente:** las mismas exportaciones de ATAS/Rithmic (Radtak Tick Downloader) que alimentan el laboratorio, copiadas a `/srv/lab/data/raw/NQ/` y pasadas por el **mismo** lector canónico y la **misma** auditoría de sesiones (`sessions_audit.py`: huecos ≥ 60 s aviso, ≥ 120 s excluida; DST; ventana 09:30–16:00).
- **Primer día elegible:** 2026-10-23 (el primero después del último día sellado). Todo lo anterior queda fuera.
- **Días de rollo:** la regla del laboratorio dice que el rollo es parte del trading. Para que un día de rollo entre, la exportación debe traer **los dos contratos**; si no, la sesión se excluye por la misma regla del manifiesto actual ("excluidos hasta tener el segundo contrato"), y se publica el motivo. Esto se fija ahora, no al ver resultados.
- **Solo agregar:** cada sesión nueva se anota en un libro `futures/lab/registry/forward_sessions.jsonl` (fecha, huella SHA-256 del archivo canónico, estado ok/aviso/excluida, fecha de ingreso) con cadena de huellas, igual que el registro de intentos. No se reordena, no se recorta, no se "limpia" después.
- **Prohibido mirar:** hasta el día de la puntuación, **ninguna** persona ni programa (Claude incluido, el investigador incluido, el mapa de señales incluido) carga una sesión posterior al 2026-10-22 en ninguna prueba, humo, estudio ni gráfica. El motor lo refuerza: `config.design_sessions()` sigue terminando en el manifiesto de diseño, y las sesiones nuevas viven en una carpeta aparte que solo lee el puntuador del prerregistro. Lo único que se publica mientras tanto es el **conteo** de sesiones ingresadas (sin ningún número de P&L ni de señales).

## 4. Cuándo se puntúa (una sola vez)

- **Tamaño mínimo:** **100 operaciones** de ABU v2 en las sesiones nuevas válidas (el mínimo del protocolo para que un veredicto cuente). A la tasa de diseño (181 operaciones en 576 sesiones, ≈ 0.31 por sesión) eso son **≈ 320 sesiones, alrededor de 15 meses**. Se escribe esta expectativa ahora para que nadie la "ajuste" después.
- Como no se puede contar operaciones sin mirar, el disparador operativo es por sesiones: se puntúa al llegar a **320 sesiones válidas**. Si en ese momento hay menos de 100 operaciones, el veredicto es **insuficiente** y se declara; no se extiende "un poco más" para alcanzar 100.
- **Tope de calendario:** si a los **24 meses** desde la aprobación no se llegó a 320 sesiones válidas (p. ej., por huecos de datos), se puntúa con lo que haya y se declara `insuficiente` si corresponde. No hay prórroga.
- **Una vez.** Dos corridas en contenedor limpio para reproducibilidad, como siempre; un solo resultado publicado con id nuevo.

## 5. La línea de aprobación (escrita antes)

Se aplican los criterios **ya codificados** en `run_test.py::verdict()` y `protocol.json` v3, sin cambios:

- **Muerta** (afirmación hacia adelante refutada): ganancia neta ≤ 0 con costos base, **o** p vs RAND > 0.20, **o** rompe el MLL en > 50 % de los arranques.
- **Pasa** solo si TODO se cumple: p vs RAND ≤ 0.05; p vs RAND2 ≤ 0.05; neto de estrés > 0 con p ≤ 0.10; ningún año con ≥ 30 operaciones termina negativo; Topstep ≥ 50 % de los arranques (consistencia 50 %, con MAE intradía) y mayor que el RAND; DSR ≥ 0.95.
- **No pasa:** cualquier otro caso. Se publica con todas las causas.

**Sobre el DSR en esta prueba:** la regla se eligió en los datos de diseño con 1,224 intentos; en los datos nuevos este es **un** examen prerregistrado, así que el DSR se calcula con **N = 1** (equivale al PSR). Esto se decide ahora, por escrito, y **se pide opinión al revisor externo antes de firmar**: si el revisor argumenta que N debe incluir los intentos de diseño, se adopta la versión más estricta antes de la aprobación, nunca después.

**Lo que NO se hace al puntuar:** no se quitan días, no se comparan remanentes con bandas de RAND, no se cambian umbrales, no se "mira por nivel" para rescatar una parte. La hoja completa se publica igual que siempre; la lectura es la de arriba.

## 6. Qué pasa con cada resultado

- **Pasa:** sigue sin tocar dinero real. Va al comité (vota Oscar). El siguiente paso posible es un periodo hacia adelante adicional o cuenta de evaluación en simulación con las reglas reales; eso se prerregistra aparte.
- **No pasa:** ABU v2 se archiva como "ventaja de diseño no confirmada hacia adelante". No se repite con vecinos sobre los mismos días nuevos: esos días quedan tan gastados como los de diseño para cualquier cosa parecida a ABU.
- **Muerta:** igual que no pasa, y además se escribe en `decisions.md` que la afirmación histórica de P031 no se sostuvo.
- **Insuficiente:** se declara; los días **no** se reutilizan para otra regla sin un prerregistro nuevo.

## 7. Cambios y vigencia

- Este documento solo puede **endurecerse** antes de puntuar (criterios más estrictos, no menos). Cualquier cambio después de ingresar la primera sesión nueva se escribe en `decisions.md` con una semana de espera, como manda la carta.
- Cualquier lectura anticipada de los datos nuevos, por quien sea, **anula** la prueba: los días leídos pasan a ser días de diseño y el reloj vuelve a cero.
- Mientras tanto el laboratorio hace solo dos cosas: ingresar y anotar sesiones nuevas, y revisar el instrumento de medida (`sim.py`: llenados, deslizamiento en noticias, rollos). Ninguna de las dos elige estrategia.

## 8. Firmas

- Jose Miguel: ☐ aprobado · fecha ____
- Oscar: ☐ aprobado · fecha ____
- Sello OTS del archivo aprobado: ____ · Estudio registrado: `forward_abu_v2`, 1 intento declarado · Commit: ____
