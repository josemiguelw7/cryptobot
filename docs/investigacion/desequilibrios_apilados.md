# Desequilibrios apilados (footprint) · IMB v1

## Por qué este tema
Los desequilibrios son una de las herramientas de flujo que pide el alcance y nunca se han probado. Las 12 pruebas anteriores usaron absorción, aceptación, órdenes grandes, VWAP y perfiles. La familia de absorción es la única positiva, pero tiene ~110 operaciones y no llega a Topstep. Aquí se espera mucha más frecuencia (~2 900 señales; en 60 sesiones salieron 301 operaciones, solo para ver que el código corre).

## Qué dicen las fuentes
- Quantower, LuxAlgo, ProCharting y scripts de TradingView coinciden: el desequilibrio es **diagonal**. El volumen agresivo comprador en un precio se compara con el vendedor un tick más abajo (y al revés). Umbral habitual: **300 %** (3 a 1).
- **Apilado** = 3 o más precios seguidos con el mismo desequilibrio (valor por defecto de LuxAlgo). Uno solo es ruido.
- Uso común: la zona apilada marca dónde el flujo iniciador atravesó la liquidez pasiva; **la primera vuelta a la zona** puede sostener o romper.
- Cautela de las mismas fuentes: describe lo que pasó, no lo que debe pasar, y es casi todo documentación de vendedores. No hay evidencia independiente de que prediga dirección. Por eso se prueba contra RAND.

Fuentes: https://www.quantower.com/blog/imbalance-footprint-chart-and-rithmic-plugin · https://www.luxalgo.com/library/concept/bid-ask-imbalance/ · https://procharting.in/docs/orderflow/imbalance-charts

## Definición operable (fijada antes de correr)
Sin velas: ventana móvil de 60 s evaluada cada 5 s.
1. Por precio p: A[p] = contratos con agresor comprador, B[p] = con agresor vendedor.
2. Desequilibrio comprador en p: A[p] ≥ 3 · B[p−1] y A[p] ≥ 10 contratos. Vendedor: B[p] ≥ 3 · A[p+1] y B[p] ≥ 10.
3. Pila: ≥ 3 precios consecutivos (se toma la más larga). Zona = de su precio más bajo al más alto.
4. Si el precio ya se alejó ≥ 4 ticks de la zona en el sentido de la iniciativa, se pone una orden límite en el borde cercano (comprador: borde alto; vendedor: borde bajo), válida 300 s. Se usa límite porque la tesis es la vuelta a la zona; el simulador usa su modelo de cola.
5. Stop 4 ticks más allá del borde lejano de la zona (entre 12 y 32 ticks), objetivo 2R, salida a 15 min, entradas 10:00–15:30, un disparo por lado cada 5 min.

## Definiciones alternativas (no se eligen mirando resultados)
Las dos que quedan son razonables y se cuentan como sensibilidad: razón 2,5 / 3,5 / 4 (en vez de 3) y volumen mínimo 6–14. La entrada a mercado al formarse la pila (continuación) no se prueba aquí; si la reprueba falla, queda como IMB v2.

## Sensibilidad (16 intentos)
razón 2 / 2,5 / 3,5 / 4 · volumen mínimo 6 / 8 / 12 / 14 · alejamiento 2 / 3 / 5 / 6 ticks · salida 5 / 10 / 20 / 25 min.

## Honestidad
Sin filtro de régimen (los filtros "abre dentro del valor" de otras pruebas salieron de ver los mismos datos; aquí no se usan). Solo se corrió el código en 60 sesiones para ver que genera operaciones; no se miró el resultado para ajustar nada.
