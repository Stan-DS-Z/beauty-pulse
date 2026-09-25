"""Beauty Pulse charts: one builder per Plotly figure on the page.

A builder takes frames the frontend has already loaded, the headline and
launch dicts where it uses them, the language, the string table and the
control values, and returns a go.Figure. It reads no file. Control values
are language-neutral keys; the option lists, defaults and bounds the
controls need are the functions beside each builder. The lookups behind the
two detail panels return plain values, and each frontend formats them.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import strings
from .data import LAUNCH_GROUPS
from .strings import LAUNCH_CAT
from .theme import C, _base, _xax, _yax


# ── Tab 1 · attention ─────────────────────────────────────────────────────

def crossover_bounds(df_cross):
    """The date slider's bounds: the first and last month."""
    min_date = df_cross["week_start"].min().to_pydatetime()
    max_date = df_cross["week_start"].max().to_pydatetime()
    return min_date, max_date


def fig_trends_crossover(df_cross, date_range, lang):
    """化粧品 and スキンケア search; date_range sets the visible x range."""
    # Always plot full dataset — slider controls xaxis.range (zoom not filter)
    fig1 = go.Figure()
    fig1.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                   opacity=0.6, layer="below", line_width=0,
                   annotation_text="COVID", annotation_position="top left",
                   annotation_font=dict(size=10, color=C["muted"]))
    for term, color, label in [("スキンケア", C["skin"], "スキンケア (skincare)"),
                                 ("化粧品", C["cosm"], "化粧品 (cosmetics)")]:
        d = df_cross[df_cross["term"] == term]
        fig1.add_trace(go.Scatter(x=d["week_start"], y=d["interest"],
                                   name=label, mode="lines",
                                   line=dict(color=color, width=2.5),
                                   hovertemplate="%{y:.0f}<extra></extra>"))
    fig1.add_annotation(x="2024-01-01", y=70,
                        text="no crossover" if lang == "en" else "逆転なし",
                        showarrow=False,
                        font=dict(size=10, color=C["muted"]), bgcolor=C["card"],
                        bordercolor=C["border"], borderwidth=1, borderpad=4)
    fig1.update_layout(**_base(height=360))
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                       legend=dict(orientation="h", yanchor="top", y=-0.12,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(range=[date_range[0], date_range[1]]),
                       yaxis=_yax(title="Search interest (0–100)"))
    return fig1


def fig_makeup_rebound(df_mk, lang):
    """Three makeup terms, each indexed to its own 2019 mean."""
    # Index each term to its own 2019 mean = 100 — per-term own-baseline reads
    # are the only valid use of unanchored block_A data (no cross-term levels).
    base_2019 = df_mk[df_mk["year"] == 2019].groupby("term")["interest"].mean()
    df_mk = df_mk[df_mk["term"].isin(base_2019.index)].copy()
    df_mk["indexed"] = 100 * df_mk["interest"] / df_mk["term"].map(base_2019)
    # 3-month centred rolling mean per term for readability (monthly is noisy)
    df_mk["smooth"] = (df_mk.sort_values("week_start")
                       .groupby("term")["indexed"]
                       .transform(lambda s: s.rolling(3, center=True, min_periods=1).mean()))

    MAKEUP_META = {
        "口紅":           (C["cosm"],  "口紅 (lipstick)"),
        "ファンデーション": (C["gold"],  "ファンデーション (foundation)"),
        "アイシャドウ":     ("#7B5EA7", "アイシャドウ (eyeshadow)"),
    }
    fig1b = go.Figure()
    fig1b.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                    opacity=0.6, layer="below", line_width=0,
                    annotation_text="COVID", annotation_position="top left",
                    annotation_font=dict(size=10, color=C["muted"]))
    fig1b.add_vline(x="2023-03-13", line_dash="dash", line_color=C["muted"],
                    line_width=1.5)
    fig1b.add_annotation(x="2023-03-13", y=0.96, yref="paper",
                         text="マスク緩和<br>masks relaxed" if lang == "en" else "マスク着用ルール緩和",
                         showarrow=False, xanchor="left", xshift=4,
                         font=dict(size=9, color=C["muted"]))
    fig1b.add_hline(y=100, line_dash="dot", line_color=C["border"], line_width=1.5,
                    annotation_text="2019 baseline = 100",
                    annotation_position="bottom right",
                    annotation_font=dict(size=9, color=C["muted"]))
    for term, (color, label) in MAKEUP_META.items():
        d = df_mk[df_mk["term"] == term].sort_values("week_start")
        fig1b.add_trace(go.Scatter(
            x=d["week_start"], y=d["smooth"], name=label, mode="lines",
            line=dict(color=color, width=2.5),
            hovertemplate="%{y:.0f}<extra>" + label + "</extra>"))
    fig1b.update_layout(**_base(height=380))
    fig1b.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.12,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(),
                        yaxis=_yax(title="Search interest, own 2019 = 100"))
    return fig1b


def ingredient_options(df_ing):
    """Every ingredient term in the asset, sorted."""
    df_ing_yr = (df_ing[df_ing["year"] <= 2026]
                 .groupby(["year", "term"])["interest"].mean().reset_index())
    all_terms = sorted(df_ing_yr["term"].unique().tolist())
    return all_terms


def ingredient_default():
    """The ingredients selected on first load."""
    return ["ナイアシンアミド", "レチノール", "ヒアルロン酸", "アゼライン酸"]


