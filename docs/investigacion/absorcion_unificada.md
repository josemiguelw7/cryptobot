# ABU v1: absorción unificada (niveles de ayer + valor del día), solo días de balance

## Por qué esta prueba
- IMB v1 (P029) perdió −$23.8k en 2,607 operaciones: gana 32.8%, justo lo del azar con objetivo 2R (33%). Sin ventaja bruta; los costos hicieron el resto. La pila de desequilibrios con orden límite queda descartada.
- Lo único que tiene ventaja es la absorción en días que abren dentro del valor de ayer: ABD v1 (P027) +$5,720, p 0.001 contra RAND, positiva en 2024, 2025 y 2026 (+$2,090, +$3,115, +$516). Pero tiene 111 operaciones: Topstep 0% porque **ninguna de las 517 cuentas resolvió** (ni pasa ni rompe: no junta $3,000 a tiempo). El problema es la frecuencia, no las pérdidas.
- En días de balance, la absorción en el valor en desarrollo (ABI v1: 37 operaciones, +$9,750; ABV v1: 40 operaciones, +$7,319) también gana. Son operaciones en momentos distintos a las de ABD.
- La idea: un solo detector con los dos universos de niveles (ayer + noche, y POC/VAH/VAL del día en desarrollo), solo en días de balance, para duplicar la frecuencia sin cambiar el detector ni la salida.

## Qué dice la literatura (de las búsquedas anteriores del laboratorio, sin definición nueva)
- Dalton / Market Profile: abrir dentro del valor y del rango de ayer = sesión de rotación; los bordes del valor (propio y de ayer) son donde el mercado rechaza precios. Fuentes y detalle en `absorcion_dias_balance.md` y `absorcion_valor_desarrollo.md`.
- No hay una definición nueva que investigar: se reutilizan las ya fijadas. Por eso no hay búsqueda nueva.

## Definición (fijada antes de correr)
- Filtro, detector, umbral relativo (el menor entre p95 de 20 sesiones y p90 de la hora anterior, piso 0.5×), confirmación a 60 s, stop 12–32, objetivo 2R, salida a 15 min, ventana 09:30–15:30: idénticos a ABD v1.
- Niveles: los de ABD (ayer y la noche) + dev_poc (cualquier lado), dev_vah (solo compra absorbida), dev_val (solo venta absorbida) del perfil que el día va construyendo, calculados solo con operaciones anteriores a la ventana y no antes de 10 min de sesión. Se queda fuera máximo/mínimo del día y VWAP (en ABI perdieron; además no son niveles de valor). Esa exclusión viene de ver P021 en los mismos datos de diseño: exploratoria.
- Niveles de ayer: una vez por día. Niveles del día: un disparo por nivel cada 10 min.
- Solo se contaron señales, nunca ganancias: en 58 sesiones (una de cada 10) ABD da 9 y ABU 20 (≈ 250 en 576 sesiones, ~2.2×).

## Riesgos y lo que no puede decir
- Es una combinación elegida mirando resultados de diseño: el DSR la va a penalizar (más de 840 intentos en el registro). Aunque dé p bajo, no es evidencia independiente.
- Si ABD ya era suerte, esto también. Una operación ABU de ayer-nivel es la misma que una de ABD (solapamiento ~45%).
- Ganancia concentrada en pocos días, como toda la familia.
- Si no llega a Topstep ≥ 50% con ~250 operaciones, la familia de absorción queda agotada para 1 contrato; el siguiente paso sería dejar de buscar frecuencia aquí.
