"""Rutas, costos y reglas congeladas. Nada aquí se calcula: todo se lee de los JSON del repo."""
import hashlib, json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)                      # futures/lab
FUT = os.path.dirname(LAB)                       # futures
ROOT = os.path.dirname(FUT)                      # repo
DATA = os.environ.get("LAB_DATA", "/srv/lab/data")
CAN = os.path.join(DATA, "canonical", "NQ")
FEAT = os.path.join(DATA, "features")
RESULTS = os.environ.get("LAB_RESULTS", os.path.join(LAB, "results"))   # el contenedor efímero escribe en /out
REGISTRY = os.path.join(LAB, "registry")
TZ = "America/New_York"
TICK_T = 1            # precios en ticks enteros (precio*4)
TICK_USD = 5.0


def _load(name):
    p = os.path.join(FUT, name)
    with open(p, encoding="utf-8") as f:
        raw = f.read()
    return json.loads(raw), hashlib.sha256(raw.encode()).hexdigest()


def costs():
    return _load("costs.json")


def topstep():
    return _load("topstep_rules.json")


def protocol():
    return _load("protocol.json")


def strategies(version=1):
    return _load(f"strategies/v{version}.json")


def strategy_file(strategy, version):
    """Archivo strategies/v*.json donde está registrada (estrategia, versión). (nombre, dict, sha) o None."""
    import glob
    for f in sorted(glob.glob(os.path.join(FUT, "strategies", "v*.json"))):
        if not re.fullmatch(r"v\d+\.json", os.path.basename(f)):
            continue
        d, h = _load("strategies/" + os.path.basename(f))
        for e in d.get("estrategias", []):
            if e["id"] == strategy and int(e.get("version", 1)) == int(version):
                return os.path.basename(f), d, h
    return None


def sessions_manifest():
    return _load("sessions_manifest.json")


def design_sessions():
    m, h = sessions_manifest()
    return m["sesiones_diseno_validas"], m["sesiones_diseno_sha256"]


def git_commit():
    """Commit del repo; en la VM (sin .git) se lee el archivo GIT_COMMIT que escribe sync_vm.sh."""
    try:
        return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        p = os.path.join(LAB, "GIT_COMMIT")
        return open(p).read().strip() if os.path.exists(p) else "sin-git"


def git_dirty():
    try:
        return bool(subprocess.check_output(["git", "-C", ROOT, "status", "--porcelain", "--", "futures"], text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        return None


def config_hash(obj):
    """Huella de una configuración (independiente del orden de las llaves)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


class Costs:
    """Costos de una corrida. slip_ticks es por lado."""
    def __init__(self, slip_ticks=None, commission_rt=None):
        c, self.sha = costs()
        self.slip_ticks = c["deslizamiento_ticks_por_lado"] if slip_ticks is None else slip_ticks
        self.commission_rt = c["comision_round_turn_usd"] if commission_rt is None else commission_rt
        self.tick_usd = c["tick_usd"]
        self.liq_fee = c.get("liquidacion_forzada_usd", 10.0)

    def round_turn_usd(self, contracts=1):
        return contracts * (self.commission_rt + 2 * self.slip_ticks * self.tick_usd)

    def as_dict(self):
        return {"slip_ticks_por_lado": self.slip_ticks, "comision_rt": self.commission_rt, "tick_usd": self.tick_usd}
