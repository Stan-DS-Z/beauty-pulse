"""
signal_pulse/src/ingest.py
──────────────────────────
Ingestion functions for each data source.
Each function takes a sqlite3 connection and raw data, cleans it,
and inserts it into the appropriate tables.

All cleaning logic lives here — NB02 calls these functions,
NB03+ query the results. No pandas in the SQL layer.
"""

import re
import json
import logging
import sqlite3
from datetime import datetime, date
from typing import Optional

from src.utils import is_japanese

log = logging.getLogger("signal_pulse.ingest")


# ── Date normalisation ────────────────────────────────────────────────────────

def normalise_date(raw: str) -> Optional[str]:
    """
    Convert any plausible date string to YYYY-MM-DD.
    Handles: ISO-8601, Japanese (2023年4月15日), Rakuten, YouTube formats.
    Returns None if unparseable.
    """
    if not raw:
        return None

    raw = str(raw).strip()

    # Already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # ISO-8601 with time: 2023-04-15T09:12:34Z
    m = re.match(r"^(\d{4}-\d{2}-\d{2})T", raw)
    if m:
        return m.group(1)

    # Japanese: 2023年4月15日
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # Rakuten: 2023-04-15 09:12:34
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2}) ", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Slash-separated: 2023/04/15
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # Japanese with time: 2026/3/28 20:35:08
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})\s", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    log.debug("Could not normalise date: %r", raw)
    return None


def extract_year_month(date_str: str) -> tuple[int, int]:
    """Extract (year, month) from a YYYY-MM-DD string."""
    parts = date_str.split("-")
    return int(parts[0]), int(parts[1])


# ── Rating normalisation ──────────────────────────────────────────────────────

def normalise_rating(raw, source: str) -> Optional[float]:
    """
    Convert source-specific rating to a 1-5 float scale.
    @cosme uses 1-7; Rakuten uses 1-5; Amazon uses 1-5; YouTube N/A.
    """
    if raw is None:
        return None
    try:
        val = float(str(raw).strip().replace("点", "").replace("/7", ""))
    except ValueError:
        return None

    if source == "cosme":
        # @cosme 1-7 → normalise to 1-5
        return round(1 + (val - 1) * (4 / 6), 2)
    else:
        # Rakuten, Amazon: already 1-5
        return round(min(max(val, 1.0), 5.0), 2)


# ── Reviewer upsert ───────────────────────────────────────────────────────────

def upsert_reviewer(conn: sqlite3.Connection, source_id: int, source_reviewer_id: str,
                    review_date: str) -> int:
    """
    Insert reviewer if new; update first/last review dates.
    Returns the internal reviewer_id.
    """
    conn.execute("""
        INSERT INTO reviewers(source_id, source_reviewer_id, review_count, first_review_date, last_review_date)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(source_id, source_reviewer_id) DO UPDATE SET
            review_count = review_count + 1,
            first_review_date = MIN(first_review_date, excluded.first_review_date),
            last_review_date  = MAX(last_review_date,  excluded.last_review_date)
    """, (source_id, source_reviewer_id, review_date, review_date))

    row = conn.execute(
        "SELECT reviewer_id FROM reviewers WHERE source_id=? AND source_reviewer_id=?",
        (source_id, source_reviewer_id),
    ).fetchone()
    return row[0]


# ── Category upsert ───────────────────────────────────────────────────────────

