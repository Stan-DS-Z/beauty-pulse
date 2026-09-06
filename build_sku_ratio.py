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


LABELLED = {                      # genre -> hand-label file, both tagged cosmetics
    "564517": "rakuten_564517_validation_labels.csv",   # 韓国コスメ, origin genre
    "204233": "rakuten_204233_validation_labels.csv",   # ベースメイク・メイクアップ
}


def _proportions(name: str) -> tuple[np.ndarray, int]:
    """(p_skincare, p_cosmetics, p_other) and n, from a hand-label file."""
    lab = pd.read_csv(ROOT / "config" / name).hand_label
    n = len(lab)
    return np.array([(lab == k).sum() / n for k in
                     ("skincare", "cosmetics", "other")]), n


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
    sizes = {g: count("cosmetics", f"AND c.source_cat_id = '{g}'") for g in LABELLED}
    origin_n = sizes["564517"]
    # cosmetics not covered by any hand-labelled genre
    cosm_rest = cosm - sum(sizes.values())

    pt_skin = count("skincare", f"AND c.source_cat_id NOT IN ('{ORIGIN_GENRE}','{CATCH_ALL}')")
    pt_cosm = count("cosmetics", f"AND c.source_cat_id NOT IN ('{ORIGIN_GENRE}','{CATCH_ALL}')")
    conn.close()

    props = {g: _proportions(f) for g, f in LABELLED.items()}

    def ratio(pmap: dict) -> float:
        """Ratio with each labelled genre split by its proportions; 'other' drops out."""
        s = skin + sum(pmap[g][0] * sizes[g] for g in pmap)
        c = cosm_rest + sum(pmap[g][1] * sizes[g] for g in pmap)
        return s / c

    point_all = ratio({g: props[g][0] for g in props})
    # 564517 alone, so the contribution of each correction stays visible
    only_origin = ((skin + props["564517"][0][0] * origin_n)
                   / (cosm - origin_n + props["564517"][0][1] * origin_n))

    rng = np.random.default_rng(SEED)
    boot = np.array([
        ratio({g: rng.multinomial(props[g][1], props[g][0]) / props[g][1] for g in props})
        for _ in range(N_BOOT)
    ])
    lo, hi = np.percentile(boot, [2.5, 97.5])

    n_lab = {g: props[g][1] for g in props}
    rows = [
        ("as_labelled", skin, cosm, skin / cosm,
         "Rakuten genre labels as-is; both genres counted wholly as cosmetics"),
        ("reclassified_564517_only", "", "", only_origin,
         f"only the origin genre split (n={n_lab['564517']})"),
        ("reclassified", round(skin + sum(props[g][0][0] * sizes[g] for g in props)),
         round(cosm_rest + sum(props[g][0][1] * sizes[g] for g in props)), point_all,
         f"both labelled genres split by hand proportions "
         f"(n={n_lab['564517']}+{n_lab['204233']})"),
        ("reclassified_lo", "", "", lo, "bootstrap 2.5%, resampling both label sets"),
        ("reclassified_hi", "", "", hi, "bootstrap 97.5%, resampling both label sets"),
        ("origin_genre_dropped", skin, cosm - origin_n, skin / (cosm - origin_n),
         "564517 removed from both sides, nothing else changed"),
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
