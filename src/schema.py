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
# without string-matching brand names in every query. Kao group flag enables
# easy subsetting for portfolio-specific analysis.

DDL_BRANDS = """
CREATE TABLE IF NOT EXISTS brands (
    brand_id        INTEGER PRIMARY KEY,
    brand_name_jp   TEXT    NOT NULL,      -- Japanese name (e.g. キュレル)
    brand_name_en   TEXT,                  -- English/romanised (e.g. Curél)
    parent_company  TEXT,                  -- e.g. 'Kao', 'Shiseido', 'Kose'
    brand_group     TEXT,                  -- group key e.g. 'kao', 'shiseido', 'rohto'
    is_target       INTEGER NOT NULL DEFAULT 0  -- 1 if brand is in active lens
                    CHECK (is_target IN (0,1)),
    is_kao          INTEGER NOT NULL DEFAULT 0  -- 1 if Kao group brand (legacy)
                    CHECK (is_kao IN (0,1)),
    tier            TEXT                   -- brand's primary positioning tier
);
"""

KAO_BRANDS_SEED = [
    # (brand_name_jp, brand_name_en, parent_company, is_kao, tier)
    ("ビオレ",     "Bioré",    "Kao", 1, "skincare"),
    ("キュレル",   "Curél",    "Kao", 1, "skincare"),
    ("メリット",   "Merit",    "Kao", 1, "haircare"),
    ("アジエンス", "Asience",  "Kao", 1, "haircare"),
    ("リーゼ",     "Liese",    "Kao", 1, "haircare"),
    ("アタック",   "Attack",   "Kao", 1, "other"),
    ("マジックリン","Magiclean","Kao", 1, "other"),
    ("ソフィーナ", "Sofina",   "Kao", 1, "cosmetics"),
]


# ── products ──────────────────────────────────────────────────────────────────
# Design: Rakuten product records — current snapshot only. No time-series.
# Separate table from reviews because these are catalog-level records, not
# customer interactions. Linked to categories and brands via FK.
# snapshot_date records when the data was pulled (NB07 will always use latest).

DDL_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES sources(source_id),
    source_item_id  TEXT    NOT NULL,      -- Rakuten itemCode or equivalent
    product_name    TEXT    NOT NULL,      -- Japanese product name
    brand_id        INTEGER REFERENCES brands(brand_id),
    category_id     INTEGER REFERENCES categories(category_id),
    price_jpy       INTEGER,               -- current price in JPY
    review_count    INTEGER,               -- aggregate review count from source
    review_avg      REAL,                  -- aggregate average rating
    ranking_position INTEGER,              -- Rakuten ranking position if from ranking API
    ranking_segment TEXT,                  -- e.g. 'all', 'female_30s'
    first_review_date TEXT,                -- oldest review seen — launch velocity proxy (NB04/NB06)
    snapshot_date   TEXT    NOT NULL,      -- ISO-8601 date of data pull
    raw_json        TEXT,                  -- full source JSON for reprocessing
    UNIQUE(source_id, source_item_id)
);
"""


# ── reviewers ─────────────────────────────────────────────────────────────────
# Design: Separate reviewer table enables the reviewer behavior analysis in NB03
# (cross-category exploration, loyalty, rating trajectory). A single reviewer
# appears once here but has many rows in the reviews table.
# No PII is stored — only the platform's anonymised reviewer ID.

DDL_REVIEWERS = """
CREATE TABLE IF NOT EXISTS reviewers (
    reviewer_id         INTEGER PRIMARY KEY,
    source_id           INTEGER NOT NULL REFERENCES sources(source_id),
    source_reviewer_id  TEXT    NOT NULL,   -- platform-assigned ID (no PII)
    review_count        INTEGER DEFAULT 0,  -- updated on ingestion
    first_review_date   TEXT,               -- ISO-8601
    last_review_date    TEXT,               -- ISO-8601
    UNIQUE(source_id, source_reviewer_id)
);
"""


# ── reviews ───────────────────────────────────────────────────────────────────
# Design: The central fact table. Every review from every source lands here.
# source_id + source_review_id enforce deduplication across ingestion runs.
# review_date is normalised to YYYY-MM-DD for consistent time-series aggregation.
# review_text is raw Japanese — tokenisation happens in NB05, not here.
# verified_purchase is Amazon-specific; NULL for @cosme.

DDL_REVIEWS = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id           INTEGER PRIMARY KEY,
    source_id           INTEGER NOT NULL REFERENCES sources(source_id),
    source_review_id    TEXT    NOT NULL,   -- platform review ID
    reviewer_id         INTEGER REFERENCES reviewers(reviewer_id),
    product_id          INTEGER REFERENCES products(product_id),
    category_id         INTEGER REFERENCES categories(category_id),
    brand_id            INTEGER REFERENCES brands(brand_id),
    review_date         TEXT,               -- YYYY-MM-DD (normalised from source); NULL if date not captured
    review_year         INTEGER,            -- NULL when date unknown; filter WHERE review_year IS NOT NULL for time-series
    review_month        INTEGER,            -- NULL when date unknown
    rating              REAL,               -- numeric rating (normalised to 1–5 scale)
    rating_raw          TEXT,               -- original rating string from source
    review_title        TEXT,               -- Japanese title (if available)
    review_text         TEXT,               -- raw Japanese review body
    char_count          INTEGER,            -- len(review_text); useful for filtering stubs
    is_japanese         INTEGER DEFAULT 1   -- 1 if text passes Japanese script check
                        CHECK (is_japanese IN (0,1)),
    verified_purchase   INTEGER             -- 1=yes, 0=no, NULL=not applicable
                        CHECK (verified_purchase IN (0,1,NULL)),
    helpful_count       INTEGER DEFAULT 0,  -- upvotes / helpful votes
    ingested_at         TEXT DEFAULT (datetime('now','utc')),
    UNIQUE(source_id, source_review_id)
);
"""


