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
    """Rakuten subcategories, coloured by color_col.

    Tiles are sized by the items each subcategory has in the pull: each genre's
    3,000 most-reviewed items. That size is set by the pull, not by Rakuten's
    listings, so no tile shows it as a count of what Rakuten sells."""
    df_sku = df_sku.copy()
    df_sku["cat_display"] = df_sku["category"].map(lambda x: CAT_LABELS.get(x, x))
    df_sku["tier_display"] = df_sku["tier_group"].str.capitalize()
    COLOR_SCALES = {"med_price": "Oranges", "avg_rating": "Greens"}
    HOVER_LABELS = {"med_price": "Median price (¥)", "avg_rating": "Avg rating (rated SKUs)"}
    hover_lbl = HOVER_LABELS[color_col]
    # customdata: [med_price, avg_rating, tier, rated_share]
    df_sku["_cval"] = df_sku[color_col]
    CELL_LABELS = {"med_price": "median price", "avg_rating": "avg rating"}
    CELL_FMT = {
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
        custom_data=["med_price", "avg_rating", "tier_group", "rated_share"],
    )
    fig3.update_traces(
        texttemplate="<b>%{label}</b>",
        textfont=dict(size=10),
        marker_line=dict(width=2, color=C["bg"]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Items in pull: %{value:,}<br>"
            "Median price: ¥%{customdata[0]:,.0f}<br>"
            "Avg rating: %{customdata[1]:.2f} / 5.0 "
            "(across the %{customdata[3]:.0%} of SKUs with ratings)"
            "<extra>%{customdata[2]}</extra>"
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
        "tier_group", "sku_count", "med_price", "avg_rating", "rated_share")}}


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


# ── Brief ───────────────────────────────────────────────────────────────────
# Colour: the skincare/makeup pair is the only categorical set; anything else
# is grey, and the one accent on an exhibit whose title is not about skincare
# against makeup is ink.
_GREY = "#A9A59E"
GROUP_COLOUR = {"skincare": C["skin"], "makeup": C["cosm"], "sunscreen": _GREY}
# Label placement for the portfolio's bubbles, so no two labels overlap on the
# September 2026 figures; an unlisted category takes "top center".
_PORTFOLIO_TEXT = {"serum": "bottom center", "emulsion": "middle left", "mask": "top right",
                   "foundation": "bottom center", "blush": "middle right"}


def fig_brief_portfolio(BRIEF, S):
    """Each category's launch-share change against its shipped-value change."""
    rows = BRIEF["rows"]
    y0, y1 = BRIEF["window"]
    ix = S["b_catix"]
    hover = (f"<b>%{{text}}</b> %{{customdata[0]}}<br>Shipped value {y0}→{y1}: %{{x:+.0f}}% "
             f"(¥%{{customdata[1]:,}}億 in {y1})<br>Launch share %{{customdata[4]}}% → "
             "%{customdata[5]}% (%{customdata[2]} → %{customdata[3]} releases)<extra></extra>"
             if ix == 0 else
             f"<b>%{{text}}</b><br>出荷金額 {y0}→{y1}年：%{{x:+.0f}}%（{y1}年 %{{customdata[1]:,}}"
             "億円）<br>リリース構成比 %{customdata[4]}% → %{customdata[5]}%（%{customdata[2]}件 → "
             "%{customdata[3]}件）<extra></extra>")
    fig = go.Figure()
    for group in ("skincare", "sunscreen", "makeup"):
        g = rows[rows["group"] == group]
        fig.add_trace(go.Scatter(
            x=g["ship_d"], y=g["launch_d"], mode="markers+text", name=S["b_p_groups"][group],
            text=[LAUNCH_CAT[k][ix] for k in g.index],
            textposition=[_PORTFOLIO_TEXT.get(k, "top center") for k in g.index],
            textfont=dict(size=11, color=C["ink"]),
            marker=dict(size=1.1 * np.sqrt(g["value_y1"]), color=GROUP_COLOUR[group],
                        opacity=0.75, line=dict(color="#fff", width=2)),
            customdata=np.stack([[LAUNCH_CAT[k][1] for k in g.index], g["value_y1"].round(),
                                 g["launch_n0"], g["launch_n1"], g["launch_s0"].round(1),
                                 g["launch_s1"].round(1)], axis=-1),
            hovertemplate=hover))
    for text, x, y, xa, ya in zip(S["b_p_q"], (0.99, 0.99, 0.01, 0.01), (0.98, 0.02, 0.98, 0.02),
                                  ("right", "right", "left", "left"),
                                  ("top", "bottom", "top", "bottom")):
        fig.add_annotation(text=text, x=x, y=y, xref="paper", yref="paper", xanchor=xa,
                           yanchor=ya, showarrow=False, font=dict(size=11, color=C["muted"]))
    fig.add_hline(y=0, line_width=1, line_color=C["border"])
    fig.add_vline(x=0, line_width=1, line_color=C["border"])
    fig.update_layout(**{**_base(520), "hovermode": "closest"}, showlegend=True,
                      legend=dict(orientation="h", y=1.06, x=0),
                      margin=dict(l=10, r=10, t=40, b=40),
                      xaxis=_xax(title=dict(text=S["b_p_x"], font=dict(size=11)),
                                 ticksuffix="%", zeroline=False),
                      yaxis=_yax(S["b_p_y"], zeroline=False))
    return fig


