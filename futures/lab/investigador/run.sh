#!/bin/bash
# Investigador autónomo del laboratorio NQ. Cron en la VM cada 30 min.
# Si el orquestador no tiene nada pendiente, le pide a Claude (con la suscripción de Jose, sin API key)
# que diseñe y deje congelada la siguiente prueba; luego sella, registra, publica y la entrega al orquestador.
#   Apagar:  touch /srv/lab/investigador/APAGADO      Encender: rm /srv/lab/investigador/APAGADO
set -u
D=/srv/lab/investigador; R=/srv/lab/research-repo; PY=/srv/lab/.venv/bin/python; OTS=/srv/lab/.venv/bin/ots
LIVE=/srv/lab/repo; MIRROR=/srv/lab/git/cryptobot.git; LOG=/srv/lab/logs/investigador.log
export PATH="$HOME/.local/bin:$PATH"
export GIT_SSH_COMMAND="ssh -i $HOME/.ssh/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
ts(){ date -u +%FT%TZ; }
log(){ echo "$(ts) $*" >> $LOG; }
exec 9>/tmp/investigador.lock; flock -n 9 || exit 0
[ -f $D/APAGADO ] && exit 0
if [ -f $D/pausa_hasta ] && [ "$(date +%s)" -lt "$(cat $D/pausa_hasta)" ]; then exit 0; fi

# 1) ¿el orquestador tiene trabajo? entonces no diseñamos nada nuevo
PEND=$($PY - <<'EOF'
import json, os
b = json.load(open('/srv/lab/repo/futures/backlog.json', encoding='utf-8'))
st = json.load(open('/srv/lab/runs/state.json')) if os.path.exists('/srv/lab/runs/state.json') else {}
n = 0
for p in b['pruebas']:
    s = {**p, **st.get(p['id'], {})}
    if s['estado'] in ('congelada', 'en_cola', 'corriendo') and not s.get('ultimo_error'):
        n += 1
print(n)
EOF
)
[ "$PEND" != "0" ] && exit 0

# 2) clon limpio + estado vivo de la VM
[ -d $R/.git ] || git clone -q git@github.com:josemiguelw7/cryptobot.git $R
cd $R && git fetch -q origin && git reset -q --hard origin/main && git clean -fdq || { log "no pude actualizar el clon"; exit 1; }
rsync -a $LIVE/futures/lab/registry/ $R/futures/lab/registry/
rsync -a $LIVE/futures/lab/results/ $R/futures/lab/results/ 2>/dev/null
cp /srv/lab/runs/state.json $R/futures/lab/runs_state.json 2>/dev/null
cp $LIVE/futures/backlog.json $R/futures/backlog.json
BASE=$(git rev-parse HEAD)
rm -f $D/salida.json

# 3) Claude diseña (suscripción de Jose)
set -a; . $HOME/.config/oscar-lab/claude.env; set +a
log "arranca diseño (base ${BASE:0:8})"
timeout 3h claude -p "$(cat $D/PROMPT.md)" --permission-mode acceptEdits \
  --allowedTools Bash Read Edit Write Glob Grep --settings $D/settings.json --max-turns 250 \
  > $D/ultima_salida.txt 2>&1
RC=$?
if grep -qiE "usage limit|limit reached|rate.limit|resets? (at|in)" $D/ultima_salida.txt; then
  echo $(( $(date +%s) + 3600 )) > $D/pausa_hasta; log "límite de la suscripción: pausa de 1 hora"; exit 0
fi
[ $RC -ne 0 ] && { log "claude salió con código $RC (ver ultima_salida.txt)"; exit 1; }

# 4) controles: nada sellado modificado, nada fuera de lugar
BAD=$(git diff --name-only $BASE -- 'futures/strategies/v*.json' 'futures/*.json.ots' futures/lab/engine/sim.py futures/lab/engine/stats.py futures/lab/engine/topstep.py futures/lab/engine/rand.py futures/lab/engine/golden.py futures/lab/engine/orchestrator.py futures/lab_rules.json futures/protocol.json futures/topstep_rules.json)
if [ -n "$BAD" ]; then log "RECHAZADO: tocó archivos sellados o del motor: $BAD"; git reset -q --hard $BASE; exit 1; fi
[ -f $D/salida.json ] || { log "RECHAZADO: no dejó salida.json"; exit 1; }

# 5) sellar reglas nuevas con OpenTimestamps
for f in futures/strategies/v*.json; do [ -f "$f.ots" ] || $OTS stamp "$f" >> $LOG 2>&1; done

# 6) commit + GitHub + espejo del orquestador
git add -A
git -c user.name="nqlab-investigador" -c user.email="lab@radtak.com" commit -qm "investigador: $($PY -c "import json;print(', '.join(json.load(open('$D/salida.json')).get('pruebas_congeladas',[])) or 'sin prueba nueva')")" || { log "sin cambios"; exit 0; }
for i in 1 2 3; do git pull -q --rebase origin main && git push -q origin main && break; sleep 20; done || log "push a GitHub falló"
git push -q $MIRROR HEAD:main --force || log "push al espejo falló"
git rev-parse HEAD > $R/futures/lab/COMMIT

# 7) entregar al orquestador (lo mismo que hacía sync_vm.sh push desde la laptop)
rsync -a --exclude '__pycache__' --exclude 'results' --exclude 'registry' --exclude 'golden.json' --exclude 'regimes.json' --exclude 'runs_state.json' --exclude 'runs' $R/futures/lab/ $LIVE/futures/lab/
rsync -a --exclude 'tests.json' --exclude 'updates.json' --exclude 'signal_map.json' $R/futures/*.json $LIVE/futures/
rsync -a $R/futures/strategies/ $LIVE/futures/strategies/
cd $LIVE/futures/lab
for s in $($PY -c "import json;print(' '.join(json.load(open('$D/salida.json')).get('estudios_nuevos',[])))"); do
  $PY -m engine.register_study "$s" >> $LOG 2>&1 && log "estudio $s registrado" || log "falló registrar $s"
done
log "listo $(git -C $R rev-parse --short HEAD): $($PY -c "import json;print(json.load(open('$D/salida.json')).get('resumen',''))")"
