"""
CRYPTOBOT mission control - local web portal.
Read-only views over bot state, trades, equity, and backtest results,
plus a whitelisted job runner for the test suite.
Binds to 127.0.0.1 only. Run: .venv/bin/python portal/app.py
"""
import csv, glob, json, os, subprocess
from flask import Flask, jsonify, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = os.path.join(ROOT, ".venv", "bin", "python")
LOGS = os.path.join(ROOT, "logs")

JOBS = {
    "daily": ["bot/daily.py"],
    "league_cycle": ["bot/league.py"],
    "build_site": ["portal/build_site.py"],
    "engine_tests": ["backtest/test_engine.py"],
    "trend_exam": ["backtest/trend_exam.py"],
    "pit_rotation": ["backtest/pit_rotation.py"],
    "walkforward": ["backtest/walkforward.py"],
    "scanner": ["backtest/scanner.py"],
    "multi": ["backtest/multi.py"],
}

app = Flask(__name__)


@app.get("/public")
def public_site():
    return send_from_directory(os.path.join(ROOT, "site"), "index.html")


@app.get("/")
def index():
    return send_from_directory(os.path.join(HERE, "static"), "index.html")


@app.get("/api/state")
def state():
    p = os.path.join(ROOT, "bot", "state.json")
    if not os.path.exists(p):
        return jsonify({})
    with open(p) as f:
        return jsonify(json.load(f))


@app.get("/api/trades")
def trades():
    p = os.path.join(LOGS, "paper_trades.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f))[-200:])


@app.get("/api/equity")
def equity():
    p = os.path.join(LOGS, "equity_history.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f)))


@app.get("/api/league")
def league():
    p = os.path.join(ROOT, "bot", "league_state.json")
    if not os.path.exists(p):
        return jsonify({})
    with open(p) as f:
        return jsonify(json.load(f))


@app.get("/api/league_equity")
def league_equity():
    p = os.path.join(LOGS, "league_equity.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f)))


@app.get("/api/league_trades")
def league_trades():
    p = os.path.join(LOGS, "league_trades.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f))[-200:])


@app.get("/api/results")
def results():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "backtest", "results", "*.csv"))):
        with open(f) as fh:
            out[os.path.basename(f)] = list(csv.DictReader(fh))
    return jsonify(out)


@app.post("/api/run/<job>")
def run_job(job):
    if job not in JOBS:
        return jsonify({"error": "unknown job"}), 404
    os.makedirs(LOGS, exist_ok=True)
    log = os.path.join(LOGS, f"job_{job}.log")
    lf = open(log, "w")
    subprocess.Popen([PY, "-u"] + JOBS[job], cwd=ROOT,
                     stdout=lf, stderr=subprocess.STDOUT)
    return jsonify({"started": job})


@app.get("/api/joblog/<job>")
def joblog(job):
    if job not in JOBS:
        return jsonify({"error": "unknown job"}), 404
    log = os.path.join(LOGS, f"job_{job}.log")
    if not os.path.exists(log):
        return jsonify({"log": ""})
    with open(log, errors="replace") as f:
        return jsonify({"log": f.read()[-8000:]})


@app.get("/api/squad")
def squad_state():
    p = os.path.join(ROOT, "bot", "squad_state.json")
    if not os.path.exists(p):
        return jsonify({})
    with open(p) as f:
        return jsonify(json.load(f))


@app.get("/api/squad_equity")
def squad_equity():
    p = os.path.join(LOGS, "squad_equity.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f))[-4000:])


@app.get("/api/squad_stocks")
def squad_stocks():
    p = os.path.join(ROOT, "bot", "squad_stocks_state.json")
    if not os.path.exists(p):
        return jsonify({})
    with open(p) as f:
        return jsonify(json.load(f))


@app.get("/api/squad_stocks_equity")
def squad_stocks_equity():
    p = os.path.join(LOGS, "squad_stocks_equity.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f))[-4000:])


@app.get("/api/exam_ledger")
def exam_ledger():
    p = os.path.join(ROOT, "backtest", "results", "exam_ledger.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f)))


def _armed(mod):
    try:
        with open(os.path.join(ROOT, "bot", mod)) as f:
            for line in f:
                if line.startswith("ARMED"):
                    return "True" in line.split("#")[0]
    except OSError:
        return None


@app.get("/api/meta")
def meta():
    armed = _armed("seeds_crypto.py")
    armed_stk = _armed("seeds_stocks.py")
    def last_ts(fname, col="time"):
        p = os.path.join(LOGS, fname)
        if not os.path.exists(p):
            return None
        rows = list(csv.DictReader(open(p)))
        return rows[-1][col] if rows else None
    return jsonify({"armed": armed, "armed_crypto": armed,
                    "armed_stocks": armed_stk,
                    "league_last": last_ts("league_equity.csv"),
                    "squad_last": last_ts("squad_equity.csv"),
                    "squad_stk_last": last_ts("squad_stocks_equity.csv")})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)
