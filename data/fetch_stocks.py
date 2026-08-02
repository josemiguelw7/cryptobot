"""
Stock data store - fixed, pre-declared universe. 1h and 1d bars via
yfinance (auto-adjusted for splits/dividends).

UNIVERSE (declared 2026-08-02, before any strategy result was seen):
3 index ETFs for breadth/regime + 7 largest liquid megacaps. Chosen by
TODAY's liquidity, so any backtest on the single names carries
survivorship optimism - that caveat is pre-registered in
docs/stocks_standard.md and the forward squad, not the backtest, is
the judge. The universe is FROZEN: changing it requires a new
generation, never an edit.
"""
import os, time
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stocks")
UNIVERSE = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN",
            "GOOGL", "META", "TSLA"]

def save(tk, interval, period, tag):
    d = yf.download(tk, period=period, interval=interval,
                    progress=False, auto_adjust=True)
    if d is None or len(d) == 0:
        print(f"  {tk} {tag}: EMPTY"); return 0
    if hasattr(d.columns, "levels"):          # flatten MultiIndex
        d.columns = d.columns.get_level_values(0)
    d = d.reset_index()
    tcol = d.columns[0]
    d["timestamp"] = (d[tcol].astype("int64") // 10**9)
    d["datetime"] = d[tcol].astype(str)
    d = d[["timestamp", "datetime", "Open", "High", "Low", "Close",
           "Volume"]]
    d.columns = ["timestamp", "datetime", "open", "high", "low",
                 "close", "volume"]
    p = os.path.join(OUT, f"{tk}_{tag}.csv")
    d.to_csv(p, index=False)
    return len(d)

def main():
    os.makedirs(OUT, exist_ok=True)
    for tk in UNIVERSE:
        n1 = save(tk, "1h", "730d", "1h")
        time.sleep(1)
        n2 = save(tk, "1d", "10y", "1d")
        time.sleep(1)
        print(f"  {tk}: {n1} 1h bars, {n2} 1d bars")
    print("stock store complete.")

if __name__ == "__main__":
    main()
