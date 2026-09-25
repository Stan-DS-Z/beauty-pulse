"""Beauty Pulse numbers: asset loaders and the headline computations.

Shared by both app frontends. Imports no UI framework and computes
nothing at import: every function that reads a file takes the assets
directory, so a frontend can point it at its own copy. Caching is the
frontend's job."""

from pathlib import Path

import pandas as pd

# The shipped assets. A default for scripts and tests; the frontends pass
# their own.
ASSETS = Path(__file__).parent.parent / "assets"

# ── Market layer: METI 生産動態統計 product lines ──────────────────────────
# The 計 subtotal rows exist only for 2019-2020; from the 2021 table onward
# e-Stat ships the 33 component lines and drops the five subtotals. Aggregates
# are therefore summed from components. This partition reproduces both subtotal
# years exactly (皮膚用 8,875.9 / 仕上用 3,729.8 億円 in 2019) and matches JCIA's
# published 2024 shares to the decimal — 皮膚用 44.5%, 仕上用 20.9%. Two traps:
# リップクリーム is 仕上用, not skincare, and ひげそり用・浴用化粧品 is 特殊用途.
# Derivation: recon/2026-09-06_gate-findings_meti-grouping-and-2022-break.md
METI_SKIN = ["化粧水", "美容液", "乳液", "モイスチャークリーム",
             "マッサージ・コールドクリーム", "クレンジングクリーム",
             "洗顔クリーム・フォーム", "パック", "男性皮膚用化粧品",
             "その他の皮膚用化粧品"]
METI_MAKE = ["ファンデーション", "おしろい", "口紅", "ほほ紅", "アイメークアップ",
             "まゆ墨・まつ毛化粧料", "つめ化粧料(除光液を含む)", "リップクリーム",
             "その他の仕上用化粧品"]

# The series breaks at January 2022. Yen per kg for 化粧水, 美容液 and 乳液
# falls 21-35% from 2021 to 2022, after seven years inside a range (2015-2021);
# 化粧水 and 美容液 stay below that range through July 2026; 乳液 was back in it
# in 2024 and below it in 2025. 口紅 and アイメークアップ yen per kg also fall
# in 2022, but through kilograms rising, with shipped value continuing to rise.
# Compare January with January: January is the low month in most years,
# so a December-to-January fall shows up in the control lines too. It is not the misreporting correction JCIA footnotes — those
# restate other lines, and the step survives on the restated vintage. Cause
# unattributed. Nothing is measured across this boundary: every skincare money
# figure on this dashboard is computed inside one regime, because the same
# figures reverse sign when measured across it (美容液 value 2019->2025 -38%,
# 2022->2025 +23%).
METI_BREAK = 2022


def _full_years(d):
    """Drop years whose monthly rows stop short of December.

    The newest months arrive from the 確報 workbook before their year is
    complete; summed as a year they would read as a collapse."""
    months = d[d["month"] >= 1].groupby("year")["month"].nunique()
    return d[d["year"].isin(months[months == 12].index)]