def fig_ingredient_surge(df_ing, selected):
    """Annual mean search for the selected ingredient terms."""
    df_ing_yr = (df_ing[df_ing["year"] <= 2026]
                 .groupby(["year", "term"])["interest"].mean().reset_index())
    ESTABLISHED = ["ヒアルロン酸", "セラミド"]  # レチナール excluded: +11.4% post-COVID, not pre-established
    INGR_COLORS = {
        "ナイアシンアミド": "#2E7D32", "レチノール": "#1565C0",
        "グルタチオン": "#6A1B9A", "ビタミンC 美容": "#E65100",
        "トラネキサム酸": "#00695C", "アゼライン酸": "#AD1457",
        "エクソソーム": "#4E342E", "ヒアルロン酸": C["skin"],
        "セラミド": C["muted"], "レチナール": "#78909C",
    }
    fig2 = go.Figure()
    fig2.add_vrect(x0=2019.8, x1=2021.2, fillcolor=C["grid"],
                   opacity=0.6, layer="below", line_width=0)
    for term in selected:
        d = df_ing_yr[df_ing_yr["term"] == term]
        fig2.add_trace(go.Scatter(
            x=d["year"], y=d["interest"].round(1), name=term,
            mode="lines+markers",
            line=dict(color=INGR_COLORS.get(term, C["muted"]), width=2,
                      dash="dot" if term in ESTABLISHED else "solid"),
            marker=dict(size=6),
            hovertemplate="%{y:.1f}<extra></extra>"))
    fig2.update_layout(**_base(height=380))
    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=90),
                       legend=dict(orientation="h", yanchor="top", y=-0.2,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                   font=dict(size=10)),
                       xaxis=_xax(dtick=1, range=[2018.8, 2026.2]),
                       yaxis=_yax(title="Avg search interest (0–100)"))
    return fig2


CAT_LABELS = {
    "korean_cosmetics": "Korean cosmetics", "cosmetics": "Cosmetics",
    "sun_protection": "Sun protection", "face_cream": "Face cream",
    "all_in_one": "All-in-one", "face_wash": "Face wash",
    "emulsion": "Emulsion", "serum_essence": "Serum / essence",
    "toner_lotion": "Toner / lotion", "skincare": "Skincare (general)",
}


def lens_options(S):
    """The colour lens: data column -> label, in the order the radio shows them."""
    return {col: label for label, col in S["t1_lens_opts"].items()}


def fig_sku_treemap(df_sku, color_col):
    """Rakuten subcategories sized by SKU count and coloured by color_col."""
    df_sku = df_sku.copy()
    df_sku["cat_display"] = df_sku["category"].map(lambda x: CAT_LABELS.get(x, x))
    df_sku["tier_display"] = df_sku["tier_group"].str.capitalize()
    COLOR_SCALES = {"sku_count": "RdPu", "avg_reviews": "Blues",
                    "med_price": "Oranges", "avg_rating": "Greens"}
    HOVER_LABELS = {"sku_count": "SKUs", "avg_reviews": "Avg reviews/SKU",
                    "med_price": "Median price (¥)", "avg_rating": "Avg rating (rated SKUs)"}
    hover_lbl = HOVER_LABELS[color_col]
    # Build customdata array: [avg_reviews, med_price, avg_rating, tier, rated_share]
    df_sku["_cval"] = df_sku[color_col]
    CELL_LABELS = {
        "sku_count": "SKUs", "avg_reviews": "rev/SKU avg",
        "med_price": "median price", "avg_rating": "avg rating",
    }
    CELL_FMT = {
        "sku_count": lambda v: f"{v:,.0f}",
        "avg_reviews": lambda v: f"{v:.1f}",
        "med_price": lambda v: f"¥{v:,.0f}",
        "avg_rating": lambda v: f"{v:.2f} ★",
    }

    # px.treemap single level — flat, butter zoom preserved
    df_sku["_color"] = df_sku[color_col]
    treemap_path = ["cat_display"]
    fig3 = px.treemap(
        df_sku,
        path=treemap_path,
        values="sku_count",
        color=color_col,
        color_continuous_scale=COLOR_SCALES[color_col],
        custom_data=["avg_reviews", "med_price", "avg_rating", "tier_group", "rated_share"],
    )
    fig3.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,} SKUs",
        textfont=dict(size=10),
        marker_line=dict(width=2, color=C["bg"]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "SKUs: %{value:,}<br>"
            "Avg reviews/SKU: %{customdata[0]:.1f}<br>"
            "Median price: ¥%{customdata[1]:,.0f}<br>"
            "Avg rating: %{customdata[2]:.2f} / 5.0 "
            "(across the %{customdata[4]:.0%} of SKUs with ratings)"
            "<extra>%{customdata[3]}</extra>"
        ),
    )
    fig3.update_layout(**_base(height=420))
    fig3.update_layout(
        margin=dict(l=0, r=55, t=10, b=0),
        coloraxis_colorbar=dict(
            thickness=10, len=0.5,
            title=dict(text=hover_lbl, font=dict(size=9), side="right"),
            tickfont=dict(size=9),
        ),
    )
    return fig3


def sku_detail(df_sku, label):
    """The clicked tile's values, or None when the label matches no subcategory."""
    match = df_sku[df_sku["category"].map(lambda x: CAT_LABELS.get(x, x)) == label]
    if match.empty:
        return None
    row = match.iloc[0]
    return {"label": label, **{k: row[k] for k in (
        "tier_group", "sku_count", "avg_reviews", "med_price", "avg_rating",
        "rated_share")}}


def korean_callout(df_sku):
    """The Korean-cosmetics genre against all categories, or None if absent."""
    _kr = df_sku[df_sku["category"] == "korean_cosmetics"]
    if _kr.empty:
        return None
    _kr = _kr.iloc[0]
    _all_rps = (df_sku["sku_count"] * df_sku["avg_reviews"]).sum() / df_sku["sku_count"].sum()
    return {"sku_count": _kr["sku_count"], "avg_reviews": _kr["avg_reviews"],
            "med_price": _kr["med_price"], "all_rps": _all_rps}


