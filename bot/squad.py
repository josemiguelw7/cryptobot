"""
INTRADAY SQUAD ENGINE — forward paper trading under the charter.

Governed by docs/intraday_success_criteria.md v1.0 (commit 5b3b84c).
ZERO real money. Every number below that looks arbitrary is a charter
section; the section is cited where it binds.

Refuses to run counted cycles until bot/seeds_crypto.py is ARMED, which
requires (a) the owner adopting the seed roster and (b) every seed
having been through backtest/exam_1h.py. Exam PASS = candidate,
exam FAIL = control — controls trade forward identically but are never
eligible for real capital, mirroring the daily league's MOM-ROT
precedent. (Interpretation pending formal record at the Saturday
review, charter section 2.5.)

Cycle cadence: hourly, driven by bot/daily.py. Decisions read COMPLETED
hourly bars from the local store; a targeted top-up (2h staleness
threshold, gap-derived window) keeps the eight squad pairs fresh
without re-buying history.

Usage:
    python bot/squad.py            # one cycle (no-op while unarmed)
    python bot/squad.py --status   # print state, no cycle
"""
from __future__ import annotations
import csv, hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "data"))
import seeds_crypto as SEEDS
from refresh_intraday import days_to_cover, newest_bar_age_hours

import requests

STATE = os.path.join(HERE, "squad_state.json")
CANDLES = os.path.join(ROOT, "data", "candles")
GATE = os.path.join(ROOT, "logs", "intraday_gate.json")
EQLOG = os.path.join(ROOT, "logs", "squad_equity.csv")
TRLOG = os.path.join(ROOT, "logs", "squad_trades.csv")
DECLOG = os.path.join(ROOT, "logs", "squad_decisions.csv")
DAYLOG = os.path.join(ROOT, "logs", "squad_daily.csv")
BASE = "https://api.exchange.coinbase.com"

SLICE = 3000.0                    # charter s3: paper slice per bot
FEE_TAKER = 0.004                 # s4.1 taker, regardless of live tier
SLIP = {"BTC-USD": 0.0002, "ETH-USD": 0.0002}   # s4.1: 2 bps majors
SLIP_OTHER = 0.0010               # s4.1 says 5-10 bps; s2.5 -> strict 10
STOP_SLIP_MULT = 2.0              # s4.1: stop-outs fill at 2x slippage
EDGE_MULT = 2.0                   # s4.3: edge >= 2x round-trip cost
MAX_POS = 2                       # s3: max 2 concurrent positions
TV_DAY = 0.02                     # vol-target: 2% daily per position
STALE_H = 2.0                     # top-up threshold before deciding
KILL_DAY = -0.03                  # s8 per bot, one day
KILL_7D = -0.06                   # s8 per bot, rolling 7 days
KILL_LIFE = -0.10                 # s8 per bot, lifetime drawdown
KILL_SQUAD_DAY = -0.05            # s8 squad aggregate, one day
DATA_EVENTS_HALT = 3              # s8 data kill switch

# s12.1 frozen loss-cause taxonomy, tie-break in THIS order:
TAXONOMY = ["fees_spread", "stop_hit", "signal_reversal", "timeout_exit",
            "regime_shift", "execution_data", "position_cap"]


def utc_now():
    return datetime.now(timezone.utc)


def slip_for(pair):
    return SLIP.get(pair, SLIP_OTHER)


# ---------------------------------------------------------------- data

MARKET = "BTC-USD"                # E2.4 cross-asset proxy (SPY for stocks)


def load_bars(pair):
    """Full COMPLETED candles (ts, o, h, l, c, v), oldest first — E2.1.

    Same completeness rule as load_hourly (s4.5b: forming bars are
    invisible). The store has always held o/h/l/c/v; until epoch 2
    nothing downstream asked for more than the close."""
    path = os.path.join(CANDLES, f"{pair}_3600s.csv")
    out = []
    try:
        with open(path) as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return out
    now = utc_now().timestamp()
    for r in rows:
        t = int(r["timestamp"])
        if t + 3600 <= now:
            out.append((t, float(r["open"]), float(r["high"]),
                        float(r["low"]), float(r["close"]),
                        float(r["volume"])))
    return out


