# Laboratorio NQ · estado actual

_Generado automáticamente el 2026-10-23 11:35 UTC desde el registro, tests.json, backlog.json y signal_map.json. No editar a mano: cambia los archivos fuente._

Página: https://cryptobot-liga-radtak-projects.vercel.app · Guía del repo: `docs/README.md` · Decisiones: `docs/decisions.md`

## En una línea

- Sesiones válidas de diseño: **576** (examen sellado desde 2026-04-22, cerrado).
- Intentos registrados: **109** · pruebas publicadas: **4** (error 1, no_pasa 3).
- Estrategias aprobadas por el comité: **0**. Nada toca dinero real.

## Pruebas corridas

| Id | Qué | Veredicto | Neto | p vs RAND | Topstep | Causa |
|---|---|---|---|---|---|---|
| P013 | BIG v1 | **error** | −$13,718 | 0.1419 | 0.0% | umbral de orden grande mal calculado (percentil truncado y sobre todas las órdenes: 15 contratos). Ver strateg |
| P002 | BIG v1 | **no_pasa** | −$2,120 | 0.4086 | 0.0% | pierde con costos base; no gana a RAND (p=0.4086); muere con costos al doble; pierde en 2024, 2025, 2026; pasa |
| P003 | ABS v1 | **no_pasa** | $4,641 | 0.002 | 6.4% | pierde en 2025 (−$405); pasa Topstep solo 6.4% (128 operaciones en 576 sesiones no alcanzan la meta); 67.7% de |
| P004 | POC v1 | **no_pasa** | −$3,934 | 0.5794 | 12.0% | pierde con costos base; no gana a RAND (p=0.5794); muere con costos al doble; pierde en 2024, 2026; pasa Topst |

## Cola de pruebas (backlog)

Estados: propuesta → aprobada (Oscar + Jose Miguel) → congelada (reglas con huella y sello, estudio registrado) → en cola → corrida. El orquestador solo arranca las **congeladas**.

| Id | Prueba | Estado | Origen | Falta |
|---|---|---|---|---|
| T2-FADE | Desvanecer órdenes grandes | **propuesta** | mapa v1 · hipótesis inversa de BIG | reglas congeladas en strategies/v2.json; estudio tanda2 registrado con N declarado |
| T2-HVN | Rechazo de zonas HVN del día anterior | **propuesta** | mapa v1 · estilo Profit Pro | definir confirmación y stop en percentiles medidos, no inventados; reglas congeladas |
| T2-ABS-EARLY | ABS con entrada temprana | **propuesta** | P003 + placebo del Red Team | cuenta como versión 2 de 3 de ABS; aprobación de Oscar |
| T2-ABS-HOURS | ABS v1 en toda la sesión de Nueva York | **propuesta** | P003 · pocas operaciones | si se combina con T2-ABS-EARLY es una sola v2; máximo 3 versiones |
| T2-ICE | Icebergs con definición medida | **propuesta** | mapa v1 · ice | agregar tamaños 'antes' del libro al lector de sesión |
| M2-DIR | Mapa v2 con azar de dirección aleatoria | **aprobada** | revisión del mapa v1 | cambio de código en signal_map.py; estudio mapa_v2 registrado |
| T3-SMT | Divergencia NQ vs ES (SMT) | **propuesta** | videos · plan v1 | descargar datos tick de ES (laptop ATAS); lector canónico para ES |

## Estudios y cuenta de intentos

- **tanda1**: Las estrategias BIG, ABS y POC v1 (reglas de los videos con números propuestos sin medir) ganan a RAND emparejado después de costos. · declarados 51, usados 67 ⚠ excedido
- **mapa_v1**: Alguna de las 12 señales de order flow mueve el precio en la dirección predicha a 1, 5, 15 o 30 min más de lo que lo hacen momentos al azar  · declarados 48, usados 38

## Mapa de señales (resumen)

576 sesiones · 5000 sorteos · 48 pruebas · Holm 5%. Ticks promedio en la dirección predicha a 15 y 30 min; sentido = contra el azar de la misma media hora.