def fig_yt_volume(df_yt_vol):
    """Comments per year, skincare against cosmetics videos."""
    df_yt_sk  = df_yt_vol[df_yt_vol["tier_group"] == "skincare"]
    df_yt_co  = df_yt_vol[df_yt_vol["tier_group"] == "cosmetics"]

    fig5 = go.Figure()
    fig5.add_vrect(x0=2019.6, x1=2021.4, fillcolor=C["grid"],
                   opacity=0.6, layer="below", line_width=0,
                   annotation_text="COVID", annotation_position="top left",
                   annotation_font=dict(size=10, color=C["muted"]))
    fig5.add_trace(go.Bar(
        x=df_yt_sk["comment_year"], y=df_yt_sk["n_comments"],
        name="Skincare", marker_color=C["skin"],
        hovertemplate="Skincare: %{y:,} comments<extra></extra>",
    ))
    fig5.add_trace(go.Bar(
        x=df_yt_co["comment_year"], y=df_yt_co["n_comments"],
        name="Cosmetics", marker_color=C["cosm"],
        hovertemplate="Cosmetics: %{y:,} comments<extra></extra>",
    ))
    fig5.update_layout(**_base(height=280))
    fig5.update_layout(
        barmode="group",
        margin=dict(l=20, r=20, t=20, b=60),
        legend=dict(orientation="h", yanchor="top", y=-0.24,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=_xax(dtick=1, tickformat="d"),
        yaxis=_yax(title="Comment count"),
    )
    return fig5


def yt_volume_counts(df_yt_vol):
    """The four comment counts the caption quotes."""
    df_yt_sk  = df_yt_vol[df_yt_vol["tier_group"] == "skincare"]
    df_yt_co  = df_yt_vol[df_yt_vol["tier_group"] == "cosmetics"]
    _yc = lambda d, y: int(d.loc[d["comment_year"] == y, "n_comments"].sum())
    return dict(c22=_yc(df_yt_co, 2022), s22=_yc(df_yt_sk, 2022),
                s24=_yc(df_yt_sk, 2024), c24=_yc(df_yt_co, 2024))


# ── Tab 1 · market ────────────────────────────────────────────────────────

def fig_meti_groups(df_grp, HEADLINE, lang):
    """Monthly shipped value, skincare and makeup, with the break marked."""
    _brk = HEADLINE["mkt_break"]
    # The rule sits between December and January so each month's point falls
    # on its own side of it.
    _brk_x = pd.Timestamp(_brk, 1, 1) - pd.Timedelta(days=15)
    _mon_hover = "%{x|%b %Y}: %{y:,.0f} 億円<extra></extra>" if lang == "en" else "%{x|%Y年%-m月}：%{y:,.0f}億円<extra></extra>"
    figM1 = go.Figure()
    figM1.add_vrect(x0=_brk_x, x1=df_grp.index.max() + pd.Timedelta(days=15),
                    fillcolor=C["grid"], opacity=0.55, layer="below", line_width=0)
    figM1.add_shape(type="line", x0=_brk_x, x1=_brk_x, y0=0, y1=1, yref="paper",
                    line=dict(dash="dash", color=C["muted"], width=1.5))
    figM1.add_annotation(x=_brk_x, y=0.97, yref="paper", xanchor="left", xshift=5,
                         text=("series break<br>Jan 2022" if lang == "en" else "断層<br>2022年1月"),
                         showarrow=False, font=dict(size=9, color=C["muted"]))
    for col, color, lab_en, lab_ja in [
            ("skincare", C["skin"], "皮膚用 (skincare)", "皮膚用化粧品"),
            ("makeup",   C["cosm"], "仕上用 (makeup)",   "仕上用化粧品")]:
        figM1.add_trace(go.Scatter(
            x=df_grp.index, y=df_grp[col], mode="lines",
            name=lab_en if lang == "en" else lab_ja,
            line=dict(color=color, width=2),
            hovertemplate=_mon_hover))
    figM1.update_layout(**_base(height=340))
    figM1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.14,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(dtick="M12", tickformat="%Y"),
                        yaxis=_yax(title="Shipped value per month (億円)" if lang == "en" else "月間出荷金額（億円）"))
    return figM1


def fig_meti_price_per_kg(px_kg_m, HEADLINE, lang):
    """Yen per kg: the three lines with the step against two comparison lines."""
    _brk = HEADLINE["mkt_break"]
    _brk_x = pd.Timestamp(_brk, 1, 1) - pd.Timedelta(days=15)
    px_kg = px_kg_m
    BROKEN = [("化粧水", C["skin"], "toner"), ("美容液", "#2E6E8E", "serum"),
              ("乳液", "#7FB2CE", "emulsion")]
    CONTROL = [("モイスチャークリーム", C["muted"], "moisture cream"),
               ("ファンデーション", C["gold"], "foundation")]
    figM2 = go.Figure()
    for item, color, gloss in BROKEN + CONTROL:
        if item not in px_kg.columns:
            continue
        row = px_kg[item].dropna()
        dashed = item not in [b[0] for b in BROKEN]
        figM2.add_trace(go.Scatter(
            x=row.index, y=row.values, mode="lines",
            name=f"{item} ({gloss})" if lang == "en" else item,
            line=dict(color=color, width=2 if dashed else 2.5,
                      dash="dot" if dashed else "solid"),
            hovertemplate=("%{x|%b %Y}: ¥%{y:,.0f}/kg<extra></extra>" if lang == "en"
                           else "%{x|%Y年%-m月}：¥%{y:,.0f}/kg<extra></extra>")))
    figM2.add_shape(type="line", x0=_brk_x, x1=_brk_x, y0=0, y1=1, yref="paper",
                    line=dict(dash="dash", color=C["cosm"], width=1.5))
    figM2.add_annotation(x=_brk_x, y=0.97, yref="paper", xanchor="left", xshift=5,
                         text=("Jan 2022" if lang == "en" else "2022年1月"),
                         showarrow=False, font=dict(size=9, color=C["cosm"]))
    figM2.update_layout(**_base(height=360))
    figM2.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.14,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(dtick="M12", tickformat="%Y"),
                        yaxis=_yax(title="¥ / kg", type="log"))
    return figM2


