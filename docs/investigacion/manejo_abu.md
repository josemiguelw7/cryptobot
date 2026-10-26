# Manejo de la operación sobre ABU v2 · ABG v1 (G2)

Escrito el 26/10/2026 por el investigador. Nadie le preguntó a Oscar.

## Problema
ABU v2 (P031): +$11.9k, p 0.001, pero Topstep 41.2% y 214 de 517 cuentas rompen el MLL. Pierde 107 de 181 operaciones; casi todas con el stop en el tope de 32 ticks ($320 con 2 contratos). El 33% de las perdedoras (35 de 107) llegó a la mitad del riesgo a favor antes de caer.

## Qué dice la literatura
- MAE/MFE (Sweeney): comparar el recorrido de ganadoras y perdedoras para ubicar stops y objetivos; un stop muy ajustado saca operaciones que habrían ganado, y las reglas afinadas sobre una sola muestra se sobreajustan ([TradesViz](https://www.tradesviz.com/glossary/maximum-adverse-excursion/), [LuxAlgo](https://www.luxalgo.com/library/concept/mae-mfe-informed-management/)).
- Cuentas de fondeo con drawdown que sube: el tamaño debe salir de la distancia al límite de pérdida, no del saldo; las rachas rompen la cuenta aunque cada operación sea pequeña ([MQL5](https://www.mql5.com/en/blogs/post/776246)).

## Definición operable (una sola, fijada antes de correr)
ABU v2 sin cambios, salvo: stop máximo 24 ticks (era 32), objetivo 1.5R (era 2R), salida a 10 min (era 15). 2 contratos, parada tras 3 pérdidas (igual).
Pérdida máxima por operación baja de ~$347 a ~$267. Un objetivo más cercano sube la tasa de aciertos.

## Qué NO se prueba y por qué
Breakeven, salida parcial, stop dinámico por flujo y piramidar: `sim.py` no los soporta (solo piramidar, y `rand.py` no lo copia, así que RAND no sería comparable) y están prohibidos de tocar. Quedan pendientes de una decisión de cambio de motor.

## Cómo se lee
Mejor Topstep que 41.2% con p vs RAND ≤ 0.05 y los 3 años positivos = el manejo ayuda. Si Topstep no sube, el cuello es la lentitud de ABU, no el riesgo por operación. Se mira la superficie (16 vecinos), no la mejor celda.

## Límites
Mismas señales y mismos datos de diseño que ABU v2: no es validación independiente. ABU gastó sus 3 versiones; ABG es un id nuevo porque cambia el manejo de salida como hipótesis propia (G2).
