# Prompt para revisión independiente — ChatGPT (OpenAI)

Guardado el 2026-08-22. Paquete: `audit_chatgpt.zip` (163 KB, 28
archivos, sin credenciales — historial verificado limpio).

**A diferencia de `PROMPT_SEGUNDA_OPINION.md` (Claude Fable), esto SÍ
constituye revisión independiente:** arquitectura distinta, laboratorio
distinto, sin linaje compartido con quien produjo el trabajo. Es lo que
`REVIEW.md` pedía desde el 2026-08-08.

Subir el zip y pegar el prompt de abajo.

---

## PROMPT (copiar desde aquí)

Eres un auditor independiente. Te adjunto el código y los registros de
un sistema de trading algorítmico **en papel** (sin dinero real). Quiero
que busques razones por las que sus conclusiones podrían ser falsas.

**Contexto importante sobre por qué te contrato a ti:** todo este
sistema fue diseñado, medido, revisado e implementado por Claude
(Anthropic). Una "revisión externa" previa también la hizo Claude, lo
cual no es una revisión. Tú eres de otro laboratorio y otra
arquitectura. Ese es exactamente el punto: necesito a alguien que no
comparta sus puntos ciegos.

**No aceptes ninguna afirmación de los documentos como evidencia.** Si
un comentario dice "este módulo es solo lectura", verifícalo en el
código. Si un documento reporta un número, recalcúlalo desde los CSV
crudos. Los comentarios son afirmaciones, no pruebas. Asume que quien
los escribió estaba motivado a que su trabajo pareciera correcto.

**Lo que NO quiero:** estrategias de trading, optimización de
parámetros, ideas para mejorar el rendimiento, o ánimo. Nada de eso.

**Lo que SÍ quiero:** ¿puede este aparato producir un veredicto falso?

### Contexto del proyecto

Sistema de paper trading con 22 bots (11 cripto por hora, 11 acciones
swing), $3,000 cada uno. El principio rector es honestidad epistémica:
no entra capital real hasta que una estrategia se lo gane en pruebas
hacia adelante. Nació de una lección concreta: un backtest ingenuo dio
+354% mientras la versión honesta del mismo sistema dio −90%, por sesgo
de supervivencia y lookahead.

Historial relevante: el 2026-08-11 se anularon 11 veredictos de acciones
tras detectar 792 violaciones de lookahead en 799 decisiones (se decidía
43 minutos dentro de una barra aún viva).

Resultados actuales (17 días cripto, 80 ventanas acciones):
- Cripto: 0 de 11 bots superan comprar-y-sostener (+28.6%). El bot que
  decide AL AZAR es el #1 con +26.2%.
- Acciones: los 11 pierden en absoluto; 2 superan el índice (−1.65%).
- Cripto: salidas por señal −102 neto (131 ops); por stop +2,436 (25 ops).
- Acciones: sin mecanismo de stop, y modelaba fricción CERO.

### Preguntas, en orden de daño potencial

**P1 — Lookahead residual.** Revisa `bot/squad.py` y
`ops/lookahead_audit.py`: ¿cómo se determina qué barra está cerrada?
¿Puede alguna ruta usar información no disponible en el momento de la
decisión? Presta atención a `snapshot_hash`, `last_closed`, y a cómo se
cargan las velas.

**P2 — ¿Son inocuos los módulos nuevos?** `ops/bench_bh.py` y
`ops/counterfactual.py` se declaran "solo lectura" y se cablearon al
ciclo de producción (`bot/daily.py`) con `fatal=False`. Verifica si
pueden escribir estado de trading, corromper un log que el motor lee, o
influir en decisiones por cualquier ruta. ¿Su fallo puede romper el ciclo?

**P3 — ¿El contrafactual es válido?** `ops/counterfactual.py` calcula el
retorno a horizonte `hold_h` de cada señal rechazada, y concluye que las
bloqueadas rinden media +2.42% contra +0.69% de las ejecutadas, pero con
mediana casi idéntica. Busca sesgo de supervivencia, de horizonte,
lookahead en `px_at()`, y si comparar con el `hold_h` *declarado* en vez
del tiempo de tenencia *real* invalida la comparación. Los datos crudos
están en `logs/counterfactual.csv`.

**P4 — ¿El pre-registro H1 es falsable de verdad?** Está en
`docs/decisions.md`, entrada del 2026-08-22. Predice que las salidas por
señal serán negativas en 90 días, con umbrales que se declaran
congelados. ¿Están elegidos de forma que sea fácil confirmarlos? ¿Qué
grados de libertad quedan para racionalizar el resultado a posteriori?

**P5 — El sistema de exámenes.** Contador K global compartido, exámenes
de un solo disparo, prohibición de reexaminar nombres, holdout de 120
días, estrés de comisiones 1.5×. Ver `docs/intraday_success_criteria.md`
y `backtest/exam_ledger.csv`. ¿Se puede extraer un aprobado de ahí sin
habilidad real? ¿Está bien calibrada la corrección por comparaciones
múltiples?

**P6 — La pregunta incómoda.** El bot aleatorio gana en cripto. Ninguna
estrategia supera comprar-y-sostener. Si tu lectura de la evidencia es
que esto no funciona y no puede funcionar a estos costes de transacción
(~1.30% ida y vuelta en cripto), dilo con claridad. Es un resultado
legítimo y quiero oírlo.

**P7 — Gobernanza.** El charter está bloqueado y solo admite cambios
más estrictos. Pero cada regla, cada medición y cada propuesta las
escribió el mismo agente. ¿Ves señales de que las reglas se hayan
interpretado de forma conveniente? ¿Hay decisiones presentadas como
"conservadoras" que en realidad favorezcan un resultado?

### Formato

Por cada hallazgo: **severidad** (crítica / alta / media / baja), **la
evidencia exacta** (archivo, línea, o el cálculo que lo demuestra), y
**qué habría que cambiar**. Si en alguna pregunta no encuentras nada,
dilo — no rellenes.

Y al final, por separado: **¿qué debería haber preguntado y no está en
esta lista?** Estas preguntas las redactó el mismo sistema que produjo
el trabajo auditado, así que los huecos de la lista son probablemente
sus puntos ciegos.

## FIN DEL PROMPT