def load_hourly(pair):
    """Completed bars only (s4.5b: forming bars are invisible)."""
    path = os.path.join(CANDLES, f"{pair}_3600s.csv")
    closes, ts = [], []
    try:
        with open(path) as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return closes, ts
    now = utc_now().timestamp()
    for r in rows:
        t = int(r["timestamp"])
        if t + 3600 <= now:
            closes.append(float(r["close"]))
            ts.append(t)
    return closes, ts


def topup(pairs):
    """Targeted freshness for the squad pairs. Returns list of pairs
    whose fetch FAILED (each is an execution_data event, s8)."""
    failed = []
    for p in pairs:
        age = newest_bar_age_hours(p, 3600)
        if age is not None and age <= STALE_H:
            continue
        d = days_to_cover(p, 3600, 365)
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "data", "fetch_candles.py"),
             p, "3600", str(d), "--quiet"],
            capture_output=True, text=True, cwd=ROOT)
        if r.returncode == 2:
            failed.append(p)
    return failed


def snapshot_hash(closes, ts):
    """s4.5a: hash of the exact snapshot the decision saw."""
    h = hashlib.sha256()
    h.update(repr((ts[-1] if ts else 0, len(closes), closes[-500:]))
             .encode())
    return h.hexdigest()[:16]


def quote(pair):
    """Live best bid/ask AT/AFTER decision time (s4.5c-d)."""
    r = requests.get(f"{BASE}/products/{pair}/ticker", timeout=15)
    r.raise_for_status()
    j = r.json()
    bid, ask = float(j["bid"]), float(j["ask"])
    time.sleep(0.1)
    return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2,
            "spread_pct": (ask - bid) / ((ask + bid) / 2)}


