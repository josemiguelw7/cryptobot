#!/bin/sh
# Sincroniza el laboratorio con la VM y trae de vuelta lo que el motor produce.
#   ./futures/lab/sync_vm.sh push    (código y JSON congelados -> VM)
#   ./futures/lab/sync_vm.sh pull    (registro, resultados, tests.json, updates.json, signal_map.json <- VM)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM=rt-oscar-lab
case "$1" in
  push)
    git -C "$ROOT" rev-parse HEAD > "$ROOT/futures/lab/COMMIT"
    git -C "$ROOT" push -q vm main 2>/dev/null || true      # espejo local en la VM: el orquestador clona commits exactos de aquí
    ssh $VM 'mkdir -p /srv/lab/repo/futures/lab /srv/lab/repo/futures/strategies'
    rsync -az --delete --exclude '__pycache__' --exclude 'results' --exclude 'registry' --exclude 'golden.json' --exclude 'regimes.json' --exclude 'runs_state.json' --exclude 'runs' "$ROOT/futures/lab/" $VM:/srv/lab/repo/futures/lab/
    rsync -az --exclude 'tests.json' --exclude 'updates.json' --exclude 'signal_map.json' "$ROOT/futures/"*.json $VM:/srv/lab/repo/futures/
    rsync -az "$ROOT/futures/strategies/" $VM:/srv/lab/repo/futures/strategies/
    # el registro y los resultados viven en la VM mientras corre el motor; el push no los pisa
    rsync -az --ignore-existing "$ROOT/futures/lab/registry/" $VM:/srv/lab/repo/futures/lab/registry/ 2>/dev/null || true
    ;;
  pull)
    rsync -az $VM:/srv/lab/repo/futures/lab/registry/ "$ROOT/futures/lab/registry/"
    rsync -az $VM:/srv/lab/repo/futures/lab/results/ "$ROOT/futures/lab/results/" 2>/dev/null || true
    rsync -az $VM:/srv/lab/repo/futures/signal_map.json "$ROOT/futures/signal_map.json" 2>/dev/null || true
    rsync -az $VM:/srv/lab/runs/state.json "$ROOT/futures/lab/runs_state.json" 2>/dev/null || true
    for f in golden.json regimes.json; do rsync -az $VM:/srv/lab/repo/futures/lab/$f "$ROOT/futures/lab/$f" 2>/dev/null || true; done
    rsync -az $VM:/srv/lab/repo/futures/canonical_manifest.json "$ROOT/futures/canonical_manifest.json" 2>/dev/null || true
    rsync -az --exclude 'src' --exclude 'out1' --exclude 'out2' $VM:/srv/lab/runs/ "$ROOT/futures/lab/runs/" 2>/dev/null || true
    # tests.json y updates.json se reconstruyen en la Mac desde results/ + registro (la Mac es la dueña de esos dos)
    (cd "$ROOT/futures/lab" && LAB_DATA=/tmp/x "$ROOT/.venv/bin/python" -m engine.rebuild_tests)
    ;;
  *) echo "uso: sync_vm.sh push|pull"; exit 1;;
esac
echo "sync $1 ok"
