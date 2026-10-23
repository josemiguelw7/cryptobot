# REVIEW.md — petición de revisión externa

**Fecha:** 2026-08-08 · **Repo:** `josemiguelw7/cryptobot` · **Estado:** papel, sin capital real

Este documento existe para que una IA (o persona) externa revise el proyecto.
Lo escribió Claude, que es también quien escribió casi todo el código —
así que quien revise debe asumir que **tiene puntos ciegos por construcción**.

El dueño del proyecto (Jose) no es programador y ha estado aprobando decisiones
técnicas que no siempre comprende del todo. Una de las funciones de esta
revisión es corregir ese desequilibrio.

---

## 0. Qué es este proyecto en una frase

Un sistema de trading algorítmico **en papel** cuyo objetivo declarado no es
ganar dinero, sino **no engañarse**: comprobar si alguna estrategia tiene ventaja
real antes de arriesgar capital. Hasta hoy: **0 estrategias aprobadas de 96 intentos.**

Motivación original: un backtest ingenuo mostró **+354%**; la versión honesta
(point-in-time, sin mirar el futuro) del mismo sistema mostró **−90%**.
Todo el andamiaje de gobernanza nace de esa diferencia.

## 1. Cómo está organizado el repo

| Ruta | Qué es |
|---|---|
| `bot/strategies.py` | Todas las estrategias ("semillas"). Fuente única de verdad. |
| `bot/squad.py` | Motor: carga velas, pide señales, aplica costes, escribe estado. |
| `bot/squad_stocks.py` | Adaptador de acciones (sobreescribe globals de `squad.py`). |
| `bot/seeds_crypto.py`, `seeds_stocks.py` | Rosters ARMADOS (ola 1). |
| `bot/seeds_crypto_v3.py` | Roster propuesto (ola 3), `ARMED = False`. |
| `backtest/exam_1h.py` | **El examen.** El archivo más importante del repo. |
| `backtest/exam.py` | Simulador de ventanas compartido. |
| `backtest/validation.py` | Sharpe deflactado, umbral de suerte. |
| `backtest/results/exam_ledger.csv` | Registro permanente de veredictos. |
| `analysis/` | Herramientas de diagnóstico (7 scripts, todos de solo lectura). |
| `docs/` | Charter, criterios, propuestas pre-registradas, bitácora. |
| `archive/` | Generaciones descartadas, nunca borradas. |

## 2. Orden de lectura sugerido

1. `docs/intraday_success_criteria.md` — las reglas del examen (§5, criterios 1-10)
2. `backtest/exam_1h.py` — la implementación de esas reglas
3. `bot/strategies.py` — las estrategias examinadas
4. `bot/squad.py` — el motor que las ejecuta en vivo
5. `docs/plan_v3.md` — plan actual y su adenda del 2026-08-08
6. `analysis/*.py` — cómo se diagnostica

## 3. Principios que el sistema intenta respetar

- **W1.1 — la semilla examinada es byte-for-byte la que opera.** Si el examen
  y el motor difieren, el veredicto no significa nada.
- **Sin lookahead.** Solo velas CERRADAS (`t + 3600 <= now`). Ninguna decisión
  puede usar información que no existía en ese momento.
- **Un examen por nombre, para siempre.** Re-examinar es "probar hasta que dé".
  Los nombres quemados no vuelven.
- **K sube con cada intento.** El umbral de suerte crece con el número de
  pruebas (múltiple testing). Hoy K=96, umbral Sharpe ≈ 1.25.
- **Ratchet §2.1 — las reglas solo se endurecen, nunca se aflojan.**
- **Pre-registro.** Expectativas escritas ANTES de correr. Ver
  `docs/seed_proposals_v2.md`, `docs/recert_2026-08-04.md`, `docs/plan_v3.md`.
- **Los controles nunca acceden a capital real.** Una semilla que falla el
  examen puede seguir operando en papel, pero jamás asciende.

## 4. Hechos medidos (no opiniones)

| Hallazgo | Valor | Dónde se midió |
|---|---|---|
| Veredictos | 0 PASS / 96 intentos | `backtest/results/exam_ledger.csv` |
| Fricción real | 0.401% por lado (0.4% teórico) | `analysis/weekly.py` |
| Movimiento típico 1h (BTC) | 0.190% | vs ~0.84% coste ida y vuelta |
| Acierto necesario a 1h | **215%** (imposible) | aritmética; a 1 semana ≈ 60% |
| MFE mediana horaria | +0.27% (nunca supera 0.84%) | `analysis/mfe_mae.py` |
| Correlación mediana del universo | 0.77 | `analysis/engine_sim.py` |
| Sesgo de régimen (muestra vieja) | 97% bajista, **0% alcista** | descubierto 2026-08-08 |
| Muestra ampliada | 1 año → 10 años; 59% alcista | `data/candles/` |

## 5. Cinco defectos encontrados el 2026-08-08 (todos por Claude, todos en su propio código)