# ── trends_weekly ─────────────────────────────────────────────────────────────
# Design: Stores Google Trends interest_over_time() output.
# One row per (term, week). interest is the 0–100 relative index.
# is_partial flags incomplete weeks (pytrends marks these).
# term_group allows grouping related terms for NB04/NB06 analysis.

DDL_TRENDS_WEEKLY = """
CREATE TABLE IF NOT EXISTS trends_weekly (
    trend_id    INTEGER PRIMARY KEY,
    term        TEXT    NOT NULL,           -- Japanese search term
    term_group  TEXT,                       -- e.g. 'core', 'ingredient', 'brand'
    week_start  TEXT    NOT NULL,           -- ISO-8601 date (Monday of week)
    week_year   INTEGER NOT NULL,
    week_num    INTEGER NOT NULL,           -- ISO week number
    interest    INTEGER NOT NULL            -- 0–100 relative index
                CHECK (interest BETWEEN 0 AND 100),
    is_partial  INTEGER DEFAULT 0
                CHECK (is_partial IN (0,1)),
    pulled_at   TEXT DEFAULT (datetime('now','utc')),
    UNIQUE(term, term_group, week_start)  -- Block A and B can have different values for same term
);
"""


# ── yt_videos ─────────────────────────────────────────────────────────────────
# Design: YouTube video metadata. One row per video.
# category_id links to the unified category taxonomy.
# stats_snapshot_date records when statistics were pulled — view/like/comment
# counts change over time; the snapshot captures a point-in-time value.

DDL_YT_VIDEOS = """
CREATE TABLE IF NOT EXISTS yt_videos (
    video_id            INTEGER PRIMARY KEY,
    yt_video_id         TEXT    NOT NULL UNIQUE,   -- YouTube's 11-char video ID
    channel_id          TEXT,
    channel_name        TEXT,
    title               TEXT,
    published_at        TEXT,              -- ISO-8601 UTC
    category_id         INTEGER REFERENCES categories(category_id),
    view_count          INTEGER,
    like_count          INTEGER,
    comment_count       INTEGER,
    stats_snapshot_date TEXT,              -- when statistics were fetched
    description_snippet TEXT,             -- first 200 chars of description
    search_category     TEXT              -- tier category from NB01e tiered scrape
);
"""


# ── yt_comments ───────────────────────────────────────────────────────────────
# Design: YouTube comment text with timestamps.
# Critical: use published_at (comment timestamp), NOT the parent video's
# publish date, for time-series analysis. This is the key architectural
# decision flagged in the project brief.
# is_reply distinguishes top-level comments from replies (different engagement signal).

