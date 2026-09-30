"""The Market page: METI shipments by product line and by group, the January
2022 break, and HS 3304 imports by origin.

A report page, so every figure is computed on data cut at the edition's
cut-off (sources.CUTOFF) from the frozen edition's files. Changes by product
line run from METI_BREAK to the last full year, inside one regime; the one
comparison with an earlier year is makeup's, whose lines have no break.
strings.py words these figures and tests/test_market.py holds the data to each
direction the copy states. Like data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from . import seasonal
from .data import (METI_BREAK, METI_MAKE, METI_SKIN, METI_SUN, cut_months,
                   load_meti_annual, load_meti_monthly)

LINES = METI_SKIN + METI_MAKE + METI_SUN

# How many lines the product-line title names, largest shipped value first.
LEAD_LINES = 2
# The bridge title names the largest value rises that came on fewer units
# (value per unit carried them), and the largest that came mostly from units.
FEWER_UNITS_NAMED, UNITS_NAMED = 2, 3
# How many origins the import exhibit draws, largest in the last year first.
IMPORT_ORIGINS = 4

# The skincare lines with the January 2022 step, the lines set against them
# January on January, and the makeup lines whose yen per kg also falls in 2022
# through kilograms rising (data.METI_BREAK).
BREAK_LINES = ["化粧水", "美容液", "乳液"]
BREAK_CONTROLS = ["モイスチャークリーム", "ファンデーション"]
BREAK_KG_LINES = ["口紅", "アイメークアップ"]
# The pre-break range of yen per kg starts at the first year the 時系列表 holds.
PRE_BREAK_FROM = 2015


def _chg(a, b):
    return 100 * (b / a - 1)


def _yen_per_kg(ASSETS: Path, cutoff) -> pd.DataFrame:
    """Yen per kg by line and year. Years with monthly rows sum them, as
    load_meti_annual does; the years before them (2015-2018) have only the
    時系列表's annual rows. The newest year may be part of a year."""
    d = cut_months(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"), cutoff)
    monthly = d[d["month"] >= 1]
    annual = d[(d["month"] == 0) & ~d["year"].isin(monthly["year"].unique())]
    both = pd.concat([monthly, annual])
    g = both.groupby(["item", "year", "measure"])["value"].sum().unstack()
    return (g["販売金額"] * 1000 / g["販売数量"]).unstack()


def _peak_months(series: pd.Series) -> dict:
    """The highest-ratio month of each full year of the seasonal window
    (bp/seasonal.py): {month: [years]}, in the order the months first peak."""
    out = {}
    for y, m in seasonal.year_peaks(series).items():
        out.setdefault(m, []).append(y)
    return out


def compute_market(ASSETS: Path, cutoff: str) -> dict:
    """The Market page's figures on data up to `cutoff` ("YYYY-MM")."""
    val, units = load_meti_annual(ASSETS, cutoff)
    y0, y1, base = METI_BREAK, int(val.columns.max()), int(val.columns.min())
    group = {**{li: "skincare" for li in METI_SKIN}, **{li: "makeup" for li in METI_MAKE},
             **{li: "sunscreen" for li in METI_SUN}}

    # ── Product lines, 2022 -> the last full year
    rows = pd.DataFrame({
        "group": [group[li] for li in LINES],
        "value_y1": val.loc[LINES, y1].values,
        "value_d": _chg(val.loc[LINES, y0], val.loc[LINES, y1]).values,
        "units_d": _chg(units.loc[LINES, y0], units.loc[LINES, y1]).values,
        "vpu_d": _chg(val.loc[LINES, y0] / units.loc[LINES, y0],
                      val.loc[LINES, y1] / units.loc[LINES, y1]).values,
        "base_d": _chg(val.loc[LINES, base], val.loc[LINES, y1]).values,
    }, index=LINES).sort_values("value_y1", ascending=False)
    lead = list(rows.index[:LEAD_LINES])
    rose = rows[rows["value_d"] > 0]
    fewer_units = list(rose[rose["units_d"] < 0].nlargest(FEWER_UNITS_NAMED, "value_d").index)
    by_units = list(rose[(rose["units_d"] > rose["vpu_d"]) & (rose["units_d"] > 0)]
                    .nlargest(UNITS_NAMED, "value_d").index)

    # ── Key figures: the whole year, each side, and the newest months
    items = [i for i in val.index if not str(i).endswith("計") and i != "化粧品合計"]
    total = val.loc[items].sum()
    skin, make = val.loc[METI_SKIN].sum(), val.loc[METI_MAKE].sum()
    keys = dict(total_y1=total[y1], n_items=len(items),
                skin_share=100 * skin[y1] / total[y1], make_share=100 * make[y1] / total[y1],
                skin_y0=skin[y0], skin_y1=skin[y1], skin_d=_chg(skin[y0], skin[y1]),
                make_y1=make[y1], make_d=_chg(make[y0], make[y1]),
                make_vs_base=_chg(make[base], make[y1]))

    # The months after the last full year, against the same months a year
    # earlier. A part-year is never set against a full one.
    raw = cut_months(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"), cutoff)
    raw = raw[(raw["month"] >= 1) & (raw["measure"] == "販売金額")]
    ytd_y = int(raw["year"].max())
    ytd = None
    if ytd_y > y1:
        ytd_m = int(raw.loc[raw["year"] == ytd_y, "month"].max())
        v = raw[raw["month"] <= ytd_m].groupby(["item", "year"])["value"].sum().unstack()
        ytd = dict(year=ytd_y, month=ytd_m,
                   skin=_chg(v.loc[METI_SKIN, ytd_y - 1].sum(), v.loc[METI_SKIN, ytd_y].sum()),
                   make=_chg(v.loc[METI_MAKE, ytd_y - 1].sum(), v.loc[METI_MAKE, ytd_y].sum()),
                   total=_chg(v.loc[items, ytd_y - 1].sum(), v.loc[items, ytd_y].sum()))

    # ── Groups by month, and each group's peak month in each full year of the
    # seasonal window
    monthly, _ = load_meti_monthly(ASSETS, cutoff)
    peaks = {g: _peak_months(monthly[g]) for g in ("skincare", "makeup")}
    last = monthly.index.max()

    # ── The January 2022 break
    jan = raw[raw["month"] == 1].groupby(["item", "year"])["value"].sum().unstack() / 1e5
    brk_jan = {li: (jan.loc[li, y0 - 1], jan.loc[li, y0], _chg(jan.loc[li, y0 - 1], jan.loc[li, y0]))
               for li in BREAK_LINES + BREAK_CONTROLS}
    kg = (cut_months(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"), cutoff)
          .query("month >= 1 and measure == '販売数量'")
          .groupby(["item", "year"])["value"].sum().unstack())
    ypk = _yen_per_kg(ASSETS, cutoff)
    # (kilograms, shipped value, yen per kg), change 2021 -> 2022
    brk_kg = {li: (_chg(kg.loc[li, y0 - 1], kg.loc[li, y0]),
                   _chg(val.loc[li, y0 - 1], val.loc[li, y0]),
                   _chg(ypk.loc[li, y0 - 1], ypk.loc[li, y0])) for li in BREAK_KG_LINES}
    pre = [y for y in ypk.columns if PRE_BREAK_FROM <= y < y0]
    post = [y for y in ypk.columns if y >= y0]
    brk_range = {}
    for li in BREAK_LINES:
        lo, hi = ypk.loc[li, pre].min(), ypk.loc[li, pre].max()
        brk_range[li] = dict(lo=lo, hi=hi,
                             inside=[y for y in post if lo <= ypk.loc[li, y] <= hi],
                             above=[y for y in post if ypk.loc[li, y] > hi])
    brk = dict(jan=brk_jan, kg=brk_kg, range=brk_range, pre=(min(pre), max(pre)),
               drop={li: _chg(ypk.loc[li, y0 - 1], ypk.loc[li, y0]) for li in BREAK_LINES})

    # ── HS 3304 imports by origin, whole years inside the cut
    tr = pd.read_csv(ASSETS / "estat_trade_hs3304.csv").assign(month=0)
    tr = cut_months(tr, cutoff)
    imp = (tr[tr["flow"] == "import"].groupby(["country", "year"])["value_1000jpy"].sum()
           .unstack() / 1e5)
    i0, i1 = int(imp.columns.min()), int(imp.columns.max())
    top = imp[i1].sort_values(ascending=False)
    origins = list(top.index[:IMPORT_ORIGINS])
    leader = origins[0]
    leads = imp.idxmax() == leader
    since = i1
    while since - 1 >= i0 and leads[since - 1]:
        since -= 1
    imports = dict(frame=imp.loc[origins], y0=i0, y1=i1, leader=leader, runner=origins[1],
                   since=since, lead_y1=top.iloc[0], runner_y1=top.iloc[1])

    return dict(cutoff=cutoff, window=(y0, y1), base=base, rows=rows, lead=lead,
                fewer_units=fewer_units, by_units=by_units, keys=keys, ytd=ytd,
                monthly=monthly, last_month=(last.year, last.month), peaks=peaks,
                brk=brk, imports=imports)
