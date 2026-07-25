"""
Download ~4 years of DAILY candles for EVERY Coinbase USD pair,
including not-currently-online ones where data exists (this shrinks
survivorship bias - a truly delisted pair can't be fetched, and that
residual bias is noted honestly in the backtest).

Saves to data/candles_daily/{PAIR}_86400s.csv. Resumable.

Usage:
    python data/download_all_daily.py
"""
import csv, os, time
from datetime import datetime, timedelta, timezone
import requests

BASE = "https://api.exchange.coinbase.com"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "candles_daily")
DAYS = 1460
EXCLUDE_BASES = {"USDT", "USDC", "DAI", "PYUSD", "GUSD", "EUR", "GBP", "USD"}


def usd_pairs():
    r = requests.get(f"{BASE}/products", timeout=30)
    r.raise_for_status()
    return sorted(p["id"] for p in r.json()
                  if p.get("quote_currency") == "USD"
                  and p.get("base_currency") not in EXCLUDE_BASES)


def fetch(pair):
    end = datetime.now(timezone.utc)
    start_limit = end - timedelta(days=DAYS)
    span = timedelta(seconds=86400 * 300)
    rows, cur = {}, end
    while cur > start_limit:
        s = max(cur - span, start_limit)
        r = requests.get(f"{BASE}/products/{pair}/candles",
                         params={"granularity": 86400,
                                 "start": s.isoformat(),
                                 "end": cur.isoformat()},
                         timeout=30)
        if r.status_code != 200:
            break
        chunk = r.json()
        if not chunk:
            break
        for row in chunk:
            rows[row[0]] = row
        cur = s
        time.sleep(0.2)
    return [rows[k] for k in sorted(rows)]


def main():
    os.makedirs(OUT, exist_ok=True)
    pairs = usd_pairs()
    print(f"{len(pairs)} USD pairs to fetch ({DAYS} days daily)")
    done = skip = 0
    failed = []
    t0 = time.time()
    for i, pair in enumerate(pairs, 1):
        path = os.path.join(OUT, f"{pair}_86400s.csv")
        if os.path.exists(path) and os.path.getsize(path) > 200:
            skip += 1
            continue
        try:
            rows = fetch(pair)
        except Exception as e:
            failed.append(pair)
            print(f"[{i}] {pair} FAILED: {e}")
            continue
        if not rows:
            failed.append(pair)
            continue
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "datetime", "low", "high",
                        "open", "close", "volume"])
            for t, lo, hi, op, cl, vol in rows:
                dt = datetime.fromtimestamp(t, timezone.utc)
                w.writerow([t, dt.strftime("%Y-%m-%d"), lo, hi, op, cl, vol])
        done += 1
        if i % 25 == 0:
            print(f"  {i}/{len(pairs)} (saved {done}, skipped {skip}, "
                  f"{(time.time()-t0)/60:.1f} min)")
        time.sleep(0.1)
    print(f"\nDONE in {(time.time()-t0)/60:.1f} min: "
          f"saved={done} skipped={skip} failed={len(failed)}")


if __name__ == "__main__":
    main()
