# REVIEW.md — petición de revisión externa (v2, 2026-08-11)

**Repo:** `josemiguelw7/cryptobot` · **Estado:** papel, sin capital real, sin
conexión a ningún exchange · **Veredictos aprobados hasta hoy: 0.**

---

## LO PRIMERO, Y LO MÁS IMPORTANTE

Buscamos un revisor que **no sea Claude**.

La petición anterior (`docs/review/REVIEW_2026-08-08.md`) fue respondida por
una instancia de Claude. Encontró quince defectos reales y valiosos —están en
`docs/review/2026-08-08_external_review.md`— pero **no fue una revisión
independiente**, y su propia sección de advertencias lo dice: encontrar errores
en código escrito por un modelo que comparte sus sesgos es evidencia débil de
no compartir los que quedan.

El código de este repo lo escribió Claude. La revisión la hizo Claude. Los
arreglos los aplicó Claude. La explicación de los arreglos al dueño la escribió
Claude. **Ese círculo es el problema que esta petición existe para romper.**

Si eres un modelo de otra arquitectura, o una persona con experiencia en
finanzas cuantitativas: eres exactamente quien hace falta. Si eres Claude,
dilo al principio de tu respuesta para que el hallazgo se pondere en
consecuencia.

El dueño (Jose) **no es programador** y ha aprobado decisiones técnicas que no
comprendía del todo. Él mismo lo señaló el 2026-08-11. Corregir ese
desequilibrio es una función explícita de esta revisión. Escribe para él, no
para un ingeniero: `docs/LIMITES_ES.md` es el registro que buscamos.

---

## 0. Qué es este proyecto en una frase

Un sistema de trading algorítmico **en papel** cuyo objetivo declarado no es
ganar dinero sino **no engañarse**.

Motivación original: un backtest ingenuo mostró **+354%**; la versión honesta
(point-in-time, sin mirar el futuro) del mismo sistema mostró **−90%**. Todo
el andamiaje nace de esa diferencia.

## 1. Qué cambió el 2026-08-11 (léelo antes que el código)

Cuatro cosas grandes ocurrieron en un solo día. Las tres primeras las
recomendó Claude; la cuarta la decidió el dueño.

1. **Arreglos de bugs.** Reloj lento congelado (decidía por longitud del
   array en vez de por marca de tiempo), acciones leyendo velas a medio
   formar (792 violaciones de 799 decisiones), historial no acotado en el
   motor en vivo, excepciones convertidas en silencio en "quédate en
   efectivo". Todos con evidencia reproducible.
2. **Cambio de estadísticos del examen.** Criterios 4/6/7/8/9 dejaron de
   usar una métrica compuesta sobre ventanas solapadas; el criterio 10 pasó
   a ser el DSR real de Bailey y López de Prado; la barrera de suerte pasó
   de una constante fija a derivarse de la muestra efectiva.
3. **Charter v2 (`docs/charter_v2.md`), firmado.** Sustituye el trinquete de
   una sola dirección ("las reglas solo se endurecen") por dos niveles: las
   reglas del dinero siguen siendo de una sola dirección; las reglas de la
   ciencia se vuelven ajustables en ambas direcciones con entrada escrita y
   una noche de espera.
4. **Trece veredictos anulados** (2 de cripto por el reloj congelado, 11 de
   acciones por las velas a medio formar).

**La pregunta que más nos importa que respondas está en el punto 3.**

## 2. Orden de lectura sugerido

1. `docs/LIMITES_ES.md` — qué limita cada regla, en llano (contexto rápido)
2. `docs/charter_v2.md` — el modelo de gobernanza nuevo
3. `docs/review/2026-08-08_external_review.md` — los 15 hallazgos de Claude
4. `backtest/exam_1h.py` — el examen; el archivo más importante del repo
5. `bot/strategies.py` y `bot/squad.py` — estrategias y motor en vivo
6. `docs/decisions.md` — el registro de decisiones desde la firma

## 3. Hechos medidos hoy (no opiniones)

| Hallazgo | Valor | Dónde |
|---|---|---|
| Veredictos | **0 PASS**, 38 filas de registro | `backtest/results/exam_ledger.csv` |
| Coste ida y vuelta | ≈1.30% | `exam_1h.py` FEE=0.006, SLIP=0.0005 |
| Correlación cripto, histórico | 0.682 mediana | `analysis/corr_pairs.py` |
| Correlación cripto, **último año** | **0.807** mediana; 1/28 pares legales | íd. |
| Correlación acciones, último año | 0.446 mediana; 40/45 pares legales | íd. |
| Auditoría de lookahead, cripto | 2589/2589 limpias | `ops/lookahead_audit.py` |
| Auditoría de lookahead, acciones | **792/799 violaciones** (arreglado) | íd. |
| Ventanas del holdout | **8** (1 por activo) | `exam_1h.py` geometría |