def fig_brief_actives(BRIEF, S):
    """Each tracked active's search change against its share of launch releases."""
    A = BRIEF["actives"]
    y0, y1 = BRIEF["window"]
    den = BRIEF["demand"]["launch_den"]
    named = set(BRIEF["demand"]["top3"])
    hover = (f"<b>%{{customdata[0]}}</b><br>Search %{{customdata[1]}} → %{{customdata[2]}} "
             f"({y0}→{y1})<br>%{{customdata[3]}} of {den:,} launch releases<extra></extra>"
             if S["b_namecol"] == "en" else
             f"<b>%{{customdata[0]}}</b><br>検索 %{{customdata[1]}} → %{{customdata[2]}}"
             f"（{y0}→{y1}年）<br>新商品リリース{den:,}件中%{{customdata[3]}}件<extra></extra>")
    colours = [C["ink"] if k in named else _GREY for k in A.index]
    fig = go.Figure(go.Scatter(
        x=A["d"], y=A["share"], mode="markers+text",
        text=[f"{name} ({n})" if S["b_namecol"] == "en" else f"{name}（{n}）"
              for name, n in zip(A[S["b_namecol"]], A["n"])],
        textposition="top center",
        textfont=dict(size=11, color=C["ink"]),
        marker=dict(size=14, color=colours, line=dict(color="#fff", width=2)),
        customdata=np.stack([A["ja"], A["s0"].round(), A["s1"].round(), A["n"]], axis=-1),
        hovertemplate=hover))
    fig.add_vline(x=float(A["d"].median()), line_width=1, line_dash="dot", line_color=C["border"])
    fig.add_hline(y=float(A["share"].median()), line_width=1, line_dash="dot",
                  line_color=C["border"])
    fig.add_annotation(text=S["b_a_q"], x=0.99, y=0.02, xref="paper", yref="paper",
                       xanchor="right", yanchor="bottom", showarrow=False,
                       font=dict(size=11, color=C["muted"]))
    fig.update_layout(**{**_base(460), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=20, b=40),
                      xaxis=_xax(title=dict(text=S["b_a_x"], font=dict(size=11)), zeroline=False),
                      yaxis=_yax(S["b_a_y"], suffix="%", rangemode="tozero"))
    return fig


# ── Market ──────────────────────────────────────────────────────────────────
# No title here is about skincare against makeup, so each exhibit is grey with
# its one accent in ink; the group chart (fig_meti_groups) is the one that
# sets skincare against makeup, in the pair's colours.
_GREY_DARK = "#6B6862"


