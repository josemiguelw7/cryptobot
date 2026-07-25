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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)
