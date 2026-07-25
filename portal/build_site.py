"""
Build the public league page: one self-contained HTML file with all
league data embedded. site/index.html works from file://, from the
local portal at /public, and later deploys to Vercel unchanged.
Run after each league cycle: python portal/build_site.py
"""
import csv, json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "site")

def read_csv(path, tail=None):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return rows[-tail:] if tail else rows

def build():
    sp = os.path.join(ROOT, "bot", "league_state.json")
    state = json.load(open(sp)) if os.path.exists(sp) else {}
    data = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "league": state,
        "equity": read_csv(os.path.join(ROOT, "logs", "league_equity.csv")),
        "trades": read_csv(os.path.join(ROOT, "logs", "league_trades.csv"),
                           tail=40),
    }
    os.makedirs(OUT, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(html)
    print(f"site/index.html built "
          f"({len(data['equity'])} equity rows, "
          f"{len(data['trades'])} trades embedded)")

TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CRYPTOBOT League</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75,700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0B0F17;--panel:#121826;--line:#1F2A3D;--txt:#C6D2E4;--dim:#5B6B84;
--amber:#F0B429;--up:#4FD97B;--down:#F4645C;--blue:#59C2FF;--ink:#0c1119}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);
font:13.5px/1.55 "IBM Plex Mono",ui-monospace,Menlo,monospace;
font-variant-numeric:tabular-nums;padding:20px;max-width:880px;margin:0 auto}
header{border-bottom:2px solid var(--amber);padding-bottom:12px;margin-bottom:8px}
h1{font-family:"Archivo",sans-serif;font-stretch:75%;font-weight:700;
font-size:24px;letter-spacing:.06em;color:var(--amber)}
h1 small{color:var(--dim);font-size:12px;letter-spacing:.2em;margin-left:8px}
.sub{color:var(--dim);font-size:11px;margin:6px 0 18px}
.panel{background:var(--panel);border:1px solid var(--line);
padding:16px;margin-bottom:16px}
.panel h2{font-size:10.5px;letter-spacing:.18em;color:var(--dim);
text-transform:uppercase;margin-bottom:12px}
.srow{display:grid;grid-template-columns:auto 1fr auto;gap:4px 14px;
padding:12px 0;border-bottom:1px solid #151d2c;align-items:baseline}
.srow:last-child{border-bottom:0}
.sname{font-weight:600;font-size:15px}
.role{color:var(--dim);font-size:10px;letter-spacing:.06em}
.eq{font-size:15px;text-align:right}
.meta{grid-column:1/-1;color:var(--dim);font-size:11px;display:flex;
gap:16px;flex-wrap:wrap}
.pos{color:var(--up)}.neg{color:var(--down)}
.halt{color:var(--down);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:11.5px}
th{color:var(--dim);text-align:left;font-weight:400;font-size:9.5px;
letter-spacing:.14em;text-transform:uppercase;
border-bottom:1px solid var(--line);padding:4px 6px}
td{padding:4px 6px;border-bottom:1px solid #151d2c}
.buy{color:var(--up)}.sell{color:var(--down)}
.foot{color:var(--dim);font-size:10.5px;line-height:1.7;margin-top:14px}
.trwrap{overflow-x:auto}
</style></head>
<body>
<header><h1>CRYPTOBOT<small>STRATEGY LEAGUE</small></h1></header>
<div class="sub" id="sub"></div>
<div class="panel"><h2>League table · forward paper results only</h2>
<div id="league"></div></div>
<div class="panel"><h2>Equity race</h2><canvas id="eqChart" height="120"></canvas></div>
<div class="panel"><h2>Recent trades</h2><div class="trwrap" id="trades"></div></div>
<div class="foot">Paper trading only — no real money. Success bar, committed
2026-07-24 before the race began: beat BTC-HOLD over 90+ days of forward
trading with a smaller drawdown, after simulated fees, without ever tripping
the −20% circuit breaker. Backtests never appear on this page.</div>
<script>
const DATA=__DATA__;
const $=id=>document.getElementById(id);
const usd=x=>'$'+Number(x).toLocaleString(undefined,
  {minimumFractionDigits:2,maximumFractionDigits:2});
const ROLES={'BTC-HOLD':'benchmark','BTC-TREND':'exam graduate',
  'MOM-ROT':'control · failed exam'};
const COLORS={'BTC-HOLD':'#5B6B84','BTC-TREND':'#59C2FF','MOM-ROT':'#F0B429'};
$('sub').textContent='updated '+DATA.generated.slice(0,16).replace('T',' ')
  +' UTC · zero real money · rules locked before the race';
const last={};DATA.equity.forEach(r=>last[r.strategy]=r);
const rows=Object.keys(DATA.league).map(n=>{
  const st=DATA.league[n],cur=last[n];
  const eq=cur?Number(cur.equity):10000;
  const peak=Number(st.peak_equity||eq);
  return{n,st,eq,ret:eq/10000-1,dd:Math.max(0,1-eq/peak),
    hold:(cur&&cur.holdings)?cur.holdings.replace(/-USD/g,''):'cash'};
}).sort((a,b)=>b.eq-a.eq);
$('league').innerHTML=rows.map((r,i)=>
  `<div class="srow">`+
  `<div class="sname" style="color:${COLORS[r.n]}">${i+1}. ${r.n}</div>`+
  `<div class="role">${ROLES[r.n]||''}</div>`+
  `<div class="eq">${usd(r.eq)} <span class="${r.ret>=0?'pos':'neg'}">`+
  `${(r.ret>=0?'+':'')+(r.ret*100).toFixed(2)}%</span></div>`+
  `<div class="meta"><span>since ${(r.st.created||'').slice(0,10)}</span>`+
  `<span>drawdown −${(r.dd*100).toFixed(1)}%</span>`+
  `<span>holding ${r.hold}</span>`+
  `${r.st.halted?'<span class="halt">HALTED</span>':''}</div></div>`).join('');
const names=[...new Set(DATA.equity.map(r=>r.strategy))];
const times=[...new Set(DATA.equity.map(r=>r.time))];
new Chart($('eqChart'),{type:'line',
 data:{labels:times.map(t=>t.slice(5,16).replace('T',' ')),
  datasets:names.map(n=>{const m={};
   DATA.equity.filter(r=>r.strategy===n).forEach(r=>m[r.time]=+r.equity);
   return{label:n,data:times.map(t=>m[t]??null),borderColor:COLORS[n]||'#C6D2E4',
    borderWidth:1.6,pointRadius:2,tension:.25,spanGaps:true};})},
 options:{plugins:{legend:{labels:{color:'#8fa2bc',boxWidth:14,
  font:{family:'IBM Plex Mono',size:11}}}},
 scales:{x:{ticks:{color:'#5B6B84',maxTicksLimit:6},grid:{color:'#151d2c'}},
  y:{ticks:{color:'#5B6B84',callback:v=>'$'+v.toLocaleString()},
   grid:{color:'#151d2c'}}}}});
$('trades').innerHTML=DATA.trades.length?
 `<table><tr><th>time</th><th>strategy</th><th>side</th><th>pair</th>`+
 `<th>price</th><th>value</th></tr>`+
 DATA.trades.slice().reverse().map(r=>`<tr>`+
  `<td>${r.time.slice(0,16).replace('T',' ')}</td>`+
  `<td style="color:${COLORS[r.strategy]||'inherit'}">${r.strategy}</td>`+
  `<td class="${r.action.includes('BUY')?'buy':'sell'}">${r.action}</td>`+
  `<td>${r.pair}</td><td>${r.price}</td><td>${r.value}</td></tr>`).join('')
 +'</table>':'No trades yet.';
</script>
</body></html>"""

if __name__ == "__main__":
    build()
