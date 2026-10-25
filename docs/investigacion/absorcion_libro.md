# Absorción medida con el libro (ABK v1)

## Qué buscamos
Las pruebas ABS, ABI, ABV y HVF detectan la absorción por el precio: "entró mucho flujo agresivo y el precio no avanzó más de 2 ticks". Los traders de order flow la definen por el libro: el lado pasivo recibe el flujo y su oferta NO retrocede.

## Fuentes
- [ATAS · absorción de demanda y oferta en el footprint](https://atas.net/exchange-trading/absorption-of-demand-and-supply-in-the-footprint-chart): grandes pasivos ponen órdenes límite en niveles que quieren defender; mucho volumen en un precio con poca expansión.
- [ATAS · cómo nace una operación](https://learn.atas.net/volume-basics/volume-analysis/matching-engine-and-absorption): el motor de emparejamiento consume la oferta pasiva.
- [Bookmap · indicador de absorción](https://bookmap.com/absorption/) y [LuxAlgo · icebergs](https://www.luxalgo.com/library/concept/iceberg-detection/): la punta visible se repone tras cada llenado; mucho más volumen operado que tamaño visible.
- [NexusFi · absorción](https://nexusfi.com/a/concepts/absorption): delta que no se traduce en desplazamiento.

## Escenarios y definición operable
1. Ventas agresivas fuertes y la mejor compra (bid) no baja: absorbe el comprador pasivo → posible largo.
2. Compras agresivas fuertes y la mejor venta (ask) no sube: absorbe el vendedor pasivo → posible corto.
3. Si el tamaño del bid/ask cae al final, no se repuso: es debilidad, no absorción.

Definición fijada antes de correr: volumen agresivo de un lado ≥ p95 en 60 s (el umbral relativo de ABS v1); precio sin avanzar más de 2 ticks; mejor oferta nunca peor que la de antes del primer llenado; tamaño final ≥ 50% del inicial (se repuso); confirmación, stop y salida como ABS v2. Sin filtro de nivel, así que no repite los niveles de ABS/ABI/ABV/HVF.
Alternativas comparadas dentro del mismo estudio (sensibilidad): sin exigir reposición (0%), 25%, 75%, 100%.

## Antes de correr
Solo se contaron señales en 80 sesiones de diseño (123 con la base; 143 sin reposición; 107 con 100%): unas 850 en total. No se miró ninguna ganancia.
