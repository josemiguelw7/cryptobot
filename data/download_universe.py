"""
Bulk-download 5-minute candles for every product in universe.json.
Resumable: skips pairs already saved. Public endpoints, no keys.

Usage:
    python data/download_universe.py --days 60
"""
import argparse, json, os, time
from datetime import datetime, timezone
import fetch_candles as fc

HERE = os.path.dirname(__file__)
UNIVERSE = os.path.join(HERE, "universe.json")
GRAN = 300  # 5-minute


def already_have(product):
    path = os.path.join(fc.OUT_DIR, f"{product}_{GRAN}s.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--force", action="store_true", help="re-download existing")
    ap.add_argument("--gran", type=int, default=300, help="candle seconds")
    args = ap.parse_args()

    global GRAN
    GRAN = args.gran

    with open(UNIVERSE) as f:
        products = json.load(f)

    print(f"Downloading {GRAN}s candles, {args.days}d, for {len(products)} pairs\n")
    t0 = time.time()
    done, skipped, failed = 0, 0, []

    for i, product in enumerate(products, 1):
        if already_have(product) and not args.force:
            print(f"[{i:2d}/{len(products)}] {product:12s} already on disk, skip")
            skipped += 1
            continue
        try:
            print(f"[{i:2d}/{len(products)}] {product:12s} fetching...")
            rows = fc.fetch_history(product, GRAN, args.days)
            fc.save_csv(product, GRAN, rows)
            print(f"              -> {len(rows)} candles")
            done += 1
        except Exception as e:
            print(f"              !! FAILED: {e}")
            failed.append(product)
        time.sleep(0.3)

    mins = (time.time() - t0) / 60
    print(f"\nDone in {mins:.1f} min. downloaded={done} skipped={skipped} "
          f"failed={len(failed)}")
    if failed:
        print(f"Failed pairs: {failed}")


if __name__ == "__main__":
    main()
