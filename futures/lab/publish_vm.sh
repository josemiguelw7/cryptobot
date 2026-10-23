#!/bin/sh
# Publicación automática desde la VM: trae el estado del motor al clon de GitHub, reconstruye fichas y página,
# y hace push (Vercel despliega). Requiere la deploy key ~/.ssh/id_ed25519_github con permiso de escritura.
# Cron: */30 * * * *  (no hace nada si no hay cambios)
set -e
export GIT_SSH_COMMAND="ssh -i $HOME/.ssh/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
R=/srv/lab/site-repo; PY=/srv/lab/.venv/bin/python
[ -d $R ] || git clone -q git@github.com:josemiguelw7/cryptobot.git $R
cd $R && git fetch -q origin && git reset -q --hard origin/main
rsync -a /srv/lab/repo/futures/lab/registry/ $R/futures/lab/registry/
rsync -a /srv/lab/repo/futures/lab/results/ $R/futures/lab/results/
cp /srv/lab/repo/futures/signal_map.json $R/futures/ 2>/dev/null || true
cp /srv/lab/runs/state.json $R/futures/lab/runs_state.json 2>/dev/null || true
for f in golden.json regimes.json; do cp /srv/lab/repo/futures/lab/$f $R/futures/lab/ 2>/dev/null || true; done
cd $R/futures/lab && LAB_DATA=/tmp/x $PY -m engine.rebuild_tests >/dev/null
cd $R && $PY portal/build_futures_site.py >/dev/null
if [ -n "$(git status --porcelain)" ]; then
  git add -A && git -c user.name="nqlab-vm" -c user.email="lab@radtak.com" commit -qm "vm: resultados del orquestador $(date -u +'%F %H:%M') UTC" && git push -q origin main && echo "$(date -u) publicado" || echo "$(date -u) push fallo"
else
  echo "$(date -u) sin cambios"
fi
