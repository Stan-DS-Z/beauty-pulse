"""
signal_pulse/src/schema.py
──────────────────────────
Canonical SQLite schema for Signal/Pulse.
All CREATE TABLE statements live here — NB02 imports and executes them.

Design decisions are documented inline. Read this file as a design document,
not just DDL.

Schema version: 1.0
"""

import gzip
import shutil
import sqlite3
import logging
from pathlib import Path

log = logging.getLogger("signal_pulse.schema")

# ── Database paths ─────────────────────────────────────────────────────────────
#
# The primary DB is gitignored (it carries product_name and raw_json), so it is
# absent from a clone. The stripped public DB ships gzipped in dashboard/assets
# and is what a reader auditing NB03-NB07 actually has. resolve_db_path() picks
# whichever is present, so the analysis notebooks run either way.

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "signal_pulse.db"
PUBLIC_DB_PATH = ROOT / "data" / "signal_pulse_public.db"
PUBLIC_DB_GZ = ROOT / "dashboard" / "assets" / "signal_pulse_public.db.gz"


def resolve_db_path() -> tuple[Path, bool]:
    """Return (path, is_public) for the best available database.

    Order: the primary DB, then an already-extracted public DB, then the shipped
    archive (extracted once into data/, which is gitignored). If none exists we
    return the primary path so NB02 can still create a database from scratch.
    """
    if DB_PATH.exists():
        return DB_PATH, False
    if PUBLIC_DB_PATH.exists():
        return PUBLIC_DB_PATH, True
    if PUBLIC_DB_GZ.exists():
        log.info("No primary DB — extracting %s (one-off, ~105 MB)", PUBLIC_DB_GZ.name)
        PUBLIC_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(PUBLIC_DB_GZ, "rb") as src, open(PUBLIC_DB_PATH, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return PUBLIC_DB_PATH, True
    return DB_PATH, False


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    """
    Return a sqlite3 connection with foreign key enforcement and
    WAL mode (better concurrent read performance during ingestion).

    With no argument the database is resolved via resolve_db_path(). The public
    DB is opened read-only: it is a published artefact and has no product_name
    or raw_json, so an ingestion or schema write against it would fail anyway —
    better it fails on the first write than half-way through.
    """
    read_only = False
    if path is None:
        path, read_only = resolve_db_path()
        if read_only:
            log.info("Using the public database (read-only): %s", path.name)

    if read_only:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.execute("PRAGMA foreign_keys = ON")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row   # dict-like access to rows
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# DDL
# Each table is a separate string so NB02 can execute and document them
# individually.
# ══════════════════════════════════════════════════════════════════════════════

# ── sources ───────────────────────────────────────────────────────────────────
# Design: A lookup table so every row in every other table can declare where
# it came from without storing a free-text string. Enables clean GROUP BY source
# comparisons in NB03.

DDL_SOURCES = """
CREATE TABLE IF NOT EXISTS sources (
    source_id   INTEGER PRIMARY KEY,
    source_name TEXT    NOT NULL UNIQUE,   -- 'rakuten', 'cosme', 'amazon_jp', 'google_trends', 'youtube'
    description TEXT,
    first_loaded_at TEXT                   -- ISO-8601 UTC timestamp
);
"""

SOURCES_SEED = [
    (1, "rakuten",       "Rakuten Ichiba API — current commercial snapshot"),
    (2, "cosme",         "@cosme — primary review/customer layer"),
    (3, "amazon_jp",     "Amazon.co.jp — secondary review layer (conditional)"),
    (4, "google_trends", "Google Trends JP — weekly search demand signal"),
    (5, "youtube",       "YouTube JP — creator/influencer signal layer"),
]


# ── categories ────────────────────────────────────────────────────────────────
# Design: Unified category taxonomy that spans all sources.
# Each source has its own genre/category naming — this table normalises them
# into a single hierarchy (parent → child).
# The `tier` column encodes the skincare vs. cosmetics distinction central to
# the hypothesis (NB04).

DDL_CATEGORIES = """
CREATE TABLE IF NOT EXISTS categories (
    category_id     INTEGER PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES sources(source_id),
    source_cat_id   TEXT,                  -- original ID from source (e.g. Rakuten genreId)
    source_cat_name TEXT    NOT NULL,      -- original name from source (Japanese)
    normalized_name TEXT    NOT NULL,      -- standardised English name for analysis
    tier            TEXT    NOT NULL       -- 'skincare' | 'cosmetics' | 'haircare' | 'bodycare' | 'other'
                    CHECK (tier IN ('skincare','cosmetics','haircare','bodycare','other')),
    parent_id       INTEGER REFERENCES categories(category_id),
    created_at      TEXT DEFAULT (datetime('now','utc'))
);
"""


# ── brands ────────────────────────────────────────────────────────────────────
# Design: Separate table for brand metadata so we can JOIN across sources
# without string-matching brand names in every query. brand_group is the key
# for portfolio-specific subsetting; no single company is privileged.

DDL_BRANDS = """
CREATE TABLE IF NOT EXISTS brands (
    brand_id        INTEGER PRIMARY KEY,
    brand_name_jp   TEXT    NOT NULL,      -- Japanese name (e.g. キュレル)
    brand_name_en   TEXT,                  -- English/romanised (e.g. Curél)
    parent_company  TEXT,                  -- e.g. 'Kao', 'Shiseido', 'Kose'
    brand_group     TEXT,                  -- group key e.g. 'kao', 'shiseido', 'rohto'
    is_target       INTEGER NOT NULL DEFAULT 0  -- 1 if brand is in active lens
                    CHECK (is_target IN (0,1)),
    tier            TEXT                   -- brand's primary positioning tier
);
"""

def dedupe_categories(conn: sqlite3.Connection, dry_run: bool = True) -> dict:
    """Collapse duplicate category rows to the copy the data actually points at.

    Deletes only rows that (a) share (source_id, source_cat_id) with a lower
    category_id and (b) are referenced by nothing. It refuses rather than
    rewriting a foreign key, so it cannot silently move a product between
    categories. Idempotent; call with dry_run=False to apply.
    """
    referenced = {r[0] for r in conn.execute("""
        SELECT DISTINCT category_id FROM products  WHERE category_id IS NOT NULL
        UNION SELECT DISTINCT category_id FROM reviews   WHERE category_id IS NOT NULL
        UNION SELECT DISTINCT category_id FROM yt_videos WHERE category_id IS NOT NULL
    """)}
    keep = {r[0] for r in conn.execute(
        "SELECT MIN(category_id) FROM categories GROUP BY source_id, source_cat_id")}

    stranded = referenced - keep
    if stranded:
        raise RuntimeError(
            f"{len(stranded)} referenced category rows are not the lowest-id copy "
            f"of their genre: {sorted(stranded)[:10]}. Deduping would orphan them.")

    doomed = [r[0] for r in conn.execute("SELECT category_id FROM categories")
              if r[0] not in keep and r[0] not in referenced]
    result = {"total": len(keep) + len(doomed), "keep": len(keep), "delete": len(doomed)}
    if not dry_run and doomed:
        conn.executemany("DELETE FROM categories WHERE category_id = ?",
                         [(c,) for c in doomed])
        conn.commit()
        result["deleted"] = len(doomed)
    return result


def get_schema_info(conn: sqlite3.Connection) -> list[dict]:
    """Return list of table stats for the schema report in NB02."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    results = []
    for (table,) in tables:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        results.append({
            "table": table,
            "columns": len(cols),
            "rows": count,
            "foreign_keys": len(fks),
            "col_names": [c[1] for c in cols],
        })
    return results
