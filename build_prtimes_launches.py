"""Regenerate the launch-layer assets in dashboard/assets/.

Runs launch gate v2 (src/prtimes.gate) over data/prtimes.db and writes three
render-safe files. The store holds release titles and excerpts, which are
third-party text under PR TIMES's private-use terms; none of it is written
here. What leaves is the release's metadata and the tags computed from it.

  prtimes_launches.csv          one row per launch release (LAUNCH_COLUMNS)
  prtimes_feeds.csv             one row per active feed: panel membership
  prtimes_ingredient_terms.csv  canonical ingredient -> display labels and Trends term

The panel is fixed by WINDOW_START: a feed is core when its history is
complete or its feed reaches that month, and present-forward otherwise. The
feed-health record is the newest data/interim/prtimes_feed_health_*.json.

The ingredient table is exported because the dashboard cannot read .xlsx on
Streamlit Cloud (openpyxl is not in requirements.txt).

    python build_prtimes_launches.py
"""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src import prtimes as pt          # noqa: E402

ASSETS = ROOT / "dashboard" / "assets"
OUT_LAUNCHES = ASSETS / "prtimes_launches.csv"
OUT_FEEDS = ASSETS / "prtimes_feeds.csv"
OUT_TERMS = ASSETS / "prtimes_ingredient_terms.csv"

# The committed schema. tests/test_prtimes_export.py holds the export to it,
# so a text-bearing column cannot be added without the test failing.
LAUNCH_COLUMNS = [
    "release_id", "company_id", "issuer", "issuer_group", "role", "origin", "panel",
    "published", "month", "category", "category_group", "ingredients", "brand", "tier",
    "is_quasi_drug", "is_renewal", "is_edition", "url",
]
FEED_COLUMNS = ["company_id", "issuer_group", "panel", "feed_reach", "history_complete",
                "fetched"]
TERM_COLUMNS = ["canonical", "label_short_en", "label_ja", "trends_term"]


def _ordered(title_tags: list[str], all_tags: list[str]) -> list[str]:
    """Title tags first: the headline names the product the release is about."""
    return title_tags + [t for t in all_tags if t not in title_tags]


def main() -> int:
    health_path = sorted(pt.HEALTH_DIR.glob("prtimes_feed_health_*.json"))[-1]
    health = json.loads(health_path.read_text(encoding="utf-8"))
    h = pd.DataFrame(health["rows"])
    h = h[h["error"] != "no_feed"].copy()
    h["history_complete"] = h["history_complete"].astype(bool)
    h["panel"] = ["core" if c or str(r)[:7] <= pt.WINDOW_START else "present_forward"
                  for c, r in zip(h["history_complete"], h["feed_reach"])]

    roster = pt.load_roster(active_only=True)
    by_id = roster.set_index("company_id")
    h["issuer_group"] = h["company_id"].map(by_id["issuer_group"])
    h["fetched"] = health["run_date"]

    mt = pt.load_matchers()
    cat = pd.read_excel(pt.CONFIG / "launch_terms.xlsx", sheet_name="categories", dtype=str)
    group = dict(zip(cat["category"], cat["group"]))
    brands = pd.read_excel(pt.CONFIG / "brand_lexicon.xlsx", sheet_name="brands",
                           dtype=str).fillna("")
    brand_tier = dict(zip(brands["brand_canonical"], brands["tier"]))

    with sqlite3.connect(pt.DB_PATH) as conn:
        rel = pd.read_sql("SELECT release_id, company_id, issuer, published_date, title, "
                          "excerpt, url FROM releases", conn)
    rel = rel[rel["company_id"].isin(h["company_id"])]

    rows = []
    for r in rel.itertuples():
        g = pt.gate(r.title, r.excerpt, mt)
        if not g["is_launch"]:
            continue
        text = f"{r.title} {r.excerpt}"
        cats = _ordered(mt["category"].tags(r.title), g["categories"])
        ings = _ordered(mt["ingredient"].tags(r.title), g["ingredients"])
        brs = _ordered(mt["brand"].tags(r.title), mt["brand"].tags(text))
        feed = by_id.loc[r.company_id]
        rows.append({
            "release_id": r.release_id,
            "company_id": r.company_id,
            "issuer": r.issuer,
            "issuer_group": feed["issuer_group"],
            "role": feed["role"],
            "origin": feed["origin"],
            "panel": h.loc[h["company_id"] == r.company_id, "panel"].iat[0],
            "published": r.published_date,
            "month": r.published_date[:7],
            "category": "|".join(cats),
            "category_group": group.get(cats[0], "none") if cats else "none",
            "ingredients": "|".join(ings),
            "brand": "|".join(brs),
            "tier": brand_tier.get(brs[0], "") if brs else feed["tier"],
            "is_quasi_drug": int("医薬部外品" in pt.norm(text) or "薬用" in pt.norm(text)),
            "is_renewal": g["renewal_flag"],
            "is_edition": g["edition_flag"],
            "url": r.url,
        })
    out = (pd.DataFrame(rows, columns=LAUNCH_COLUMNS)
           .sort_values(["published", "release_id"]).reset_index(drop=True))

    terms = pd.read_excel(pt.CONFIG / "ingredients.xlsx", sheet_name="ingredients",
                          dtype=str).fillna("")[TERM_COLUMNS]

    ASSETS.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_LAUNCHES, index=False)
    h[FEED_COLUMNS].sort_values("company_id").to_csv(OUT_FEEDS, index=False)
    terms.to_csv(OUT_TERMS, index=False)

    core = out[(out["panel"] == "core") & (out["month"] >= pt.WINDOW_START)]
    print(f"health record  {health_path.name}")
    print(f"wrote {OUT_LAUNCHES.relative_to(ROOT)}  {len(out):,} launch releases "
          f"({len(core):,} core from {pt.WINDOW_START}), "
          f"{OUT_LAUNCHES.stat().st_size / 1024:.0f} KB")
    print(f"wrote {OUT_FEEDS.relative_to(ROOT)}  {len(h)} feeds "
          f"({(h['panel'] == 'core').sum()} core)")
    print(f"wrote {OUT_TERMS.relative_to(ROOT)}  {len(terms)} ingredients")
    return 0


if __name__ == "__main__":
    sys.exit(main())