def fig_market_lines(M, S):
    """Each METI product line's shipped value in the last full year, the
    lines the title names in ink; label: the change since the break year."""
    rows = M["rows"].sort_values("value_y1")
    y0, y1 = M["window"]
    names = S["mk_line"]
    vs = [S["mk_l_vs"].format(d=r["value_d"], y=y0) for _, r in rows.iterrows()]
    more = [v + (" · " + S["mk_l_vs"].format(d=r["base_d"], y=M["base"])
                 if r["group"] == "makeup" else "") for v, (_, r) in zip(vs, rows.iterrows())]
    fig = go.Figure(go.Bar(
        x=rows["value_y1"], y=[names[li] for li in rows.index], orientation="h",
        marker=dict(color=[C["ink"] if li in M["lead"] else _GREY for li in rows.index]),
        text=[f"{d:+.0f}%" for d in rows["value_d"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=C["muted"]),
        customdata=np.stack([list(rows.index), more], axis=-1),
        hovertemplate=(f"<b>%{{y}}</b> %{{customdata[0]}}<br>{S['mk_l_hover']} · "
                       "%{customdata[1]}<extra></extra>")))
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["mk_l_x"], font=dict(size=11)),
                                 range=[0, 1.2 * rows["value_y1"].max()]),
                      yaxis=_yax(automargin=True))
    return fig


def fig_market_bridge(M, S):
    """Each line's change since the break year in units, value per unit and
    shipped value, largest value change at the top."""
    rows = M["rows"].sort_values("value_d")
    y = [S["mk_line"][li] for li in rows.index]
    fig = go.Figure()
    marks = (("units_d", dict(color="rgba(0,0,0,0)", size=10, symbol="circle",
                              line=dict(color=C["muted"], width=1.5))),
             ("vpu_d", dict(color=_GREY_DARK, size=10, symbol="diamond",
                            line=dict(color=_GREY_DARK, width=1))),
             ("value_d", dict(color=C["ink"], size=16, symbol="line-ns",
                              line=dict(color=C["ink"], width=2.5))))
    for (col, marker), name in zip(marks, S["mk_b_names"]):
        fig.add_trace(go.Scatter(
            x=rows[col], y=y, mode="markers", name=name, marker=marker,
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:+.0f}}%<extra></extra>"
            if S["mk_en"] else
            f"<b>%{{y}}</b><br>{name}：%{{x:+.0f}}%<extra></extra>"))
    fig.add_vline(x=0, line_width=1, line_color=C["border"])
    # The exhibit note names the three markers: a legend wraps over the rows
    # at phone width.
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["mk_b_x"], font=dict(size=11)),
                                 ticksuffix="%", zeroline=False),
                      yaxis=_yax(automargin=True))
    return fig


def fig_market_imports(M, S):
    """HS 3304 imports by origin, the largest origins in the last year; the
    leading origin in ink, each line labelled at its end."""
    I = M["imports"]
    f = I["frame"]
    en = S["mk_en"]
    # End labels, moved apart where two lines end close together.
    gap, label_y = 0.06 * f.values.max(), {}
    for c, v in f.iloc[:, -1].sort_values().items():
        label_y[c] = max(v, max(label_y.values(), default=-gap) + gap)
    fig = go.Figure()
    for c, row in f.iterrows():
        name = S["mk_origin"][c]
        lead = c == I["leader"]
        colour = C["ink"] if lead else _GREY
        fig.add_trace(go.Scatter(
            x=list(f.columns), y=row.values, mode="lines+markers", name=name,
            line=dict(color=colour, width=2.5 if lead else 1.5), marker=dict(size=5),
            hovertemplate=(f"{name} %{{x}}: ¥%{{y:,.0f}}億<extra></extra>" if en else
                           f"{name} %{{x}}年：%{{y:,.0f}}億円<extra></extra>")))
        fig.add_annotation(x=f.columns[-1], y=label_y[c], text=name, showarrow=False,
                           xanchor="left", xshift=8,
                           font=dict(size=11, color=C["ink"] if lead else C["muted"]))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=100, t=20, b=30),
                      xaxis=_xax(tickformat="d", tickangle=0,
                                 range=[f.columns[0] - 0.4, f.columns[-1] + 0.4]),
                      yaxis=_yax(S["mk_i_y"], rangemode="tozero"))
    return fig


# ── Demand ──────────────────────────────────────────────────────────────────
# Grey, with the one accent in ink on what each title names. Actives are
# never ranked against each other: the change chart lists each group of terms
# alphabetically (五十音 in Japanese), top to bottom.