def fig_search_vs_value(val_all, att, HEADLINE, period, lang, S):
    """Search against shipped value by category, within one period: "pre" or "post"."""
    # Trends term -> METI product line. アイシャドウ maps to アイメークアップ, which
    # is broader than eyeshadow alone — it is the only eye-makeup line the
    # statistics carry, and the mismatch is stated rather than hidden.
    PAIRS = [("美容液", "美容液", "serum"), ("化粧水", "化粧水", "toner"),
             ("乳液", "乳液", "emulsion"), ("ファンデーション", "ファンデーション", "foundation"),
             ("口紅", "口紅", "lipstick"), ("アイシャドウ", "アイメークアップ", "eye makeup")]
    REGIMES = [(S["t1_dv_pre"], HEADLINE["mkt_y0"], HEADLINE["mkt_pre1"]),
               (S["t1_dv_post"], HEADLINE["mkt_break"], HEADLINE["mkt_y1"])]
    title, ry0, ry1 = REGIMES[("pre", "post").index(period)]
    cats, d_att, d_val = [], [], []
    for term, item, gloss in PAIRS:
        if term not in att.columns or item not in val_all.index:
            continue
        cats.append(f"{term}<br>{gloss}" if lang == "en" else term)
        d_att.append(100 * (att[term][ry1] - att[term][ry0]) / att[term][ry0])
        d_val.append(100 * (val_all.loc[item, ry1] - val_all.loc[item, ry0])
                     / val_all.loc[item, ry0])
    figD = go.Figure()
    figD.add_trace(go.Bar(x=cats, y=d_att, name=S["t1_dv_att"],
                          marker_color=C["ingr"],
                          hovertemplate="%{y:+.0f}%<extra></extra>"))
    figD.add_trace(go.Bar(x=cats, y=d_val, name=S["t1_dv_val"],
                          marker_color=C["gold"],
                          hovertemplate="%{y:+.0f}%<extra></extra>"))
    figD.add_hline(y=0, line_color=C["text"], line_width=1)
    figD.update_layout(**_base(height=330))
    figD.update_layout(barmode="group", hovermode="x",
                       title=dict(text=f"{title} · {ry0}→{ry1}",
                                  font=dict(size=13, color=C["text"]), x=0, xanchor="left"),
                       margin=dict(l=20, r=10, t=44, b=40),
                       legend=dict(orientation="h", yanchor="top", y=-0.16,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(tickfont=dict(size=10)),
                       yaxis=_yax(title="% change", range=[-80, 80]))
    return figD


# ── Tab 2 ─────────────────────────────────────────────────────────────────

def fig_cosine_sizecurve(df_curve, HEADLINE):
    """Cross-tier cosine against subsample size."""
    fig_cv = go.Figure()
    fig_cv.add_trace(go.Scatter(
        x=df_curve["sample_size"], y=df_curve["cross_tier_cosine"],
        mode="lines+markers",
        line=dict(color=C["cosm"], width=2.5),
        marker=dict(size=8, color=C["cosm"]),
        hovertemplate="N=%{x:,} reviews<br>cosine = %{y:.2f}<extra></extra>",
    ))
    fig_cv.add_hline(
        y=HEADLINE["conv_lo"], line_dash="dot", line_color=C["skin"],
        annotation_text=f"size-matched ≈ {HEADLINE['conv_lo']:.2f}",
        annotation_position="bottom left",
        annotation_font=dict(size=9, color=C["skin"]),
    )
    fig_cv.update_layout(**_base(height=380))
    fig_cv.update_layout(
        margin=dict(l=20, r=20, t=20, b=50),
        showlegend=False,
        xaxis=_xax(title=dict(text="Reviews per slice (subsample size)",
                              font=dict(size=11))),
        yaxis=_yax(title="Skincare ↔ cosmetics cosine",
                   range=[0, 0.8]),
    )
    return fig_cv


def wordcloud_years():
    """The years a word cloud is drawn for, oldest first."""
    return [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]


def wordcloud_note(year):
    """The note under a year's word cloud: its string key, and the colour keys
    of its background and left rule."""
    if year <= 2021:
        return "t2_wc_early", "cosm_lt", "cosm"
    if year == 2022:
        return "t2_wc_2022", "grid", "muted"
    if year == 2023:
        return "t2_wc_2023", "grid", "gold"
    return "t2_wc_late", "skin_lt", "skin"


# ── Tab 3 · launches ──────────────────────────────────────────────────────

# Colours passed the dataviz validator as a set (blue, rose, ochre); the
# no-category line is gray and dashed, and every line is labelled at its end.
LG_COLOR = {"skincare": "#3F86B5", "makeup": "#C4627A", "other": "#A8861A",
            "none": C["muted"]}


def fig_launch_groups(LAUNCH, S):
    """12-month rolling launch releases by category group."""
    _gname = {g: S[f"t3_lg_{g}"] for g in LAUNCH_GROUPS}
    _roll = LAUNCH["roll"]
    _x = pd.to_datetime(_roll.index + "-01")
    fig_l1 = go.Figure()
    for g in LAUNCH_GROUPS:
        fig_l1.add_trace(go.Scatter(
            x=_x, y=_roll[g], name=_gname[g], mode="lines",
            line=dict(color=LG_COLOR[g], width=2, dash="dash" if g == "none" else "solid"),
            hovertemplate="%{y:.0f}<extra>" + _gname[g] + "</extra>"))
        fig_l1.add_annotation(x=_x[-1], y=_roll[g].iloc[-1], text=_gname[g],
                              showarrow=False, xanchor="left", xshift=6,
                              font=dict(size=10, color=C["text"]))
    fig_l1.update_layout(**_base(height=360))
    fig_l1.update_layout(margin=dict(l=20, r=150, t=10, b=40), showlegend=True,
                         legend=dict(orientation="h", yanchor="top", y=-0.12,
                                     xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                         xaxis=_xax(range=[_x[0], _x[-1] + pd.Timedelta(days=20)]),
                         yaxis=_yax(title=S["t3_l1ax"], rangemode="tozero", automargin=True))
    return fig_l1


def fig_launch_categories(LAUNCH, lang, S):
    """Launch releases per category, latest 12 months against the 12 before."""
    _li = strings._li(lang)
    _c = LAUNCH["cats"].head(12).iloc[::-1]
    _cl = [LAUNCH_CAT[k][_li] for k in _c.index]
    _cc = [LG_COLOR.get(g, C["muted"]) for g in _c["group"]]
    fig_l2 = go.Figure()
    fig_l2.add_trace(go.Bar(y=_cl, x=_c["n_p12"], orientation="h", name=S["t3_lwin_p12"],
                            marker=dict(color=_cc, opacity=0.35),
                            hovertemplate="%{x}<extra>" + S["t3_lwin_p12"] + "</extra>"))
    fig_l2.add_trace(go.Bar(y=_cl, x=_c["n_l12"], orientation="h", name=S["t3_lwin_l12"],
                            marker=dict(color=_cc),
                            hovertemplate="%{x}<extra>" + S["t3_lwin_l12"] + "</extra>"))
    fig_l2.update_layout(**_base(height=420))
    # Bars take their category group's colour, so a legend swatch would show one
    # group's hue for every bar; the expl line names dark and light instead.
    fig_l2.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08,
                         hovermode="y unified", showlegend=False,
                         margin=dict(l=10, r=10, t=10, b=30),
                         xaxis=_xax(), yaxis=_yax(automargin=True))
    return fig_l2


def fig_launch_roster(LAUNCH, S):
    """Every issuer, latest 12 months, present-forward feeds stacked on the core."""
    _gname = {g: S[f"t3_lg_{g}"] for g in LAUNCH_GROUPS}
    _f = LAUNCH["full_grp"].iloc[::-1]
    fig_l3 = go.Figure()
    for pan, col, lab in [("core", "#5A6B7B", S["t3_lpan_core"]),
                          ("present_forward", "#B9C2CC", S["t3_lpan_pf"])]:
        fig_l3.add_trace(go.Bar(y=[_gname[g] for g in _f.index], x=_f[pan], name=lab,
                                orientation="h", marker=dict(color=col, line=dict(color=C["bg"], width=2)),
                                texttemplate="%{x}", textposition="inside",
                                insidetextfont=dict(size=10),
                                hovertemplate="%{x}<extra>" + lab + "</extra>"))
    fig_l3.update_layout(**_base(height=230))
    fig_l3.update_layout(barmode="stack", hovermode="y unified",
                         margin=dict(l=10, r=10, t=10, b=30),
                         legend=dict(orientation="h", yanchor="top", y=-0.15,
                                     xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                     traceorder="normal"),
                         xaxis=_xax(), yaxis=_yax(automargin=True))
    return fig_l3


def fig_launch_ingredients(LAUNCH, lang, S):
    """Share of launch releases naming each ingredient, both windows."""
    def _ing_label(canon):
        return strings._ing_label(canon, lang, LAUNCH)

    _i = LAUNCH["ing"].iloc[::-1]
    _il = [_ing_label(k) for k in _i.index]
    fig_l4 = go.Figure()
    for yv, a, b in zip(_il, _i["s_p12"], _i["s_l12"]):
        fig_l4.add_shape(type="line", x0=a, x1=b, y0=yv, y1=yv,
                         line=dict(color=C["border"], width=2), layer="below")
    fig_l4.add_trace(go.Scatter(
        x=_i["s_p12"], y=_il, mode="markers", name=S["t3_lwin_p12"],
        marker=dict(size=9, color=C["card"], line=dict(color=C["ingr"], width=2)),
        customdata=_i["n_p12"],
        hovertemplate="%{x:.1f}% (%{customdata})<extra>" + S["t3_lwin_p12"] + "</extra>"))
    fig_l4.add_trace(go.Scatter(
        x=_i["s_l12"], y=_il, mode="markers", name=S["t3_lwin_l12"],
        marker=dict(size=10, color=C["ingr"]),
        customdata=_i["n_l12"],
        hovertemplate="%{x:.1f}% (%{customdata})<extra>" + S["t3_lwin_l12"] + "</extra>"))
    fig_l4.update_layout(**_base(height=460))
    fig_l4.update_layout(hovermode="y unified", margin=dict(l=10, r=10, t=10, b=40),
                         legend=dict(orientation="h", yanchor="top", y=-0.08,
                                     xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                         xaxis=_xax(ticksuffix="%", rangemode="tozero"),
                         yaxis=_yax(automargin=True))
    return fig_l4


def launch_ingredient_options(LAUNCH):
    """Canonical keys of the ingredients that have a Trends term, in chart order."""
    _paired = LAUNCH["ing"][LAUNCH["ing"]["trends_term"] != ""]
    return list(_paired.index)


def fig_launch_vs_search(LAUNCH, df_ing, canon, S):
    """One ingredient: launch share over its search interest, one axis each."""
    _paired = LAUNCH["ing"][LAUNCH["ing"]["trends_term"] != ""]
    _canon = canon
    _sr = LAUNCH["ing_roll"].get(_canon)
    _tr = df_ing
    _tr = (_tr[_tr["term"] == _paired.loc[_canon, "trends_term"]]
           .set_index("week_start")["interest"].sort_index().rolling(12).mean().dropna())
    _x0 = pd.Timestamp(LAUNCH["roll"].index[0] + "-01")
    _tr = _tr[_tr.index >= _x0]
    fig_l5 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
    fig_l5.add_trace(go.Scatter(
        x=pd.to_datetime(_sr.index + "-01"), y=_sr, mode="lines", name=S["t3_l5ax1"],
        line=dict(color=C["ingr"], width=2),
        hovertemplate="%{y:.1f}%<extra>" + S["t3_l5ax1"] + "</extra>"), row=1, col=1)
    fig_l5.add_trace(go.Scatter(
        x=_tr.index, y=_tr, mode="lines", name=S["t3_l5ax2"],
        line=dict(color=C["text"], width=2),
        hovertemplate="%{y:.0f}<extra>" + S["t3_l5ax2"] + "</extra>"), row=2, col=1)
    fig_l5.update_layout(**_base(height=420))
    fig_l5.update_layout(showlegend=False, margin=dict(l=20, r=10, t=10, b=30))
    fig_l5.update_xaxes(**_xax())
    fig_l5.update_yaxes(**_yax(title=S["t3_l5y1"], suffix="%", rangemode="tozero",
                               automargin=True), row=1, col=1)
    fig_l5.update_yaxes(**_yax(title=S["t3_l5y2"], rangemode="tozero", automargin=True),
                        row=2, col=1)
    return fig_l5


# ── Tab 3 · search, video and reviews ────────────────────────────────────

SIG_COLORS = {
    "korean_brand": C["korean"],
    "ingredient":   C["skin"],
    "other":        C["ingr"],
}


def blockc_window_options(S):
    """The two windows: key -> label."""
    return {"recent": S["t3_win_r"], "covid": S["t3_win_c"]}


def blockc_signal_labels(S):
    """Signal type -> its label in the current language."""
    SIG_DISPLAY = {
        "korean_brand": S["t3_sig_kr"],
        "ingredient":   S["t3_sig_in"],
        "other":        S["t3_sig_ot"],
    }
    return SIG_DISPLAY


def blockc_window_frame(df_bc, window_key):
    """The top 20 rising searches in one window, strongest first."""
    df_window = df_bc[df_bc["window"] == window_key].copy()
    df_window = df_window[df_window["metric"] > 0].sort_values(
        "metric", ascending=False
    ).head(20).reset_index(drop=True)
    return df_window


def fig_blockc(df_bc, window_key, S):
    """Rising related searches, coloured by signal type."""
    df_window = blockc_window_frame(df_bc, window_key)

    # Grammar + signal display setup
    df_window["seed_label"] = df_window["seed_count"].apply(
        lambda n: f"{n} seed" if n == 1 else f"{n} seeds"
    )
    SIG_DISPLAY = blockc_signal_labels(S)
    df_window["sig_display"] = df_window["signal_type"].map(SIG_DISPLAY).fillna("Other")
    df_window["color"] = df_window["signal_type"].map(SIG_COLORS).fillna(C["ingr"])

    # px.treemap single level — flat, butter zoom, colour by signal type
    df_window["_color_val"] = df_window["signal_type"].map({
        "korean_brand": 0,
        "ingredient":   1,
        "other":        2,
    }).fillna(2)

    fig_bc = px.treemap(
        df_window,
        path=["root"],
        values="metric",
        color="signal_type",
        color_discrete_map={
            "korean_brand": C["korean"],
            "ingredient":   C["skin"],
            "other":        C["ingr"],
        },
        custom_data=["metric", "seed_count", "sig_display", "seeds", "seed_label"],
    )
    fig_bc.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[4]}",
        textfont=dict(size=11),
        marker_line=dict(width=2, color=C["bg"]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Signal strength: %{customdata[0]:.3f}<br>"
            "Found via %{customdata[4]}<br>"
            "Type: %{customdata[2]}<br>"
            "Search entry points: %{customdata[3]}"
            "<extra></extra>"
        ),
    )
    fig_bc.update_layout(**_base(height=400))
    fig_bc.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    return fig_bc


