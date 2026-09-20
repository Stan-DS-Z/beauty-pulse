"""Regenerate the two Rakuten SKU assets NB07 produces from the products table.

    python build_sku_assets.py

  nb07_headline.csv     skin_skus / cosm_skus — the dashboard's shelf-share KPI
  nb07_sku_treemap.csv  per-category counts, reviews, rating and price

Both are written to outputs/ and dashboard/assets/, which NB07 keeps identical.

The queries are NB07 cells 6 and 13 unchanged, lifted here so the SKU assets can
be refreshed on the weekly Rakuten cadence without re-running an 8 MB notebook
that would also regenerate the wordclouds, the UMAP render and the language
panel — none of which move when a Rakuten snapshot lands. Same reason
build_sku_ratio.py exists.

Run it after ingest_rakuten_weekly.py, then build_sku_ratio.py, then check the
published prose still matches: pytest tests/test_published_figures.py.
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


def headline(conn) -> pd.DataFrame:
    """NB07 cell 6. Full ALL_TIERS counts, so the KPI matches the headline.

    The treemap drops beauty_all-categorised products, so summing it understates
    the catalogue. These counts do not.
    """
    def count(tiers: str) -> int:
        return conn.execute(f"""
            SELECT COUNT(*) FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.source_id = 1 AND {CANON} IN ({tiers})""").fetchone()[0]

    skin, cosm = count(SKIN_TIERS), count(COSM_TIERS)
    print(f"  skin_skus={skin:,}  cosm_skus={cosm:,}  "
          f"as-tagged ratio={skin / cosm:.2f}x")
    return pd.DataFrame({"metric": ["skin_skus", "cosm_skus"],
                         "value": [skin, cosm]})


def treemap(conn) -> pd.DataFrame:
    """NB07 cell 13.

    avg_rating is over RATED SKUs only — review_avg = 0 means "no reviews yet",
    not "rated zero". Price is the MEDIAN: Rakuten listings carry ¥1 junk and
    ¥300k+ outliers that distort a mean.
    """
    raw = pd.read_sql(f"""
        SELECT
            CASE WHEN {CANON} IN ({SKIN_TIERS})
                 THEN 'skincare' ELSE 'cosmetics' END AS tier_group,
            c.normalized_name AS category,
            p.review_count, p.review_avg, p.price_jpy
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.source_id = 1
          AND {CANON} IN ({ALL_TIERS})
          AND c.normalized_name != 'beauty_all'
    """, conn)

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
            .sort_values(["tier_group", "sku_count"], ascending=[True, False]))


def main() -> int:
    conn = get_connection()
    try:
        print("nb07_headline.csv")
        write_both(headline(conn), "nb07_headline.csv")
        print("\nnb07_sku_treemap.csv")
        df = treemap(conn)
        write_both(df, "nb07_sku_treemap.csv")
        print()
        print(df.to_string(index=False))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
