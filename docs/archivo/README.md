# Laboratorio NQ · order flow sobre datos tick

Proyecto de Jose Miguel y Oscar. Reorientado el 2026-10-22 desde cripto/acciones (archivado en `docs/archivo/`
y en la etiqueta git `archivo-cripto-acciones-2026-10-22`). Nada toca dinero real.

**Página:** https://cryptobot-liga.vercel.app (una sola página con pestañas: Floor · Pruebas · Estrategias · Explorador · Bitácora).

## Qué hay aquí

| Carpeta / archivo | Qué es |
|---|---|
| `futures/lab_rules.json` | Reglas del laboratorio (instrumento, horario, costos, criterio Topstep, sesiones, registro). |
| `futures/costs.json` | Costos exactos verificados: NQ $3.78 ida y vuelta + 1 tick/lado. |
| `futures/topstep_rules.json` | Reglas de la cuenta Topstep $50K verificadas (MLL, DLL, consistencia, contratos). |
| `futures/protocol.json` | Protocolo estadístico: RAND emparejado, p valores, largo mínimo, criterios de muerte, DSR, CPCV, Red Team. |
| `futures/research_plan.json` | Plan de investigación v1: mapa de señales → tandas de 3 → comité. |
| `futures/strategies/v1.json` | Estrategias BIG, ABS y POC v1, congeladas antes de probar. Cambios = v2. |
| `futures/sessions_manifest.json` | Lista congelada de sesiones válidas (576 de diseño) con motivo de cada exclusión. |
| `futures/news.json` | Fechas de Fed, CPI y NFP y ventanas sin entradas. |
| `futures/signal_map.json` | Resultado de la fase 1 (lo escribe el motor). |
| `futures/tests.json` | Fichas de todas las pruebas corridas (lo escribe el motor). |
| `futures/updates.json` | Bitácora (manual + automática por prueba). |
| `futures/lab/engine/` | Motor de pruebas (ver abajo). |
| `futures/lab/registry/` | Registro de estudios e intentos, solo agregar, con cadena de huellas. |
| `futures/lab/results/<id>/` | Operaciones (csv/json) y hoja de resultados de cada prueba. |
| `futures/lab/ingest.py`, `features.py`, `sessions_audit.py`, `export_day.py` | Lector canónico, medidas por sesión, auditoría de sesiones, exportador del explorador. |
| `portal/build_futures_site.py` | Genera `site/index.html` y `site/data/*.json` para Vercel. |
| `docs/decisions.md` | Registro de decisiones (se mantiene a mano, se publica en la página). |
| `*.ots` | Sellos OpenTimestamps de cada documento congelado (prueba externa de fecha). |

## Dónde están los datos

Servidor **rt-oscar-lab** (Tailscale 100.88.193.80, alias ssh `rt-oscar-lab`), `/srv/lab`:
`data/raw/NQ` (727 sesiones ATAS, solo lectura, SHA-256 verificadas) · `data/canonical/NQ` (595 parquet de diseño) ·
`data/features` (perfil, órdenes, resumen, `lab_stats_NQ.jsonl`) · `data/sealed` (examen 2026-04-22→10-22, cifrado; llave fuera del servidor).
El motor corre en la VM desde `/srv/lab/repo/futures/lab` con `/srv/lab/.venv/bin/python`.

## Cómo se corre una prueba

```sh
sh futures/lab/sync_vm.sh push                                   # Mac -> VM (motor + JSON congelados)
ssh rt-oscar-lab 'cd /srv/lab/repo/futures/lab && /srv/lab/.venv/bin/python -m engine.register_study tanda1'
ssh rt-oscar-lab 'cd /srv/lab/repo/futures/lab && /srv/lab/.venv/bin/python -m engine.run_test --strategy BIG --version 1 --study tanda1 --sens'
ssh rt-oscar-lab 'cd /srv/lab/repo/futures/lab && /srv/lab/.venv/bin/python -m engine.signal_map --study mapa_v1'
sh futures/lab/sync_vm.sh pull                                   # VM -> Mac (results, registry, tests.json, signal_map.json, updates.json)
.venv/bin/python portal/build_futures_site.py && git add -A && git commit -m "..." && git push origin main
```

Pruebas unitarias del motor (cinta sintética, sin datos): `cd futures/lab && LAB_DATA=/tmp/x ../../.venv/bin/python tests/test_engine.py`.

## Reglas que ningún programa puede saltarse

1. Las reglas de una estrategia se escriben y se congelan (SHA-256 + OTS) antes de probar. Cualquier cambio es versión nueva y cuenta como intento.
2. Un estudio declara cuántos intentos va a correr antes de empezar. Todo intento (bueno, malo, fallido, de sensibilidad) va al registro.
3. Los umbrales se calculan solo con las 20 sesiones anteriores. Nada mira el futuro; el placebo desplazado lo verifica.
4. Costos y lista de sesiones no se tocan después de ver resultados.
5. El examen sellado se abre una sola vez, con una estrategia aprobada por Jose Miguel y Oscar.