def _end_labels(fig, series, names, accent, top, gap_frac=0.045):
    """A label at the end of each line, moved apart where lines end close
    together; `series` maps key -> (x, y) of the line's last point, and `top`
    is the highest value drawn, so the gap is a share of the axis. Labels sit
    in the right margin; a data-placed annotation widens Plotly's autorange,
    so each chart that uses these fixes its x range."""
    gap, placed = gap_frac * top, {}
    for k, (_, y) in sorted(series.items(), key=lambda kv: kv[1][1]):
        placed[k] = max(y, max(placed.values(), default=-gap) + gap)
    for k, (x, _) in series.items():
        fig.add_annotation(x=x, y=placed[k], text=names[k], showarrow=False, xanchor="left",
                           xshift=8, font=dict(size=11, color=C["ink"] if k == accent
                                               else C["muted"]))


def fig_demand_change(M, S):
    """Each term's change in search over the aligned window, by group."""
    from .brief import TRENDS_PULL_SPREAD
    ch = M["change"]
    order = S["dm_order"][::-1]                   # Plotly draws the first category at the bottom
    rose = set(M["changes"]["rose"])
    names = [S["dm_term"][t] for t in order]
    fig = go.Figure(go.Bar(
        x=ch.loc[order, "d"], y=names, orientation="h",
        marker=dict(color=[C["ink"] if t in rose else _GREY for t in order]),
        customdata=np.stack([order, ch.loc[order, "s0"], ch.loc[order, "s1"]], axis=-1),
        hovertemplate=f"<b>%{{y}}</b> %{{customdata[0]}}<br>{S['dm_c_hover']}<extra></extra>"))
    fig.add_vrect(x0=-TRENDS_PULL_SPREAD, x1=TRENDS_PULL_SPREAD, fillcolor=C["grid"], opacity=0.8,
                  layer="below", line_width=0)
    fig.add_vline(x=0, line_width=1, line_color=C["border"])
    # Group labels at the right edge, on each group's first row, and a rule
    # between groups. Row i of the drawn order sits at y = i.
    for g, label in S["dm_c_groups"].items():
        first = next(t for t in S["dm_order"] if ch.loc[t, "kind"] == g)
        fig.add_annotation(x=1, xref="paper", y=S["dm_term"][first], text=label, showarrow=False,
                           xanchor="right", font=dict(size=10, color=C["muted"]))
    kinds = [ch.loc[t, "kind"] for t in order]
    for i in range(1, len(order)):
        if kinds[i] != kinds[i - 1]:
            fig.add_hline(y=i - 0.5, line_width=1, line_color=C["rule"])
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["dm_c_x"], font=dict(size=11)),
                                 zeroline=False,
                                 range=[1.1 * min(ch["d"].min(), -TRENDS_PULL_SPREAD),
                                        1.35 * ch["d"].max()]),
                      yaxis=_yax(automargin=True))
    return fig


def fig_demand_pair(M, S):
    """化粧品 and スキンケア by month, from one request on one scale."""
    cross = M["cross"]
    fig = go.Figure()
    ends = {}
    for term in ("スキンケア", "化粧品"):
        d = cross[cross["term"] == term].sort_values("week_start")
        accent = term == "化粧品"
        fig.add_trace(go.Scatter(
            x=d["week_start"], y=d["interest"], mode="lines", name=S["dm_p_names"][term],
            line=dict(color=C["ink"] if accent else _GREY, width=2.5 if accent else 2),
            hovertemplate=f"{S['dm_p_names'][term]} %{{x|%Y-%m}}: %{{y:.0f}}<extra></extra>"))
        ends[term] = (d["week_start"].iloc[-1], d["interest"].iloc[-1])
    _end_labels(fig, ends, S["dm_p_names"], "化粧品", cross["interest"].max())
    x0, x1 = cross["week_start"].min(), cross["week_start"].max()
    fig.update_layout(**{**_base(360), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=20, r=110, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x0 - pd.Timedelta(days=20), x1 + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["dm_p_y"], rangemode="tozero"))
    return fig


