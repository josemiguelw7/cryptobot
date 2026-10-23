# Laboratorio NQ · order flow sobre datos tick

Proyecto de Jose Miguel y Oscar. Objetivo: encontrar, con método, si alguna estrategia de order flow
en el futuro NQ le gana al azar después de costos y pasaría una cuenta Topstep $50K. Nada toca dinero real.

Página pública (Oscar): https://cryptobot-liga-radtak-projects.vercel.app · se despliega con `git push origin main`.
Lo anterior (cripto y acciones, cerrado el 22/10/2026) está en `docs/archivo/` y `site/archivo/`.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del laboratorio (instrumento, horario, costos, criterio Topstep) | `futures/lab_rules.json` |
| Costos exactos (verificados en Topstep) | `futures/costs.json` |
| Reglas Topstep $50K exactas | `futures/topstep_rules.json` |
| Protocolo estadístico (RAND, p, DSR, CPCV, placebos, muerte) | `futures/protocol.json` |
| Plan de investigación (fases, 12 señales, criterios) | `futures/research_plan.json` |
| Estrategias congeladas por versión | `futures/strategies/v1.json` (v2, v3…) |
| Lista congelada de sesiones válidas | `futures/sessions_manifest.json` |
| Calendario de noticias (Fed, CPI, NFP) | `futures/news.json` |
| Registro de estudios e intentos (solo agregar, cadena de huellas) | `futures/lab/registry/*.jsonl` |
| Resultados de cada prueba (operaciones CSV/JSON, hoja completa) | `futures/lab/results/<id>/` |
| Fichas publicadas de pruebas | `futures/tests.json` |
| Mapa de señales | `futures/signal_map.json` |
| Bitácora (se alimenta sola con cada prueba) | `futures/updates.json` |
| Decisiones con fecha | `docs/decisions.md` |
| Glosario y preguntas abiertas para Oscar | `docs/glosario.md`, `docs/preguntas_oscar.md` |
| Motor de pruebas | `futures/lab/engine/` |
| Lector, medidas y auditoría de datos | `futures/lab/ingest.py`, `features.py`, `sessions_audit.py` |
| Página | `portal/build_futures_site.py` → `site/index.html` |

Todo documento congelado tiene su `.ots` (OpenTimestamps) junto al archivo: prueba externa de la fecha.

## Datos
- 727 sesiones NQ (2024-01-02 → 2026-10-22), 197 M operaciones, ATAS vía Rithmic, validadas contra Databento.
- VM `rt-oscar-lab` (Tailscale 100.88.193.80): `/srv/lab/data/raw` (solo lectura), `canonical` (parquet), `features`, `sealed`.
- Examen sellado: 132 sesiones desde 2026-04-22, cifradas; la llave está solo en la Mac (`~/.radtak/lab-seal/`).
- Diseño: 595 sesiones hasta 2026-04-21 → **576 válidas** tras la auditoría (`sessions_manifest.json`).

## Cómo se corre una prueba
```
./futures/lab/sync_vm.sh push                       # código y JSON congelados a la VM
ssh rt-oscar-lab
cd /srv/lab/repo/futures/lab
/srv/lab/.venv/bin/python -m engine.register_study tanda1          # una vez, antes de correr
/srv/lab/.venv/bin/python -m engine.run_test --strategy BIG --version 1 --study tanda1 --sens
/srv/lab/.venv/bin/python -m engine.signal_map --study mapa_v1
exit
./futures/lab/sync_vm.sh pull                       # registro, resultados, tests.json, bitácora
.venv/bin/python portal/build_futures_site.py && git add -A && git commit -m "..." && git push origin main
```
Pruebas unitarias del motor: `cd futures/lab && LAB_DATA=/tmp/x ../../.venv/bin/python tests/test_engine.py`.

## Reglas que no se negocian
1. Las reglas de una estrategia se escriben y congelan **antes** de probar. Cambiar un número = versión nueva = otro intento.
2. Todo intento queda en el registro, también los fallidos y los de sensibilidad. Nadie borra líneas.
3. La lista de sesiones no se toca después de ver resultados.
4. El examen sellado se abre una sola vez, con una estrategia aprobada por el comité (Jose Miguel + Oscar).
5. La IA (Claude) diseña, propone y ataca (Red Team); las cifras las producen programas deterministas.