def blockc_detail(df_bc, window_key, root):
    """The clicked tile's values, or None when the root is not in the window."""
    df_window = blockc_window_frame(df_bc, window_key)
    match = df_window[df_window["root"] == root]
    if match.empty:
        return None
    row = match.iloc[0]
    return {"root": row["root"], "signal_type": row["signal_type"],
            "metric": row["metric"], "seed_count": row["seed_count"],
            "seeds": row.get("seeds", "—")}


def fig_yt_channels(df_ch):
    """The 15 YouTube beauty channels with the most views."""
    TIER_COLOURS = {
        "skincare":  C["skin"],
        "cosmetics": C["cosm"],
        "korean":    C["korean"],
        "other":     C["muted"],
    }
    # Aggregate by channel — primary tier = category with highest total_views
    df_agg = (df_ch.groupby("channel_name")
              .agg(total_views=("total_views", "sum"),
                   video_count=("video_count", "sum"),
                   total_comments=("total_comments", "sum"))
              .reset_index())
    primary = (df_ch.sort_values("total_views", ascending=False)
               .groupby("channel_name").first()[["tier_group", "search_category"]]
               .reset_index())
    df_agg = df_agg.merge(primary, on="channel_name")
    df_agg = df_agg.sort_values("total_views", ascending=True).tail(15).copy()
    df_agg["colour"]  = df_agg["tier_group"].map(TIER_COLOURS).fillna(C["muted"])
    df_agg["views_M"] = (df_agg["total_views"] / 1_000_000).round(1)

    fig_yt_ch = go.Figure()
    fig_yt_ch.add_trace(go.Bar(
        x=df_agg["total_views"],
        y=df_agg["channel_name"],
        orientation="h",
        marker_color=df_agg["colour"].tolist(),
        marker_line=dict(width=0),
        customdata=np.stack([
            df_agg["views_M"],
            df_agg["video_count"],
            df_agg["total_comments"],
            df_agg["search_category"],
        ], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "%{customdata[0]:.1f}M views · "
            "%{customdata[1]:.0f} videos · "
            "%{customdata[2]:,.0f} comments<br>"
            "Category: %{customdata[3]}"
            "<extra></extra>"
        ),
    ))
    fig_yt_ch.update_layout(**_base(height=380))
    fig_yt_ch.update_layout(
        margin=dict(l=10, r=20, t=10, b=50),
        xaxis=dict(
            title=dict(text="Total views", font=dict(size=10)),
            gridcolor=C["grid"], linecolor=C["border"],
            zerolinecolor=C["border"], tickformat=".2s",
        ),
        yaxis=dict(
            autorange=True,
            tickfont=dict(size=10),
            gridcolor="rgba(0,0,0,0)",
            linecolor="rgba(0,0,0,0)",
        ),
    )
    return fig_yt_ch


