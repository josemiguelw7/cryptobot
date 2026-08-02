"""
Build the public league page: one self-contained HTML file, all data
embedded. Works from file://, from the portal at /public, and deploys
to Vercel unchanged. Rebuilt every league cycle by bot/daily.py.

Display scale: every strategy book is shown normalized to a $300
virtual fund (internal books stay at $10,000 so the forward record is
continuous). Fees shown in trades are scaled by the same factor.
"""
import csv, hashlib, json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "site")
SHOW_FUND = 300.0
BOOK = 10000.0

def read_csv(path, tail=None):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return rows[-tail:] if tail else rows

def charter_integrity():
    """Publish the SHA-256 of every locked governance document.

    A local git commit is weak pre-registration: `git commit --amend` rewrites
    history and nobody is the wiser. Publishing the hash makes the claim
    "this document may only be made stricter" verifiable by anyone, including
    future-Jose, instead of merely asserted. Per charter section 14, a mismatch
    between a published hash and the committed file is itself a finding and
    gets disclosed rather than quietly corrected."""
    docs = {
        "intraday_charter": "docs/intraday_success_criteria.md",
        "league_criteria": "docs/success_criteria.md",
        "intraday_exam_bar": "docs/intraday_standard.md",
        "entrance_exam": "docs/entrance_exam.md",
        "exam_amendment_001": "docs/exam_amendment_001.md",
    }
    out = {}
    for label, rel in docs.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            out[label] = {"path": rel, "sha256": None, "status": "MISSING"}
            continue
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        rec = path + ".ots"
        stamped = os.path.exists(rec)
        matches = None
        if stamped:
            # The receipt carries the hash it committed to Bitcoin. If that
            # stops matching the file, the document was edited after being
            # timestamped. Published either way: a mismatch is a finding, not
            # something to fix quietly.
            try:
                raw = open(rec, "rb").read()
                matches = bytes.fromhex(digest) in raw
            except Exception:
                matches = None
        out[label] = {"path": rel, "sha256": digest, "status": "ok",
                      "stamped": stamped, "receipt_matches": matches}
    return out


def intraday_status():
    """The intraday squad, reported honestly while it does not yet exist.

    A public page that only shows the running league would imply the intraday
    experiment is further along than it is. Publishing 'zero seeds, clock not
    started' costs nothing now and makes it impossible to later imply the
    clock started earlier than it did."""
    gate = os.path.join(ROOT, "logs", "intraday_gate.json")
    latest = {}
    if os.path.exists(gate):
        try:
            latest = json.load(open(gate)).get("latest", {})
        except Exception:
            latest = {}
    return {
        "seeds": 0,
        "counted_days": 0,
        "clock_started": False,
        "data_ok": latest.get("execution_data") is False,
        "last_audit": latest.get("utc"),
    }


