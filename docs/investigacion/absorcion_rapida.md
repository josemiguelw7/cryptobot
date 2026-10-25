# ABQ v1: absorción rápida (escala de 30 s)

## Por qué esta prueba
- P032 (ABT v1, días que abren fuera del valor): −$3,588, 128 operaciones, p 0.71. Ampliar el universo de días no sirve: la absorción solo gana cuando el día abre dentro del valor de ayer.
- Lo que sí tiene ventaja: ABU v1/v2 (P030/P031), +$5.9k / +$11.9k, p 0.001, positiva en 2024, 2025 y 2026. Pero Topstep 9.9% (1 contrato, lento) o 41% con 214 cuentas rotas (2 contratos).
- La meta de Oscar es scalping de segundos a minutos. ABU usa ventana de 60 s, stop de 12–32 ticks y 15 min en mercado: es lento. Pregunta: ¿la ventaja sobrevive a una escala más corta (menos riesgo por operación, menos tiempo expuesto)?

## Qué dice la teoría
- Auction market theory (Dalton) y footprint: la absorción es volumen agresivo grande que no mueve el precio; no define una duración fija. Las plataformas (ATAS, Bookmap) la miran en ventanas de segundos. Ver `absorcion_intradia.md` y `absorcion_libro.md` (búsquedas anteriores del laboratorio; no hay definición nueva que investigar).
- Por eso la escala es una elección de diseño, no de la literatura. Se declara una sola (30 s) y las vecinas entran como sensibilidad.

## Definición (una sola, fijada antes de correr)
- Todo igual a ABU v1 (días que abren dentro del valor de ayer, mismos niveles, 09:30–15:30) salvo:
  - ventana 30 s (no 60 s); umbral = p90 de las ventanas de 30 s de los 60 min anteriores de la propia sesión; los primeros 10 min y como piso: fracción del p95 de 60 s de 20 sesiones (0.5 y 0.25). No existe p95 de 30 s de 20 sesiones en los datos derivados.
  - confirmación en 20 s con alejamiento de 3 ticks; stop 3 ticks más allá del extremo, entre 8 y 20 ticks; objetivo 2R; salida a 5 min.
  - nivel del día: un disparo cada 5 min; tope de 12 operaciones al día (en vez de 6); 3 pérdidas seguidas detienen el día.
- Sensibilidad (16 intentos): cercanía 2/3/5/6 ticks, confirmación 10/15/25/30 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R.

## Humo (solo señales, nunca ganancias)
- 80 sesiones consecutivas: ABQ 32 señales, ABU 33. **No hay más frecuencia**: el cuello de botella son los niveles cercanos, no la ventana. La prueba no se vende como solución de Topstep; es la pregunta de si la ventaja existe a escala corta.

## Riesgos
- Exploratoria: sale de ver resultados de ABU en los mismos datos de diseño. El DSR (más de 900 intentos) la penaliza; no es validación independiente.
- Costos fijos ($13.78) pesan más con stops de 8 ticks ($40): un stop de 8 ticks cuesta 34% extra. Si la ventaja bruta es pequeña, muere por costos.
- Muy parecida a ABU (solapamiento de señales alto): si ABU era suerte, esta también.