def fig_yt_tfidf(df_yt_tfidf, S):
    """Terms that separate skincare from cosmetics comments."""
    # ── Diverging view: terms that distinguish registers ───────────────
    # Raw top-15 per tier is dominated by shared generic verbs (使う, 動画).
    # The insight is what differs between skincare and cosmetics YouTube.
    # Compute TF-IDF delta: skincare score minus cosmetics score per term.
    # Positive = skews skincare · Negative = skews cosmetics.
    sk_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "skincare"].set_index("term")["tfidf"]
    co_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "cosmetics"].set_index("term")["tfidf"]
    all_terms_yt = sk_tf.index.union(co_tf.index)
    df_div = pd.DataFrame({
        "skin": sk_tf.reindex(all_terms_yt, fill_value=0),
        "cosm": co_tf.reindex(all_terms_yt, fill_value=0),
    })
    df_div["delta"] = df_div["skin"] - df_div["cosm"]
    # Exclude generic Japanese verbs that appear in all YouTube comments
    # regardless of topic — these are not register-specific signals
    YT_EXCL = {'使う', '思う', 'する', 'なる', 'いる', 'ある', 'くれる', 'もらう'}
    df_div = df_div[~df_div.index.isin(YT_EXCL)]
    # Take top 12 each direction, exclude near-zero shared terms
    skin_terms = df_div[df_div["delta"] > 0].nlargest(12, "delta")
    cosm_terms = df_div[df_div["delta"] < 0].nsmallest(12, "delta")
    df_diverge = pd.concat([
        skin_terms.assign(label="skincare"),
        cosm_terms.assign(label="cosmetics"),
    ]).sort_values("delta")

    colors = [C["skin"] if r.label == "skincare" else C["cosm"]
              for _, r in df_diverge.iterrows()]

    fig_yt_div = go.Figure()
    fig_yt_div.add_trace(go.Bar(
        x=df_diverge["delta"],
        y=df_diverge.index,
        orientation="h",
        marker_color=colors,
        marker_line=dict(width=0),
        customdata=np.stack([
            df_diverge["skin"].round(4),
            df_diverge["cosm"].round(4),
        ], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Skincare TF-IDF: %{customdata[0]:.4f}<br>"
            "Cosmetics TF-IDF: %{customdata[1]:.4f}<br>"
            "Delta: %{x:+.4f}"
            "<extra></extra>"
        ),
    ))
    fig_yt_div.add_vline(x=0, line_color=C["border"], line_width=1.5)
    fig_yt_div.update_layout(**_base(height=420))
    fig_yt_div.update_layout(
        margin=dict(l=10, r=20, t=30, b=40),
        title=dict(
            text=S["t3_ytdivtitle"],
            font=dict(size=11, color=C["muted"]), x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title=dict(text=S["t3_ytdivax"], font=dict(size=10)),
            gridcolor=C["grid"], linecolor=C["border"], zerolinecolor=C["border"],
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)",
        ),
    )
    return fig_yt_div


