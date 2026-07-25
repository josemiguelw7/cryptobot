"""
Rank Coinbase USD spot pairs by 24h dollar volume and save the top N.
Public endpoints only - no API keys.

Usage:
    python data/build_universe.py --top 25
"""
import argparse, json, os, time
import requests

BASE = "https://api.exchange.coinbase.com"
OUT = os.path.join(os.path.dirname(__file__), "universe.json")

# Skip stablecoins and wrapped/staked derivatives - they don't day-trade
EXCLUDE_BASES = {
    "USDT", "USDC", "DAI", "PYUSD", "GUSD", "USD", "EUR", "GBP",
    "WBTC", "CBETH", "CBBTC", "WCFG",
}


def get_usd_products():
    r = requests.get(f"{BASE}/products", timeout=30)
    r.raise_for_status()
    out = []
    for p in r.json():
        if (p.get("quote_currency") == "USD"
                and p.get("status") == "online"
                and not p.get("trading_disabled", False)
                and not p.get("limit_only", False)
                and p.get("base_currency") not in EXCLUDE_BASES):
            out.append(p["id"])
    return out


def dollar_volume(product):
    """24h volume (in base units) x last price = approx USD volume."""
    try:
        s = requests.get(f"{BASE}/products/{product}/stats", timeout=30).json()
        vol = float(s.get("volume", 0) or 0)
        last = float(s.get("last", 0) or 0)
        return vol * last
    except Exception:
        return 0.0


def build(top_n):
    products = get_usd_products()
    print(f"Found {len(products)} eligible USD pairs. Ranking by 24h volume...")

    ranked = []
    for i, prod in enumerate(products, 1):
        dv = dollar_volume(prod)
        ranked.append((prod, dv))
        if i % 25 == 0:
            print(f"  ...checked {i}/{len(products)}")
        time.sleep(0.1)

    ranked.sort(key=lambda x: x[1], reverse=True)
    top = ranked[:top_n]

    with open(OUT, "w") as f:
        json.dump([p for p, _ in top], f, indent=2)

    print(f"\nTop {top_n} by 24h dollar volume:")
    for rank, (prod, dv) in enumerate(top, 1):
        print(f"  {rank:2d}. {prod:12s} ${dv/1e6:,.1f}M")
    print(f"\nSaved -> {OUT}")
    return [p for p, _ in top]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()
    build(args.top)
