"""
CRYPTOBOT mission control - local web portal.
Read-only views over bot state, trades, equity, and backtest results,
plus a whitelisted job runner for the test suite.
Binds to 127.0.0.1 only. Run: .venv/bin/python portal/app.py
"""
import csv, glob, json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
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


@app.get("/api/squad_costs")
def squad_costs():
    """Fee-drag + benchmark, derived from logs only (no bot, no state,
    no governance surface): cumulative fees paid, gross vs net on
    closed trades, and what the squad's $30K would be worth parked in
    BTC since the first counted cycle, charged one charter-cost entry
    (0.40% taker + 2bps slip). The sobering chart, per 2026-08-03."""
    out = {}
    for key, tf, sf in [("crypto", "squad_trades.csv", "squad_equity.csv"),
                        ("stocks", "squad_stocks_trades.csv",
                         "squad_stocks_equity.csv")]:
        d = {"fees": 0.0, "gross": 0.0, "net": 0.0, "closed": 0}
        p = os.path.join(LOGS, tf)
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                try:
                    d["fees"] += float(r["fee"] or 0)
                    if r["action"] == "SELL":
                        d["closed"] += 1
                        d["gross"] += float(r["gross_pnl"] or 0)
                        d["net"] += float(r["net_pnl"] or 0)
                except (ValueError, KeyError):
                    pass
        out[key] = {k: round(v, 2) for k, v in d.items()}
    # BTC-hold benchmark (crypto only)
    try:
        rows = list(csv.DictReader(
            open(os.path.join(LOGS, "squad_equity.csv"))))
        t0 = datetime.fromisoformat(rows[0]["time"]).timestamp()
        px0 = pxN = None
        cp = os.path.join(ROOT, "data", "candles", "BTC-USD_3600s.csv")
        for r in csv.DictReader(open(cp)):
            if px0 is None and int(r["timestamp"]) >= t0:
                px0 = float(r["close"])
            pxN = float(r["close"])
        if px0 and pxN:
            spend = 30000.0
            units = spend * (1 - 0.004) / (px0 * 1.0002)
            out["btc_hold"] = {"start_px": px0, "now_px": pxN,
                               "equity": round(units * pxN, 2)}
    except Exception:
        pass
    return jsonify(out)


@app.get("/api/exits")
def exits():
    """MFE/MAE summary over closed trades + the TP counterfactual.
    Answers 'were we up and gave it back?' on the dashboard instead of
    in a terminal. Read-only over logs (charter s9.7 safe)."""
    out = {}
    for key, tf in [("crypto", "squad_trades.csv"),
                    ("stocks", "squad_stocks_trades.csv")]:
        mfes, maes, rows = [], [], []
        p = os.path.join(LOGS, tf)
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                if r["action"] != "SELL":
                    continue
                # blank != zero: trades closed before the MFE tape
                # existed have no excursion and must not read as 0.00%
                if not (r.get("mfe_pct") or "").strip():
                    continue
                try:
                    mfe = float(r["mfe_pct"])
                    mae = float(r["mae_pct"] or 0)
                except ValueError:
                    continue
                mfes.append(mfe)
                maes.append(mae)
                rows.append({"bot": r["bot"], "pair": r["pair"],
                             "mfe": mfe, "mae": mae,
                             "net": float(r["net_pnl"] or 0),
                             "exit": r["exit_kind"],
                             "cause": r["loss_cause"]})
        def q(xs, f):
            if not xs:
                return None
            s = sorted(xs)
            return s[min(len(s) - 1, int(f * len(s)))]
        # round-trip cost floor: 2x(taker+slip) + typical spread
        rt = 2 * (0.004 + 0.0010) if key == "crypto" else 2 * 0.0005
        out[key] = {"n": len(rows), "rt_cost": rt,
                    "mfe_max": max(mfes) if mfes else None,
                    "mfe_med": q(mfes, 0.5), "mfe_p75": q(mfes, 0.75),
                    "mae_med": q(maes, 0.5), "mae_min": min(maes) if maes else None,
                    "above_cost": sum(1 for m in mfes if m >= rt),
                    "worst": sorted(rows, key=lambda r: r["net"])[:6]}
    return jsonify(out)


@app.get("/api/exam_ledger")
def exam_ledger():
    p = os.path.join(ROOT, "backtest", "results", "exam_ledger.csv")
    if not os.path.exists(p):
        return jsonify([])
    with open(p) as f:
        return jsonify(list(csv.DictReader(f)))


