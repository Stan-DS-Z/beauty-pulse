"""Rakuten weekly ingest — hand-run, on the NB01a cadence.

    python ingest_rakuten_weekly.py                 # today's snapshot
    python ingest_rakuten_weekly.py --date 2026-09-13
    python ingest_rakuten_weekly.py --latest        # newest complete snapshot
    python ingest_rakuten_weekly.py --all           # every snapshot on disk
    python ingest_rakuten_weekly.py --check         # resolve genres, ingest nothing

Run it after NB01a. It fills both Rakuten tables from the raw snapshot files:

  products         current state — one row per SKU, newest values
  products_weekly  history — one row per (product_id, snapshot_date)

This is the ingest path NB02 section 3 and NB02c sections 3-4 perform in the
notebooks. It exists as a script so the weekly loop does not have to re-run all
of NB02, which re-walks the @cosme, Amazon, YouTube and Trends files every time
even though none of them move on the Rakuten cadence.

The notebooks and this script agree. Both carried two defects until 2026-09-20,
stacked so that the first hid the second:

  - NB02 read ranking files as data["Items"]; NB01a writes them under "items".
    Every ranking file ingested zero rows, so a SKU that appears only in the
    ranking API never reached products with its genre attached.
  - NB02c resolved genre -> category_id with
    `normalized_name LIKE '%{genre_id}%'`, but normalized_name holds
    'serum_essence', 'korean_cosmetics' and the like. No genre ever matched, so
    every insert silently took the fallback category (美容液, skincare).
  - Behind the first: NB02's ranking loop passed is_ranking=True to
    ingest_rakuten_product, which has no such parameter. It would have raised
    on its first item — the loop body was simply never reached.

Together the first two filed 336 ranking-only SKUs as 美容液 between 2026-04-02
and 2026-09-13; 131 of them were not skincare. Repaired 2026-09-20.

Two rules here that the notebooks do not have:
  - genre resolution is exact on source_cat_id and RAISES if a genre is
    missing. A silent fallback is what caused the misfiling.
  - a date whose files are not all present and non-empty is refused outright,
    so a half-finished scrape never lands as a genuine week-on-week collapse.

Category for a new SKU follows NB02's rule unchanged: product files first, then
ranking files, both in sorted filename order, first file to carry the SKU wins.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import load_rakuten_genres          # noqa: E402
from src.schema import get_connection, DB_PATH      # noqa: E402
from src.utils import DATA_RAW                      # noqa: E402

PRODUCTS_DIR = DATA_RAW / "rakuten" / "products"
RANKING_DIR = DATA_RAW / "rakuten" / "ranking"

DDL = [
    """CREATE TABLE IF NOT EXISTS products_weekly (
        snapshot_id      INTEGER PRIMARY KEY,
        product_id       INTEGER NOT NULL,
        source_item_id   TEXT    NOT NULL,
        snapshot_date    TEXT    NOT NULL,
        price_jpy        INTEGER,
        review_count     INTEGER,
        review_avg       REAL,
        ranking_position INTEGER,
        is_ranking       INTEGER DEFAULT 0,
        is_new_product   INTEGER DEFAULT 0,
        ingested_at      TEXT    DEFAULT (datetime('now','utc')),
        UNIQUE(product_id, snapshot_date),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_pw_date ON products_weekly(snapshot_date)",
    "CREATE INDEX IF NOT EXISTS idx_pw_product ON products_weekly(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_pw_new ON products_weekly(is_new_product, snapshot_date)",
]


class IngestError(RuntimeError):
    """A snapshot is not fit to ingest. Nothing is written."""


def resolve_genres(conn) -> dict[str, int]:
    """genre_id -> category_id, exact on source_cat_id.

    Raises if any configured genre has no category row: an unmapped genre means
    the seed step in NB02 section 2 has not run for it, and guessing a category
    is how 336 SKUs ended up in the wrong one.
    """
    genres = load_rakuten_genres(layer1=True)
    mapping, missing = {}, []
    for _, row in genres.iterrows():
        gid = str(row["rakuten_genre_id"])
        got = conn.execute(
            "SELECT category_id FROM categories WHERE source_id = 1 AND source_cat_id = ?",
            (gid,),
        ).fetchone()
        if got is None:
            missing.append(f"{gid} ({row['genre_name_jp']})")
        else:
            mapping[gid] = got[0]
    if missing:
        raise IngestError(
            "no categories row for genre(s): " + ", ".join(missing)
            + "\nRun NB02 section 2 (seed categories) before ingesting."
        )
    return mapping


