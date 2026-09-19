# Época 2 — pre-registro (BORRADOR, SIN FIRMAR)

Escrito 2026-09-18. No tiene efecto hasta que Jose Miguel lo firme en una
revisión de sábado. Nada aquí toca Tier 1. Nada aquí corre todavía.

## 0. Por qué existe
La Época 1 contestó su pregunta: 22 indicadores de libro de texto, a 1h
(cripto) y swing (acciones), no muestran ventaja neta de costes; el bot
aleatorio encabeza cripto; desde el 2026-09-02 la pista cripto está
0-9% invertida porque 9 de 11 bots están en halt o retirados. La Época 1
NO se apaga ni se reescribe: sigue como línea base hasta H1 (2026-11-21).

## 1. Principios de diseño (lo que cambia respecto a Época 1)
1. POCOS bots (4 + control), cada uno con una hipótesis escrita de
   *quién pierde el dinero que el bot gana*. Sin esa frase no entra.
2. Marco DIARIO. Máximo ~2 decisiones por bot por semana. La fricción
   deja de ser el factor dominante.
3. Interruptores de Tier 1 SIN TOCAR (−3% día / −6% 7d / −10% pico).
   Para que no disparen por ruido se reduce el TAMAÑO, no se afloja el
   interruptor: objetivo de volatilidad 1% diario por posición (hoy 2%)
   y tope de 2 posiciones (valor del charter). Dirección: tightening.
4. Se juzga por retorno ajustado a riesgo y drawdown frente al
   benchmark CON LAS MISMAS comisiones, no por retorno bruto.
5. Nombres nuevos, examen propio, K global sigue subiendo (D2, §4.3).

## 2. Candidatos

### E2-SF · hipótesis "Set and Forget" (origen: método de A. Gonzalez)
Afirmación a probar: con la MISMA entrada, una salida fija colocada al
entrar (stop y objetivo, R:R 1:2, sin intervención) rinde más que la
salida por señal. Es H1 en forma de experimento controlado.
- Par de bots gemelos: `e2_sf_bracket` y `e2_sf_signal`. Entrada idéntica
  (ruptura de máximo de 20 días, diario). Solo difiere la salida.
- Stop = 2×ATR(14); objetivo = 4×ATR(14). Números fijados HOY por
  razonamiento, no por búsqueda.
- NO se codifican "zonas de oferta/demanda": son discrecionales y meten
  decenas de parámetros libres.
- Me equivoco si: tras ≥40 operaciones por gemelo, la diferencia de
  expectativa por operación no es distinguible de cero.

### E2-CONG · copia de divulgaciones del Congreso (acciones)
Afirmación: comprar en la FECHA DE PUBLICACIÓN (nunca la de transacción:
eso es lookahead) las compras divulgadas, mantener 90 días, bate a SPY.
- Expectativa pre-registrada: NO lo bate. La evidencia posterior a la
  STOCK Act (Belmont et al. 2022; Chen & Sacerdote 2026) no encuentra
  ventaja tras el retraso de hasta 45 días.
- Fuente: archivos públicos House/Senate. Importes en rangos → peso
  igual por operación. Control: mismas fechas, ticker al azar del S&P 500.
- Riesgo regulatorio: si se prohíbe operar a congresistas, la señal muere.
- Benchmark adicional: ETF NANC (si no bato al ETF, el ETF es la respuesta).

### E2-13F · clonado de gestores (13F)
Afirmación: las 5 mayores posiciones de N gestores de baja rotación,
rebalanceo trimestral en fecha de publicación del 13F, baten a SPY.
- Retraso de 45 días: solo tiene sentido con gestores que mantienen años.
- Lista de gestores fijada ANTES de mirar resultados (sesgo de
  supervivencia: elegir hoy a los que ya ganaron es el +354%).

### E2-RISK · benchmark con gestión de riesgo
Afirmación: comprar-y-sostener (BTC+ETH / SPY) con filtro de tendencia
de 200 días y objetivo de volatilidad reduce el drawdown máximo ≥1/3
cediendo <1/4 del retorno. No pretende batir al benchmark en retorno.

### E2-RAND · control aleatorio
Mismas frecuencia y tamaño que el promedio de los demás. Si queda en la
mitad superior, la época no demostró nada. Esa frase aparece literal.

## 3. Lo que NO se hace
- No se reanuda, renombra ni "arregla" ningún bot de Época 1.
- No se acorta ninguna ventana de evaluación. 10 bots sin ventaja dan
  99.9% de probabilidad de un "ganador" a 7 días.
- Ningún LLM decide operaciones (Tier 1).

## 4. Pendiente antes de firmar
[ ] Auditoría no-Claude (D4) hecha o formalmente retirada como bloqueo
[ ] Jose Miguel explica con sus palabras cada candidato (§6.1)
[ ] Horizonte y nº mínimo de operaciones por candidato
[ ] Fuente de datos concreta para E2-CONG y E2-13F