def compute_headline(ASSETS: Path):
    """Headline metrics — single source of truth, computed live from dashboard assets.

    The Google Trends comparison uses the anchored block_B (cross-comparable
    scale); convergence is the size-matched cosine."""
    # Rakuten SKU counts — full in-scope (ALL_TIERS) from NB07's headline export.
    # The treemap CSV excludes beauty_all-categorised products, so summing it
    # undercounts the catalogue and lands on a different ratio; fall back to it
    # only if the headline export is missing. No figures quoted here on purpose
    # — both move with every weekly snapshot.
    _hl_path = ASSETS / "nb07_headline.csv"
    if _hl_path.exists():
        _hl = pd.read_csv(_hl_path).set_index("metric")["value"]
        skin_skus, cosm_skus = int(_hl["skin_skus"]), int(_hl["cosm_skus"])
    else:
        df_sku = pd.read_csv(ASSETS / "nb07_sku_treemap.csv")
        skin_skus = int(df_sku[df_sku["tier_group"] == "skincare"]["sku_count"].sum())
        cosm_skus = int(df_sku[df_sku["tier_group"] == "cosmetics"]["sku_count"].sum())
    sku_ratio = round(skin_skus / max(cosm_skus, 1), 1)

    # The SKU ratio is not one number. Genre 564517 韓国コスメ carries
    # tier='cosmetics' but is a country-of-origin genre: 150 of its products
    # labelled by hand are 49% skincare, 36% makeup, 15% neither. It is also
    # 62% of the cosmetics denominator. The one real makeup genre is 24%
    # out of scope as well, so both sides are hand-measured now.
    # build_sku_ratio.py writes every treatment; we report the
    # reclassified figure with its bootstrap CI and keep the span for the
    # caveat. Older assets predate the file — fall back to the raw ratio.
    _sr_path = ASSETS / "nb07_sku_ratio.csv"
    if _sr_path.exists():
        _sr = pd.read_csv(_sr_path).set_index("basis")["ratio"]
        sku_measured = round(float(_sr["reclassified"]), 1)
        sku_lo = round(float(_sr["reclassified_lo"]), 1)
        sku_hi = round(float(_sr["reclassified_hi"]), 1)
        sku_span_lo = round(float(_sr["as_labelled"]), 1)
        sku_span_hi = round(float(_sr["product_type_genres"]), 1)
    else:
        sku_measured = sku_lo = sku_hi = sku_ratio
        sku_span_lo = sku_span_hi = sku_ratio

    # Google Trends — anchored block_B (the only cross-term-comparable block)
    df_tr = pd.read_csv(ASSETS / "nb07_trends_crossover.csv", parse_dates=["week_start"])
    df_tr["year"] = df_tr["week_start"].dt.year
    # Compare full calendar years only — the latest year is partial (Jan–Mar),
    # and cosmetics search is seasonal (December gifting), so a partial-year
    # endpoint biases the decline estimate.
    months_per_year = df_tr.groupby("year")["week_start"].nunique()
    full_years = months_per_year[months_per_year >= 12].index
    annual = df_tr.groupby(["year", "term"])["interest"].mean().unstack(fill_value=0)
    annual = annual.loc[annual.index.isin(full_years)]
    y0, y1 = annual.index.min(), annual.index.max()
    cosm_decline = int(round(100 * (annual.loc[y1, "化粧品"] - annual.loc[y0, "化粧品"])
                             / annual.loc[y0, "化粧品"]))
    ratio_0 = round(annual.loc[y0, "スキンケア"] / annual.loc[y0, "化粧品"], 2)
    ratio_1 = round(annual.loc[y1, "スキンケア"] / annual.loc[y1, "化粧品"], 2)

    # Vocabulary convergence — size-matched cosine
    df_sv = pd.read_csv(ASSETS / "nb06_cosine_salvage.csv")
    sm = df_sv[df_sv["method"] == "size_matched"]["cosine"].tolist()
    v1 = df_sv[df_sv["method"] == "v1_full_data"]["cosine"].tolist()
    # 3 decimals, and every derived figure computed from the raw values. At 2
    # decimals the size-matched delta sits on a rounding boundary (0.0650) and
    # flips 0.06/0.07 between runs on a 0.001 move in one endpoint; the share
    # then compounds it (0.07/0.31 = 23% vs the raw 0.065/0.307 = 21%, which is
    # what NB06 reports). Keep NB06 and the dashboard on the same arithmetic.
    conv_lo, conv_hi = round(sm[0], 3), round(sm[1], 3)
    conv_delta = round(sm[1] - sm[0], 3)
    conv_v1 = round(v1[1] - v1[0], 3)
    v1_lo, v1_hi = round(v1[0], 2), round(v1[1], 2)
    # Period labels come from the CSV, not from prose. NB06 re-runs as the corpus
    # grows and the late window moves with it; the size-curve copy said 2023-25
    # while the data said 2023-26, dropping the largest year in the corpus.
    _sm = df_sv[df_sv["method"] == "size_matched"]
    conv_p0, conv_p1 = str(_sm["period"].iloc[0]), str(_sm["period"].iloc[1])
    _mn = df_sv[df_sv["method"] == "matched_n"]["cosine"]
    matched_n = int(_mn.iloc[0]) if len(_mn) else 249
    # Bootstrap CI on the delta, exported by NB06 §2. Older assets predate the
    # row, so fall back to the qualitative phrasing rather than inventing bounds.
    _dl = df_sv[df_sv["method"] == "size_matched_delta"]
    if len(_dl):
        conv_ci = f"95% CI [+{float(_dl['ci_lo'].iloc[0]):.3f}, +{float(_dl['ci_hi'].iloc[0]):.3f}]"
        conv_ci_jp = f"95%CI [+{float(_dl['ci_lo'].iloc[0]):.3f}, +{float(_dl['ci_hi'].iloc[0]):.3f}]"
    else:
        conv_ci, conv_ci_jp = "95% CI excludes zero", "95%CIはゼロを除外"
    conv_share = round(100 * (sm[1] - sm[0]) / (v1[1] - v1[0])) if v1[1] != v1[0] else 0

    # Sample-size effect — identical data, cosine vs N
    df_cv = pd.read_csv(ASSETS / "nb06_cosine_sizecurve.csv")
    size_lo, size_hi = df_cv.iloc[0], df_cv.iloc[-1]

    # Ingredient search — same full-calendar-year anchors as cosm_decline above,
    # so both headline figures rest on one window instead of two. A <=2020
    # baseline would fold in the first COVID year and is not a pre-COVID read.
    # Reported as levels, not a multiplier: niacinamide's baseline is ~5 on a
    # 0-100 index, and a ratio off a base that small swings from 7x to 16x with
    # the window while its level movement is stable.
    df_ing = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
    df_ing["year"] = df_ing["week_start"].dt.year
    _ipy = df_ing.groupby("year")["week_start"].nunique()
    _ifull = _ipy[_ipy >= 12].index
    ing_y0, ing_y1 = int(_ifull.min()), int(_ifull.max())

    def _levels(term):
        t = df_ing[df_ing["term"] == term]
        return (int(round(t[t.year == ing_y0]["interest"].mean())),
                int(round(t[t.year == ing_y1]["interest"].mean())))

    nia_pre, nia_post = _levels("ナイアシンアミド")
    ret_pre, ret_post = _levels("レチノール")

    # ── Market layer — METI shipments and 財務省 trade ────────────────────
    # Money, not attention. Kept in its own block and labelled as a different
    # measurement everywhere it is shown.
    _meti = _full_years(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"))
    _mv = (_meti[(_meti["month"] >= 1) & (_meti["measure"] == "販売金額")]
           .groupby(["item", "year"])["value"].sum().unstack() / 1e5)   # 千円 → 億円
    _mu = (_meti[(_meti["month"] >= 1) & (_meti["measure"] == "販売個数")]
           .groupby(["item", "year"])["value"].sum().unstack())         # 十個
    mkt_y0, mkt_y1 = int(_mv.columns.min()), int(_mv.columns.max())
    _skin, _make = _mv.loc[METI_SKIN].sum(), _mv.loc[METI_MAKE].sum()
    _pre1 = METI_BREAK - 1

    def _pct(s_, a, b):
        return int(round(100 * (s_[b] - s_[a]) / s_[a]))

    # The ratio, reported inside each regime rather than across the break.
    # Endpoint-to-endpoint it reads 2.38 -> 2.13, a narrowing; the path is
    # 2.38 -> 3.22 (widening) then a one-year step down then flat. The step is
    # the break, so the narrowing is not published as a finding.
    mkt_ratio_pre0 = round(_skin[mkt_y0] / _make[mkt_y0], 2)
    mkt_ratio_pre1 = round(_skin[_pre1] / _make[_pre1], 2)
    mkt_ratio_post0 = round(_skin[METI_BREAK] / _make[METI_BREAK], 2)
    mkt_ratio_post1 = round(_skin[mkt_y1] / _make[mkt_y1], 2)

    # Makeup is the clean half: its collapse is 2019->2021, entirely before the
    # break, in lines the break does not touch. Both the full window and the
    # pre-break window are honest here; the full window is what the KPI shows.
    found_d = _pct(_mv.loc["ファンデーション"], mkt_y0, mkt_y1)
    lip_d = _pct(_mv.loc["口紅"], mkt_y0, mkt_y1)
    found_d_pre = _pct(_mv.loc["ファンデーション"], mkt_y0, _pre1)
    lip_d_pre = _pct(_mv.loc["口紅"], mkt_y0, _pre1)
    found_d_post = _pct(_mv.loc["ファンデーション"], METI_BREAK, mkt_y1)
    lip_d_post = _pct(_mv.loc["口紅"], METI_BREAK, mkt_y1)

    # Serum: the case where measuring across the break reverses the sign.
    _sv, _su = _mv.loc["美容液"], _mu.loc["美容液"]
    serum_val_span = _pct(_sv, mkt_y0, mkt_y1)
    serum_val_post = _pct(_sv, METI_BREAK, mkt_y1)
    _ppu = _sv / _su
    serum_ppu_span = _pct(_ppu, mkt_y0, mkt_y1)
    serum_ppu_post = _pct(_ppu, METI_BREAK, mkt_y1)

    _all_items = [i for i in _mv.index if not str(i).endswith("計") and i != "化粧品合計"]
    mkt_total = _mv.loc[_all_items].sum()
    mkt_total_y1 = int(round(mkt_total[mkt_y1]))
    skin_share_y1 = round(100 * _skin[mkt_y1] / mkt_total[mkt_y1], 1)
    make_share_y1 = round(100 * _make[mkt_y1] / mkt_total[mkt_y1], 1)

    # Attention on the same categories, anchored block_B (cross-comparable).
    _att = (pd.read_csv(ASSETS / "nb04b_attention_annual.csv")
            .pivot(index="year", columns="term", values="interest"))
    serum_att_span = _pct(_att["美容液"], mkt_y0, mkt_y1)

    # 財務省 貿易統計 HS 3304 — imports never absorb the domestic fall.
    _tr = pd.read_csv(ASSETS / "estat_trade_hs3304.csv")
    _flow = (_tr.groupby(["flow", "year"])["value_1000jpy"].sum() / 1e5)
    imp_y0, imp_y1 = int(round(_flow["import"][mkt_y0])), int(round(_flow["import"][mkt_y1]))
    imp_share_y1 = round(100 * _flow["import"][mkt_y1] / mkt_total[mkt_y1], 1)
    _imp = _flow["import"].loc[mkt_y0:mkt_y1]
    imp_peak_y, imp_peak = int(_imp.idxmax()), int(round(_imp.max()))

    # The newest months, from the 確報 workbook, compared on the same months of
    # the year before. A part-year is never set against a full one.
    _raw = pd.read_csv(ASSETS / "estat_meti_cosmetics.csv")
    _raw = _raw[(_raw["month"] >= 1) & (_raw["measure"] == "販売金額")]
    ytd_y = int(_raw["year"].max())
    ytd_m = int(_raw.loc[_raw["year"] == ytd_y, "month"].max())
    _ytd = (_raw[_raw["month"] <= ytd_m].groupby(["item", "year"])["value"].sum().unstack())

    def _ytd_pct(items):
        a, b = _ytd.loc[items, ytd_y - 1].sum(), _ytd.loc[items, ytd_y].sum()
        return round(100 * (b - a) / a, 1)

    ytd_skin, ytd_make, ytd_total = (_ytd_pct(METI_SKIN), _ytd_pct(METI_MAKE),
                                     _ytd_pct(_all_items))


    return {
        "sku_ratio":     sku_ratio,
        "sku_measured":  sku_measured,
        "sku_lo":        sku_lo,
        "sku_hi":        sku_hi,
        "sku_span_lo":   sku_span_lo,
        "sku_span_hi":   sku_span_hi,
        "skin_skus":    skin_skus,
        "cosm_skus":    cosm_skus,
        "cosm_decline": cosm_decline,
        "ratio_0":      ratio_0,
        "ratio_1":      ratio_1,
        "conv_lo":      conv_lo,
        "conv_hi":      conv_hi,
        "conv_delta":   conv_delta,
        "conv_v1":      conv_v1,
        "v1_lo":        v1_lo,
        "v1_hi":        v1_hi,
        "matched_n":    matched_n,
        "conv_p0":      conv_p0,
        "conv_p1":      conv_p1,
        "conv_ci":      conv_ci,
        "conv_ci_jp":   conv_ci_jp,
        "conv_share":   conv_share,
        "size_lo_n":    int(size_lo["sample_size"]),
        "size_lo_cos":  round(size_lo["cross_tier_cosine"], 2),
        "size_hi_n":    int(size_hi["sample_size"]),
        "size_hi_cos":  round(size_hi["cross_tier_cosine"], 2),
        "nia_pre":      nia_pre,
        "nia_post":     nia_post,
        "ret_pre":      ret_pre,
        "ret_post":     ret_post,
        "ing_y0":       ing_y0,
        "ing_y1":       ing_y1,
        # market layer
        "mkt_y0":         mkt_y0,
        "mkt_y1":         mkt_y1,
        "mkt_break":      METI_BREAK,
        "mkt_pre1":       _pre1,
        "mkt_ratio_pre0": mkt_ratio_pre0,
        "mkt_ratio_pre1": mkt_ratio_pre1,
        "mkt_ratio_post0": mkt_ratio_post0,
        "mkt_ratio_post1": mkt_ratio_post1,
        "found_d":        found_d,
        "lip_d":          lip_d,
        "found_d_pre":    found_d_pre,
        "lip_d_pre":      lip_d_pre,
        "found_d_post":   found_d_post,
        "lip_d_post":     lip_d_post,
        "serum_att_span": serum_att_span,
        "serum_val_span": serum_val_span,
        "serum_val_post": serum_val_post,
        "serum_ppu_span": serum_ppu_span,
        "serum_ppu_post": serum_ppu_post,
        "mkt_total_y1":   mkt_total_y1,
        "skin_share_y1":  skin_share_y1,
        "make_share_y1":  make_share_y1,
        "imp_y0":         imp_y0,
        "imp_y1":         imp_y1,
        "imp_share_y1":   imp_share_y1,
        "imp_peak_y":     imp_peak_y,
        "imp_peak":       imp_peak,
        "ytd_y":          ytd_y,
        "ytd_m":          ytd_m,
        "ytd_skin":       ytd_skin,
        "ytd_make":       ytd_make,
        "ytd_total":      ytd_total,
    }


# ── Launch layer — PR TIMES product-launch releases ──────────────────────
# Written by build_prtimes_launches.py; one row per release that gate v2
# calls a launch. The core panel is the feeds whose PR TIMES history reaches
# LAUNCH_WINDOW_START (src/prtimes.WINDOW_START; the app does not import src/).
# Every historical figure uses the core only, so an issuer whose feed starts
# later never puts a step in the series. Launch timing is seasonal, so changes
# are read as 12-month totals against the 12 months before, never month on month.
LAUNCH_WINDOW_START = "2021-09"
LAUNCH_GROUPS = ["skincare", "makeup", "other", "none"]
# Measured on hand labels, not computable from the export: the gate on a
# 100-release holdout weighted to the store, and PR TIMES coverage of the brand
# list by tier. recon/2026-09-19_prtimes-gate-score_v2-holdout.md.
LAUNCH_GATE = dict(asof="2026-09-19", n_holdout=100, n_store=6554,
                   precision=0.89, p_lo=0.76, p_hi=0.98,
                   recall=0.81, r_lo=0.68, r_hi=0.92,
                   prestige_unseen=11, prestige_n=26, other_unseen=28, other_n=92,
                   edition_found=7, edition_n=13)


def compute_launch_headline(ASSETS: Path):
    """Launch-layer figures, or None when the export is absent."""
    path = ASSETS / "prtimes_launches.csv"
    if not path.exists():
        return None
    d = pd.read_csv(path, dtype=str).fillna("")
    feeds = pd.read_csv(ASSETS / "prtimes_feeds.csv", dtype=str).fillna("")
    terms = pd.read_csv(ASSETS / "prtimes_ingredient_terms.csv", dtype=str).fillna("")

    # The fetch month is partial; the last complete month is the one before it.
    last = pd.Period(feeds["fetched"].max()[:7], freq="M") - 1
    months = pd.period_range(LAUNCH_WINDOW_START, last, freq="M").astype(str)
    l12, p12 = list(months[-12:]), list(months[-24:-12])
    core = d[(d["panel"] == "core") & d["month"].isin(months)]

    monthly = (core.groupby(["month", "category_group"]).size().unstack(fill_value=0)
               .reindex(index=months, columns=LAUNCH_GROUPS, fill_value=0))
    grp_l12, grp_p12 = monthly.loc[l12].sum(), monthly.loc[p12].sum()

    prim = core.assign(cat=core["category"].str.split("|").str[0])
    prim = prim[prim["cat"] != ""]
    cats = pd.DataFrame({"n_l12": prim[prim["month"].isin(l12)]["cat"].value_counts(),
                         "n_p12": prim[prim["month"].isin(p12)]["cat"].value_counts()}
                        ).fillna(0).astype(int)
    cats["group"] = prim.drop_duplicates("cat").set_index("cat")["category_group"]

    # Ingredient share: editions (the title names a re-release, refill or
    # limited packaging of an existing formula) are left out of both sides,
    # because an unchanged formula carries no new ingredient decision.
    ne = core[core["is_edition"] == "0"]
    den = ne.groupby("month").size().reindex(months, fill_value=0)
    ex = ne.assign(ing=ne["ingredients"].str.split("|")).explode("ing")
    ex = ex[ex["ing"] != ""]
    num = (ex.groupby(["month", "ing"]).size().unstack(fill_value=0)
           .reindex(index=months, fill_value=0))
    den_l12, den_p12 = int(den[l12].sum()), int(den[p12].sum())
    ing = pd.DataFrame({"n_l12": num.loc[l12].sum(), "n_p12": num.loc[p12].sum()})
    ing["s_l12"] = 100 * ing["n_l12"] / den_l12
    ing["s_p12"] = 100 * ing["n_p12"] / den_p12
    ing = ing.join(terms.set_index("canonical")).sort_values(["s_l12", "n_p12"],
                                                              ascending=False)
    ing_share_roll = (num.rolling(12).sum().div(den.rolling(12).sum(), axis=0) * 100).dropna()
    any_ing_l12 = int((ne["month"].isin(l12) & (ne["ingredients"] != "")).sum())

    # Full roster, latest 12 months: every feed whose history covers all 12.
    first_day = f"{l12[0]}-01"
    elig = feeds[(feeds["history_complete"] == "True") | (feeds["feed_reach"] <= first_day)]
    full = d[d["company_id"].isin(elig["company_id"]) & d["month"].isin(l12)]
    full_grp = (full.groupby(["category_group", "panel"]).size().unstack(fill_value=0)
                .reindex(index=LAUNCH_GROUPS, columns=["core", "present_forward"], fill_value=0))

    core_feeds = feeds[feeds["panel"] == "core"]
    top = ing.iloc[0]
    return {
        "months": list(months), "l12": l12, "p12": p12, "last": str(last),
        "monthly": monthly, "roll": monthly.rolling(12).sum().dropna(),
        "grp_l12": grp_l12, "grp_p12": grp_p12,
        "tot_l12": int(grp_l12.sum()), "tot_p12": int(grp_p12.sum()),
        "cats": cats.sort_values("n_l12", ascending=False),
        "ing": ing[(ing["n_l12"] + ing["n_p12"]) > 0], "ing_roll": ing_share_roll,
        "den_l12": den_l12, "den_p12": den_p12,
        "any_ing_share": round(100 * any_ing_l12 / den_l12, 1),
        "top_ing": top.name, "top_n_l12": int(top["n_l12"]), "top_n_p12": int(top["n_p12"]),
        "top_s_l12": round(float(top["s_l12"]), 1), "top_s_p12": round(float(top["s_p12"]), 1),
        "full_grp": full_grp, "full_tot": int(full_grp.values.sum()),
        "full_pf": int(full_grp["present_forward"].sum()),
        "n_core": core_feeds["issuer_group"].nunique(),
        "n_all": elig["issuer_group"].nunique(),
        "n_pf_feeds": int((elig["panel"] == "present_forward").sum()),
        "n_core_feeds": len(core_feeds), "n_all_feeds": len(elig),
        "terms": terms,
    }


def load_trends_crossover(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_trends_crossover.csv", parse_dates=["week_start"])

def load_ingredient_surge(ASSETS: Path):
    df = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    return df

def load_sku_treemap(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_sku_treemap.csv")

def load_makeup_rebound(ASSETS: Path):
    df = pd.read_csv(ASSETS / "nb07_makeup_rebound.csv", parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    return df

def load_review_slope(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_review_slope.csv")

def load_blockc(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_blockc.csv")

def load_umap(ASSETS: Path):
    return pd.read_csv(ASSETS / "umap_embedding.csv")

def load_tfidf_delta(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_tfidf_delta.csv")

def load_cosine_sizecurve(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb06_cosine_sizecurve.csv")

def load_yt_volume(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_yt_volume.csv")

def load_yt_channels(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_yt_channels.csv")

def load_meti_annual(ASSETS: Path):
    """METI shipments, annual, by product line. 販売金額 in 億円, 販売個数 in 十個.

    Annual figures are summed from the monthly rows (month >= 1) rather than
    read from the month == 0 annual rows: the annual rows are a 時系列表 restated
    in a later table, so mixing the two would put two vintages in one series."""
    d = _full_years(pd.read_csv(ASSETS / "estat_meti_cosmetics.csv"))
    d = d[d["month"] >= 1]
    val = d[d["measure"] == "販売金額"].groupby(["item", "year"])["value"].sum().unstack() / 1e5
    units = d[d["measure"] == "販売個数"].groupby(["item", "year"])["value"].sum().unstack()
    return val, units


def load_meti_monthly(ASSETS: Path):
    """Monthly shipped value by group (億円) and yen per kg by product line.

    Monthly rows exist from January 2019; the annual loaders above reach back to
    2015 through the 時系列表 rows, which carry no month."""
    d = pd.read_csv(ASSETS / "estat_meti_cosmetics.csv")
    d = d[d["month"] >= 1].assign(date=lambda x: pd.to_datetime(
        dict(year=x["year"], month=x["month"], day=1)))
    wide = lambda m: d[d["measure"] == m].pivot_table(index="date", columns="item",
                                                      values="value", aggfunc="sum")
    val, kg = wide("販売金額"), wide("販売数量")
    items = [i for i in val.columns if not str(i).endswith("計") and i != "化粧品合計"]
    groups = pd.DataFrame({
        "skincare": val[METI_SKIN].sum(axis=1) / 1e5,
        "makeup":   val[METI_MAKE].sum(axis=1) / 1e5,
        "total":    val[items].sum(axis=1) / 1e5,
    })
    return groups, val * 1000 / kg


def load_attention_annual(ASSETS: Path):
    return (pd.read_csv(ASSETS / "nb04b_attention_annual.csv")
            .pivot(index="year", columns="term", values="interest"))


def load_yt_tfidf(ASSETS: Path):
    return pd.read_csv(ASSETS / "nb07_yt_tfidf.csv")
