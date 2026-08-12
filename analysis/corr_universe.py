import csv, os, glob, math, itertools, time, statistics as st
ROOT="/Users/haroonrasheed/Projects/cryptobot"
MAXC=0.70; MINBARS=6000
now=int(time.time()); since=now-365*86400

def load(p):
    d={}
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t=int(float(row["timestamp"]))
                if t>=since: d[t]=float(row["close"])
            except Exception: pass
    return d

def rets(d):
    ks=sorted(d); out={}
    for i in range(1,len(ks)):
        if ks[i]-ks[i-1]!=3600: continue
        if d[ks[i-1]]>0: out[ks[i]]=math.log(d[ks[i]]/d[ks[i-1]])
    return out

R={}
for p in sorted(glob.glob(os.path.join(ROOT,"data","candles","*_3600s.csv"))):
    name=os.path.basename(p).replace("_3600s.csv","")
    r=rets(load(p))
    if len(r)>=MINBARS: R[name]=r
names=sorted(R)
print(f"activos con >= {MINBARS} barras horarias en los ultimos 365d: {len(names)}")

def corr(a,b):
    ks=sorted(set(a)&set(b))
    if len(ks)<3000: return None
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx,my=sum(x)/len(x),sum(y)/len(y)
    sx=math.sqrt(sum((v-mx)**2 for v in x)); sy=math.sqrt(sum((v-my)**2 for v in y))
    if sx==0 or sy==0: return None
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy)

C={}
for a,b in itertools.combinations(names,2):
    c=corr(R[a],R[b])
    if c is not None: C[(a,b)]=c
def g(x,y): return C.get((x,y), C.get((y,x)))
names=[n for n in names if any(g(n,m) is not None for m in names if m!=n)]
print(f"pares medidos: {len(C)}")

med=sorted(((st.median([g(n,m) for m in names if m!=n and g(n,m) is not None]), n) for n in names))
print("\n--- activos MENOS acoplados al resto (mediana de su correlacion) ---")
for v,n in med[:12]: print(f"  {n:14s} {v:.3f}")
print("--- MAS acoplados ---")
for v,n in med[-5:]: print(f"  {n:14s} {v:.3f}")

adj={n:{m for m in names if m!=n and (g(n,m) is not None) and g(n,m)<MAXC} for n in names}
# greedy: arranca por el activo menos acoplado y anade el siguiente compatible
best=[]
for seed in [n for _,n in med]:
    cur=[seed]; cand=set(adj[seed])
    while cand:
        nxt=min(cand, key=lambda m: st.median([g(m,c) for c in cur]))
        cur.append(nxt); cand &= adj[nxt]
    if len(cur)>len(best): best=cur
print(f"\nCARTERA LEGAL MAS GRANDE posible (toda corr < {MAXC}): {len(best)} activos")
print("  ", ", ".join(sorted(best)))
for k in (2,3,4):
    tot=good=0
    for cb in itertools.combinations(names,k):
        tot+=1
        if all(g(x,y) is not None and g(x,y)<MAXC for x,y in itertools.combinations(cb,2)): good+=1
    print(f"  carteras legales tamano {k}: {good}/{tot} ({100.0*good/tot:.1f}%)")