| Señal | Eventos | 15 min | 30 min | Veredicto |
|---|---|---|---|---|
| Órdenes grandes (tamaño y niveles barridos) | 19,255 | -6.07 | -6.71 | distinta del azar · contraria |
| Absorción | 5,782 | 3.72 | 6.07 | distinta del azar · contraria |
| Desequilibrios apilados | 12,198 | 1.24 | 1.56 | distinta del azar · contraria |
| Divergencia de delta | 33,555 | -1.43 | -0.24 | distinta del azar · a favor |
| Ruptura del rango inicial | 556 | 11.74 | 17.51 | distinta del azar · contraria |
| Agotamiento | 10,519 | 0.14 | -0.65 | distinta del azar · a favor |
| Rechazo del área de valor | 246 | -3.29 | -18.21 | distinta del azar · a favor |
| Zonas HVN (estilo Profit Pro) | 2,561 | 9.43 | 16.99 | distinta del azar · a favor |
| Desequilibrio de la mejor compra/venta | 2,480 | -5.98 | -2.75 | distinta del azar · a favor |
| Icebergs (orden que se repone) | 17 | 10.12 | 59.94 | no distinta |
| Ráfagas de intensidad | 10,152 | -1.74 | -1.0 | distinta del azar · contraria |
| Momentum primera → última media hora | 554 | -1.09 | -5.83 | distinta del azar · mixto |

## Documentos congelados

- `futures/strategies/v1.json` · 73abb571d6bab88a… · OTS ✓
- `futures/strategies/v1_aclaraciones.json` · 7bfee3753adbb8fa… · OTS ✓
- `futures/research_plan.json` · 5387f568a734f5ed… · OTS ✓
- `futures/protocol.json` · b4f30dc2cc8d1fc2… · OTS ✓
- `futures/protocol_v1.json` · dad6c111f88fab2d… · OTS ✓
- `futures/sessions_manifest.json` · 2bd01ecbb101b240… · OTS ✓
- `futures/costs.json` · 5ff35311b7dbbb73… · OTS ✓
- `futures/topstep_rules.json` · 7f2d0e0385d9d9c4… · OTS ✓
- `futures/lab_rules.json` · 16df96bb8216fb99… · OTS ✓
- `futures/news.json` · 8cede1c4dfd98531… · OTS ✓

## Preguntas abiertas para Oscar

1. ¿Los niveles que tú miras son los del perfil de Nueva York del día anterior (09:30–16:00) o del día completo (incluida la noche)? Hoy usamos Nueva York.
2. Para una 'orden grande', ¿te importa más el tamaño absoluto (70–100 contratos) o lo raro que es ese tamaño para esa hora? La v1 usa percentil 99 de las 20 sesiones anteriores.
3. Cuando ves absorción, ¿cuánto tiempo esperas la confirmación antes de descartarla? La v1 espera 60 s.
4. ¿Operas después de las 11:30? La v1 cierra todo a las 11:45. Si tú operas la tarde, vale la pena una variante.
5. ¿Qué stop usas en puntos para un scalp normal y cuánto máximo aguantas en tu peor operación? Lo necesito para comparar con los 24 ticks (6 puntos) de BIG.
6. ¿Puedes abrir en ATAS el 27 de febrero de 2025 (NQH5, Nueva York) y comparar: máximo 21381.00, mínimo 20597.75, POC 21050.00, VAH 21235.25, VAL 20847.25? Si coincide, cerramos la validación visual.
7. ¿Hay alguna señal que uses y que no esté en la lista de 12 del mapa? Si sí, se agrega al mapa 2.

## Últimos movimientos (bitácora)

- 2026-10-23 · hallazgo · Mapa de señales v1 publicado: 38 de 48 pruebas distintas del azar
- 2026-10-23 · decisión · Protocolo v2: placebo sospechoso → revisar; mapa con 5,000 sorteos
- 2026-10-23 · hallazgo · Red Team: la primera corrida tenía el umbral mal y se marca como error
- 2026-10-22 · avance · Lector y primeras medidas listos
- 2026-10-22 · avance · Examen final sellado de verdad
- 2026-10-22 · avance · Descarga completa y datos en el servidor
- 2026-10-22 · decisión · Reglas del laboratorio acordadas
- 2026-10-22 · hallazgo · Los datos de ATAS coinciden con Databento

## Cómo se corre una prueba nueva

1. Escribir la regla en `futures/strategies/v<N>.json`, sellar (`ots stamp`), registrar el estudio (`engine/register_study.py`).
2. Poner la prueba en `futures/backlog.json` con estado `congelada` y `./futures/lab/sync_vm.sh push`.
3. El orquestador (cron en la VM, cada 15 min) la corre dos veces en contenedores efímeros sin red con datos en solo lectura; publica solo si `trades.csv` es idéntico.
4. `./futures/lab/sync_vm.sh pull && .venv/bin/python portal/build_futures_site.py && git push origin main`.
5. Si pasa o queda en revisar: `engine/redteam_pack.py <id>` → revisión ciega → `docs/redteam/<id>.md`.