def umap_year_options():
    """The year pills: "all", then each year, newest first."""
    return ["all", 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019]


def umap_year_label(value, lang):
    """What a year pill shows."""
    if value == "all":
        return "全" if lang == "jp" else "All"
    return str(value)


def umap_count(df_umap, year_filter):
    """Reviews shown for a year pill."""
    n_shown = len(df_umap) if year_filter == "all" else \
              len(df_umap[df_umap.review_year == int(year_filter)])
    return n_shown


def fig_umap(df_umap, year_filter, S):
    """Reviews placed by vocabulary; year_filter is "all" or a year."""
    df_umap = df_umap.copy()
    # Topic labels mapped from NB06 Cell 13
    TOPIC_LABELS = {
        "Skin T1": "Cleansing & face wash",
        "Skin T2": "Moisturising routine",
        "Skin T3": "Makeup (miscategorised)",
        "Skin T4": "Eye makeup & liner",
        "Skin T5": "Sun protection & base",
        "Cosm T1": "Foot care (off-topic)",
        "Cosm T2": "Foundation, skincare words ★",
        "Cosm T3": "Eyebrow pencil",
        "Cosm T4": "Powder & colour",
    }
    df_umap["topic_label"] = df_umap["dominant_topic"].map(TOPIC_LABELS).fillna("Unknown")
    n_shown = umap_count(df_umap, year_filter)

    # Vocabulary centroid keywords — always visible regardless of year
    TOPIC_KEYWORDS = {
        "Cleansing & face wash":     "洗顔 · 洗い上がり · 毛穴",
        "Moisturising routine":      "香り · 乾燥 · 保湿 · 化粧水",
        "Makeup (miscategorised)":   "メイク · 描く · 発色",
        "Eye makeup & liner":        "アイライナー · ライン · コットン",
        "Sun protection & base":     "日焼け止め · トーンアップ · 下地",
        "Foot care (off-topic)":         "⚠ 靴下 · 暖かい",
        "Foundation, skincare words ★": "乾燥 · しっとり · 毛穴 · ツヤ ★",
        "Eyebrow pencil":            "細い · 眉毛 · コスパ",
        "Powder & colour":           "パウダー · 香り · 発色",
    }
    TOPIC_ANNOT_COLORS = {
        "Cleansing & face wash":     "#4A90B8",
        "Moisturising routine":      "#5B8C6E",
        "Makeup (miscategorised)":   "#78909C",
        "Eye makeup & liner":        "#C4627A",
        "Sun protection & base":     "#B8965A",
        "Foot care (off-topic)":         "#B0BEC5",
        "Foundation, skincare words ★": "#D4785C",
        "Eyebrow pencil":            "#9C4E8A",
        "Powder & colour":           "#C4627A",
    }

    # Filter by year only
    df_u = df_umap.copy()
    if year_filter != "all":
        df_u = df_u[df_u["review_year"] == int(year_filter)]

    fig_umap = go.Figure()

    # Plot Tier — skincare and cosmetics always coloured the same
    for tier, color, name in [
        ("skincare",  C["skin"], S["t3_umap_sk"]),
        ("cosmetics", C["cosm"], S["t3_umap_co"]),
    ]:
        d = df_u[df_u["tier_group"] == tier]
        if len(d) == 0:
            continue
        # Scattergl: 21k points render via WebGL — SVG Scatter is sluggish here
        fig_umap.add_trace(go.Scattergl(
            x=d["umap_x"], y=d["umap_y"],
            mode="markers", name=S["t3_umap_sk"] if tier=="skincare" else S["t3_umap_co"],
            marker=dict(color=color, size=3, opacity=0.5,
                        line=dict(width=0)),
            customdata=np.stack([
                d["review_year"].astype(int),
                d["topic_label"],
            ], axis=-1),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Year: %{customdata[0]}<br>"
                "Topic: %{customdata[1]}"
                "<extra></extra>"
            ),
        ))

    # Centroid annotations — fixed coordinates from NB06 corpus analysis
    # Positions computed from full corpus so labels stay stable across year filters
    # Standard topic centroids from corpus median positions
    for topic, kw in TOPIC_KEYWORDS.items():
        color = TOPIC_ANNOT_COLORS.get(topic, C["muted"])
        d_full = df_umap[df_umap["topic_label"] == topic]
        if len(d_full) < 10:
            continue
        cx = d_full["umap_x"].median()
        cy = d_full["umap_y"].median()
        fig_umap.add_annotation(
            x=cx, y=cy,
            text=f"<b>{kw}</b>",
            showarrow=False,
            font=dict(size=9.5, color=color, family="sans-serif"),
            bgcolor="rgba(255,255,255,0.82)",
            borderpad=3,
            bordercolor=color,
            borderwidth=1,
        )

    # ── Manual island annotations ─────────────────────────────────────
    # Top island: influencer/monitor reviews — template vocabulary
    fig_umap.add_annotation(
        x=-1.72, y=9.47,
        text="<b>⚠ インフルエンサー · モニター</b><br>giveaway reviews",
        showarrow=True, arrowhead=2, arrowcolor=C["gold"],
        ax=60, ay=30,
        font=dict(size=9, color=C["gold"], family="sans-serif"),
        bgcolor="rgba(255,255,255,0.88)",
        borderpad=4,
        bordercolor=C["gold"],
        borderwidth=1.5,
    )

    # Right satellite: tone-up SPF — cosmetic SPF sub-category
    fig_umap.add_annotation(
        x=8.60, y=2.38,
        text="<b>トーンアップ · ファンデ · 伸び</b><br>Tone-up SPF as base makeup",
        showarrow=True, arrowhead=2, arrowcolor=C["ingr"],
        ax=-70, ay=-30,
        font=dict(size=9, color=C["ingr"], family="sans-serif"),
        bgcolor="rgba(255,255,255,0.88)",
        borderpad=4,
        bordercolor=C["ingr"],
        borderwidth=1.5,
    )

    # Northeast convergence zone
    fig_umap.add_annotation(
        x=3.41, y=7.22,
        text="<b>保湿 · 洗顔 · 乾燥</b><br>★ skincare and makeup words overlap",
        showarrow=True, arrowhead=2, arrowcolor=C["skin"],
        ax=-80, ay=20,
        font=dict(size=9, color=C["skin"], family="sans-serif"),
        bgcolor="rgba(255,255,255,0.88)",
        borderpad=4,
        bordercolor=C["skin"],
        borderwidth=1.5,
    )

    suffix = f" — {year_filter}" if year_filter != "all" else " — all years"
    fig_umap.update_layout(**_base(height=520))
    fig_umap.update_layout(
        margin=dict(l=10, r=10, t=30, b=20),
        title=dict(
            text=f"UMAP embedding{suffix} · {n_shown:,} reviews",
            font=dict(size=12, color=C["muted"]),
            x=0,
        ),
        legend=dict(
            orientation="v", yanchor="top", y=1,
            xanchor="left", x=1.01,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
        xaxis=dict(showgrid=False, showticklabels=False,
                   linecolor="rgba(0,0,0,0)", zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False,
                   linecolor="rgba(0,0,0,0)", zeroline=False),
    )
    return fig_umap
