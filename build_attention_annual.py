"""Regenerate dashboard/assets/nb04b_attention_annual.csv and
nb04b_attention_monthly.csv.

The dashboard reads pre-computed CSV assets, never the database. The market
layer sets each category's search against METI's money for the same category,
and every use is a term's change against its own earlier years, never one term's
level against another's. That is block_A: one Google Trends request per term,
one window, so each series has one scale. block_A lives in the database, so it
is exported here. (Until 2026-09-27 this read block_B, which was three anchored
payloads on three different scales; block_B now holds only the スキンケア/化粧品
pair from one request.)

block_A is monthly. The year is derived from week_start, not read from the
trends_weekly.week_year column: that column labels January 2021, 2022 and 2023
as the *previous* year, which leaves 2020 with thirteen months and shifts every
annual mean that has a January in it. Derived from the date, all of 2019-2025
carry exactly twelve. compute_headline() already derives the year this way for
every other Trends figure; this keeps the market layer on the same arithmetic.

Full calendar years only — the current year is partial and beauty search is
seasonal, so a partial-year endpoint biases any delta. The monthly file carries
the same full years, month by month.

trends_monthly.csv carries every month of the pull, the partial year included:
the seasonal ratio (bp/seasonal.py) divides each month by a centred 12-month
average, which for January 2026 needs the months to July 2026. Report pages cut
it at the edition's cut-off.

    python build_attention_annual.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.schema import get_connection          # noqa: E402

OUT = ROOT / "dashboard" / "assets" / "nb04b_attention_annual.csv"
OUT_M = ROOT / "dashboard" / "assets" / "nb04b_attention_monthly.csv"
OUT_ALL = ROOT / "dashboard" / "assets" / "trends_monthly.csv"


def main() -> int:
    con = get_connection()
    df = pd.read_sql(
        "SELECT term, week_start, interest "
        "FROM trends_weekly WHERE term_group = 'block_A'", con,
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
    monthly = (df[df["year"].isin(keep)]
               .assign(month=df["week_start"].dt.month)
               .groupby(["term", "year", "month"])["interest"].mean()
               .round(2).reset_index())
    monthly.to_csv(OUT_M, index=False)
    (df.assign(month=df["week_start"].dt.month)
       .groupby(["term", "year", "month"])["interest"].mean().round(2).reset_index()
       .to_csv(OUT_ALL, index=False))
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"{out['term'].nunique()} terms x {out['year'].nunique()} years "
          f"({out['year'].min()}-{out['year'].max()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