def _armed(mod):
    """Read the ARMED assignment, not prose. The docstrings of both
    seed modules contain lines that BEGIN with 'ARMED' ("ARMED flips
    only after owner signature..."), so a startswith() match read the
    docstring and reported stocks UNARMED while it was armed and
    trading. Require an actual assignment."""
    try:
        with open(os.path.join(ROOT, "bot", mod)) as f:
            for line in f:
                head = line.split("#")[0]
                if head.replace(" ", "").startswith("ARMED="):
                    return "True" in head
    except OSError:
        return None


@app.get("/api/meta")
def meta():
    armed = _armed("seeds_crypto.py")
    armed_stk = _armed("seeds_stocks.py")

    def cycles_24h():
        """Missed-cycle detector. launchd's StartInterval does not fire
        while the Mac sleeps, and until 2026-08-03 a skipped hour was
        completely invisible (the 01:00 UTC gap that night was found by
        hand). Expected = the last 24 full UTC hours; the squad marks
        every hour it actually cycled."""
        try:
            rows = list(csv.DictReader(
                open(os.path.join(LOGS, "squad_equity.csv"))))
            have = {r["time"][:13] for r in rows}
            now = datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0)
            expect = [(now - timedelta(hours=i)).strftime("%Y-%m-%dT%H")
                      for i in range(1, 25)]
            missing = [h for h in expect if h not in have]
            return {"marked": 24 - len(missing), "expected": 24,
                    "missing": sorted(missing)}
        except Exception:
            return None

    def last_ts(fname, col="time"):
        p = os.path.join(LOGS, fname)
        if not os.path.exists(p):
            return None
        rows = list(csv.DictReader(open(p)))
        return rows[-1][col] if rows else None
    return jsonify({"armed": armed, "armed_crypto": armed,
                    "armed_stocks": armed_stk,
                    "cycles": cycles_24h(),
                    "league_last": last_ts("league_equity.csv"),
                    "squad_last": last_ts("squad_equity.csv"),
                    "squad_stk_last": last_ts("squad_stocks_equity.csv")})
@app.get("/api/diversity")
def diversity_api():
    """E2.6 diversity gauge. Read-only: how many of the squad's slices
    are buying an opinion the squad already owns."""
    sys.path.insert(0, os.path.join(ROOT, "bot"))
    import importlib
    dv = importlib.import_module("diversity")
    importlib.reload(dv)
    out = {}
    for label, path in dv.SQUADS:
        r = dv.analyse(path)
        if not r:
            continue
        out[label] = {
            "bots": r["bots"], "invested": r["invested"],
            "overlap": round(r["overlap_invested"], 4),
            "distinct_books": r["distinct"],
            "effective": round(r["effective"], 4),
            "clusters": [{"book": sorted(b), "members": sorted(m)}
                         for b, m in r["clusters"]],
            "clone_sets": [sorted(m) for b, m in r["clusters"]
                           if len(m) > 1],
        }
    hist = []
    p = os.path.join(LOGS, "diversity.csv")
    if os.path.exists(p):
        hist = list(csv.DictReader(open(p)))[-200:]
    return jsonify({"now": out, "history": hist})


@app.get("/api/exam_status")
def exam_status():
    """Instrument truthfulness (2026-08-04): K with its breakdown, and
    whether an exam process is ACTUALLY running right now — the old
    page asserted "exams in progress" as a static string."""
    rows = 0
    lp = os.path.join(ROOT, "backtest", "results", "exam_ledger.csv")
    if os.path.exists(lp):
        rows = max(0, sum(1 for _ in open(lp)) - 1)
    carried = screened = 0
    off = os.path.join(ROOT, "backtest", "results", "k_offset.json")
    if os.path.exists(off):
        try:
            carried = int(json.load(open(off)).get("carried_ledger_rows", 0))
        except Exception:
            pass
    scr = os.path.join(ROOT, "backtest", "results", "screened_1h.json")
    if os.path.exists(scr):
        try:
            screened = int(json.load(open(scr)).get("count", 0))
        except Exception:
            pass
    try:
        running = subprocess.run(["pgrep", "-f", "exam_1h"],
                                 capture_output=True).returncode == 0
    except Exception:
        running = False
    return jsonify({"ledger_rows": rows, "carried": carried,
                    "screened": screened, "K": rows + carried + screened,
                    "exam_running": running})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)
