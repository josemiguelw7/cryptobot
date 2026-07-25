"""
Refresh daily candles for the entrance-exam pairs: fetch the last ~300
days from Coinbase and merge into the existing CSVs by timestamp.
League trading does NOT depend on these files (it fetches live);
this keeps backtest/exam data current. Safe to run daily.

Usage: python data/refresh_daily.py
"""
import csv, os, time
from datetime import datetime, timezone
import requests

BASE = "https://api.exchange.coinbase.com"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "candles_daily")
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
         "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD"]


def existing(path):
    rows = {}
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                rows[int(r["timestamp"])] = [
                    r["timestamp"], r["datetime"], r["low"], r["high"],
                    r["open"], r["close"], r["volume"]]
    return rows


def refresh(pair):
    path = os.path.join(OUT, f"{pair}_86400s.csv")
    rows = existing(path)
    r = requests.get(f"{BASE}/products/{pair}/candles",
                     params={"granularity": 86400}, timeout=30)
    r.raise_for_status()
    added = 0
    for t, lo, hi, op, cl, vol in sorted(r.json()):
        dt = datetime.fromtimestamp(t, timezone.utc)
        if int(t) not in rows:
            added += 1
        rows[int(t)] = [str(t), dt.strftime("%Y-%m-%d"),
                        lo, hi, op, cl, vol]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "datetime", "low", "high",
                    "open", "close", "volume"])
        for k in sorted(rows):
            w.writerow(rows[k])
    return added, len(rows)


def main():
    for pair in PAIRS:
        try:
            added, total = refresh(pair)
            print(f"  {pair}: +{added} new, {total} total")
        except Exception as e:
            print(f"  {pair}: FAILED ({e})")
        time.sleep(0.15)
    print("refresh complete.")


if __name__ == "__main__":
    main()
