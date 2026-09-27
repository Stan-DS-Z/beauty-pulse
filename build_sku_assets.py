"""Regenerate the Rakuten treemap asset from the latest weekly snapshot.

    python build_sku_assets.py

  nb07_sku_treemap.csv  per subcategory: items, reviews per item, rating, price

Written to outputs/ and dashboard/assets/.

The frame is what NB01a pulls: each genre's 3,000 most-reviewed items, one
snapshot. Only per-item measures are read from it. The number of items per
subcategory is set by how many genres are pulled and by the cap, not by what
Rakuten lists, so no count or ratio of counts is published from this frame
(METHODOLOGY Revision 11). Rakuten's own listing counts per genre are stored in
genre_totals by ingest_rakuten_weekly.py.

Until 2026-09-27 this read the products table, which holds every SKU seen in any
pull, and also wrote nb07_headline.csv, the skincare and makeup SKU counts
behind the withdrawn ratio.

Run it after ingest_rakuten_weekly.py.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.schema import get_connection          # noqa: E402

OUTPUTS = ROOT / "outputs"
ASSETS = ROOT / "dashboard" / "assets"

# NB07 cell 2 — the canonical tier expression and the in-scope tier sets.
CANON = "COALESCE(p.tier_predicted, p.tier_override, c.tier)"
SKIN_TIERS = ("'skincare','mass_skincare','sensitive_skincare',"
              "'prestige_skincare','sun_protection','dermo_skincare'")
COSM_TIERS = "'cosmetics','mass_cosmetics','prestige_cosmetics','base_makeup'"
ALL_TIERS = SKIN_TIERS + ',' + COSM_TIERS


def write_both(df: pd.DataFrame, name: str) -> None:
    for dst in (OUTPUTS / name, ASSETS / name):
        dst.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"wrote {name} -> outputs/ and dashboard/assets/")


def treemap(conn) -> pd.DataFrame:
    """Per-item measures by subcategory, from the latest weekly snapshot.

    avg_rating is over RATED SKUs only — review_avg = 0 means "no reviews yet",
    not "rated zero". Price is the MEDIAN: Rakuten listings carry ¥1 junk and
    ¥300k+ outliers that distort a mean.
    """
    (snap,) = conn.execute("SELECT MAX(snapshot_date) FROM products_weekly").fetchone()
    raw = pd.read_sql(f"""
        SELECT
            CASE WHEN {CANON} IN ({SKIN_TIERS})
                 THEN 'skincare' ELSE 'cosmetics' END AS tier_group,
            c.normalized_name AS category,
            w.review_count, w.review_avg, w.price_jpy
        FROM products_weekly w
        JOIN products p ON w.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.source_id = 1
          AND w.snapshot_date = ?
          AND {CANON} IN ({ALL_TIERS})
          AND c.normalized_name != 'beauty_all'
    """, conn, params=(snap,))

    return (raw
            .groupby(["tier_group", "category"])
            .apply(lambda g: pd.Series({
                "sku_count":   len(g),
                "avg_reviews": round(g["review_count"].fillna(0).mean(), 1),
                "avg_rating":  round(g.loc[g["review_avg"] > 0, "review_avg"].mean(), 2),
                "rated_share": round((g["review_avg"] > 0).mean(), 3),
                "med_price":   round(g["price_jpy"].median(), 0),
                "min_price":   g["price_jpy"].min(),
                "max_price":   g["price_jpy"].max(),
            }), include_groups=False)
            .reset_index()
            .astype({"sku_count": int})
            .sort_values(["tier_group", "sku_count"], ascending=[True, False])
            .assign(snapshot_date=snap[:10]))


def main() -> int:
    conn = get_connection()
    try:
        print("nb07_sku_treemap.csv")
        df = treemap(conn)
        write_both(df, "nb07_sku_treemap.csv")
        print()
        print(df.to_string(index=False))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
