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
    ssh $VM 'mkdir -p /srv/lab/repo/futures/lab /srv/lab/repo/futures/strategies'
    rsync -az --delete --exclude '__pycache__' --exclude 'results' --exclude 'registry' "$ROOT/futures/lab/" $VM:/srv/lab/repo/futures/lab/
    rsync -az "$ROOT/futures/"*.json $VM:/srv/lab/repo/futures/
    rsync -az "$ROOT/futures/strategies/" $VM:/srv/lab/repo/futures/strategies/
    # el registro y los resultados viven en la VM mientras corre el motor; el push no los pisa
    rsync -az --ignore-existing "$ROOT/futures/lab/registry/" $VM:/srv/lab/repo/futures/lab/registry/ 2>/dev/null || true
    ;;
  pull)
    rsync -az $VM:/srv/lab/repo/futures/lab/registry/ "$ROOT/futures/lab/registry/"
    rsync -az $VM:/srv/lab/repo/futures/lab/results/ "$ROOT/futures/lab/results/" 2>/dev/null || true
    for f in tests.json updates.json signal_map.json; do rsync -az $VM:/srv/lab/repo/futures/$f "$ROOT/futures/$f" 2>/dev/null || true; done
    ;;
  *) echo "uso: sync_vm.sh push|pull"; exit 1;;
esac
echo "sync $1 ok"
