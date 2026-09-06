"""Regenerate dashboard/assets/nb04b_attention_annual.csv.

The dashboard reads pre-computed CSV assets, never the database. The market
layer needs per-category *attention* alongside METI's per-category money, and
the only cross-comparable attention scale is the anchored block_B query block
(block_A terms are each normalised to their own peak and carry no cross-term
levels). block_B lives in the database, so it is exported here.

block_B is monthly. The year is derived from week_start, not read from the
trends_weekly.week_year column: that column labels January 2021, 2022 and 2023
as the *previous* year, which leaves 2020 with thirteen months and shifts every
annual mean that has a January in it. Derived from the date, all of 2019-2025
carry exactly twelve. compute_headline() already derives the year this way for
every other Trends figure; this keeps the market layer on the same arithmetic.

Full calendar years only — the current year is partial and beauty search is
seasonal, so a partial-year endpoint biases any delta.

    python build_attention_annual.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.schema import get_connection          # noqa: E402

OUT = ROOT / "dashboard" / "assets" / "nb04b_attention_annual.csv"


def main() -> int:
    con = get_connection()
    df = pd.read_sql(
        "SELECT term, week_start, interest "
        "FROM trends_weekly WHERE term_group = 'block_B'", con,
        parse_dates=["week_start"])
    con.close()
    df["year"] = df["week_start"].dt.year

    months = df.groupby("year")["week_start"].nunique()
    keep = months[months >= 12].index
    out = (df[df["year"].isin(keep)]
           .groupby(["term", "year"])
           .agg(interest=("interest", "mean"),
                n_months=("week_start", "nunique"))
           .round({"interest": 2}).reset_index()
           .sort_values(["term", "year"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"{out['term'].nunique()} terms x {out['year'].nunique()} years "
          f"({out['year'].min()}-{out['year'].max()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
