"""Write dashboard/assets/source_dates.csv: the dates only the database holds.

    python build_source_dates.py            # from data/signal_pulse.db
    python build_source_dates.py --db PATH  # from another copy, e.g. the public DB

The site dates every exhibit by its source (bp/sources.py). Four sources carry
their dates in the CSV assets the app already ships: METI and 貿易統計 by year and
month, Google Trends by month, PR TIMES by release and fetch date. The rest are
visible only in the database, which the app image never opens (.dockerignore),
so this script exports them. One row per source and date:

  source     rakuten | cosme | youtube | amazon | trends
  date_kind  data_to (newest data) | first (oldest collection) |
             collections (how many) | collected (the last pull, where it
             differs from data_to)
  value      an ISO date, or a count for collections

Which column each date comes from, and why:
  rakuten  products_weekly.snapshot_date: the weekly pull's own date.
  cosme    reviews.review_date, newest: the scrape reads a product's newest
           reviews first, so the newest review is dated the day of the scrape.
           Not products.snapshot_date, which a later ingest re-stamps.
  youtube  yt_comments.published_at, newest, for the same reason. Not
           yt_videos.stats_snapshot_date, which a later ingest re-stamps.
  amazon   products.snapshot_date for source 3: each pull's product list is
           stamped on the day it ran. Its review dates are sampled per product
           and stop months earlier.
  trends   trends_weekly.pulled_at for block_A and block_B, the two blocks the
           site uses. The newest month is read from the shipped assets instead.

Run it after the Rakuten ingest, as update_data.command does. The suite checks
the file against the public DB (tests/test_sources.py), and against this Mac's
database when it is present.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dashboard" / "assets" / "source_dates.csv"
DB = ROOT / "data" / "signal_pulse.db"

# source_id in the sources table.
RAKUTEN, COSME, AMAZON = 1, 2, 3
SITE_TRENDS_BLOCKS = ("block_A", "block_B")


def source_dates(conn: sqlite3.Connection) -> pd.DataFrame:
    """The dates, read from one database connection."""
    one = lambda sql, *a: conn.execute(sql, a).fetchone()
    rows = []

    def add(source, kind, value):
        rows.append({"source": source, "date_kind": kind, "value": str(value)})

    first, last, n = one("SELECT MIN(snapshot_date), MAX(snapshot_date), "
                         "COUNT(DISTINCT snapshot_date) FROM products_weekly")
    add("rakuten", "data_to", last[:10])
    add("rakuten", "first", first[:10])
    add("rakuten", "collections", n)

    (newest,) = one("SELECT MAX(review_date) FROM reviews WHERE source_id = ?", COSME)
    add("cosme", "data_to", newest[:10])

    (newest,) = one("SELECT MAX(published_at) FROM yt_comments")
    add("youtube", "data_to", newest[:10])

    last, n = one("SELECT MAX(snapshot_date), COUNT(DISTINCT snapshot_date) "
                  "FROM products WHERE source_id = ?", AMAZON)
    add("amazon", "data_to", last[:10])
    add("amazon", "collections", n)

    marks = ",".join("?" * len(SITE_TRENDS_BLOCKS))
    (pulled,) = one(f"SELECT MAX(pulled_at) FROM trends_weekly "
                    f"WHERE term_group IN ({marks})", *SITE_TRENDS_BLOCKS)
    add("trends", "collected", pulled[:10])

    return pd.DataFrame(rows, columns=["source", "date_kind", "value"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DB)
    args = ap.parse_args()
    if not args.db.exists():
        print(f"missing: {args.db}", file=sys.stderr)
        return 1
    with sqlite3.connect(f"file:{args.db}?mode=ro", uri=True) as conn:
        df = source_dates(conn)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}")
    for r in df.itertuples():
        print(f"  {r.source:8s} {r.date_kind:12s} {r.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
