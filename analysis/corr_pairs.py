import csv, os, itertools, math, statistics as st
ROOT="/Users/haroonrasheed/Projects/cryptobot"
CRY=["BTC-USD","ETH-USD","SOL-USD","XRP-USD","ADA-USD","DOGE-USD","LINK-USD","LTC-USD"]
STK=["SPY","QQQ","IWM","AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"]
MAXC=0.70

def load(path):
    d={}
    with open(path) as f:
        r=csv.DictReader(f)
        for row in r:
            try: d[int(float(row["timestamp"]))]=float(row["close"])
            except Exception: pass
    return d

def rets(d, since=None):
    ks=sorted(k for k in d if since is None or k>=since)
    out={}
    for i in range(1,len(ks)):
        if ks[i]-ks[i-1]!=3600: continue          # solo barras contiguas
        p0=d[ks[i-1]]
        if p0>0: out[ks[i]]=math.log(d[ks[i]]/p0)
    return out

def corr(a,b):
    ks=sorted(set(a)&set(b))
    if len(ks)<500: return None,len(ks)
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx,my=sum(x)/len(x),sum(y)/len(y)
    sx=math.sqrt(sum((v-mx)**2 for v in x)); sy=math.sqrt(sum((v-my)**2 for v in y))
    if sx==0 or sy==0: return None,len(ks)
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy), len(ks)

def analyze(label, names, D, since=None):
    R={n:rets(D[n],since) for n in names}
    C={}; ns=[]
    for a,b in itertools.combinations(names,2):
        c,n=corr(R[a],R[b])
        if c is not None: C[(a,b)]=c; ns.append(n)
    if not C: print(f"{label}: sin datos suficientes"); return
    vals=sorted(C.values())
    print(f"\n=== {label} ===")
    print(f"solapamiento medio {int(sum(ns)/len(ns))} barras · {len(C)} pares")
    print(f"correlacion  mediana={st.median(vals):.3f}  min={min(vals):.3f}  max={max(vals):.3f}")
    print(f"pares por debajo de {MAXC}: {sum(1 for v in vals if v<MAXC)}/{len(vals)}")
    lo=sorted(C.items(), key=lambda kv: kv[1])[:3]
    hi=sorted(C.items(), key=lambda kv: -kv[1])[:3]
    print("  mas bajos :", ", ".join(f"{a}/{b}={c:.2f}" for (a,b),c in lo))
    print("  mas altos :", ", ".join(f"{a}/{b}={c:.2f}" for (a,b),c in hi))
    def ok(cb): return all(C.get((x,y),C.get((y,x),1.0))<MAXC for x,y in itertools.combinations(cb,2))
    print(f"  carteras legales (toda corr < {MAXC}):")
    for k in range(2,7):
        tot=list(itertools.combinations(names,k)); good=[c for c in tot if ok(c)]
        print(f"    tamano {k}: {len(good):5d}/{len(tot):5d}  ({100.0*len(good)/len(tot):5.1f}%)")

DC={p:load(os.path.join(ROOT,"data","candles",f"{p}_3600s.csv")) for p in CRY
    if os.path.exists(os.path.join(ROOT,"data","candles",f"{p}_3600s.csv"))}
DS={s:load(os.path.join(ROOT,"data","stocks",f"{s}_1h.csv")) for s in STK
    if os.path.exists(os.path.join(ROOT,"data","stocks",f"{s}_1h.csv"))}
import time
now=int(time.time()); d365=now-365*86400
analyze("CRIPTO 1h - historico completo", list(DC), DC)
analyze("CRIPTO 1h - ultimos 365 dias", list(DC), DC, d365)
analyze("ACCIONES 1h - historico completo", list(DS), DS)
analyze("ACCIONES 1h - ultimos 365 dias", list(DS), DS, d365)
