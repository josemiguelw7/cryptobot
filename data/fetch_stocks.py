"""
Fetch daily stock/ETF history via yfinance (split/dividend adjusted)
and store it in the system's candle format:
    timestamp,datetime,low,high,open,close,volume
Saved as {SYM}-US_86400s.csv in candles_daily so the research screen
discovers them automatically. Stocks are a RESEARCH universe only; the
entrance exam pair set and the league are untouched.

    python data/fetch_stocks.py
"""
import csv, os
from datetime import timezone
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "candles_daily")

SYMS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL",
        "AMZN", "META", "TSLA", "JPM", "XOM", "UNH"]

def fetch(sym):
    df = yf.Ticker(sym).history(period="max", interval="1d",
                                auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError("empty response")
    out = os.path.join(OUT, f"{sym}-US_86400s.csv")
    n = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "datetime", "low", "high",
                    "open", "close", "volume"])
        for ts, row in df.iterrows():
            try:
                d = ts.strftime("%Y-%m-%d")
                epoch = int(ts.tz_convert(timezone.utc).timestamp()
                            if ts.tzinfo else ts.timestamp())
                w.writerow([epoch, d,
                            round(float(row["Low"]), 6),
                            round(float(row["High"]), 6),
                            round(float(row["Open"]), 6),
                            round(float(row["Close"]), 6),
                            int(row.get("Volume", 0) or 0)])
                n += 1
            except Exception:
                continue
    return n

def main():
    for s in SYMS:
        try:
            print(f"  {s:>6}: {fetch(s)} daily bars")
        except Exception as e:
            print(f"  {s:>6}: FAILED ({e})")

if __name__ == "__main__":
    main()
