"""The Demand page: Google Trends search for the tracked actives, the
category words and the two umbrella terms; 化粧品 against スキンケア on one
scale; the ingredient and makeup series; and the rising related searches.

A report page: every figure is computed from the frozen edition, cut at the
edition's cut-off (sources.CUTOFF). Changes between terms run over the
report's aligned window (funnel.funnel_window, 2022→2025 on the September 2026
edition), the same window as the Brief. strings.py words these figures and
tests/test_demand.py holds the data to each direction the copy states. Like
data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from .brief import TRENDS_PULL_SPREAD
from .data import load_attention_annual, load_blockc, load_makeup_rebound, load_trends_crossover
from .funnel import CATEGORIES, funnel_window

# block_A holds the tracked actives, one word per category and the two
# umbrella terms, each in its own request and scaled to its own peak.
UMBRELLA = ("スキンケア", "化粧品")
CATEGORY_TERMS = tuple(t for _, _, t, _ in CATEGORIES.values() if t)

# v3's key figures and ingredient exhibit: niacinamide over the whole series,
# azelaic acid over the aligned window, and four ingredient lines.
LONG_ACTIVE, WINDOW_ACTIVE = "ナイアシンアミド", "アゼライン酸"
INGREDIENT_LINES = ("ナイアシンアミド", "レチノール", "ヒアルロン酸", "アゼライン酸")

# The makeup series: three terms, each against its own 2019 mean.
MAKEUP_TERMS = ("口紅", "ファンデーション", "アイシャドウ")
MAKEUP_BASE = 2019
# 厚生労働省: from 13 March 2023 mask wearing is left to the individual. The
# years before it in which masks were worn are 2020-2022.
MASK_RELAXED = "2023-03-13"
MASK_YEARS = (2020, 2021, 2022)
SMOOTH_MONTHS = 3

# The related-search exhibit: the most tiles drawn, by the file's metric.
RELATED_TILES = 20


def _cut(d: pd.DataFrame, cutoff, col="week_start") -> pd.DataFrame:
    """Monthly Trends rows dated no later than the cut-off month."""
    return d if cutoff is None else d[d[col] <= pd.Timestamp(cutoff + "-01")]


def _full_years(d: pd.DataFrame, col="week_start") -> pd.Series:
    n = d.groupby(d[col].dt.year)[col].nunique()
    return n[n >= 12].index


def compute_demand(ASSETS: Path, cutoff: str) -> dict:
    """The Demand page's figures on data up to `cutoff` ("YYYY-MM")."""
    y0, y1 = funnel_window(ASSETS, cutoff=cutoff)
    att = load_attention_annual(ASSETS, cutoff)
    terms = pd.read_csv(ASSETS / "prtimes_ingredient_terms.csv", dtype=str).fillna("")
    terms = terms[terms["trends_term"] != ""].set_index("trends_term")
    actives = tuple(terms.index)

    # ── Change by term over the aligned window
    kind = {**{t: "active" for t in actives}, **{t: "category" for t in CATEGORY_TERMS},
            **{t: "umbrella" for t in UMBRELLA}}
    change = pd.DataFrame({"kind": pd.Series(kind), "s0": att.loc[y0], "s1": att.loc[y1]})
    change = change.dropna()
    change["d"] = change["s1"] - change["s0"]
    act, words = change[change["kind"] == "active"], change[change["kind"] == "category"]
    rose = act[act["d"] >= TRENDS_PULL_SPREAD]
    within = change[change["d"].abs() < TRENDS_PULL_SPREAD]
    changes = dict(
        n_actives=len(act), n_rose=len(rose), rose_lo=float(rose["d"].min()),
        rose_hi=float(rose["d"].max()), rose=list(rose.index),
        within_actives=list(act.index[act["d"].abs() < TRENDS_PULL_SPREAD]),
        n_words=len(words), words_down=list(words.index[words["d"] <= -TRENDS_PULL_SPREAD]),
        words_up=list(words.index[words["d"] >= TRENDS_PULL_SPREAD]),
        words_within=list(words.index[words["d"].abs() < TRENDS_PULL_SPREAD]),
        within=list(within.index))

    # ── 化粧品 against スキンケア: block_B, both terms from one request
    cross = _cut(load_trends_crossover(ASSETS), cutoff)
    full = _full_years(cross)
    ann = (cross[cross["week_start"].dt.year.isin(full)]
           .groupby([cross["week_start"].dt.year, "term"])["interest"].mean().unstack())
    c0, c1 = int(full.min()), int(full.max())
    s_0, s_1 = ann.loc[c0, "スキンケア"], ann.loc[c1, "スキンケア"]
    k_0, k_1 = ann.loc[c0, "化粧品"], ann.loc[c1, "化粧品"]
    every = (cross.groupby([cross["week_start"].dt.year, "term"])["interest"].mean().unstack())
    pair = dict(
        y0=c0, y1=c1, cosm_d=100 * (k_1 / k_0 - 1), skin_d=100 * (s_1 / s_0 - 1),
        gap_d=100 * ((k_1 - s_1) / (k_0 - s_0) - 1),
        cosm_share=100 * (k_0 - k_1) / ((k_0 - s_0) - (k_1 - s_1)),
        ratio_0=s_0 / k_0, ratio_1=s_1 / k_1,
        above_every_year=bool((every["化粧品"] > every["スキンケア"]).all()),
        years=(int(every.index.min()), int(every.index.max())))

    # ── The ingredient lines: annual means, full years only
    ing = att[list(INGREDIENT_LINES)]
    a0, a1 = int(att.index.min()), int(att.index.max())
    keys = dict(long=(LONG_ACTIVE, a0, a1, att.loc[a0, LONG_ACTIVE], att.loc[a1, LONG_ACTIVE]),
                window=(WINDOW_ACTIVE, y0, y1, att.loc[y0, WINDOW_ACTIVE],
                        att.loc[y1, WINDOW_ACTIVE]))

    # ── The makeup series against each term's own 2019
    mk = _cut(load_makeup_rebound(ASSETS), cutoff)
    mk = mk[mk["term"].isin(MAKEUP_TERMS)].copy()
    base = mk[mk["year"] == MAKEUP_BASE].groupby("term")["interest"].mean()
    mk["indexed"] = 100 * mk["interest"] / mk["term"].map(base)
    mk = mk.sort_values("week_start")
    mk["smooth"] = (mk.groupby("term")["indexed"]
                    .transform(lambda s: s.rolling(SMOOTH_MONTHS, center=True, min_periods=1).mean()))
    mfull = _full_years(mk)
    rb = (mk[mk["year"].isin(mfull)].groupby(["year", "term"])["indexed"].mean().unstack())
    makeup = dict(frame=mk, annual=rb, last=int(rb.index.max()),
                  relaxed=pd.Timestamp(MASK_RELAXED))

    # ── Rising related searches: the recent window's tiles, the brand with
    # the most seed terms, and the two roots with the most in the earlier window
    bc = load_blockc(ASSETS)
    seeds = sorted({s.strip() for x in bc["seeds"].dropna() for s in str(x).split(",")})
    recent = bc[(bc["window"] == "recent") & (bc["metric"] > 0)]
    tiles = recent.nlargest(RELATED_TILES, "metric").reset_index(drop=True)
    others = recent[recent["signal_type"] != "ingredient"]
    top = others.loc[others["seed_count"].idxmax()]
    covid = bc[bc["window"] == "covid"].nlargest(2, "seed_count")
    related = dict(tiles=tiles, n_seeds=len(seeds), seeds=seeds, brand=top["root"],
                   brand_seeds=int(top["seed_count"]), brand_type=top["signal_type"],
                   runner_up=int(others.loc[others["root"] != top["root"], "seed_count"].max()),
                   covid=list(zip(covid["root"], covid["seed_count"].astype(int))))

    return dict(cutoff=cutoff, window=(y0, y1), change=change, changes=changes,
                terms=terms, pair=pair, cross=cross, ing=ing, keys=keys, makeup=makeup,
                related=related)
