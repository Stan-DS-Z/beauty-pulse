"""The Brief: the figures behind the governing thought, the five key findings
and the Brief's three exhibits.

Every figure is computed here from the shipped assets; strings.py words them.
The Brief is a report page, so it computes on data cut at its edition's cut-off
(sources.CUTOFF): no row dated after the cut-off month enters a figure, and
newer data reaches it only when a new edition moves the cut-off. Windows come
from the cut data: the category window is funnel.funnel_window's, the launch
window is compute_launch_headline's. Like data.py, nothing runs at import.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from . import seasonal
from .data import (METI_MAKE, METI_SKIN, compute_launch_headline, cut_months,
                   load_attention_annual, load_meti_annual, load_trends_monthly)
from .funnel import CATEGORIES, compute_funnel_matrix

# Repeat Google Trends pulls differ by 5–20 index points on the same month
# (recon/2026-09-27_report_trends-s1-block-a.md). A change smaller than the low
# end is inside that spread, and is counted as neither a rise nor a fall.
TRENDS_PULL_SPREAD = 5
# The top of that spread. A search term's seasonal swing (bp/seasonal.py,
# profile peak to trough in index points) must exceed it to count as a season.
SEARCH_SWING = 20

# The governing thought names the categories whose shipped value rose this
# much or more over the category window.
VALUE_RISE_NAMED = 30

def _meti_monthly_value(ASSETS: Path, cutoff) -> dict:
    """Monthly shipped value by METI line, each a series by month."""
    d = cut_months(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"), cutoff)
    d = d[(d["month"] >= 1) & (d["measure"] == "販売金額")]
    return {li: seasonal.monthly(g) for li, g in d.groupby("item")}


def _core(ASSETS: Path, cutoff) -> pd.DataFrame:
    d = pd.read_csv(ASSETS / "prtimes_launches.csv", dtype=str).fillna("")
    d = d[(d["panel"] == "core") & (d["month"] <= cutoff)].copy()
    d["year"] = d["month"].str[:4].astype(int)
    return d


def _half(month: str) -> str:
    return f"{month[:4]} H{1 if int(month[5:7]) <= 6 else 2}"


def compute_brief(ASSETS: Path, HEADLINE: dict, cutoff: str):
    """The Brief's figures on data up to `cutoff` ("YYYY-MM"), or None without
    the launch export (the Brief rests on launches as much as on shipments and
    search). From HEADLINE it takes only mkt_y0, the first METI year, and the
    @cosme-YouTube term overlap (build_vocab_overlap.py)."""
    LAUNCH = compute_launch_headline(ASSETS, cutoff)
    if LAUNCH is None:
        return None
    fm = compute_funnel_matrix(ASSETS, cutoff)
    y0, y1 = fm["window"]
    rows = fm["rows"].copy()
    val, units = load_meti_annual(ASSETS, cutoff)
    att = load_attention_annual(ASSETS, cutoff)
    base = int(HEADLINE["mkt_y0"])

    # ── Market: shipped value by side, and serum's split into units and price
    def _chg(items, a, b):
        return 100 * (val.loc[items, b].sum() / val.loc[items, a].sum() - 1)

    serum = CATEGORIES["serum"][0]
    market = dict(
        skin_d=_chg(METI_SKIN, y0, y1), make_d=_chg(METI_MAKE, y0, y1),
        make_vs_base=_chg(METI_MAKE, base, y1), base=base,
        serum_d=float(rows.loc["serum", "ship_d"]),
        serum_units=100 * (units.loc[serum, y1] / units.loc[serum, y0] - 1),
        serum_vpu=100 * ((val.loc[serum, y1] / units.loc[serum, y1])
                         / (val.loc[serum, y0] / units.loc[serum, y0]) - 1))

    # ── Table: the funnel rows plus units, value per unit, Korean issuers'
    # share and the shipment peak
    line = rows["meti_line"]
    rows["units_d"] = [100 * (units.loc[li, y1] / units.loc[li, y0] - 1) for li in line]
    rows["vpu_d"] = [100 * ((val.loc[li, y1] / units.loc[li, y1])
                            / (val.loc[li, y0] / units.loc[li, y0]) - 1) for li in line]

    core = _core(ASSETS, cutoff)
    cat1 = core[(core["year"] == y1) & (core["category"] != "")]
    tags1 = cat1["category"].str.split("|")
    rows["kr_n"] = [int(tags1.apply(lambda t, k=k: k in t).sum()) for k in rows.index]
    rows["kr_s"] = [100 * (cat1.loc[tags1.apply(lambda t, k=k: k in t), "origin"] == "KR").mean()
                    if n else np.nan for k, n in zip(rows.index, rows["kr_n"])]

    # A line's shipment peak is named only when it is stable (bp/seasonal.py).
    mv = _meti_monthly_value(ASSETS, cutoff)
    seas_meti = {li: seasonal.assess(mv[li]) for li in line.unique()}
    rows["peak"] = pd.Series([seas_meti[li]["peak"] if seas_meti[li]["stable"] else None
                              for li in line], index=rows.index, dtype=object)
    rows = rows.sort_values("value_y1", ascending=False)

    # ── Demand: the ten actives both Trends and PR TIMES track, and the
    # category words
    terms = LAUNCH["terms"]
    terms = terms[terms["trends_term"] != ""]
    ing = LAUNCH["ing"]
    n_ing = (ing["n_l12"] + ing["n_p12"]).reindex(terms["canonical"]).fillna(0).astype(int)
    den = LAUNCH["den_l12"] + LAUNCH["den_p12"]
    actives = pd.DataFrame(dict(
        canonical=terms["canonical"].values, en=terms["label_short_en"].values,
        ja=terms["label_ja"].values, term=terms["trends_term"].values,
        s0=att.loc[y0, terms["trends_term"]].values, s1=att.loc[y1, terms["trends_term"]].values,
        n=n_ing.values)).set_index("canonical")
    actives["d"] = actives["s1"] - actives["s0"]
    actives["share"] = 100 * actives["n"] / den
    top3 = actives.nlargest(3, "d")
    rose = actives[actives["d"] >= TRENDS_PULL_SPREAD]
    within = actives[actives["d"].abs() < TRENDS_PULL_SPREAD]

    cat_terms = [t for _, _, t, _ in CATEGORIES.values() if t]
    words = pd.Series({t: att.loc[y1, t] - att.loc[y0, t] for t in cat_terms})
    term_key = {t: k for k, (_, _, t, _) in CATEGORIES.items() if t}

    demand = dict(
        n_actives=len(actives), n_rose=len(rose),
        rose_lo=float(rose["d"].min()), rose_hi=float(rose["d"].max()),
        within=list(within.index), top3=list(top3.index),
        top3_lo=float(top3["d"].min()), top3_hi=float(top3["d"].max()),
        top3_n=int(top3["n"].sum()), launch_den=den,
        launch_from=LAUNCH["p12"][0], launch_to=LAUNCH["l12"][-1],
        words_up={term_key[t]: float(v) for t, v in words.sort_values(ascending=False).items()
                  if v >= TRENDS_PULL_SPREAD},
        words_within={term_key[t]: float(v) for t, v in words.sort_values(ascending=False).items()
                      if abs(v) < TRENDS_PULL_SPREAD},
        words_down=int((words <= -TRENDS_PULL_SPREAD).sum()), n_words=len(words))

    # ── Supply: launch share by category, and Korean issuers by half-year,
    # complete halves inside the launch window
    ld = rows["launch_d"].dropna()
    gainers = ld.nlargest(2)
    months = [m for m in LAUNCH["months"]]
    halves = pd.Series(months).map(_half)
    complete = halves.value_counts()
    complete = sorted(h for h, n in complete.items() if n == 6)
    h_first, h_last = complete[0], complete[-1]
    inwin = core[core["month"].isin(months)].assign(h=lambda x: x["month"].map(_half))
    def _kr(h):
        g = inwin[inwin["h"] == h]
        return int((g["origin"] == "KR").sum()), len(g)
    kr0, kr1 = _kr(h_first), _kr(h_last)
    supply = dict(
        gainers=list(gainers.index), gain_lo=float(gainers.min()), gain_hi=float(gainers.max()),
        loser=ld.idxmin(), loss=float(ld.min()),
        h_first=h_first, h_last=h_last,
        kr_first=kr0, kr_last=kr1)

    # ── Governing thought and the portfolio exhibit
    risers = rows[rows["ship_d"] >= VALUE_RISE_NAMED].sort_values("ship_d", ascending=False)
    fell_share = risers[risers["launch_d"] < 0]
    portfolio = dict(
        gainers=supply["gainers"],
        gain_ship_lo=float(rows.loc[supply["gainers"], "ship_d"].min()),
        gain_ship_hi=float(rows.loc[supply["gainers"], "ship_d"].max()),
        risers=list(risers.index),
        fell=list(fell_share.index),
        fell_ship_lo=float(fell_share["ship_d"].min()) if len(fell_share) else np.nan,
        fell_ship_hi=float(fell_share["ship_d"].max()) if len(fell_share) else np.nan,
        den=fm["launch_den"])

    # ── Timing: sunscreen's shipment and search peak runs, each full year, and
    # how many lines ship most in the same month every year
    sun_line, _, sun_term, _ = CATEGORIES["sunscreen"]
    tm = load_trends_monthly(ASSETS, cutoff)
    sun_search = seasonal.monthly(tm[tm["term"] == sun_term], "interest")
    ship_runs, search_runs = seasonal.year_runs(mv[sun_line]), seasonal.year_runs(sun_search)
    timing = dict(ship=ship_runs, search=search_runs,
                  offset={y: search_runs[y][0] - ship_runs[y][0] for y in seasonal.FULL_YEARS},
                  n_stable=int(sum(a["stable"] for a in seas_meti.values())),
                  n_lines=len(seas_meti))

    # The few headline figures the Brief's copy uses, kept with its own
    # figures so the copy never reads a headline built on other files.
    H = {k: HEADLINE[k] for k in ("mkt_y0", "vocab_top", "vocab_shared")}
    return dict(cutoff=cutoff, H=H, window=(y0, y1), market=market, demand=demand, supply=supply,
                portfolio=portfolio, timing=timing, rows=rows, actives=actives,
                n_rows=len(rows), n_core=LAUNCH["n_core"])