Se listan porque **sugieren que hay más**:

1. **Permutación ciega** — el test de permutación barajaba los cierres, pero las
   semillas de barras se re-evaluaban sobre los datos REALES. El criterio 9
   devolvía p=1.0 por construcción: un FAIL automático que parecía un resultado.
2. **Ledger imposible de escribir** — se guardaba el CSV de resultados *antes* de
   comprobar el árbol limpio, que a su vez exigía árbol limpio. Ningún veredicto
   se podía registrar desde el commit `9c68af8`.
3. **`bool(dict)`** — la puerta DSR se escribió como `bool(deflated_check(...))`,
   pero esa función devuelve un dict. `bool(dict)` es siempre `True`: la puerta
   existía sin filtrar nada.
4. **`SlowClock` no ralentizaba** — resamplear los datos a barras diarias no
   cambiaba la frecuencia de DECISIÓN. Una semilla "diaria" operaba cada hora.
5. **Columnas fantasma** — `pct_traded` y `median_traded` se añadieron a la
   cabecera del ledger pero nunca a la fila escrita.

## 6. Preguntas concretas para quien revise

Por favor, priorizad estas sobre una revisión genérica:

**Sobre corrección del examen**
1. ¿Hay **lookahead bias** en alguna parte de `backtest/exam_1h.py` o
   `backtest/exam.py`? Especialmente en `simulate_window_bars`, el corte de
   holdout, y el troceado por timestamp de las semillas cross-sectional.
2. La métrica de cobertura `pct_windows_traded` (C0.1b) se añadió porque la
   mediana por ventana no distinguía "no perdí porque acerté" de "no perdí
   porque no jugué". **¿Tiene el mismo tipo de agujero que intenta tapar?**
3. `permute_bars()` baraja la *forma* de cada vela relativa al cierre anterior.
   ¿Es un nulo válido, o destruye/preserva algo que invalida el test?

**Sobre calibración estadística**
4. Con **0 PASS en 96 intentos**, ¿el umbral de suerte (Sharpe ≈1.25 vía
   `expected_max_sharpe`, `var_sharpe=0.25`) está bien calibrado, o es tan
   estricto que ninguna estrategia real podría pasarlo nunca?
5. Ventanas de 2160 barras con paso de 1080 → **solapan 50%**. Ya se retiró
   `stitched()` por componer solapes. ¿Sesga también el Sharpe, el conteo de
   ventanas o el p-valor de permutación?
6. Las 22 filas anteriores al 2026-08-08 se examinaron sobre 1 año (0% ventanas
   alcistas) y las nuevas sobre 10 años. Se declaran poblaciones distintas.
   ¿Es suficiente, o el ledger debería separarlas formalmente?

**Sobre el diseño**
7. El tope de correlación **0.70 con MAX_POS=6 es imposible**: de 28 carteras
   de 6 monedas, **cero** son legales (correlación mediana 0.77). Se firmaron
   ambas reglas sin detectar la incompatibilidad. ¿Cuál es la salida correcta?
8. Las estrategias son **solo-largo**. Ganan a buy-and-hold el 77% de las veces
   en régimen bajista y solo el 21% en alcista: son **defensivas**, no alfa.
   ¿Los criterios deberían premiar eso explícitamente, o es autoengaño?
9. `d3_trend` obtuvo Sharpe **0.66** con permutación **p=0.0100** (señal real)
   pero falló por el umbral de suerte. ¿Es una señal genuina insuficiente, o
   un artefacto?

**Sobre lo que no vemos**
10. ¿Qué defecto **no** está en la lista de la sección 5?

## 7. Cómo tratar los hallazgos (acordado de antemano)

Para no descartar lo incómodo ni reescribir las reglas en caliente:

- Los hallazgos entran como **propuestas** a la revisión del sábado, no como
  cambios inmediatos.
- Un veredicto ya registrado **no se reabre** porque un revisor opine distinto.
  El ledger es permanente.
- Si se encuentra un defecto que invalida veredictos, se **documenta** y se
  decide si la generación se archiva — como ya ocurrió el 2026-08-04.
- Cualquier cambio de regla debe ser un **endurecimiento** (§2.1).

## 8. Contexto que evita malentendidos

- **No hay conexión a ningún exchange.** Sin API keys, sin órdenes. El dinero
  es un número en un JSON. Ver `bot/paper_trader.py`.
- **Los datos son reales:** velas horarias de Coinbase (público) y acciones vía
  `yfinance`, ajustadas por splits.
- **Techo absoluto de capital real: $3,000**, y solo puede bajar.
- **Nada ha aprobado un examen jamás**, así que nada tiene derecho a capital real.
- El sistema **no usa IA para decidir operaciones**. Las semillas son funciones
  deterministas de 5-20 líneas. Se rechazó explícitamente meter un LLM en el
  bucle de decisión: contamina con lookahead (el modelo ya sabe qué pasó) y
  rompe la reproducibilidad.
