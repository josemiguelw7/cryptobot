# Motor de pruebas · por qué está hecho así

Cada decisión de diseño del motor, con su motivo, para que "¿y esto por qué?" tenga respuesta antes de que alguien la haga.

## Simulación (`sim.py`)
- **Entrada a mercado = mejor oferta contraria + 1 tick.** Una orden a mercado cruza el spread; el tick extra es el deslizamiento típico de NQ en Nueva York. Nunca se llena al último precio operado, que puede ser el lado favorable.
- **El objetivo solo se llena si la cinta pasa de largo.** Una orden límite en el objetivo compite con la cola de ese precio; tocar el precio no garantiza llenado. Exigir que opere más allá es conservador a propósito. Costo de esta regla: ~5–10% de los objetivos reales no se dan por llenados; preferimos subestimar.
- **El stop lleva deslizamiento.** Un stop de mercado se ejecuta después de que el precio lo toca, nunca en el precio exacto.
- **Salida por tiempo y cierre forzado a mercado.** Mismo deslizamiento que la entrada.
- **Una posición a la vez, máximo 6 por día, parar tras 3 pérdidas seguidas.** Son las reglas comunes de la v1; el simulador no las inventa, las lee.
- **Órdenes límite con cola.** Para estrategias pasivas (ninguna en v1): la orden entra detrás del tamaño visible en el libro y se llena cuando se opera ese volumen en ese precio o cuando el precio pasa de largo. Usa `bid_size_after`/`ask_size_after` de la cinta.
- **Precios en ticks enteros.** Evita errores de coma flotante en comparaciones de stop y objetivo.
- **Ventanas de noticias.** Sin entradas −2/+5 min en CPI y NFP y −5/+15 en Fed. Para el horario de la v1 (09:30–11:30) no aplican, pero el motor las impone siempre.

## Niveles y umbrales (`levels.py`)
- **Solo pasado.** Los niveles de referencia son del día válido anterior y de la noche del mismo día (antes de las 09:30). Los percentiles son de las 20 sesiones válidas anteriores. Ningún número viene del día que se está simulando.
- **Población de los percentiles de órdenes = órdenes de 10+ contratos.** Sobre todas las órdenes, el p99 cae en ~15 contratos porque casi todas son de 1 lote (hallazgo del Red Team, `strategies/v1_aclaraciones.json`).
- **Percentil agrupado exacto o error.** Se guardan suficientes valores por sesión para que el percentil pedido quede dentro de lo guardado; si no, el programa se detiene en vez de inventar un número.
- **20 sesiones de referencia.** Un mes bursátil: suficiente para que el umbral refleje el régimen reciente sin reaccionar a un solo día. Es una elección, no una verdad; está en `PARAMS` y la sensibilidad puede moverla (cuenta como intento).

## RAND emparejado (`rand.py`)
- Copia cantidad, duración y horario de las operaciones reales; sortea momento y dirección. Sale por tiempo, sin stop ni objetivo. Mide si la **selección del momento y la dirección** vale algo; no mide la gestión de la salida.
- 1,000 corridas con semilla derivada de SHA-256(id, fecha, k): reproducible bit a bit.

## Topstep (`topstep.py`)
- MLL revisado contra el **peor momento de cada operación** (MAE), no solo contra el cierre, porque Topstep lo vigila con P&L no realizado.
- Una cuenta nueva arranca en cada sesión: el resultado es una distribución, no un número.
- Consistencia 50% (laboratorio) y 55% (oficial) se reportan ambas.

## Estadística (`stats.py`)
- PSR y DSR (Bailey & López de Prado): el DSR usa la cuenta total de intentos del registro, no solo los que salieron bien.
- CPCV con 6 grupos y 1 sesión de purga: 15 caminos fuera de muestra.
- Concentración: top 5 operaciones y top 5 días; más del 50% en 5 días se marca.

## Red Team automático (`redteam.py`)
- **Placebo desplazado** (señal 5 min antes): detecta fuga de futuro en señales de momento; en señales de nivel puede ganar más sin fuga (ABS v1), por eso el protocolo v2 lo manda a "revisar" y no a "error".
- **Direcciones barajadas** (200 veces): ¿la dirección aporta o solo el momento?
- **Curva de costos 0–4 ticks** y **sensibilidad ±2 pasos** por parámetro: se buscan mesetas, no picos.

## Registro (`registry.py`)
- Solo agregar, con cadena de huellas: cada línea lleva el SHA-256 de la anterior. Borrar o editar rompe la cadena y la página lo muestra.
- Las correcciones son líneas nuevas que apuntan a la prueba; la original no se toca.

## Orquestador (`orchestrator.py`)
- Contenedor efímero sin red con datos en solo lectura, dos corridas, publica solo si `trades.csv` es idéntico.
- Antes de cada prueba: **golden** (ABS v1 sobre 60 sesiones debe dar la huella fijada) y **manifiesto de datos** (tamaños de todos los parquet + SHA-256 de 30 al azar). Si algo difiere, no corre.

## Régimen (`regime.py`)
- Reglas fijas y simples (cuerpo ≥ 50% del rango, rango vs mediana de 20 sesiones, día de noticias, apertura dentro/fuera del valor). Se eligieron **antes** de mirar resultados por régimen; cambiarlas sería versión nueva.