def read_items(path: Path) -> list[dict]:
    """The items in a raw snapshot file.

    NB01a writes {'genre_id', 'genre_name', 'pulled_date', 'item_count',
    'items'} for both products and ranking. The other keys are tolerated for
    older files.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = data
    else:
        items = data.get("items") or data.get("Items") or data.get("products") or []
    return [i.get("Item", i) for i in items]


def files_for(snapshot_date: str | None) -> list[tuple[Path, bool]]:
    """(path, is_ranking) for a date, or for every date when None.

    Product files first, then ranking files, each sorted — this is the order
    NB02 ingests in, and it decides which genre a new SKU is filed under.
    """
    suffix = f"_{snapshot_date}.json" if snapshot_date else "_*.json"
    products = sorted(PRODUCTS_DIR.glob(f"rakuten_products_*{suffix}"))
    ranking = sorted(RANKING_DIR.glob(f"rakuten_ranking_*{suffix}"))
    return [(f, False) for f in products] + [(f, True) for f in ranking]


def check_complete(files: list[tuple[Path, bool]], expected_genres: int) -> None:
    """Refuse a snapshot that is short or carries an empty file."""
    if not files:
        raise IngestError("no snapshot files found — run NB01a first.")
    empty = [f.name for f, _ in files if not read_items(f)]
    if empty:
        raise IngestError(
            f"{len(empty)} empty file(s) — a failed pull, not a real week:\n  "
            + "\n  ".join(empty)
            + "\nDelete them and re-run NB01a; it re-pulls only what is missing."
        )
    n_products = sum(1 for _, is_rank in files if not is_rank)
    n_ranking = len(files) - n_products
    for label, n in (("product", n_products), ("ranking", n_ranking)):
        if n != expected_genres:
            raise IngestError(
                f"{n} {label} file(s) for {expected_genres} genres — the scrape "
                "is incomplete. Re-run NB01a."
            )


def ingest_item(conn, item: dict, category_id: int, snapshot_date: str,
                ranking_position: int | None, is_ranking: bool) -> bool:
    """One SKU into products and products_weekly. Returns whether it was new.

    products UPDATE uses COALESCE so a NULL from a partial scrape never
    overwrites a good value, and never touches category_id — a SKU keeps the
    genre it was first filed under, which is NB02's rule.
    """
    source_item_id = item.get("itemCode") or item.get("item_code") or item.get("itemUrl", "")
    if not source_item_id:
        return False

    name = item.get("itemName") or item.get("item_name", "")
    price = item.get("itemPrice", item.get("price_jpy"))
    reviews = item.get("reviewCount", item.get("review_count", 0))
    avg = item.get("reviewAverage", item.get("review_avg"))
    try:
        price = int(price) if price is not None else None
        reviews = int(reviews) if reviews is not None else 0
        avg = float(avg) if avg is not None else None
        ranking_position = int(ranking_position) if ranking_position else None
    except (TypeError, ValueError):
        pass

    cur = conn.cursor()
    row = cur.execute(
        "SELECT product_id FROM products WHERE source_id = 1 AND source_item_id = ?",
        (source_item_id,),
    ).fetchone()
    is_new = row is None

    if is_new:
        cur.execute(
            """INSERT OR IGNORE INTO products
                   (source_id, source_item_id, product_name, category_id,
                    price_jpy, review_count, review_avg, ranking_position, snapshot_date)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_item_id, name, category_id, price, reviews, avg,
             ranking_position, snapshot_date),
        )
        product_id = cur.lastrowid
    else:
        product_id = row[0]
        cur.execute(
            """UPDATE products SET
                   review_count     = COALESCE(?, review_count),
                   review_avg       = COALESCE(?, review_avg),
                   price_jpy        = COALESCE(?, price_jpy),
                   ranking_position = COALESCE(?, ranking_position),
                   snapshot_date    = ?
               WHERE product_id = ?""",
            (reviews, avg, price, ranking_position, snapshot_date, product_id),
        )

    cur.execute(
        """INSERT INTO products_weekly
               (product_id, source_item_id, snapshot_date, price_jpy, review_count,
                review_avg, ranking_position, is_ranking, is_new_product)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(product_id, snapshot_date) DO UPDATE SET
               ranking_position = CASE WHEN excluded.is_ranking = 1
                                       THEN excluded.ranking_position
                                       ELSE ranking_position END,
               is_ranking       = CASE WHEN excluded.is_ranking = 1
                                       THEN 1 ELSE is_ranking END""",
        (product_id, source_item_id, snapshot_date, price, reviews, avg,
         ranking_position, int(is_ranking), int(is_new)),
    )
    return is_new


def dates_on_disk() -> list[str]:
    return sorted({f.stem.split("_")[3] for f, _ in files_for(None)
                   if len(f.stem.split("_")) > 3})


