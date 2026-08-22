# Petición de revisión independiente — paquete para revisor NO-Claude

**Fecha:** 2026-08-22 · **Estado:** ABIERTA, sin revisor asignado
**Documento previo:** `REVIEW.md` (misma petición, sin respuesta desde 2026-08-08)

---

## Por qué existe este documento

La "revisión externa" del 2026-08-08 la hizo otra instancia de Claude.
Eso no es un control independiente: es el mismo sistema evaluándose con
otro nombre. `REVIEW.md` ya lo dice.

El 2026-08-22 el problema se agravó. En una sola sesión, Claude:

1. midió el sistema,
2. interpretó las mediciones,
3. redactó las propuestas de cambio,
4. recomendó al propietario cuáles aprobar,
5. implementó las aprobadas,
6. y escribió esta misma petición.

No queda nadie fuera del circuito. El propietario ha declarado
explícitamente que no es programador y que depende de Claude para las
decisiones técnicas. Esa combinación —un evaluador único y un
propietario que no puede auditarlo— es el riesgo de gobernanza más
grande del proyecto, por encima de cualquier problema de estrategia.

## Qué se busca

Un revisor que sea **una de estas dos cosas**:

- una arquitectura de IA distinta (no Anthropic), o
- una persona con experiencia en finanzas cuantitativas

No sirve otra instancia de Claude, ni con prompt distinto, ni con
contexto distinto, ni afirmando ser adversarial.

## Preguntas concretas para el revisor

Ordenadas por lo que más daño haría si estuviera mal.

**P1 — ¿El backtest point-in-time es realmente point-in-time?**
El proyecto nació de un +354% falso contra un −90% honesto. El
2026-08-11 se anularon 11 veredictos de acciones por sesgo de barra en
formación (792 violaciones en 799 decisiones). ¿Queda algún camino de
lookahead sin cerrar? Ver `ops/lookahead_audit.py`, `data/pit_*.py`.

**P2 — ¿El sistema de exámenes de un solo disparo es sólido?**
Contador K global compartido, prohibición de reexaminar nombres,
holdout de 120 días, estrés de comisiones 1.5×. ¿Se puede sacar un
aprobado de ahí sin habilidad real? Ver `docs/intraday_success_criteria.md`
(bloqueado, sha256 `072b78c7...`), `backtest/results/exam_ledger.csv`.

**P3 — ¿Los módulos de medición del 2026-08-22 son realmente inocuos?**
`ops/bench_bh.py` y `ops/counterfactual.py` se declaran "solo lectura".
¿Lo son? ¿Puede alguno filtrar información hacia una decisión de
trading, aunque sea indirectamente vía el dashboard y el propietario?

**P4 — ¿El contrafactual está bien construido?**
Calcula el retorno a `hold_h` de cada señal rechazada. ¿Introduce sesgo
de supervivencia, o de horizonte, o compara peras con manzanas al usar
el `hold_h` declarado en vez del tiempo de tenencia real?

**P5 — La pregunta incómoda: ¿vale la pena seguir?**
Cripto: 0 de 11 bots superan comprar-y-sostener (+28.60%). Acciones: 2
de 11 lo superan, y las tres pistas están negativas en absoluto. El bot
ALEATORIO es el #1 de cripto. Si un revisor independiente concluye que
la evidencia dice "esto no funciona y no va a funcionar a estos costes",
eso es un resultado legítimo y el propietario quiere oírlo.

## Qué NO se pide

No se pide una estrategia. No se pide optimizar parámetros. No se pide
una opinión sobre si el mercado es predecible. Se pide auditar si el
aparato que produce veredictos puede producir un veredicto falso.

## Materiales

| Qué | Dónde |
|---|---|
| Charter (bloqueado, inmutable) | `docs/intraday_success_criteria.md` |
| Gobernanza de dos niveles | `docs/charter_v2.md` |
| Registro de decisiones | `docs/decisions.md` |
| Ledger de exámenes (append-only) | `backtest/results/exam_ledger.csv` |
| Auditoría de lookahead | `ops/lookahead_audit.py` |
| Motor cripto / acciones | `bot/squad.py`, `bot/squad_stocks.py` |
| Módulos de medición nuevos | `ops/bench_bh.py`, `ops/counterfactual.py` |
| Cable trampa | `ops/selfcheck.py` |
| Petición previa sin respuesta | `REVIEW.md` |

## Conflicto de interés declarado

Este documento lo redactó Claude, que es el sujeto de la revisión que
solicita. Un revisor debería tratar la lista de preguntas de arriba
como **sospechosa por construcción**: las preguntas que Claude no supo
hacerse son, por definición, las que no están en esta lista.
