# Laboratorio NQ · estado actual

_Generado automáticamente el 2026-10-25 19:05 UTC desde el registro, tests.json, backlog.json y signal_map.json. No editar a mano: cambia los archivos fuente._

Página: https://cryptobot-liga.vercel.app · Guía del repo: `docs/README.md` · Decisiones: `docs/decisions.md`

## En una línea

- Sesiones válidas de diseño: **576** (examen sellado desde 2026-04-22, cerrado).
- Intentos registrados: **973** · pruebas publicadas: **33** (error 1, superada 7, no_pasa 14, revisar 11).
- Estrategias aprobadas por el comité: **0**. Nada toca dinero real.

## Pruebas corridas

| Id | Qué | Veredicto | Neto | p vs RAND | Topstep | Causa |
|---|---|---|---|---|---|---|
| P013 | POC v1 | **error** | −$3,934 | 0.5804 | 12.0% | umbral de orden grande mal calculado (percentil truncado y sobre todas las órdenes: 15 contratos). Ver strateg |
| P002 | BIG v1 | **superada** | −$2,120 | 0.4086 | 0.0% | pierde con costos base; no gana a RAND (p=0.4086); muere con costos al doble; pierde en 2024, 2025, 2026; pasa |
| P003 | ABS v1 | **superada** | $4,641 | 0.002 | 6.4% | pierde en 2025 (−$405); pasa Topstep solo 6.4% (128 operaciones en 576 sesiones no alcanzan la meta); 67.7% de |
| P004 | POC v1 | **superada** | −$3,934 | 0.5794 | 12.0% | pierde con costos base; no gana a RAND (p=0.5794); muere con costos al doble; pierde en 2024, 2026; pasa Topst |
| P005 | ABS v2 | **superada** | $8,869 | 0.003 | 43.5% | pasa Topstep solo 43.5% (umbral 50%); 72% de la ganancia viene de 5 días; ganancia concentrada en 2024 (2025 + |
| P006 | HVN v1 | **superada** | −$30,239 | 0.5624 | 0.0% | pierde con costos base; no gana a RAND (p=0.5624); muere con costos al doble; pierde en 2024, 2025, 2026; pasa |
| P007 | BIG v2 | **superada** | −$72,187 | 0.8052 | 0.0% | pierde con costos base; no gana a RAND (p=0.8052); muere con costos al doble; pierde en 2024, 2025, 2026; pasa |
| P008 | ORB v1 | **superada** | −$15,144 | 0.5005 | 0.0% | pierde con costos base; no gana a RAND (p=0.5005); muere con costos al doble; pierde en 2024, 2025, 2026; pasa |
| P009 | ORB v1 | **no_pasa** | −$19,064 | 0.5455 | 0.0% | pierde con costos base; no gana a RAND (p=0.5455); no gana a RAND2 con las mismas salidas (p=0.5614); DSR 0.0  |
| P010 | BIG v2 | **no_pasa** | −$102,618 | 0.95 | 0.0% | pierde con costos base; no gana a RAND (p=0.95); no gana a RAND2 con las mismas salidas (p=0.9391); DSR 0.0 <  |
| P011 | HVN v1 | **no_pasa** | −$87,676 | 0.999 | 0.0% | pierde con costos base; no gana a RAND (p=0.999); no gana a RAND2 con las mismas salidas (p=1.0); DSR 0.0 < 0. |
| P012 | ABS v2 | **revisar** | $7,874 | 0.005 | 41.4% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.0 < 0.95 con 601 intentos; 80.9% de |
| P014 | ABS v1 | **revisar** | $4,320 | 0.003 | 3.7% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.0 < 0.95 con 634 intentos; 65.9% de |
| P015 | BIG v1 | **no_pasa** | −$2,235 | 0.4845 | 0.0% | pierde con costos base; no gana a RAND (p=0.4845); no gana a RAND2 con las mismas salidas (p=0.4675); DSR 0.0  |
| P016 | ABS v3 | **revisar** | $4,404 | 0.0539 | 13.9% | placebo desplazado sospechoso: revisión de código pendiente; además: no gana a RAND (p=0.0539); no gana a RAND |
| P017 | ACC v1 | **revisar** | $2,028 | 0.1928 | 0.0% | placebo desplazado sospechoso: revisión de código pendiente; además: 97 operaciones / 556 sesiones: por debajo |
| P018 | SMT v1 | **no_pasa** | −$67,444 | 0.958 | 1.2% | pierde con costos base; no gana a RAND (p=0.958); no gana a RAND2 con las mismas salidas (p=0.96); DSR 0.0 < 0 |
| P019 | VAR v1 | **no_pasa** | −$7,947 | 0.8911 | 0.0% | pierde con costos base; no gana a RAND (p=0.8911); no gana a RAND2 con las mismas salidas (p=0.9131); DSR 0.0  |
| P020 | ACC v2 | **revisar** | $4,346 | 0.1209 | 0.0% | placebo desplazado sospechoso: revisión de código pendiente; además: 91 operaciones / 556 sesiones: por debajo |
| P021 | ABI v1 | **revisar** | $7,261 | 0.045 | 23.0% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.0 < 0.95 con 743 intentos; 206.4% d |
| P022 | ABV v1 | **revisar** | $1,819 | 0.1648 | 12.2% | placebo desplazado sospechoso: revisión de código pendiente; además: no gana a RAND (p=0.1648); no gana a RAND |
| P023 | HVF v1 | **revisar** | $536 | 0.2607 | 4.4% | placebo desplazado sospechoso: revisión de código pendiente; además: no gana a RAND (p=0.2607); no gana a RAND |
| P024 | ABK v1 | **no_pasa** | −$36,133 | 0.5574 | 8.7% | pierde con costos base; no gana a RAND (p=0.5574); no gana a RAND2 con las mismas salidas (p=0.7812); DSR 0.0  |
| P025 | LVN v1 | **no_pasa** | −$8,670 | 0.6763 | 0.0% | pierde con costos base; no gana a RAND (p=0.6763); no gana a RAND2 con las mismas salidas (p=0.6374); DSR 0.0  |
| P026 | ABI v2 | **no_pasa** | −$1,124 | 0.3606 | 0.0% | pierde con costos base; no gana a RAND (p=0.3606); no gana a RAND2 con las mismas salidas (p=0.3057); DSR 0.0  |
| P027 | ABD v1 | **revisar** | $5,720 | 0.001 | 0.0% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.001 < 0.95 con 842 intentos; 57.8%  |
| P028 | VBR v1 | **no_pasa** | −$33,702 | 1.0 | 0.0% | pierde con costos base; no gana a RAND (p=1.0); no gana a RAND2 con las mismas salidas (p=0.998); DSR 0.0 < 0. |
| P029 | IMB v1 | **no_pasa** | −$23,784 | 0.001 | 0.0% | pierde con costos base; DSR 0.0 < 0.95 con 876 intentos; muere con costos al doble; pierde en 2024, 2025, 2026 |
| P030 | ABU v1 | **revisar** | $5,956 | 0.001 | 9.9% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.0 < 0.95 con 893 intentos; 69.1% de |
| P031 | ABU v2 | **revisar** | $11,912 | 0.001 | 41.2% | placebo desplazado sospechoso: revisión de código pendiente; además: DSR 0.0 < 0.95 con 910 intentos; 69.1% de |
| P032 | ABT v1 | **no_pasa** | −$3,589 | 0.7143 | 0.0% | pierde con costos base; no gana a RAND (p=0.7143); no gana a RAND2 con las mismas salidas (p=0.7093); DSR 0.0  |
| P033 | ABQ v1 | **no_pasa** | −$1,961 | 0.2428 | 0.0% | pierde con costos base; no gana a RAND (p=0.2428); no gana a RAND2 con las mismas salidas (p=0.2527); DSR 0.0  |
| P034 | DVG v1 | **no_pasa** | −$57,139 | 0.998 | 0.0% | pierde con costos base; no gana a RAND (p=0.998); no gana a RAND2 con las mismas salidas (p=1.0); DSR 0.0 < 0. |

## Cola de pruebas (backlog)

Estados: propuesta → aprobada (Oscar + Jose Miguel) → congelada (reglas con huella y sello, estudio registrado) → en cola → corrida. El orquestador solo arranca las **congeladas**.

| Id | Prueba | Estado | Origen | Falta |
|---|---|---|---|---|
| R-ORB1 | Repetición de P008 (ORB v1) con el motor 1.1 | **corrida** → P009 | revisión ciega P005 |  · ERROR: falló una corrida; ver log |
| R-BIG2 | Repetición de P007 (BIG v2) con el motor 1.1 | **corrida** → P010 | revisión ciega P005 |  |
| R-HVN1 | Repetición de P006 (HVN v1) con el motor 1.1 | **corrida** → P011 | revisión ciega P005 |  |
| R-ABS2 | Repetición de P005 (ABS v2) con el motor 1.1 | **corrida** → P012 | revisión ciega P005 |  |
| R-POC1 | Repetición de P004 (POC v1) con el motor 1.1 | **corrida** → P013 | revisión ciega P005 |  |
| R-ABS1 | Repetición de P003 (ABS v1) con el motor 1.1 | **corrida** → P014 | revisión ciega P005 |  |
| R-BIG1 | Repetición de P002 (BIG v1) con el motor 1.1 | **corrida** → P015 | revisión ciega P005 |  |
| T3-BIG2 | BIG v2: seguir a la orden grande con entrada inmediata y objetivo corto | **corrida** → P007 | mapa v3 |  |
| T3-ORB | ORB v1: ruptura del rango de los primeros 15 minutos | **corrida** → P008 | mapa v3 |  |
| S-SALIDAS | Estudio de salidas (TP fijo, SL fijo, tiempo, piramidar) sobre las v1 | **corrida** → salidas_v1 | Oscar · 23/10/2026 | estudio salidas_v1 registrado con 159 intentos declarados |
| T2-ABS-RUN | ABS v2: dejar correr al ganador 15 min (TP ≥ 40 puntos o sin TP), stop v1 | **corrida** → P005 | estudio de salidas · pedido de Oscar | reglas escritas y selladas en strategies/v2.json como ABS v2 (listo); aprobación de Oscar y Jose Miguel → pasar a congel |
| T2B-FADE2 | FADE v2: desvanecer órdenes grandes con objetivo corto | **descartada** | mapa v2 + humo de FADE v1 |  |
| T2B-FADEL | FADEL v1: desvanecer con entrada pasiva (orden límite con cola) | **descartada** | mapa v2 + modelo de cola del simulador |  |
| E-PROXY | Estudio: proxy de régimen en tiempo real | **corrida** → proxy_v1 | mapa v2 (HVN +53 en balance, −22 en tendencia) | estudio proxy_v1 registrado; script engine/regime_proxy.py |
| T2-FADE | Desvanecer órdenes grandes | **descartada** | mapa v1 · hipótesis inversa de BIG | reglas escritas y selladas en strategies/v2.json (listo); aprobación de Oscar y Jose Miguel → pasar a congelada |
| T2-HVN | Rechazo de zonas HVN del día anterior | **corrida** → P006 | mapa v1 · estilo Profit Pro | reglas escritas y selladas en strategies/v2.json (listo); aprobación de Oscar y Jose Miguel → pasar a congelada |
| T2-ABS-EARLY | ABS con entrada temprana | **corrida** → P016 | P003 + placebo del Red Team + P012 (ABS v2 con motor 1.1: +$7,874, p 0.005, Topstep 41%) |  |
| T2-ABS-HOURS | ABS v1 en toda la sesión de Nueva York | **descartada** | P003 · pocas operaciones | si se combina con T2-ABS-EARLY es una sola v2; máximo 3 versiones |
| T2-ICE | Icebergs con definición medida | **descartada** | mapa v1 · ice | agregar tamaños 'antes' del libro al lector de sesión |
| M2-DIR | Mapa v2 con azar de dirección aleatoria | **corrida** → mapa_v2 | revisión del mapa v1 | cambio de código en signal_map.py; estudio mapa_v2 registrado |
| T3-SMT | Divergencia NQ vs ES (SMT) | **corrida** → P018 | videos · plan v1 |  |
| E-HVN-FUERZA | Estudio: qué hace poderoso a un HVN (base del indicador para ATAS) | **aprobada** | pedido de Oscar en el buzón (24/10/2026): indicador de ATAS que muestre HVN poderosos en vivo | estudio registrado antes de correr (fases y umbrales); definición de 'HVN poderoso' congelada con huella y sello; cheque |
| E-ACEPTACION-VA | Aceptación fuera del valor (VAH/VAL) · ACC v1 | **corrida** → P017 | nota del buzón de Oscar (2026-10-25), resumida por el asistente |  |
| T4-VAR | Regla del 80%: re-entrada aceptada al área de valor · VAR v1 | **corrida** → P019 | pendiente de aceptacion.md (VAR v1) · ACC v1 casi positiva (P017: +$2,028 pero sin significancia): se prueba el espejo |  |
| T5-ACC2 | ACC v2: aceptación fuera de los bordes de la subasta anterior, solo días que abren dentro del valor | **corrida** → P020 | pedido de Oscar (aceptación, 25/10/2026) · P017 casi positiva · tablas por régimen de P012, P016, P017 |  |
| T6-ABI | ABI v1: absorción en los niveles del propio día | **corrida** → P021 | ABS v2 (P012) única familia positiva; ABS agotó sus 3 versiones; niveles de ayer ya probados (HVN, POC, ACC, VAR) |  |
| T7-ABV | ABV v1: absorción en el valor en desarrollo del día (POC, VAH, VAL) | **corrida** → P022 | P021 (ABI v1: +$7,261, p 0.045; POC/VAH/VAL en desarrollo +$9.4 mil en 72 operaciones, extremos y VWAP −$2.2 mil) · familia de absorción, única positiva |  |
| T8-HVF | HVF v1: absorción en HVN poderoso del día anterior | **corrida** → P023 | pedido de Oscar (E-HVN-FUERZA, 24/10/2026) · familia de absorción, única positiva |  |
| T9-ABK | ABK v1: absorción medida con el libro (la mejor oferta aguanta y se repone) | **corrida** → P024 | familia de absorción (única positiva: P012, P021) · definición de ATAS/Bookmap en docs/investigacion/absorcion_libro.md |  |
| T10-LVN | LVN v1: travesía de un vacío de volumen del perfil de ayer con flujo iniciador | **corrida** → P025 | hueco de investigación: LVN nunca probado; familia de absorción agotada (P024 ABK no pasa) |  |
| T11-ABI2 | ABI v2: absorción en los niveles del propio día, tarde (11:30–15:30) | **corrida** → P026 | P021 + parte del día nunca medida |  |
| T12-ABD | ABD v1: absorción en niveles de ayer, solo días que abren dentro del valor | **corrida** → P027 | P012/P014/P016/P017/P020: la absorción y la aceptación solo ganan en días que abren dentro del valor; ABS agotó sus 3 versiones |  |
| T13-VBR | VBR v1: reversión a la VWAP desde la banda de 2σ, días que abren dentro del valor | **corrida** → P028 | P012/P016/P017/P027: lo que gana lo hace en días de balance, pero con ~100 operaciones y Topstep bajo; se busca una idea distinta con más frecuencia |  |
| T14-IMB | IMB v1: desequilibrios diagonales apilados y reprueba de la zona | **corrida** → P029 | hueco de investigación: desequilibrios nunca probados; la absorción (única positiva) tiene pocas operaciones y no llega a Topstep · P028 (VBR) no pasa |  |
| T15-ABU | ABU v1: absorción unificada (niveles de ayer + valor en desarrollo), solo días que abren dentro del valor | **corrida** → P030 | P027 (ABD v1) + P021/P022 por régimen · P029 (IMB v1) no pasa: la pila de desequilibrios no tiene ventaja bruta |  |
| T16-ABU2 | ABU v2: las señales de ABU v1 con 2 contratos (tamaño fijado por el límite diario de Topstep) | **corrida** → P031 | P030 (ABU v1): el problema de Topstep es lentitud, no pérdidas · overnight/Londres no se puede probar sin cambiar rand.py |  |
| T17-ABT | ABT v1: absorción a favor de la tendencia, días que abren fuera del valor de ayer | **corrida** → P032 | P031 (ABU v2): más tamaño no resuelve Topstep (41.2%, 214 cuentas rompen MLL); la frecuencia debe venir de días que ABU/ABD no operan |  |
| T18-ABQ | ABQ v1: absorción rápida (ventana de 30 s) en días que abren dentro del valor | **corrida** → P033 | P032 (ABT v1) no pasa: ampliar días no sirve; ABU (P030/P031) es la única familia con ventaja pero lenta y con costos de riesgo por operación altos |  |
| T19-DVG | DVG v1: divergencia de delta acumulado en el extremo del día | **corrida** → P034 | P033 (ABQ v1) no pasa: la absorción depende de niveles y de días de balance y no gana frecuencia; falta una señal de flujo agresivo independiente del nivel |  |
| T20-FAF | FAF v1: subasta fallida en los extremos de ayer y de la noche | **congelada** | P034 (DVG v1) no pasa: el agotamiento sin nivel no sirve; falta probar el intento fallido en los niveles donde ABU sí tiene ventaja |  |

## Estudios y cuenta de intentos

- **tanda1**: Las estrategias BIG, ABS y POC v1 (reglas de los videos con números propuestos sin medir) ganan a RAND emparejado después de costos. · declarados 51, usados 67 ⚠ excedido
- **mapa_v1**: Alguna de las 12 señales de order flow mueve el precio en la dirección predicha a 1, 5, 15 o 30 min más de lo que lo hacen momentos al azar  · declarados 48, usados 38
- **salidas_v1**: Pedido de Oscar (23/10/2026): con las mismas señales v1, un take profit fijo (20/30/40/50 puntos), otro stop fijo (3/4/6/8 puntos), más tiem · declarados 159, usados 159
- **mapa_v2**: Las 12 señales, además del azar de la misma dirección, se comparan contra un azar con dirección aleatoria (¿la dirección es rentable?), se p · declarados 72, usados 24
- **tanda2**: FADE v1 (desvanecer órdenes grandes), HVN v1 (rechazo de nodos de ayer) y ABS v2 (dejar correr al ganador), con números medidos en el mapa v · declarados 51, usados 34
- **tanda2b**: FADE v2 (objetivo 8, stop 12, 10 min) y FADEL v1 (entrada pasiva con cola) capturan el efecto de 6–7 ticks contra las órdenes grandes y gana · declarados 34, usados 0
- **mapa_v3**: Repetición del mapa v2 midiendo desde el mid del libro operable (bid/ask antes del primer llenado posterior) en vez del último llenado, que  · declarados 72, usados 12
- **proxy_v1**: Con el rango y el cuerpo de los primeros 15 minutos, la apertura dentro/fuera del valor y la distancia al VWAP a las 09:45 se puede anticipa · declarados 1, usados 1
- **tanda3**: BIG v2 (seguir la orden grande con entrada inmediata, objetivo 12, stop 16) y ORB v1 (ruptura del rango inicial, 16/16, 30 min), con premisa · declarados 34, usados 32
- **repeticion_1_1**: Repetición de P002–P008 con el motor 1.1 (llenados corregidos tras la revisión ciega del 24/10/2026). Las reglas selladas no cambian. Se esp · declarados 119, usados 116
- **salidas_1_1**: Repetición del estudio de salidas (pedido de Oscar) con el motor 1.1 y percentiles exactos. · declarados 159, usados 159
- **mapa_v4**: Repetición del mapa v3 con percentiles exactos de órdenes y ventanas (los umbrales de 'órdenes grandes' y 'absorción' cambian). · declarados 72, usados 12
- **abs_v3**: ABS v3 (absorción con entrada temprana, sin confirmación de 60 s, stop v1, salida por tiempo a 15 min) gana a RAND y RAND2 después de costos · declarados 17, usados 16
- **aceptacion_v1**: Pedido de Oscar (25/10/2026): cuando el precio sale del área de valor de ayer (VAH/VAL) y la acepta (180 s seguidos fuera con delta agresivo · declarados 17, usados 14
- **smt_v1**: T3-SMT (aprobada por Jose Miguel 24/10/2026): cuando NQ barre el máximo (mínimo) de la sesión y ES no lo confirma, y NQ regresa adentro en m · declarados 17, usados 16
- **regla80_v1**: VAR v1 (regla del 80%, pendiente de aceptacion.md): cuando el precio abre fuera del área de valor de ayer (VAH/VAL), vuelve adentro y se que · declarados 17, usados 15
- **aceptacion_v2**: ACC v2 (aceptación fuera de los bordes de la subasta anterior: VAH, VAL, máximo y mínimo de ayer, máximo y mínimo de la noche; solo días que · declarados 17, usados 14
- **abi_v1**: ABI v1 (absorción en los niveles del propio día: máximo y mínimo de la sesión, VWAP, POC/VAH/VAL del perfil en desarrollo; mismo detector de · declarados 17, usados 17
- **abv_v1**: ABV v1 (absorción de flujo agresivo en POC, VAH y VAL del perfil en desarrollo del propio día; mismo detector que ABS/ABI con confirmación a · declarados 17, usados 17
- **hvf_v1**: HVF v1 (E-HVN-FUERZA, pedido de Oscar): la absorción de flujo agresivo (mismo detector que ABS, confirmación a 60 s, salida a 15 min) en un  · declarados 17, usados 17
- **abk_v1**: ABK v1 (absorción medida con el libro, no solo con el precio): cuando entra ≥ p95 de flujo agresivo de un lado en 60 s, la mejor oferta cont · declarados 17, usados 16
- **lvn_v1**: LVN v1 (travesía de un vacío de volumen del perfil NY de ayer: cubos de 8 ticks, cubo fino ≤ percentil 20, vacío ≥ 16 ticks): cuando el prec · declarados 17, usados 15
- **abi_v2**: ABI v2 (misma absorción en los niveles del propio día que ABI v1, pero en la tarde de Nueva York, entradas 11:30–15:30, cierre 15:45, umbral · declarados 17, usados 17
- **abd_v1**: ABD v1 (absorción de flujo agresivo en los niveles de ayer y de la noche, solo en días que abren dentro del valor de ayer, entradas 09:30–15 · declarados 17, usados 17
- **vbr_v1**: VBR v1 (reversión a la VWAP desde la banda de 2σ, solo en días que abren dentro del valor de ayer): cuando el precio toca VWAP ± 2σ (pondera · declarados 17, usados 17
- **imb_v1**: IMB v1 (desequilibrios diagonales apilados): cuando en 60 s hay 3 o más precios seguidos con desequilibrio agresivo diagonal >= 3:1 y >= 10  · declarados 17, usados 17
- **abu_v1**: ABU v1 (absorción de flujo agresivo en los niveles de ayer y de la noche y en POC/VAH/VAL del perfil en desarrollo, solo en días que abren d · declarados 17, usados 17
- **abu_v2**: ABU v2 (las mismas señales de ABU v1 —absorción de flujo agresivo en niveles de ayer y de la noche y en POC/VAH/VAL del día, solo días que a · declarados 17, usados 17
- **abt_v1**: ABT v1 (absorción de flujo agresivo A FAVOR de la tendencia, solo en días que abren FUERA del valor de ayer: si abre sobre el VAH solo se co · declarados 17, usados 17
- **abq_v1**: ABQ v1 (el detector de absorción de ABU v1 a escala de scalping: ventana de flujo agresivo de 30 s con umbral relativo p90 de la hora anteri · declarados 17, usados 17
- **dvg_v1**: DVG v1 (divergencia de delta acumulado en el extremo del día: nuevo máximo de la sesión con menos delta acumulado que el máximo anterior, ma · declarados 13, usados 13
- **faf_v1**: FAF v1 (subasta fallida: una celda de 10 s cruza VAH/máximo de ayer/máximo de la noche (o VAL/mínimos) ≥ 2 ticks con flujo agresivo del lado · declarados 17, usados 0

## Mapa de señales (resumen)

576 sesiones · 5000 sorteos · 48 pruebas · Holm 5%. Ticks promedio en la dirección predicha a 15 y 30 min; sentido = contra el azar de la misma media hora.

| Señal | Eventos | 15 min | 30 min | Veredicto |
|---|---|---|---|---|
| Órdenes grandes (tamaño y niveles barridos) | 19,257 | 12.42 | 12.16 | distinta del azar · mixto |
| Absorción | 5,784 | 3.68 | 7.98 | distinta del azar · contraria |
| Desequilibrios apilados | 12,202 | 1.47 | 1.83 | distinta del azar · contraria |
| Divergencia de delta | 33,785 | -1.4 | -0.66 | distinta del azar · a favor |
| Ruptura del rango inicial | 556 | 8.22 | 17.79 | distinta del azar · contraria |
| Agotamiento | 10,519 | 0.06 | -0.78 | distinta del azar · a favor |
| Rechazo del área de valor | 246 | -1.27 | -13.05 | distinta del azar · a favor |
| Zonas HVN (estilo Profit Pro) | 2,561 | -11.8 | -4.52 | distinta del azar · a favor |
| Desequilibrio de la mejor compra/venta | 2,481 | -6.19 | -3.31 | no distinta |
| Icebergs (orden que se repone) | 17 | 8.94 | 59.68 | no distinta |
| Ráfagas de intensidad | 10,153 | -3.45 | -2.58 | distinta del azar · contraria |
| Momentum primera → última media hora | 554 | -0.98 | -5.87 | distinta del azar · mixto |

## Documentos congelados

- `futures/strategies/v1.json` · 73abb571d6bab88a… · OTS ✓
- `futures/strategies/v1_aclaraciones.json` · 7bfee3753adbb8fa… · OTS ✓
- `futures/strategies/v2.json` · d2145d6dbd0c76f7… · OTS ✓
- `futures/strategies/v2_aclaraciones.json` · fd6e4bc634b51536… · OTS ✓
- `futures/strategies/v3.json` · 8f3620feb56b07d9… · OTS ✓
- `futures/strategies/v4.json` · edc0cd12ce8fe98c… · OTS ✓
- `futures/research_plan.json` · 5387f568a734f5ed… · OTS ✓
- `futures/protocol.json` · 5b094ef861a68140… · OTS ✓
- `futures/protocol_v1.json` · dad6c111f88fab2d… · OTS ✓
- `futures/protocol_v2.json` · b4f30dc2cc8d1fc2… · OTS ✓
- `futures/sessions_manifest.json` · 2bd01ecbb101b240… · OTS ✓
- `futures/costs.json` · 5ff35311b7dbbb73… · OTS ✓
- `futures/topstep_rules.json` · 7f2d0e0385d9d9c4… · OTS ✓
- `futures/lab_rules.json` · 16df96bb8216fb99… · OTS ✓
- `futures/news.json` · 8cede1c4dfd98531… · OTS ✓

## Buzón de Oscar

- `docs/oscar/inbox/2026-10-25_0230_has-probado-aceptacion.md`
- `docs/oscar/inbox/2026-10-24_1645_sugerencia-o-pedido-aparte-de-las-pruebas-que-estas-haciendo.md`

## Preguntas abiertas para Oscar

1. ¿Los niveles que tú miras son los del perfil de Nueva York del día anterior (09:30–16:00) o del día completo (incluida la noche)? Hoy usamos Nueva York.
2. Para una 'orden grande', ¿te importa más el tamaño absoluto (70–100 contratos) o lo raro que es ese tamaño para esa hora? La v1 usa percentil 99 de las 20 sesiones anteriores.
3. Cuando ves absorción, ¿cuánto tiempo esperas la confirmación antes de descartarla? La v1 espera 60 s.
4. ¿Operas después de las 11:30? La v1 cierra todo a las 11:45. Si tú operas la tarde, vale la pena una variante.
5. ¿Qué stop usas en puntos para un scalp normal y cuánto máximo aguantas en tu peor operación? Lo necesito para comparar con los 24 ticks (6 puntos) de BIG.
6. ¿Puedes abrir en ATAS el 27 de febrero de 2025 (NQH5, Nueva York) y comparar: máximo 21381.00, mínimo 20597.75, POC 21050.00, VAH 21235.25, VAL 20847.25? Si coincide, cerramos la validación visual.
7. ¿Hay alguna señal que uses y que no esté en la lista de 12 del mapa? Si sí, se agrega al mapa 2.

## Últimos movimientos (bitácora)

- 2026-10-25 · prueba · Prueba P016 · ABS v3 · revisar
- 2026-10-25 · prueba · Prueba P017 · ACC v1 · revisar
- 2026-10-25 · prueba · Prueba P018 · SMT v1 · no pasa
- 2026-10-25 · prueba · Prueba P019 · VAR v1 · no pasa
- 2026-10-25 · prueba · Prueba P020 · ACC v2 · revisar
- 2026-10-25 · prueba · Prueba P021 · ABI v1 · revisar
- 2026-10-25 · prueba · Prueba P022 · ABV v1 · revisar
- 2026-10-25 · prueba · Prueba P023 · HVF v1 · revisar

## Cómo se corre una prueba nueva

1. Escribir la regla en `futures/strategies/v<N>.json`, sellar (`ots stamp`), registrar el estudio (`engine/register_study.py`).
2. Poner la prueba en `futures/backlog.json` con estado `congelada` y `./futures/lab/sync_vm.sh push`.
3. El orquestador (cron en la VM, cada 15 min) la corre dos veces en contenedores efímeros sin red con datos en solo lectura; publica solo si `trades.csv` es idéntico.
4. `./futures/lab/sync_vm.sh pull && .venv/bin/python portal/build_futures_site.py && git push origin main`.
5. Si pasa o queda en revisar: `engine/redteam_pack.py <id>` → revisión ciega → `docs/redteam/<id>.md`.