def latest_complete(genre_map: dict[str, int]) -> str:
    """The newest date whose 22 files are all present and non-empty."""
    for d in reversed(dates_on_disk()):
        try:
            check_complete(files_for(d), len(genre_map))
            return d
        except IngestError:
            continue
    raise IngestError("no complete snapshot on disk — run NB01a first.")


def ingest_date(conn, snapshot_date: str, genre_map: dict[str, int]) -> dict:
    """One complete snapshot date. Refuses an incomplete one."""
    files = files_for(snapshot_date)
    check_complete(files, len(genre_map))

    def weekly_rows() -> int:
        return conn.execute("SELECT COUNT(*) FROM products_weekly").fetchone()[0]

    totals = {"files": 0, "rows": 0, "new": 0}
    for path, is_ranking in files:
        genre_id = path.stem.split("_")[2]
        items = read_items(path)
        before = weekly_rows()
        for i, item in enumerate(items):
            totals["new"] += ingest_item(
                conn, item, genre_map[genre_id], snapshot_date, i + 1, is_ranking
            )
        conn.commit()
        added = weekly_rows() - before
        totals["files"] += 1
        totals["rows"] += added
        print(f"  {path.name:<48} {added:>6,} new rows  ({len(items):,} items)")
    return totals


def run(conn, snapshot_date: str | None, genre_map: dict[str, int]) -> dict:
    """One date, or every complete date on disk.

    --all skips incomplete dates rather than ingesting them: 2026-03-28 has
    ranking files and no product files, and ingesting it would put a 330-row
    snapshot_date into the series that reads as a week-on-week collapse.
    """
    if snapshot_date:
        return ingest_date(conn, snapshot_date, genre_map)

    totals = {"files": 0, "rows": 0, "new": 0}
    targets = dates_on_disk()
    if not targets:
        raise IngestError("no snapshot files found.")
    for d in targets:
        try:
            check_complete(files_for(d), len(genre_map))
        except IngestError as e:
            print(f"  SKIP {d} — {str(e).splitlines()[0]}")
            continue
        print(f"\n{d}")
        got = ingest_date(conn, d, genre_map)
        for k in totals:
            totals[k] += got[k]
    return totals


def report(conn) -> None:
    # GROUP BY on the expression, not on the alias: SQLite resolves a bare
    # `tier` to the categories column and splits each tier in two.
    canon = "COALESCE(p.tier_predicted, p.tier_override, c.tier)"
    print("\nSKUs by tier:")
    for tier, n in conn.execute(f"""
            SELECT {canon} AS tier_canonical, COUNT(*) FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.source_id = 1
            GROUP BY {canon} ORDER BY COUNT(*) DESC"""):
        print(f"  {tier or '(none)':<22} {n:>8,}")

    rows, dates = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT snapshot_date) FROM products_weekly"
    ).fetchone()
    print(f"\nproducts_weekly : {rows:,} rows across {dates} snapshot dates")

    orphans = conn.execute("""
        SELECT COUNT(*) FROM products_weekly pw
        LEFT JOIN products p ON pw.product_id = p.product_id
        WHERE p.product_id IS NULL""").fetchone()[0]
    print(f"orphaned rows   : {orphans}" + ("" if orphans == 0 else "   *** CHECK ***"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--date", help="snapshot date YYYY-MM-DD (default: today)")
    g.add_argument("--all", action="store_true", help="every snapshot on disk")
    g.add_argument("--latest", action="store_true",
                   help="newest complete snapshot on disk, whatever its date")
    ap.add_argument("--check", action="store_true", help="resolve genres and exit")
    args = ap.parse_args()

    conn = get_connection()
    print(f"DB: {DB_PATH}")
    try:
        genre_map = resolve_genres(conn)
        print(f"Genres resolved: {len(genre_map)}/{len(genre_map)}")
        if args.check:
            for gid, cid in genre_map.items():
                print(f"  genre {gid:<8} -> category_id {cid}")
            return 0

        for ddl in DDL:
            conn.execute(ddl)
        conn.commit()

        if args.all:
            target = None
        elif args.latest:
            target = latest_complete(genre_map)
            print(f"Newest complete snapshot on disk: {target}")
        else:
            # Default is today, and a missing today is a refusal, not a
            # fallback: after a scrape, silence means the scrape failed.
            target = args.date or str(date.today())
        print(f"Ingesting: {target or 'all snapshots'}\n")
        totals = run(conn, target, genre_map)
        print(f"\n{totals['files']} files | {totals['rows']:,} weekly rows | "
              f"{totals['new']:,} new SKUs")
        report(conn)
    except IngestError as e:
        print(f"\nREFUSED: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