DDL_YT_COMMENTS = """
CREATE TABLE IF NOT EXISTS yt_comments (
    comment_id          INTEGER PRIMARY KEY,
    yt_comment_id       TEXT    NOT NULL UNIQUE,
    video_id            INTEGER NOT NULL REFERENCES yt_videos(video_id),
    published_at        TEXT    NOT NULL,  -- ISO-8601 UTC — USE THIS for time-series
    comment_year        INTEGER NOT NULL,
    comment_month       INTEGER NOT NULL,
    comment_text        TEXT,
    like_count          INTEGER DEFAULT 0,
    is_reply            INTEGER DEFAULT 0
                        CHECK (is_reply IN (0,1)),
    is_japanese         INTEGER DEFAULT 1
                        CHECK (is_japanese IN (0,1)),
    ingested_at         TEXT DEFAULT (datetime('now','utc'))
);
"""


# ── Indexes ───────────────────────────────────────────────────────────────────
# Design rationale: NB03 queries heavily by (category, date) and (brand, date).
# Covering indexes on these combinations avoid full table scans on reviews,
# which will be the largest table (potentially 100K+ rows from @cosme).

DDL_INDEXES = [
    # reviews — the most queried table
    # One row per (source, source_cat_id). Without this every ingest appended a
    # fresh copy of each genre — 16 ingests left 352 rows for 22 genres, 330 of
    # them orphans. Products always referenced the first copy, so joins on
    # category_id were unaffected and nothing looked wrong; a join on
    # source_cat_id fanned out 16x.
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_source_cat "
    "ON categories(source_id, source_cat_id);",

    "CREATE INDEX IF NOT EXISTS idx_reviews_date       ON reviews(review_date);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_year_month ON reviews(review_year, review_month);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_category   ON reviews(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_brand      ON reviews(brand_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_source     ON reviews(source_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer   ON reviews(reviewer_id);",

    # trends — queried by term and date range
    "CREATE INDEX IF NOT EXISTS idx_trends_term_week   ON trends_weekly(term, week_start);",
    "CREATE INDEX IF NOT EXISTS idx_trends_week        ON trends_weekly(week_start);",

    # yt_comments — queried by date
    "CREATE INDEX IF NOT EXISTS idx_ytcomments_date    ON yt_comments(published_at);",
    "CREATE INDEX IF NOT EXISTS idx_ytcomments_year    ON yt_comments(comment_year, comment_month);",
    "CREATE INDEX IF NOT EXISTS idx_ytcomments_video   ON yt_comments(video_id);",

    # products — queried by category, brand, snapshot
    "CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_brand     ON products(brand_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_snapshot  ON products(snapshot_date);",
]


# ── Ordered DDL list (for NB02 execution in sequence) ─────────────────────────

ALL_DDL = [
    ("sources",        DDL_SOURCES),
    ("categories",     DDL_CATEGORIES),
    ("brands",         DDL_BRANDS),
    ("products",       DDL_PRODUCTS),
    ("reviewers",      DDL_REVIEWERS),
    ("reviews",        DDL_REVIEWS),
    ("trends_weekly",  DDL_TRENDS_WEEKLY),
    ("yt_videos",      DDL_YT_VIDEOS),
    ("yt_comments",    DDL_YT_COMMENTS),
]


# ── Schema creation function ───────────────────────────────────────────────────

def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes. Idempotent (IF NOT EXISTS)."""
    cur = conn.cursor()
    for name, ddl in ALL_DDL:
        cur.execute(ddl)
        log.info("Table ready: %s", name)

    for idx_ddl in DDL_INDEXES:
        cur.execute(idx_ddl)

    conn.commit()
    log.info("Schema created — %d tables, %d indexes", len(ALL_DDL), len(DDL_INDEXES))


def seed_sources(conn: sqlite3.Connection) -> None:
    """Insert the five source records. Idempotent."""
    conn.executemany(
        "INSERT OR IGNORE INTO sources(source_id, source_name, description) VALUES (?,?,?)",
        SOURCES_SEED,
    )
    conn.commit()


def seed_kao_brands(conn: sqlite3.Connection) -> None:
    """Insert Kao brand records. Idempotent."""
    conn.executemany(
        """INSERT OR IGNORE INTO brands
           (brand_name_jp, brand_name_en, parent_company, is_kao, tier)
           VALUES (?,?,?,?,?)""",
        KAO_BRANDS_SEED,
    )
    conn.commit()


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