def upsert_category(conn: sqlite3.Connection, source_id: int, source_cat_id: str,
                    source_cat_name: str, normalized_name: str, tier: str,
                    parent_id: Optional[int] = None) -> int:
    """Insert or retrieve a category. Returns internal category_id."""
    conn.execute("""
        INSERT OR IGNORE INTO categories
            (source_id, source_cat_id, source_cat_name, normalized_name, tier, parent_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (source_id, source_cat_id, source_cat_name, normalized_name, tier, parent_id))
    row = conn.execute(
        "SELECT category_id FROM categories WHERE source_id=? AND source_cat_id=?",
        (source_id, source_cat_id),
    ).fetchone()
    return row[0]


# ══════════════════════════════════════════════════════════════════════════════
# Source-specific ingestion
# ══════════════════════════════════════════════════════════════════════════════

# ── Rakuten products ──────────────────────────────────────────────────────────

def ingest_rakuten_product(conn: sqlite3.Connection, item: dict,
                           category_id: Optional[int] = None,
                           brand_id: Optional[int] = None,
                           ranking_position: Optional[int] = None,
                           ranking_segment: Optional[str] = None,
                           snapshot_date: Optional[str] = None) -> bool:
    """
    Insert a Rakuten product record.
    snapshot_date: actual scrape date from the file (YYYY-MM-DD).
                   Falls back to today if not provided.
    source_item_id = itemCode from Rakuten API.
    """
    SOURCE_ID = 1  # rakuten
    snap = snapshot_date or str(date.today())

    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO products
                (source_id, source_item_id, product_name, brand_id, category_id,
                 price_jpy, review_count, review_avg,
                 ranking_position, ranking_segment, snapshot_date, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            SOURCE_ID,
            item.get("itemCode") or item.get("itemUrl", "")[-20:],
            item.get("itemName", "")[:400],
            brand_id, category_id,
            item.get("itemPrice"),
            item.get("reviewCount"),
            item.get("reviewAverage"),
            ranking_position, ranking_segment,
            snap,
            json.dumps(item, ensure_ascii=False)[:2000],
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False


# ── @cosme products (Layer 1 metadata) ───────────────────────────────────────

def ingest_cosme_product(conn: sqlite3.Connection, item: dict,
                         category_id: Optional[int] = None,
                         brand_id: Optional[int] = None) -> bool:
    """
    Insert a @cosme product metadata record (Layer 1 sweep).
    source_item_id = cosme product_id.
    first_review_date = launch velocity proxy.
    """
    SOURCE_ID = 2  # cosme

    product_id  = str(item.get("product_id", ""))
    if not product_id:
        return False

    product_name = item.get("product_name", "")[:400]
    review_count = item.get("review_count")
    review_avg   = item.get("review_avg")

    # Normalise aggregate rating from @cosme 1-7 scale if needed
    if review_avg is not None:
        try:
            review_avg = float(review_avg)
        except (ValueError, TypeError):
            review_avg = None

    first_review_date = normalise_date(item.get("first_review_date", ""))
    snapshot          = str(date.today())

    try:
        cursor = conn.execute("""
            INSERT INTO products
                (source_id, source_item_id, product_name, brand_id, category_id,
                 review_count, review_avg, first_review_date, snapshot_date)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id, source_item_id) DO UPDATE SET
                review_count      = excluded.review_count,
                review_avg        = excluded.review_avg,
                first_review_date = CASE
                    WHEN excluded.first_review_date IS NOT NULL
                         AND (products.first_review_date IS NULL
                              OR excluded.first_review_date < products.first_review_date)
                    THEN excluded.first_review_date
                    ELSE products.first_review_date
                END,
                snapshot_date = excluded.snapshot_date
        """, (
            SOURCE_ID, product_id, product_name,
            brand_id, category_id,
            review_count, review_avg,
            first_review_date, snapshot,
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False


# ── Amazon JP products (Layer 1 metadata) ────────────────────────────────────

def ingest_amazon_product(conn: sqlite3.Connection, item: dict,
                          category_id: Optional[int] = None,
                          brand_id: Optional[int] = None) -> bool:
    """
    Insert an Amazon JP product metadata record.
    source_item_id = ASIN.
    """
    SOURCE_ID = 3  # amazon_jp

    asin = str(item.get("source_item_id", item.get("asin", "")))
    if not asin:
        return False

    product_name      = item.get("product_name", "")[:400]
    price_jpy         = item.get("price_jpy")
    review_count      = item.get("review_count")
    review_avg        = item.get("review_avg")
    first_review_date = normalise_date(item.get("first_review_date", ""))
    snapshot          = item.get("pulled_date") or str(date.today())

    # Use category from item if not provided externally
    if category_id is None:
        # category stored as string "skincare"/"makeup" — not mapped to internal ID here
        # NB02 can pass category_id directly if needed
        pass

    try:
        cursor = conn.execute("""
            INSERT INTO products
                (source_id, source_item_id, product_name, brand_id, category_id,
                 price_jpy, review_count, review_avg,
                 first_review_date, snapshot_date)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id, source_item_id) DO UPDATE SET
                review_count      = excluded.review_count,
                review_avg        = excluded.review_avg,
                price_jpy         = excluded.price_jpy,
                first_review_date = CASE
                    WHEN excluded.first_review_date IS NOT NULL
                         AND (products.first_review_date IS NULL
                              OR excluded.first_review_date < products.first_review_date)
                    THEN excluded.first_review_date
                    ELSE products.first_review_date
                END,
                snapshot_date = excluded.snapshot_date
        """, (
            SOURCE_ID, asin, product_name,
            brand_id, category_id,
            price_jpy, review_count, review_avg,
            first_review_date, snapshot,
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False


# ── @cosme reviews ────────────────────────────────────────────────────────────

def ingest_cosme_review(conn: sqlite3.Connection, review_dict: dict,
                        category_id: Optional[int] = None,
                        brand_id: Optional[int] = None) -> bool:
    """
    Insert a single @cosme review record.
    Returns True if inserted, False if duplicate.
    """
    SOURCE_ID = 2  # cosme

    raw_date  = review_dict.get("review_date", "")
    norm_date = normalise_date(raw_date)
    # Do NOT skip reviews with missing dates — text is still valuable for NLP.
    # NULL date = excluded from temporal analysis, included in NLP corpus.
    # Query pattern: WHERE review_year IS NOT NULL for time-series (NB03/NB04)
    #                No date filter for TF-IDF/sentiment (NB05/NB06)

    year, month = extract_year_month(norm_date) if norm_date else (None, None)

    review_text = review_dict.get("review_text", "") or ""
    rating_raw  = review_dict.get("rating_raw")
    rating      = normalise_rating(rating_raw, "cosme")

    reviewer_id = None
    if rid := review_dict.get("source_reviewer_id"):
        # Use a safe fallback date for reviewer upsert when review date is unknown
        reviewer_id = upsert_reviewer(conn, SOURCE_ID, rid, norm_date or "1900-01-01")

    # Resolve internal product_id from source_item_id
    # review_dict["product_id"] is the @cosme product ID (source_item_id), not the DB PK
    product_id = None
    if src_pid := review_dict.get("product_id"):
        row = conn.execute(
            "SELECT product_id FROM products WHERE source_id=? AND source_item_id=?",
            (SOURCE_ID, str(src_pid))
        ).fetchone()
        product_id = row[0] if row else None

    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO reviews (
                source_id, source_review_id, reviewer_id, product_id,
                category_id, brand_id, review_date, review_year, review_month,
                rating, rating_raw, review_title, review_text,
                char_count, is_japanese, verified_purchase, helpful_count
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?)
        """, (
            SOURCE_ID,
            review_dict["source_review_id"],
            reviewer_id,
            product_id,
            category_id,
            brand_id,
            norm_date, year, month,
            rating, str(rating_raw) if rating_raw else None,
            review_dict.get("review_title"),
            review_text,
            len(review_text),
            1 if is_japanese(review_text) else 0,
            review_dict.get("helpful_count", 0),
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as e:
        log.debug("Duplicate review skipped: %s", e)
        return False


# ── Amazon JP reviews ─────────────────────────────────────────────────────────

def ingest_amazon_review(conn: sqlite3.Connection, review_dict: dict,
                         category_id: Optional[int] = None,
                         brand_id: Optional[int] = None) -> bool:
    """
    Insert a single Amazon JP review record.
    Handles both raw date strings and pre-parsed ISO dates.
    """
    SOURCE_ID = 3  # amazon_jp

    # Prefer pre-parsed ISO date, fall back to raw
    raw_date  = review_dict.get("review_date") or review_dict.get("review_date_raw", "")
    norm_date = normalise_date(raw_date)
    if not norm_date:
        log.warning("Amazon: skipping review — unparseable date: %r", raw_date)
        return False

    year, month = extract_year_month(norm_date)
    review_text = review_dict.get("review_text", "") or ""
    rating_raw  = review_dict.get("rating_raw")
    rating      = normalise_rating(rating_raw, "amazon_jp")

    reviewer_id = None
    if rid := review_dict.get("source_reviewer_id"):
        reviewer_id = upsert_reviewer(conn, SOURCE_ID, rid, norm_date)

    # Resolve internal product_id from ASIN (source_item_id)
    product_id = None
    if src_pid := review_dict.get("asin", review_dict.get("product_id")):
        row = conn.execute(
            "SELECT product_id FROM products WHERE source_id=? AND source_item_id=?",
            (SOURCE_ID, str(src_pid))
        ).fetchone()
        product_id = row[0] if row else None

    verified = review_dict.get("verified_purchase")
    if verified is not None:
        verified = 1 if verified else 0

    # Japanese flag: use stored value if available, else detect
    is_jp = review_dict.get("is_japanese")
    if is_jp is None:
        is_jp = is_japanese(review_text)
    is_jp = 1 if is_jp else 0

    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO reviews (
                source_id, source_review_id, reviewer_id, product_id,
                category_id, brand_id, review_date, review_year, review_month,
                rating, rating_raw, review_title, review_text,
                char_count, is_japanese, verified_purchase, helpful_count
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            SOURCE_ID,
            review_dict["source_review_id"],
            reviewer_id,
            product_id,
            category_id, brand_id,
            norm_date, year, month,
            rating, str(rating_raw) if rating_raw else None,
            review_dict.get("review_title"),
            review_text, len(review_text),
            is_jp,
            verified,
            review_dict.get("helpful_count", 0),
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False


# ── Google Trends ─────────────────────────────────────────────────────────────

def ingest_trends_dataframe(conn: sqlite3.Connection, df, term_group: str = "core") -> int:
    """
    Ingest a pytrends interest_over_time() DataFrame.
    df: pandas DataFrame with DatetimeIndex, columns = search terms, optional 'isPartial'.
    Returns count of rows inserted.
    """
    import pandas as pd
    inserted  = 0
    cols      = [c for c in df.columns if c != "isPartial"]
    partial_col = "isPartial" in df.columns

    for idx_date, row in df.iterrows():
        week_str   = str(idx_date.date())
        week_year  = idx_date.isocalendar().year
        week_num   = idx_date.isocalendar().week
        is_partial = 1 if (partial_col and row.get("isPartial", False)) else 0

        for term in cols:
            val = int(row[term])
            try:
                cursor_t = conn.execute("""
                    INSERT OR IGNORE INTO trends_weekly
                        (term, term_group, week_start, week_year, week_num, interest, is_partial)
                    VALUES (?,?,?,?,?,?,?)
                """, (term, term_group, week_str, week_year, week_num, val, is_partial))
                if cursor_t.rowcount > 0:
                    inserted += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    log.info("Trends ingested: %d rows for %d terms", inserted, len(cols))
    return inserted


# ── YouTube videos ────────────────────────────────────────────────────────────

def ingest_yt_video(conn: sqlite3.Connection, video_dict: dict,
                    category_id: Optional[int] = None) -> bool:
    """
    Insert or update a YouTube video record.
    Preserves search_category from tiered scrape (NB01e).
    Returns True if inserted or updated.
    """
    pub_date = normalise_date(video_dict.get("published_at", ""))

    cursor = conn.execute("""
        INSERT INTO yt_videos
            (yt_video_id, channel_id, channel_name, title, published_at,
             category_id, search_category, view_count, like_count, comment_count,
             stats_snapshot_date, description_snippet)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(yt_video_id) DO UPDATE SET
            view_count          = excluded.view_count,
            like_count          = excluded.like_count,
            comment_count       = excluded.comment_count,
            search_category     = COALESCE(excluded.search_category, yt_videos.search_category),
            stats_snapshot_date = excluded.stats_snapshot_date
    """, (
        video_dict["yt_video_id"],
        video_dict.get("channel_id"),
        video_dict.get("channel_name"),
        video_dict.get("title"),
        pub_date,
        category_id,
        video_dict.get("search_category", ""),
        video_dict.get("view_count"),
        video_dict.get("like_count"),
        video_dict.get("comment_count"),
        str(date.today()),
        (video_dict.get("description") or "")[:200],
    ))
    return cursor.rowcount > 0


def ingest_yt_comment(conn: sqlite3.Connection, comment_dict: dict, video_id: int) -> bool:
    """
    Insert a YouTube comment.
    CRITICAL: uses comment published_at, NOT video publish date.
    """
    pub_raw  = comment_dict.get("published_at", "")
    pub_date = normalise_date(pub_raw)
    if not pub_date:
        log.debug("YT comment: unparseable date %r", pub_raw)
        return False

    year, month = extract_year_month(pub_date)
    text = comment_dict.get("text", "") or ""

    is_jp = comment_dict.get("is_japanese")
    if is_jp is None:
        is_jp = is_japanese(text)
    is_jp = 1 if is_jp else 0

    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO yt_comments
                (yt_comment_id, video_id, published_at, comment_year, comment_month,
                 comment_text, like_count, is_reply, is_japanese)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            comment_dict["yt_comment_id"],
            video_id,
            pub_date,
            year, month,
            text,
            comment_dict.get("like_count", 0),
            1 if comment_dict.get("is_reply", False) else 0,
            is_jp,
        ))
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False


