# Laboratorio NQ · estado actual

_Generado automáticamente el 2026-10-24 16:35 UTC desde el registro, tests.json, backlog.json y signal_map.json. No editar a mano: cambia los archivos fuente._

Página: https://cryptobot-liga.vercel.app · Guía del repo: `docs/README.md` · Decisiones: `docs/decisions.md`

## En una línea

- Sesiones válidas de diseño: **576** (examen sellado desde 2026-04-22, cerrado).
- Intentos registrados: **667** · pruebas publicadas: **14** (error 1, superada 7, no_pasa 4, revisar 2).
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
| T2-ABS-EARLY | ABS con entrada temprana | **propuesta** | P003 + placebo del Red Team | cuenta como versión 2 de 3 de ABS; aprobación de Oscar |
| T2-ABS-HOURS | ABS v1 en toda la sesión de Nueva York | **propuesta** | P003 · pocas operaciones | si se combina con T2-ABS-EARLY es una sola v2; máximo 3 versiones |
| T2-ICE | Icebergs con definición medida | **descartada** | mapa v1 · ice | agregar tamaños 'antes' del libro al lector de sesión |
| M2-DIR | Mapa v2 con azar de dirección aleatoria | **corrida** → mapa_v2 | revisión del mapa v1 | cambio de código en signal_map.py; estudio mapa_v2 registrado |
| T3-SMT | Divergencia NQ vs ES (SMT) | **propuesta** | videos · plan v1 | descargar datos tick de ES (laptop ATAS); lector canónico para ES |

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

- sin notas todavía (se suben desde la página › Estrategias › Buzón de Oscar)

## Preguntas abiertas para Oscar

1. ¿Los niveles que tú miras son los del perfil de Nueva York del día anterior (09:30–16:00) o del día completo (incluida la noche)? Hoy usamos Nueva York.
2. Para una 'orden grande', ¿te importa más el tamaño absoluto (70–100 contratos) o lo raro que es ese tamaño para esa hora? La v1 usa percentil 99 de las 20 sesiones anteriores.
3. Cuando ves absorción, ¿cuánto tiempo esperas la confirmación antes de descartarla? La v1 espera 60 s.
4. ¿Operas después de las 11:30? La v1 cierra todo a las 11:45. Si tú operas la tarde, vale la pena una variante.
5. ¿Qué stop usas en puntos para un scalp normal y cuánto máximo aguantas en tu peor operación? Lo necesito para comparar con los 24 ticks (6 puntos) de BIG.
6. ¿Puedes abrir en ATAS el 27 de febrero de 2025 (NQH5, Nueva York) y comparar: máximo 21381.00, mínimo 20597.75, POC 21050.00, VAH 21235.25, VAL 20847.25? Si coincide, cerramos la validación visual.
7. ¿Hay alguna señal que uses y que no esté en la lista de 12 del mapa? Si sí, se agrega al mapa 2.

## Últimos movimientos (bitácora)

- 2026-10-24 · avance · Comité con PIN: Jose Miguel y Oscar votan desde la página
- 2026-10-24 · avance · Buzón con captura de pantalla en todas las pestañas
- 2026-10-24 · prueba · Repeticiones con el motor 1.1: BIG v2 (P010) y HVN v1 (P011) no pasan
- 2026-10-24 · avance · ES y YM en el servidor
- 2026-10-24 · hallazgo · Revisión ciega: el motor 1.0 era optimista y todas las pruebas se repiten
- 2026-10-24 · prueba · Prueba P007 · BIG v2 · no pasa
- 2026-10-24 · prueba · Prueba P008 · ORB v1 · no pasa
- 2026-10-24 · prueba · Prueba P009 · ORB v1 · no pasa

## Cómo se corre una prueba nueva

1. Escribir la regla en `futures/strategies/v<N>.json`, sellar (`ots stamp`), registrar el estudio (`engine/register_study.py`).
2. Poner la prueba en `futures/backlog.json` con estado `congelada` y `./futures/lab/sync_vm.sh push`.
3. El orquestador (cron en la VM, cada 15 min) la corre dos veces en contenedores efímeros sin red con datos en solo lectura; publica solo si `trades.csv` es idéntico.
4. `./futures/lab/sync_vm.sh pull && .venv/bin/python portal/build_futures_site.py && git push origin main`.
5. Si pasa o queda en revisar: `engine/redteam_pack.py <id>` → revisión ciega → `docs/redteam/<id>.md`.

