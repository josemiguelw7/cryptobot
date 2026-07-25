"""
Download historical OHLCV candles from Coinbase's public market-data API.
No API keys required - this endpoint is public, read-only.

Usage:
    python data/fetch_candles.py BTC-USD 3600 365
    (product, granularity_seconds, days_back)
"""
import sys, time, csv, os
from datetime import datetime, timedelta, timezone
import requests

BASE = "https://api.exchange.coinbase.com"
MAX_CANDLES = 300  # Coinbase caps each request at 300 rows
OUT_DIR = os.path.join(os.path.dirname(__file__), "candles")

GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}


def fetch_chunk(product, granularity, start, end):
    url = f"{BASE}/products/{product}/candles"
    params = {
        "granularity": granularity,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    # Coinbase returns [time, low, high, open, close, volume], newest first
    return r.json()


def fetch_history(product, granularity, days_back):
    if granularity not in GRANULARITIES:
        raise ValueError(f"granularity must be one of {sorted(GRANULARITIES)}")

    end = datetime.now(timezone.utc)
    start_limit = end - timedelta(days=days_back)
    span = timedelta(seconds=granularity * MAX_CANDLES)

    rows = []
    cursor_end = end
    while cursor_end > start_limit:
        cursor_start = max(cursor_end - span, start_limit)
        chunk = fetch_chunk(product, granularity, cursor_start, cursor_end)
        if not chunk:
            break
        rows.extend(chunk)
        cursor_end = cursor_start
        time.sleep(0.35)  # stay well under the public rate limit
        print(f"  ...{len(rows)} candles so far (back to {cursor_start:%Y-%m-%d})")

    # dedupe by timestamp, sort oldest -> newest
    seen = {}
    for row in rows:
        seen[row[0]] = row
    return [seen[k] for k in sorted(seen)]


def save_csv(product, granularity, rows):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{product}_{granularity}s.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "datetime", "low", "high", "open", "close", "volume"])
        for t, low, high, op, close, vol in rows:
            dt = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([t, dt, low, high, op, close, vol])
    return path


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    granularity = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 365

    print(f"Fetching {product} @ {granularity}s for the last {days} days...")
    rows = fetch_history(product, granularity, days)
    path = save_csv(product, granularity, rows)
    print(f"\nSaved {len(rows)} candles -> {path}")
    if rows:
        first = datetime.fromtimestamp(rows[0][0], timezone.utc)
        last = datetime.fromtimestamp(rows[-1][0], timezone.utc)
        print(f"Range: {first:%Y-%m-%d} to {last:%Y-%m-%d}")