def fig_demand_ingredients(M, S):
    """Annual mean search for the ingredient lines, full years; the line the
    title names in ink."""
    from .demand import LONG_ACTIVE
    ing = M["ing"]
    fig = go.Figure()
    ends = {}
    for term in ing.columns:
        accent = term == LONG_ACTIVE
        name = S["dm_term"][term]
        fig.add_trace(go.Scatter(
            x=list(ing.index), y=ing[term].round(1), mode="lines+markers", name=name,
            line=dict(color=C["ink"] if accent else _GREY, width=2.5 if accent else 1.5),
            marker=dict(size=5),
            hovertemplate=f"{name} %{{x}}: %{{y:.1f}}<extra></extra>"))
        ends[term] = (ing.index[-1], ing[term].iloc[-1])
    _end_labels(fig, ends, S["dm_term"], LONG_ACTIVE, float(ing.max().max()))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=20, r=120, t=20, b=40),
                      xaxis=_xax(tickformat="d", range=[ing.index[0] - 0.3, ing.index[-1] + 0.3]),
                      yaxis=_yax(S["dm_i_y"], rangemode="tozero"))
    return fig


def fig_demand_makeup(M, S):
    """Three makeup terms by month against each term's own 2019 mean; the
    term the title names in ink."""
    MK = M["makeup"]
    mk = MK["frame"]
    fig = go.Figure()
    fig.add_hline(y=100, line_dash="dot", line_color=C["border"], line_width=1.5)
    fig.add_vline(x=MK["relaxed"], line_dash="dash", line_color=C["muted"], line_width=1.5)
    fig.add_annotation(x=MK["relaxed"], y=0.98, yref="paper", text=S["dm_m_mask"],
                       showarrow=False, xanchor="left", xshift=4,
                       font=dict(size=10, color=C["muted"]))
    fig.add_annotation(x=1, xref="paper", y=100, text=S["dm_m_base"], showarrow=False,
                       xanchor="right", yanchor="bottom", font=dict(size=10, color=C["muted"]))
    ends = {}
    for term in ("ファンデーション", "アイシャドウ", "口紅"):
        d = mk[mk["term"] == term]
        accent = term == "口紅"
        name = S["dm_m_names"][term]
        fig.add_trace(go.Scatter(
            x=d["week_start"], y=d["smooth"], mode="lines", name=name,
            line=dict(color=C["ink"] if accent else _GREY, width=2.5 if accent else 1.5),
            hovertemplate=f"{name} %{{x|%Y-%m}}: %{{y:.0f}}<extra></extra>"))
        ends[term] = (d["week_start"].iloc[-1], d["smooth"].iloc[-1])
    _end_labels(fig, ends, {t: S["dm_term"].get(t, t) for t in ends}, "口紅", mk["smooth"].max())
    x0, x1 = mk["week_start"].min(), mk["week_start"].max()
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=20, r=110, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x0 - pd.Timedelta(days=20), x1 + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["dm_m_y"], rangemode="tozero"))
    return fig


def fig_demand_related(M, S):
    """The recent window's rising related searches; the brand the title names
    in ink."""
    R = M["related"]
    t = R["tiles"]
    accent = t["root"] == R["brand"]
    seeds = [f"{n} seed" + ("" if n == 1 else "s") if S["dm_en"] else f"起点語{n}"
             for n in t["seed_count"]]
    fig = go.Figure(go.Treemap(
        labels=[S["dm_root"][r] for r in t["root"]], parents=[""] * len(t),
        values=t["metric"], branchvalues="total", sort=True,
        marker=dict(colors=[C["ink"] if a else "#E4E1DB" for a in accent],
                    line=dict(color=C["bg"], width=2)),
        textfont=dict(size=11, color=["#FFFFFF" if a else C["ink"] for a in accent]),
        customdata=np.stack([seeds, t["seeds"]], axis=-1),
        texttemplate="<b>%{label}</b><br>%{customdata[0]}",
        hovertemplate="<b>%{label}</b><br>%{customdata[0]}: %{customdata[1]}<extra></extra>"))
    fig.update_layout(**{**_base(400), "hovermode": "closest"}, margin=dict(l=0, r=0, t=10, b=0))
    return fig
