# ABF v1: absorción fallida (la trampa) 

## Por qué esta prueba
- ABU (P030/P031) es la única familia con ventaja: gana el 40% de las veces y pierde el 60% con el stop. Ese 60% es información: cuando la absorción falla, el lado agresivo ganó y los pasivos quedaron atrapados.
- Todos los reversos sin nivel (DVG, FAF, VBR, SMT) perdieron con p ≈ 1.0 contra RAND: el precio tiende a seguir, no a volver. Esta prueba no desvanece: sigue la ruptura, pero solo después de ver una absorción que falló.

## Qué encontré (búsqueda 25/10/2026)
- Footprint/delta: la absorción es flujo agresivo fuerte que no mueve el precio; cuando lo mueve más allá del extremo, los vendedores/compradores pasivos son superados y los atrapados cierran a mercado, lo que acelera el movimiento (descripciones de TradingView "Footprint Delta Trap", Tradezella, NinjaTrader). Son heurísticas de vendedores de indicadores; no hay estudio estadístico. Una regla de dedo: la ruptura es creíble si el delta está claramente a su favor.
- No encontré fuentes sobre "absorción fallida" como señal de continuación: la definición es mía.

## Definición (una sola, fijada antes de correr)
1. Detector de absorción de ABU v1, sin cambios (niveles de ayer, de la noche y POC/VAH/VAL del día en desarrollo; umbral relativo; confirmación a 60 s).
2. Fallo: dentro de 300 s tras la confirmación, una celda de 10 s rompe el extremo absorbido ≥ 4 ticks y el delta de los últimos 30 s va a favor del lado que agredía.
3. Entrada a mercado en la dirección de la ruptura (a favor del lado absorbido), al cierre de esa celda. Stop 16 ticks, objetivo 2R (32), salida a 15 min. 1 contrato. 09:30–15:30. Todos los días (sin filtro de apertura: ABT mostró que el filtro por día no era la clave, y así se conserva la frecuencia).
4. Guarda de datos: no se entra si el mid de la cotización antes de la operación está a > 20 ticks del último precio.

## Hallazgo de calidad de datos (importante para todo el laboratorio)
Escaneé la cotización (solo bid/ask contra precio, sin mirar ganancias) en las 576 sesiones. Cinco sesiones tienen la cotización congelada en más del 8% de las operaciones de NY: 2024-02-02 (14%), 2024-02-22 (16%), 2025-04-07 (29%), 2026-01-29 (54%), 2026-03-06 (9%). En esos días el motor llena entradas contra una cotización falsa y un stop puede costar de $1,000 a $25,000 en una sola operación. Ejemplos: FAF (P035) pierde $36k solo en 2025-04-07; DVG (P034) $23k y SMT (P018) $40k en 2026-01-29 y 2025-04-07. Las pruebas positivas (ABS, ABU, ABI, ABD, ACC) casi no operan esos días, así que no están infladas. Las negativas están más negativas de lo real, pero siguen negativas sin esas operaciones (FAF −$14k, DVG −$34k, VBR −$27k, SMT −$25k). No toqué sesiones ni motor (están congelados); ABF lleva la guarda y se recomienda a un humano revisar si el motor debería tratar la cotización anómala (sim.py).

## Sensibilidad (16 intentos)
Ruptura 2/3/5/6 ticks, ventana de fallo 180/240/360/420 s, stop 8/12/20/24, objetivo 1/1.5/2.5/3 R.

## Humo (solo señales)
20 sesiones espaciadas: 9 señales (~0.45 por día, ~250 en el periodo).

## Riesgos
- Exploratoria: la idea sale de ver resultados del periodo de diseño; no es validación independiente.
- El que entra tarde en la ruptura puede comprar el techo; el stop de 16 ticks cuesta ~$80 + costos.
