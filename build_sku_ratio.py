"""Regenerate dashboard/assets/nb07_sku_ratio.csv.

The Rakuten SKU ratio is not one number. Genre 564517 韓国コスメ carries
tier='cosmetics', but it is a country-of-origin genre, not a product-type one:
150 products drawn at random from it and labelled by hand (see
config/rakuten_564517_validation_labels.csv) are 49% skincare, 36% makeup and
15% neither. It is also the largest single block of the cosmetics denominator,
so how it is treated moves the ratio from 3.7x to 9.4x.

This writes every defensible treatment to one asset so the dashboard can report
the measured figure with its sensitivity instead of a single multiplier.

    python build_sku_ratio.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.schema import get_connection          # noqa: E402

ORIGIN_GENRE = "564517"          # 韓国コスメ — country of origin, not product type
CATCH_ALL = "100939"             # 美容・コスメ・香水 — Rakuten's catch-all
CANON = "COALESCE(p.tier_predicted, p.tier_override, c.tier)"
N_BOOT = 20000
SEED = 42


def main() -> Path:
    conn = get_connection()

    def count(tier: str, extra: str = "") -> int:
        return conn.execute(f"""
            SELECT COUNT(*) FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.source_id = 1 AND {CANON} = '{tier}' {extra}
        """).fetchone()[0]

    skin = count("skincare")
    cosm = count("cosmetics")
    origin_n = count("cosmetics", f"AND c.source_cat_id = '{ORIGIN_GENRE}'")
    cosm_ex = cosm - origin_n

    # Product-type genres only: drop the origin genre and the catch-all.
    pt_skin = count("skincare", f"AND c.source_cat_id NOT IN ('{ORIGIN_GENRE}','{CATCH_ALL}')")
    pt_cosm = count("cosmetics", f"AND c.source_cat_id NOT IN ('{ORIGIN_GENRE}','{CATCH_ALL}')")
    conn.close()

    labels = pd.read_csv(ROOT / "config" / "rakuten_564517_validation_labels.csv")
    counts = labels.hand_label.value_counts()
    n = int(counts.sum())
    p_skin = counts.get("skincare", 0) / n
    p_cosm = counts.get("cosmetics", 0) / n

    def ratio(ps: float, pc: float) -> float:
        return (skin + ps * origin_n) / (cosm_ex + pc * origin_n)

    rng = np.random.default_rng(SEED)
    probs = np.array([p_skin, p_cosm, 1 - p_skin - p_cosm])
    boot = np.array([ratio(*(rng.multinomial(n, probs) / n)[:2]) for _ in range(N_BOOT)])
    lo, hi = np.percentile(boot, [2.5, 97.5])

    rows = [
        ("as_labelled", skin, cosm, skin / cosm,
         "Rakuten genre labels as-is; 564517 counted wholly as cosmetics"),
        ("reclassified", round(skin + p_skin * origin_n), round(cosm_ex + p_cosm * origin_n),
         ratio(p_skin, p_cosm),
         f"564517 split by hand-labelled proportions (n={n})"),
        ("reclassified_lo", "", "", lo, "bootstrap 2.5% on the label sample"),
        ("reclassified_hi", "", "", hi, "bootstrap 97.5% on the label sample"),
        ("origin_genre_dropped", skin, cosm_ex, skin / cosm_ex,
         "564517 removed from both sides"),
        ("product_type_genres", pt_skin, pt_cosm, pt_skin / pt_cosm,
         "only genres whose name determines product type (8 skincare vs 1 makeup)"),
    ]
    df = pd.DataFrame(rows, columns=["basis", "skin_skus", "cosm_skus", "ratio", "note"])
    df["ratio"] = df["ratio"].astype(float).round(2)

    out = ROOT / "dashboard" / "assets" / "nb07_sku_ratio.csv"
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    main()