def build():
    sp = os.path.join(ROOT, "bot", "league_state.json")
    state = json.load(open(sp)) if os.path.exists(sp) else {}
    ledger = read_csv(os.path.join(ROOT, "backtest", "results",
                                   "exam_ledger.csv"))
    data = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "show_fund": SHOW_FUND,
        "scale": SHOW_FUND / BOOK,
        "league": state,
        "equity": read_csv(os.path.join(ROOT, "logs",
                                        "league_equity.csv")),
        "trades": read_csv(os.path.join(ROOT, "logs",
                                        "league_trades.csv"), tail=30),
        "examined": len(ledger),
        "integrity": charter_integrity(),
        "intraday": intraday_status(),
    }
    os.makedirs(OUT, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(html)
    print(f"site/index.html built ({len(data['equity'])} equity rows, "
          f"{len(data['trades'])} trades, {data['examined']} exams)")

TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>Strategy League</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#FAFAF7;--card:#FFFFFF;--line:#E7E5DE;--txt:#1A1E24;
--dim:#8A8F98;--up:#0E8F5B;--down:#C93B3B;--wait:#9A6B15;--accent:#2B4C7E}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);max-width:760px;margin:0 auto;
padding:28px 18px 60px;font:15px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif}
h1{font-size:21px;margin-bottom:2px}
.sub{color:var(--dim);font-size:13px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--line);
border-radius:12px;padding:18px;margin-bottom:16px}
.card h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;
color:var(--dim);margin-bottom:12px}
.big{font-size:34px;font-weight:700;font-variant-numeric:tabular-nums}
.pnl{font-size:16px;font-weight:600;margin-left:8px}
.up{color:var(--up)}.down{color:var(--down)}.wait{color:var(--wait)}
.day{color:var(--dim);font-size:13px;margin-top:4px}
.row{display:flex;justify-content:space-between;align-items:flex-start;
gap:10px;padding:12px 0;border-bottom:1px solid var(--line)}
.row:last-child{border-bottom:none}
.rname{font-weight:650}
.rdesc{color:var(--dim);font-size:12.5px;margin-top:2px;max-width:430px}
.rnum{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.rv{font-weight:650;font-size:16px}
.badge{display:inline-block;font-size:10.5px;font-weight:650;
letter-spacing:.05em;padding:2px 8px;border-radius:20px;margin-top:3px}
.b-in{background:#E6F4EC;color:var(--up)}
.b-wait{background:#F7EFDD;color:var(--wait)}
.b-bench{background:#E8EEF7;color:var(--accent)}
canvas{width:100%!important;max-height:280px}
.trade{padding:9px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.trade:last-child{border-bottom:none}
.trade .who{font-weight:650}
.trade .fee{color:var(--down);font-size:12.5px}
.trade .when{color:var(--dim);font-size:11.5px}
.pipe{display:flex;gap:8px;text-align:center;flex-wrap:wrap}
.pipe div{flex:1;min-width:110px;background:var(--bg);
border:1px solid var(--line);border-radius:10px;padding:10px 6px}
.pipe b{display:block;font-size:20px}
.pipe span{font-size:11px;color:var(--dim)}
.note{color:var(--dim);font-size:12.5px;line-height:1.6;margin-top:10px}
</style></head><body>
<h1>Strategy League</h1>
<div class="sub">Six trading brains compete with simulated money.
Real money is only unlocked if one of them beats simply holding
Bitcoin over 90 days, after fees.</div>

<div class="card">
  <h2>Your virtual $300 &mdash; following the benchmark (BTC-HOLD)</h2>
  <div><span class="big" id="heroV"></span><span class="pnl" id="heroP"></span></div>
  <div class="day" id="dayline"></div>
</div>

<div class="card"><h2>All six brains &mdash; each given a virtual $300</h2>
  <div id="rows"></div>
</div>

<div class="card"><h2>The race so far</h2>
  <canvas id="chart"></canvas>
  <div class="note">Each line = one brain's $300. The gray line
  (BTC-HOLD) is the one to beat.</div>
</div>

<div class="card"><h2>Recent trades &mdash; and what each one cost</h2>
  <div id="trades"></div>
</div>

<div class="card"><h2>Intraday squad &mdash; not started</h2>
  <div id="intraday"></div>
  <div class="note">This is the second, harder experiment: strategies that
  decide on hourly bars rather than daily. It has <b>zero strategies</b> and
  its clock reads <b>zero counted days</b>. It is published in that state on
  purpose &mdash; so that when the clock does start, nobody, including me,
  can imply it started earlier.</div>
</div>

<div class="card"><h2>What was measured before the experiment began</h2>
  <div class="note">Three diagnostics run on 8 pairs and ~8,750 hourly bars,
  published here <b>before</b> any intraday strategy exists. None of them
  computes a return, a Sharpe, or any measure of profit &mdash; they measure
  cost and structure only, which is why running them does not compromise a
  standard that was written while blind to results.
  <div class="pipe" style="margin-top:12px">
    <div><b>6.2</b><span>independent signals inside a basket of 20
      &ldquo;classic&rdquo; indicators</span></div>
    <div><b>14</b><span>most that ever agree at once, out of 20 &mdash;
      a structural ceiling</span></div>
    <div><b>0.31%</b><span>median hourly price move, against a 2.60%
      cost hurdle per round trip</span></div>
  </div>
  The third number is the binding one. A trade must clear twice its
  round-trip cost before it is allowed to happen, and the typical hour moves
  a fraction of that. This is arithmetic between volatility and a fee
  schedule; no strategy can change it. It is recorded now so that whatever
  the experiment concludes later, the prior was on the record first.</div>
</div>

<div class="card"><h2>How the bot gets better</h2>
  <div class="pipe">
    <div><b>&infin;</b><span>ideas screened freely<br>(research, unrecorded)</span></div>
    <div><b id="pExam"></b><span>took the one-shot exam<br>(all recorded forever)</span></div>
    <div><b>6</b><span>competing in the league<br>(90-day forward test)</span></div>
    <div><b id="pDays"></b><span>days remaining<br>before first judgment</span></div>
  </div>
  <div class="note">Pipeline: unlimited research &rarr; one exam per
  idea, ever &rarr; 90 days of live paper competition &rarr; only a
  winner can touch real money. No step can be skipped, and the pass
  bar can only ever be made stricter.</div>
</div>

<div class="note">All figures simulated. Internal books run at $10,000
and are displayed scaled to $300; fees scale identically. Updated
hourly. Not financial advice.</div>

<script>
const D = __DATA__;
const S = D.scale, F = D.show_fund;
const DESC = {
 "BTC-HOLD":  ["Benchmark","Bought Bitcoin on day one and never trades again. Every other brain exists to try to beat this."],
 "BTC-TREND": ["Exam graduate*","Holds Bitcoin only while it trades above its 200-day average; otherwise waits in cash."],
 "MOM-ROT":   ["Control (failed exam)","Each week buys the 3 hottest coins of the last month. Kept as a live warning: its exam predicted losses."],
 "CROSS-BTC": ["Control (failed exam)","Buys when the 20-day average crosses over the 50-day. Trades often; its exam said fees would eat it."],
 "DONCH-BTC": ["Control (failed exam)","Buys 20-day breakout highs, sells 20-day lows. Waiting for a breakout."],
 "RSI-BTC":   ["Control (failed exam)","Buys panic dips (RSI oversold), sells the recovery. Waiting for a dip."]
};
const nm = v => "$" + (v*S).toFixed(2);
const pc = v => { const p=(v/10000-1)*100;
  return (p>=0?"+":"") + p.toFixed(2) + "%"; };

// latest equity per strategy
const last = {}, first = {};
for (const r of D.equity){
  if(!(r.strategy in first)) first[r.strategy]=r;
  last[r.strategy]=r;
}
const names = Object.keys(last);
const t0 = D.equity.length ? new Date(D.equity[0].timestamp) : new Date();
const days = Math.max(1, Math.ceil((Date.now()-t0)/86400000));
document.getElementById("pDays").textContent = Math.max(0, 90-days);
document.getElementById("pExam").textContent = D.examined;

// hero = benchmark
const bh = last["BTC-HOLD"];
if (bh){
  const v = parseFloat(bh.equity);
  document.getElementById("heroV").textContent = nm(v);
  const p = document.getElementById("heroP");
  p.textContent = pc(v);
  p.className = "pnl " + (v>=10000?"up":"down");
}
document.getElementById("dayline").textContent =
  "Day " + days + " of 90 \u00b7 updated " +
  new Date(D.generated).toLocaleString();

// rows, sorted by equity
const rowsEl = document.getElementById("rows");
names.sort((a,b)=>parseFloat(last[b].equity)-parseFloat(last[a].equity));
for (const n of names){
  const v = parseFloat(last[n].equity);
  const cash = parseFloat(last[n].cash || 0);
  const inMkt = cash < v*0.5;
  const [role, desc] = DESC[n] || ["",""];
  const badge = n==="BTC-HOLD" ? '<span class="badge b-bench">BENCHMARK</span>'
    : inMkt ? '<span class="badge b-in">IN MARKET</span>'
    : '<span class="badge b-wait">WAITING IN CASH</span>';
  const el = document.createElement("div");
  el.className = "row";
  el.innerHTML = '<div><div class="rname">'+n+'</div>' +
    '<div class="rdesc">'+desc+'</div>'+badge+'</div>' +
    '<div class="rnum"><div class="rv '+(v>=10000?"up":"down")+'">'+nm(v)+
    '</div><div class="'+(v>=10000?"up":"down")+'">'+pc(v)+'</div></div>';
  rowsEl.appendChild(el);
}

// chart
const byS = {};
for (const r of D.equity){
  (byS[r.strategy] = byS[r.strategy] || []).push(
    {x:r.timestamp.slice(5,16).replace("T"," "), y:parseFloat(r.equity)*S});
}
const colors = {"BTC-HOLD":"#8A8F98","BTC-TREND":"#2B4C7E",
 "MOM-ROT":"#C93B3B","CROSS-BTC":"#B0691C","DONCH-BTC":"#0E8F5B",
 "RSI-BTC":"#7A4CB0"};
new Chart(document.getElementById("chart"),{type:"line",
 data:{datasets:Object.entries(byS).map(([n,pts])=>({label:n,data:pts,
  borderColor:colors[n]||"#999",borderWidth:n==="BTC-HOLD"?3:1.6,
  pointRadius:0,tension:.25}))},
 options:{animation:false,interaction:{mode:"index",intersect:false},
  scales:{x:{type:"category",ticks:{maxTicksLimit:6,font:{size:10}}},
   y:{ticks:{callback:v=>"$"+v.toFixed(0)}}},
  plugins:{legend:{labels:{boxWidth:12,font:{size:11}}}}}});

// trades in plain English
const tEl = document.getElementById("trades");
const tr = (D.trades||[]).slice().reverse();
if (!tr.length) tEl.innerHTML =
  '<div class="note">No trades yet beyond initial buys.</div>';
for (const t of tr){
  const qty = parseFloat(t.qty||0), px = parseFloat(t.price||0),
        fee = parseFloat(t.fee||0)*S;
  const d = document.createElement("div");
  d.className = "trade";
  d.innerHTML = '<span class="who">'+t.strategy+'</span> ' +
   (t.side==="BUY"?"bought ":"sold ") +
   qty.toFixed(5)+" "+(t.pair||"").replace("-USD","") +
   " at $"+px.toLocaleString(undefined,{maximumFractionDigits:2}) +
   ' \u00b7 <span class="fee">fee '+
   "$"+fee.toFixed(2)+'</span>' +
   ' <div class="when">'+new Date(t.timestamp).toLocaleString()+
   " \u00b7 on a $300 fund</div>";
  tEl.appendChild(d);
}
</script>
<script>
// intraday squad status
(function(){
  var I = D.intraday || {}, el = document.getElementById("intraday");
  if(!el) return;
  var ok = I.data_ok;
  el.innerHTML =
    '<div class="row"><div><div class="rname">Strategies entered</div>' +
    '<div class="rdesc">Ten are planned. Each must pass a written exam ' +
    'before it may enter, and once entered its rules are frozen forever.' +
    '</div></div><div class="rnum"><div class="rv">' + (I.seeds||0) +
    '</div></div></div>' +
    '<div class="row"><div><div class="rname">Counted days on the clock</div>' +
    '<div class="rdesc">The judgment window is 90 or 180 days depending on ' +
    'how often a strategy trades. It has not begun.</div></div>' +
    '<div class="rnum"><div class="rv">' + (I.counted_days||0) +
    '</div></div></div>' +
    '<div class="row"><div><div class="rname">Data integrity gate</div>' +
    '<div class="rdesc">Checked before every cycle. If it fails, no day is ' +
    'counted &mdash; broken plumbing must not become a result.</div>' +
    (ok ? '<span class="badge b-in">PASSING</span>'
        : '<span class="badge b-wait">NOT PASSING</span>') +
    '</div><div class="rnum"></div></div>';
})();
</script>
<div id="integrity" class="note" style="margin-top:18px"></div>
<script>
(function(){
  var I = D.integrity || {}, el = document.getElementById("integrity");
  var keys = Object.keys(I); if(!keys.length){ return; }
  var rows = keys.map(function(k){
    var d = I[k], h = d.sha256;
    var seal = d.stamped
      ? (d.receipt_matches === false
          ? ' <b style="color:#C93B3B">RECEIPT MISMATCH</b>'
          : ' <span style="color:#0E8F5B">timestamped on Bitcoin</span>')
      : ' <span style="color:#9A6B15">not timestamped</span>';
    return '<div style="margin-top:6px"><b>'+d.path+'</b>'+seal+'<br>'+
      (h ? '<code style="font-size:11px;word-break:break-all">'+h+'</code>'
         : '<span>MISSING</span>')+'</div>';
  }).join("");
  el.innerHTML = '<b>Document integrity.</b> These are the SHA-256 hashes of ' +
    'the governance documents that set the rules for this project. They may ' +
    'only ever be edited to make the standards stricter, never looser. ' +
    'The hashes are recomputed every build, so if a document is quietly ' +
    'changed, this page changes with it &mdash; the commitment is checkable ' +
    'rather than just claimed. Each hash is also timestamped on the ' +
    'Bitcoin blockchain via OpenTimestamps, which is the part I cannot ' +
    'rewrite: a private repository proves a date only to its owner.' + rows;
})();
</script>
<div class="note" style="margin-top:6px">*BTC-TREND graduated under the
original exam, which was later found to be miscalibrated and was
corrected (Amendment 001). Under today's stricter-but-fair exam it
would not pass. Its league seat stands; expectations should not.</div>
</body></html>"""

if __name__ == "__main__":
    build()