Nota: la cifra de correlación 0.77 que este documento citaba antes no era
estable — depende por completo de la ventana medida.

## 4. Preguntas concretas. Prioriza estas sobre una revisión genérica.

**Sobre la gobernanza (lo que más nos importa)**

1. Charter v2 lo propuso el mismo sistema al que restringía, empaquetado en el
   mismo parche que arreglos de bugs urgentes y reales. El dueño lo firmó el
   mismo día, sin poder evaluar los detalles técnicos. **¿Fue un cambio
   defendible, o fue una IA aflojando sus propias restricciones aprovechando
   una crisis que ella misma había causado?** Responde sin diplomacia.
2. El trinquete de v1 tenía una propiedad que v2 no tiene: funcionaba sin que
   el dueño entendiera nada, porque solo había que mirar la dirección del
   cambio. V2 exige juicio informado en cada cambio. **¿Existe un diseño que
   permita corregir reglas erróneas sin perder esa propiedad?**
3. Las 13 anulaciones: ¿estaban justificadas por la evidencia, o el criterio
   de "bug documentado" es lo bastante elástico como para justificar casi
   cualquier cosa? Ver `backtest/results/void_log.csv`.

**Sobre corrección estadística**

4. El criterio 10 reconstruido (`exam_1h.py` ~línea 600, usando
   `bot/stats.py`): ¿el DSR está bien implementado, en las unidades
   correctas, y el umbral de 0.95 es apropiado con K=38?
5. La barrera de suerte ahora deriva su dispersión de `365/T_eff` con
   `T_eff` estimado descontando solape de ventanas y correlación entre
   activos. ¿Es defendible o es un número inventado con mejor prosa que el
   anterior?
6. El holdout son **8 observaciones** (una ventana por activo). Es el
   criterio out-of-sample, el más importante del examen. ¿Cómo debería
   rediseñarse la geometría?
7. ¿Queda **lookahead bias** en algún sitio? Es la pregunta original y sigue
   siendo la que más importa.

**Sobre el diseño**

8. Las 8 monedas están a 0.81 de correlación en el último año, y solo 1 par
   de 28 cumple el tope de 0.70. Las opciones parecen ser: aceptar que los
   bots estén casi siempre en efectivo, subir el tope (aflojar), o ampliar el
   universo (con riesgo de iliquidez y sesgo de supervivencia — ver
   `docs/review/2026-08-11_correlacion_universo.md`). **¿Hay una cuarta?**
9. Las estrategias son solo-largo y por tanto defensivas, no generadoras de
   alfa. ¿Es esto medible como virtud, o es autoengaño estructural?

**Sobre lo que no vemos**

10. ¿Qué defecto **no** está en ninguna lista todavía? La revisión anterior
    encontró diez que no estaban. Asume que sigue habiendo más.

## 5. Reproducibilidad — limitación conocida

`data/candles/` y `data/candles_daily/` están excluidos del repo por tamaño
(~115MB). Eso significa que **ningún veredicto de este repo es reproducible
por un tercero hoy**. Es el hallazgo M-7 de la revisión anterior y sigue
abierto. Los datos son velas horarias públicas de Coinbase y de `yfinance`;
los scripts de descarga están en `data/`. Si necesitas los datos exactos para
revisar, pídelos y se publicarán como artefacto aparte.

## 6. Cómo se tratarán tus hallazgos

- Entran como **propuestas**, no como cambios inmediatos.
- Ningún veredicto se reabre porque un revisor opine distinto; hace falta
  evidencia de un bug (charter v2 §4.2).
- Cambios que hagan más fácil que una estrategia llegue al dinero real
  requieren una semana y una declaración escrita de a quién benefician si
  resultan erróneos (§3.3).
- **Las reglas del dinero (§2 de charter v2) no se tocan pase lo que pase:**
  techo de $3.000, escalera, papel antes que real, ningún LLM en decisiones
  con dinero real.

## 7. Contexto que evita malentendidos

- **No hay conexión a ningún exchange.** Sin claves de API, sin órdenes. El
  dinero es un número en un JSON.
- **Nada ha aprobado un examen jamás**, así que nada tiene derecho a capital.
- Las estrategias son funciones deterministas de 5-20 líneas. Se rechazó
  explícitamente meter un LLM en el bucle de decisión.
- El registro de veredictos solo crece; nada se borra ni se reescribe.
