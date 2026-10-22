"""Futures tick-data downloader (Databento, CME Globex MDP3).

Downloads trade-by-trade data (price, size, aggressor side) one session day
per file, so downloads can resume and nothing is fetched twice.

SAFETY: every run prices the request first and refuses to spend more than
--budget USD unless you raise the budget explicitly. Costs are logged.

Examples:
  .venv/bin/python futures/fetch.py --symbol NQ --start 2026-10-01 --end 2026-10-22 --quote
  .venv/bin/python futures/fetch.py --symbol NQ --start 2026-10-01 --end 2026-10-22 --budget 10
"""
import argparse, csv, datetime as dt, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = "GLBX.MDP3"


def api_key():
    k = os.environ.get("DATABENTO_API_KEY")
    if not k:
        for line in open(os.path.join(ROOT, ".env")):
            if line.startswith("DATABENTO_API_KEY="):
                k = line.split("=", 1)[1].strip()
    if not k:
        sys.exit("No DATABENTO_API_KEY in environment or .env")
    return k


def days(start, end):
    d = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    while d < e:
        if d.weekday() < 5:          # CME equity futures: no Sat sessions
            yield d
        d += dt.timedelta(days=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="NQ", help="root: NQ, MNQ, ES, MES")
    p.add_argument("--schema", default="trades")
    p.add_argument("--start", required=True, help="YYYY-MM-DD inclusive")
    p.add_argument("--end", required=True, help="YYYY-MM-DD exclusive")
    p.add_argument("--budget", type=float, default=5.0, help="max USD this run")
    p.add_argument("--quote", action="store_true", help="price only, download nothing")
    a = p.parse_args()

    import databento as db
    c = db.Historical(api_key())
    sym = f"{a.symbol}.c.0"   # front-month continuous (rolls by open interest/calendar)
    outdir = os.path.join(ROOT, "data", "futures", a.symbol, a.schema)
    os.makedirs(outdir, exist_ok=True)
    todo = [d for d in days(a.start, a.end)
            if not os.path.exists(os.path.join(outdir, f"{d}.parquet"))]
    if not todo:
        print("Nothing to do: all days already downloaded."); return

    q = dict(dataset=DATASET, symbols=[sym], stype_in="continuous", schema=a.schema,
             start=str(todo[0]), end=str(todo[-1] + dt.timedelta(days=1)))
    cost = c.metadata.get_cost(**q)
    nrec = c.metadata.get_record_count(**q)
    print(f"{a.symbol} {a.schema} {todo[0]} -> {todo[-1]}: {len(todo)} days, "
          f"{nrec:,} records, estimated ${cost:.2f} (budget ${a.budget:.2f})")
    if a.quote:
        return
    if cost > a.budget:
        sys.exit("REFUSED: estimate exceeds budget. Re-run with a higher --budget if intended.")

    log = os.path.join(ROOT, "data", "futures", "fetch_log.csv")
    new = not os.path.exists(log)
    spent = 0.0
    with open(log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["fetched_at", "symbol", "schema", "day", "records", "est_cost_usd"])
        for d in todo:
            one = dict(q, start=str(d), end=str(d + dt.timedelta(days=1)))
            dc = c.metadata.get_cost(**one)
            df = c.timeseries.get_range(**one).to_df()
            if len(df) == 0:
                print(f"  {d}: no data (holiday?)"); continue
            df.to_parquet(os.path.join(outdir, f"{d}.parquet"))
            spent += dc
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), a.symbol,
                        a.schema, d, len(df), round(dc, 4)])
            fh.flush()
            print(f"  {d}: {len(df):,} trades, ${dc:.3f}  (run total ${spent:.2f})")
    print(f"Done. Spent about ${spent:.2f}.")


if __name__ == "__main__":
    main()