def edge_proxy(closes, hold_h, lookback_h=2160):
    """s4.3 expected-edge model, declared in advance: the trailing
    unconditional median |return| over the seed's declared holding
    horizon — move_scale.py's statistic, rolling. Signal-free: it
    measures whether the market moves enough to pay for a trade, not
    which direction."""
    xs = closes[-lookback_h:]
    if len(xs) <= hold_h:
        return 0.0
    moves = sorted(abs(xs[i] / xs[i - hold_h] - 1)
                   for i in range(hold_h, len(xs)))
    return moves[len(moves) // 2]


def vol_weight(closes):
    """s3 vol-targeted sizing: per-position weight of slice, cap 1/MAX_POS.
    Daily vol estimated from the last 24 hourly returns."""
    if len(closes) < 26:
        return 0.0
    rets = [closes[i] / closes[i - 1] - 1 for i in range(-24, 0)]
    mu = sum(rets) / 24
    var = sum((r - mu) ** 2 for r in rets) / 23
    vol_day = (var ** 0.5) * (24 ** 0.5)
    if vol_day <= 0:
        return 1.0 / MAX_POS
    return min(1.0 / MAX_POS, TV_DAY / vol_day)


# ---------------------------------------------------------------- state

def fresh_bot():
    return {"cash": SLICE, "units": {}, "entries": {}, "ctx": {},
            "slice_peak": SLICE, "day_open": SLICE, "day_date": None,
            "eod": [],                      # [[date, close_equity], ...]
            "halt_day": None,               # s8 -3% day halt (date str)
            "halt_review": False,           # s8 -6%/7d, resumes at review
            "benched": False,               # s8 -10% lifetime
            "data_events": {},              # {date: count}
            "exam": "unexamined"}           # candidate | control


def load_state():
    st = {"bots": {}, "squad_day_open": None, "squad_day_date": None,
          "squad_halt_review": False, "voided_days": []}
    if os.path.exists(STATE):
        try:
            st = json.load(open(STATE))
        except Exception:
            pass
    for name in SEEDS.SEEDS:
        st["bots"].setdefault(name, fresh_bot())
    # exam verdicts flow from the one shared ledger: PASS -> candidate
    # (eligible, someday, under every other rule), FAIL -> control
    # (forward demonstration only, never real money).
    ledger = os.path.join(ROOT, "backtest", "results", "exam_ledger.csv")
    try:
        with open(ledger) as f:
            for r in csv.DictReader(f):
                if r["candidate"] in st["bots"]:
                    st["bots"][r["candidate"]]["exam"] = (
                        "candidate" if r["verdict"] == "PASS" else "control")
    except Exception:
        pass
    return st


def save_state(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE)


def append(path, header, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow(row)


def log_decision(now, bot, pair, snap, last_bar, w, action, edge, rt, ok):
    append(DECLOG, ["utc_ms", "bot", "pair", "snapshot_sha", "last_closed",
                    "signal_w", "action", "edge_proxy", "rt_cost", "gate"],
           [now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", bot, pair,
            snap, last_bar, f"{w:.3f}", action, f"{edge:.5f}",
            f"{rt:.5f}", "pass" if ok else "block"])


def loss_cause(gross, exit_kind):
    """s12.1: deterministic, first match in the frozen order."""
    if gross >= 0:
        return "fees_spread"          # costs turned a winner into a loser
    return {"stop": "stop_hit", "signal": "signal_reversal",
            "timeout": "timeout_exit", "regime": "regime_shift",
            "data": "execution_data", "cap": "position_cap"}[exit_kind]


# ---------------------------------------------------------------- trading

def update_excursions(st_bot, quotes, data):
    """MFE/MAE tape — instrumentation only, decides NOTHING (s9.7 safe).
    Samples each held position's mid at every cycle. Hourly sampling is
    the truthful resolution here: bots only act at cycles, so
    cycle-sampled MFE is exactly what any exit rule running in this
    engine could actually have harvested."""
    for p, e in st_bot["entries"].items():
        px = None
        if p in quotes:
            px = quotes[p]["mid"]
        elif data.get(p, ([], []))[0]:
            px = data[p][0][-1]
        if px is None:
            continue
        e["peak_mid"] = max(e.get("peak_mid", px), px)
        e["trough_mid"] = min(e.get("trough_mid", px), px)


def close_position(st_bot, bot, pair, q, now, exit_kind):
    u = st_bot["units"].pop(pair)
    e = st_bot["entries"].pop(pair, {})
    slip = slip_for(pair) * (STOP_SLIP_MULT if exit_kind == "stop" else 1)
    px = q["bid"] * (1 - slip)
    gross_notional = u * px
    fee = gross_notional * FEE_TAKER
    st_bot["cash"] += gross_notional - fee
    gross = (q["mid"] - e.get("mid", px)) * u
    net = (gross_notional - fee) - e.get("cost_basis", gross_notional)
    cause = loss_cause(gross, exit_kind) if net < 0 else ""
    hold_h = (now.timestamp() - e.get("ts", now.timestamp())) / 3600
    # MFE/MAE: peak/trough mids sampled each cycle, incl. this exit.
    base = e.get("mid") or px
    peak = max(e.get("peak_mid", base), q["mid"])
    trough = min(e.get("trough_mid", base), q["mid"])
    mfe, mae = peak / base - 1, trough / base - 1
    append(TRLOG, ["utc", "bot", "action", "pair", "px", "units", "fee",
                   "net_pnl", "gross_pnl", "hold_h", "exit_kind",
                   "loss_cause", "mfe_pct", "mae_pct"],
           [now.isoformat(), bot, "SELL", pair, f"{px:.6f}", f"{u:.8f}",
            f"{fee:.2f}", f"{net:.2f}", f"{gross:.2f}", f"{hold_h:.1f}",
            exit_kind, cause, f"{mfe:.4f}", f"{mae:.4f}"])
    st_bot["ctx"].setdefault(pair, {})["weight"] = 0.0
    st_bot["ctx"][pair]["entry_price"] = None
    print(f"  [{bot}] SELL {pair} @ {px:,.4f} net {net:+,.2f} "
          f"({exit_kind}{', ' + cause if cause else ''})")


def open_position(st_bot, bot, pair, q, now, weight, equity):
    """weight is the vol-targeted fraction of slice EQUITY (s3), already
    capped at 1/MAX_POS upstream; spend is bounded by available cash."""
    notional = min(st_bot["cash"], equity * max(0.0, weight))
    if notional < 25:
        return
    px = q["ask"] * (1 + slip_for(pair))
    fee = notional * FEE_TAKER
    u = (notional - fee) / px
    st_bot["cash"] -= notional
    st_bot["units"][pair] = u
    st_bot["entries"][pair] = {"px": px, "mid": q["mid"],
                               "ts": now.timestamp(),
                               "cost_basis": notional,
                               "peak_mid": q["mid"],    # MFE/MAE tape
                               "trough_mid": q["mid"]}
    append(TRLOG, ["utc", "bot", "action", "pair", "px", "units", "fee",
                   "net_pnl", "gross_pnl", "hold_h", "exit_kind",
                   "loss_cause", "mfe_pct", "mae_pct"],
           [now.isoformat(), bot, "BUY", pair, f"{px:.6f}", f"{u:.8f}",
            f"{fee:.2f}", "", "", "", "", "", "", ""])
    st_bot["ctx"].setdefault(pair, {})["weight"] = weight
    st_bot["ctx"][pair]["entry_price"] = px
    print(f"  [{bot}] BUY {pair} @ {px:,.4f} (${notional:,.2f}, "
          f"fee ${fee:.2f})")


# ---------------------------------------------------------------- cycle

def mark(st_bot, quotes, data):
    eq = st_bot["cash"]
    for p, u in st_bot["units"].items():
        if p in quotes:
            eq += u * quotes[p]["mid"]
        elif data.get(p, ([], []))[0]:
            eq += u * data[p][0][-1]
    return eq


def flatten(st_bot, name, quotes, now, kind):
    for p in list(st_bot["units"]):
        if p in quotes:
            close_position(st_bot, name, p, quotes[p], now, kind)


def rollover(st, name, b, today):
    """First cycle of a new UTC date: write yesterday's counted-day row
    (s3). Halted or flat days are counted at their realized return;
    execution_data days are voided — struck, not zeroed (s4.5f)."""
    if b["day_date"] is None:
        b["day_date"], b["day_open"] = today, b.get("last_eq", SLICE)
        return
    if b["day_date"] == today:
        return
    ydate, yopen = b["day_date"], b["day_open"]
    yclose = b.get("last_eq", yopen)
    voided = ydate in st.get("voided_days", []) \
        or ydate in b.get("void_dates", [])
    ret = (yclose / yopen - 1) if yopen else 0.0
    append(DAYLOG, ["date", "bot", "ret", "counted", "reason"],
           [ydate, name, f"{ret:.6f}", "no" if voided else "yes",
            "execution_data" if voided else ""])
    b["eod"] = (b.get("eod", []) + [[ydate, yclose]])[-30:]
    b["day_date"], b["day_open"] = today, yclose


def kill_switches(st, name, b, eq, quotes, now, today):
    """s8. Halting is always permitted; resuming only at the review."""
    if b["benched"] or b["halt_review"] or b.get("halt_data"):
        return False
    if b["halt_day"] == today:
        return False
    if b["day_open"] and eq / b["day_open"] - 1 <= KILL_DAY:
        print(f"  [{name}] KILL -3% day: flatten + halt until tomorrow")
        flatten(b, name, quotes, now, "stop")
        b["halt_day"] = today
        return False
    week = [e for d, e in b.get("eod", [])[-7:]]
    if week and eq / week[0] - 1 <= KILL_7D:
        print(f"  [{name}] KILL -6%/7d: flatten + halt until review")
        flatten(b, name, quotes, now, "stop")
        b["halt_review"] = True
        return False
    b["slice_peak"] = max(b.get("slice_peak", SLICE), eq)
    if eq / b["slice_peak"] - 1 <= KILL_LIFE:
        print(f"  [{name}] KILL -10% lifetime: benched, retirement autopsy due")
        flatten(b, name, quotes, now, "stop")
        b["benched"] = True
        return False
    if b.get("data_events", {}).get(today, 0) >= DATA_EVENTS_HALT:
        print(f"  [{name}] KILL data: 3 execution_data events today")
        flatten(b, name, quotes, now, "data")
        b["halt_data"] = True
        return False
    return True


def cycle():
    now = utc_now()
    today = f"{now:%Y-%m-%d}"
    print(f"[{now:%Y-%m-%d %H:%M} UTC] squad cycle "
          f"({'ARMED' if SEEDS.ARMED else 'UNARMED'})")
    if not SEEDS.ARMED:
        print("  seed roster is PROPOSED, not adopted. No counted cycles,")
        print("  no state, no logs until the owner signs "
              "docs/seed_proposals_crypto.md")
        print("  and every seed has an exam_1h verdict. (charter s9.3)")
        return 0

    st = load_state()
    gate_void = False
    try:
        g = json.load(open(GATE))["latest"]
        gate_void = g.get("execution_data") and g.get("utc", "")[:10] == today
    except Exception:
        pass

    failed = topup(SEEDS.PAIRS)
    data = {p: load_hourly(p) for p in SEEDS.PAIRS}
    # E2.3: position cap is a roster property. Epoch 1 rosters declare
    # nothing and keep the charter default of 2.
    global MAX_POS
    MAX_POS = getattr(SEEDS, "MAX_POS", MAX_POS)
    bars = {p: load_bars(p) for p in SEEDS.PAIRS}      # E2.1
    mkt_bars = bars.get(MARKET) or load_bars(MARKET)   # E2.4
    snaps = {p: snapshot_hash(*data[p]) for p in SEEDS.PAIRS}
    lastbar = {p: (datetime.fromtimestamp(data[p][1][-1], timezone.utc)
                   .strftime("%Y-%m-%dT%H:%MZ") if data[p][1] else "")
               for p in SEEDS.PAIRS}

    if gate_void and today not in st["voided_days"]:
        st["voided_days"] = (st["voided_days"] + [today])[-365:]
        print("  execution_data gate: today is VOIDED for the squad (s4.5f)")

    quotes = {}
    def q(pair):
        if pair not in quotes:
            try:
                quotes[pair] = quote(pair)
            except Exception as e:
                print(f"  quote failed {pair}: {e}")
                for b in st["bots"].values():
                    b.setdefault("data_events", {})
                    b["data_events"][today] = \
                        b["data_events"].get(today, 0) + 1
        return quotes.get(pair)

    if st["squad_day_date"] != today:
        st["squad_day_date"] = today
        st["squad_day_open"] = st.get("squad_last_eq") or \
            sum(mark(b, quotes, data) for b in st["bots"].values())

    for pf in failed:
        print(f"  fetch FAILED {pf}: execution_data event for all bots")
        for b in st["bots"].values():
            b.setdefault("data_events", {})
            b["data_events"][today] = b["data_events"].get(today, 0) + 1

    total_eq = 0.0
    squad_frozen = st.get("squad_halt_review", False)
    for name, cfg in SEEDS.SEEDS.items():
        b = st["bots"][name]
        strat, hold_h = cfg["strat"], cfg["hold_h"]
        for p in list(b["units"]):
            q(p)
        eq = mark(b, quotes, data)
        update_excursions(b, quotes, data)
        rollover(st, name, b, today)
        b["last_eq"] = eq
        total_eq += eq
        append(EQLOG, ["time", "bot", "equity", "cash", "holdings"],
               [now.isoformat(), name, f"{eq:.2f}", f"{b['cash']:.2f}",
                " ".join(b["units"]) or "cash"])
        tradable = kill_switches(st, name, b, eq, quotes, now, today) \
            and not gate_void and not squad_frozen
        status = []
        if b["benched"]: status.append("BENCHED")
        if b["halt_review"]: status.append("halt->review")
        if b.get("halt_data"): status.append("halt-data")
        if b["halt_day"] == today: status.append("halt-day")
        print(f"  [{name}] ${eq:,.2f} {list(b['units']) or 'cash'}"
              + (f"  {' '.join(status)}" if status else ""))
        if not tradable:
            continue

        sigs, conv = {}, {}
        cross = getattr(strat, "cross_sectional", False)
        wants_bars = getattr(strat, "wants_bars", False)
        wants_mkt = getattr(strat, "wants_market", False)

        if cross:
            # E2.5: strategy ranks the names against EACH OTHER.
            elig = {p: bars[p] for p in SEEDS.PAIRS
                    if len(bars[p]) >= strat.warmup + 1}
            try:
                allw = strat.step_all(elig, b["ctx"])
            except Exception as e:
                print(f"  [{name}] step_all failed: {e}")
                allw = {}
            for p in elig:
                b["ctx"].setdefault(p, {"weight": 0.0,
                                        "entry_price": None})
                sigs[p] = float(allw.get(p, 0.0))
                conv[p] = strat.conviction_all(p)
        else:
            for p in SEEDS.PAIRS:
                closes, ts = data[p]
                series = bars[p] if wants_bars else closes
                if len(series) < strat.warmup + 1:
                    continue
                ctx = b["ctx"].setdefault(p, {"weight": 0.0,
                                              "entry_price": None})
                if wants_mkt:
                    ctx["market"] = mkt_bars
                try:
                    if wants_bars:
                        sigs[p] = strat.step_bars(bars[p], ctx)
                        conv[p] = strat.conviction(bars[p], ctx)
                    else:
                        sigs[p] = strat.step(closes, ctx)
                        conv[p] = sigs[p]
                except Exception as e:
                    print(f"  [{name}] {p} signal failed: {e}")
                    sigs[p] = 0.0
                finally:
                    ctx.pop("market", None)

        held = set(b["units"])
        for p in list(held):
            if sigs.get(p, 0) <= 0:
                qq = q(p)
                if qq:
                    log_decision(now, name, p, snaps[p], lastbar[p],
                                 0.0, "EXIT", 0, 0, True)
                    close_position(b, name, p, qq, now, "signal")
                    held.discard(p)

        # E2.2: order by THIS bot's own conviction, not by the shared
        # biggest-mover rule. edge_proxy stays exactly where it was --
        # as the signal-free s4.3 cost GATE below. Ordering != permission.
        # Epoch 1 seeds return conviction == signal weight, so with a
        # flat 1.0 signal the fallback key reproduces old behaviour.
        want = sorted([p for p, w in sigs.items()
                       if w > 0 and p not in held],
                      key=lambda p: (-conv.get(p, sigs[p]),
                                     -edge_proxy(data[p][0], hold_h), p))
        for p in want:
            if len(b["units"]) >= MAX_POS:
                log_decision(now, name, p, snaps[p], lastbar[p],
                             sigs[p], "SKIP-cap", 0, 0, False)
                continue
            qq = q(p)
            if not qq:
                continue
            edge = edge_proxy(data[p][0], hold_h)
            rt = 2 * (FEE_TAKER + slip_for(p)) + qq["spread_pct"]
            ok = edge >= EDGE_MULT * rt
            log_decision(now, name, p, snaps[p], lastbar[p], sigs[p],
                         "ENTER" if ok else "SKIP-gate", edge, rt, ok)
            if ok:
                w = vol_weight(data[p][0]) * sigs[p]
                open_position(b, name, p, qq, now, w, eq)

    st["squad_last_eq"] = total_eq
    if st["squad_day_open"] and not squad_frozen and \
            total_eq / st["squad_day_open"] - 1 <= KILL_SQUAD_DAY:
        print("  SQUAD KILL -5% aggregate day: halt everything -> review")
        for name, b in st["bots"].items():
            flatten(b, name, quotes, now, "stop")
        st["squad_halt_review"] = True
    save_state(st)
    print(f"  squad total ${total_eq:,.2f} · state saved")
    return 0


def status():
    st = load_state()
    print(f"squad status ({'ARMED' if SEEDS.ARMED else 'UNARMED'})")
    for name, b in st["bots"].items():
        print(f"  {name:16s} ${b.get('last_eq', SLICE):9,.2f} "
              f"{list(b['units']) or 'cash'}"
              f"{'  BENCHED' if b['benched'] else ''}"
              f"{'  halt->review' if b['halt_review'] else ''}")


if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
    else:
        raise SystemExit(cycle())