# ── Batch helpers ─────────────────────────────────────────────────────────────

def batch_ingest_cosme_reviews(conn: sqlite3.Connection, reviews: list[dict],
                                category_id: Optional[int] = None,
                                brand_id: Optional[int] = None) -> dict:
    """Ingest a list of @cosme reviews. Returns {inserted, skipped, errors}."""
    stats = {"inserted": 0, "skipped": 0, "errors": 0}
    for rev in reviews:
        try:
            ok = ingest_cosme_review(conn, rev, category_id, brand_id)
            stats["inserted" if ok else "skipped"] += 1
        except Exception as e:
            log.warning("Review ingest error: %s", e)
            stats["errors"] += 1

    conn.commit()
    log.info("@cosme batch: %s", stats)
    return stats


def batch_ingest_yt_comments(conn: sqlite3.Connection, comments: list[dict],
                              video_id: int) -> dict:
    """Ingest a list of YouTube comments for a video. Returns {inserted, skipped, errors}."""
    stats = {"inserted": 0, "skipped": 0, "errors": 0}
    for c in comments:
        try:
            ok = ingest_yt_comment(conn, c, video_id)
            stats["inserted" if ok else "skipped"] += 1
        except Exception as e:
            log.warning("YT comment ingest error: %s", e)
            stats["errors"] += 1

    conn.commit()
    log.info("YouTube comments batch: %s", stats)
    return stats
