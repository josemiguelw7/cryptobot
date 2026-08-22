# Prompt para segunda opinión técnica (NO revisión independiente)

Guardado el 2026-08-22. Para pegar en un chat nuevo con el proyecto
`cryptobot` accesible vía desktop-commander.

**ADVERTENCIA:** quien responda a este prompt es un modelo de Anthropic,
igual que quien produjo el trabajo que va a revisar. Esto NO cierra el
hueco de gobernanza registrado en `REVIEW.md` y
`docs/REVISION_INDEPENDIENTE.md`. Etiquetar cualquier resultado como
`NO-INDEPENDIENTE`.

---

## PROMPT (copiar desde aquí)

Necesito que audites un sistema de trading algorítmico en papel. Tienes
acceso al repo en `/Users/haroonrasheed/Projects/cryptobot/` vía
desktop-commander. Usa `.venv/bin/python`, nunca el python del sistema.

**Contexto que debes saber antes de empezar:** todo el trabajo del
2026-08-22 que vas a revisar lo produjo Claude. Tú también eres Claude.
Eso significa que probablemente compartes sus puntos ciegos. Tu valor
aquí NO es confirmar que el razonamiento suena sensato — suena sensato
porque lo escribió algo que razona como tú. Tu valor es encontrar
errores mecánicos verificables ejecutando código.

**Regla de trabajo: no aceptes ninguna afirmación sin verificarla
ejecutándola.** Si un documento dice "este módulo es solo lectura",
compruébalo leyendo el código, no el comentario. Si dice "0 de 11 bots
superan el benchmark", recalcula el número tú mismo desde los logs
crudos. Los comentarios y los documentos son afirmaciones, no evidencia.

**No propongas estrategias. No optimices parámetros. No sugieras
mejoras de rendimiento.** El encargo es exclusivamente: ¿puede este
aparato producir un veredicto falso?

Empieza leyendo, en este orden:
1. `docs/intraday_success_criteria.md` — el charter, inmutable
2. `docs/decisions.md` — sobre todo las entradas del 2026-08-22
3. `docs/REVISION_INDEPENDIENTE.md` — las 5 preguntas abiertas
4. `bot/squad.py`, `bot/squad_stocks.py` — el motor
5. `ops/bench_bh.py`, `ops/counterfactual.py` — módulos nuevos

Y responde a esto, en orden de daño potencial:

**P1. Lookahead.** El proyecto nació de un backtest que dio +354%
cuando la versión honesta daba −90%. El 2026-08-11 se anularon 11
veredictos por sesgo de barra en formación (792 violaciones en 799
decisiones). ¿Queda algún camino de lookahead abierto? Revisa
`ops/lookahead_audit.py`, `data/pit_*.py`, y cómo `squad.py` decide qué
barra está cerrada. Ejecuta el auditor tú mismo.

**P2. ¿Los módulos nuevos son realmente inocuos?** `ops/bench_bh.py` y
`ops/counterfactual.py` se declaran "solo lectura" y se cablearon a
`bot/daily.py` con `fatal=False`. Verifica: ¿pueden escribir en estado
de trading, alterar un log que el motor lee, o influir en una decisión
por cualquier ruta, incluida la indirecta vía dashboard? ¿Puede su fallo
corromper el ciclo?

**P3. ¿El contrafactual está bien construido?** `ops/counterfactual.py`
calcula el retorno a `hold_h` de cada señal rechazada. Busca: sesgo de
supervivencia, sesgo de horizonte, lookahead en `px_at()`, y si comparar
señales rechazadas contra ejecutadas usando el `hold_h` declarado (en
vez del tiempo de tenencia real) es una comparación válida. Concluyó que
las bloqueadas tienen media +2.42% contra +0.69% de las ejecutadas, pero
mediana casi idéntica. ¿Es real ese hallazgo o un artefacto del método?

**P4. ¿El pre-registro H1 es honesto?** Está en `docs/decisions.md`,
2026-08-22. Predice que las salidas por señal serán negativas en 90
días, con umbrales congelados. ¿Están los umbrales elegidos de forma que
sea fácil confirmarlos? ¿Hay grados de libertad que permitan
racionalizar el resultado después? ¿Es falsable de verdad?

**P5. El sistema de exámenes.** Contador K global compartido, un solo
disparo, prohibición de reexaminar nombres, holdout de 120 días, estrés
de comisiones 1.5×. Ver `backtest/results/exam_ledger.csv`. ¿Se puede
sacar un aprobado de ahí sin habilidad real?

**P6. La pregunta incómoda.** En cripto, 0 de 11 bots superan comprar y
sostener (+28.6%), y el bot que decide AL AZAR va primero. En acciones
los 11 pierden en absoluto. Si tu lectura de la evidencia es que esto no
funciona y no va a funcionar a estos costes, dilo claramente. Ese es un
resultado legítimo y el propietario quiere oírlo.

**Formato de respuesta:** para cada hallazgo, indica (a) severidad, (b)
el comando o fragmento de código exacto que lo demuestra, (c) qué habría
que cambiar. Si no encuentras nada en una pregunta, dilo — no rellenes.

Y al final, respóndeme esto por separado: **¿qué debería haber
preguntado y no está en esta lista?** Las preguntas las escribió el
mismo sistema que produjo el trabajo, así que los huecos de la lista son
exactamente sus puntos ciegos.

## FIN DEL PROMPT
