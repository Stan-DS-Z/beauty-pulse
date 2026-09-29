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
import plotly.graph_objects as go

from .data import LAUNCH_GROUPS
from .strings import LAUNCH_CAT
from .theme import C, _base, _xax, _yax


# ── Market · shipped value by group ───────────────────────────────────────


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


# ── Tab 3 · search, video and reviews ────────────────────────────────────

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
    is the highest value drawn, so the gap is a share of the axis. `accent` is
    the key whose label is set in ink, or a tuple of them. Labels sit in the
    right margin; a data-placed annotation widens Plotly's autorange, so each
    chart that uses these fixes its x range."""
    inks = accent if isinstance(accent, tuple) else (accent,)
    gap, placed = gap_frac * top, {}
    for k, (_, y) in sorted(series.items(), key=lambda kv: kv[1][1]):
        placed[k] = max(y, max(placed.values(), default=-gap) + gap)
    for k, (x, _) in series.items():
        fig.add_annotation(x=x, y=placed[k], text=names[k], showarrow=False, xanchor="left",
                           xshift=8, font=dict(size=11, color=C["ink"] if k in inks
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


# ── Supply ──────────────────────────────────────────────────────────────────
# The launch-total chart sets skincare against makeup, in the pair's colours;
# every other exhibit is grey with its accent in ink on what its title names.
# Hollow marks are the earlier year or window, filled marks the later one.
# Ingredients are never ranked: they are listed alphabetically (五十音 in
# Japanese), top to bottom.
_GREY_LIGHT = "#CFCBC4"
_ORIGIN_COLOUR = {"KR": C["ink"], "JP": _GREY, "global": _GREY_LIGHT, "CN": _GREY_DARK}


def _dumbbell(fig, names, x0, x1, n0, n1, inked, hover0, hover1):
    """One row per name: a rule from x0 to x1, a hollow mark at x0 and a filled
    mark at x1, in ink where `inked` is true and grey otherwise."""
    colour = [C["ink"] if i else _GREY for i in inked]
    for name, a, b, i in zip(names, x0, x1, inked):
        fig.add_shape(type="line", x0=a, x1=b, y0=name, y1=name, layer="below",
                      line=dict(color=C["ink"] if i else C["border"], width=2))
    fig.add_trace(go.Scatter(x=list(x0), y=names, mode="markers", customdata=list(n0),
                             marker=dict(size=9, color=C["card"], line=dict(color=colour, width=2)),
                             cliponaxis=False, hovertemplate=hover0))
    fig.add_trace(go.Scatter(x=list(x1), y=names, mode="markers", customdata=list(n1),
                             marker=dict(size=10, color=colour, line=dict(color=colour, width=1)),
                             cliponaxis=False, hovertemplate=hover1))


def fig_supply_share(M, S):
    """Each category's share of categorised core launch releases in the first
    and last year of the window, largest last-year share at the top; the
    categories the title names in ink."""
    SH = M["share"]
    y0, y1 = M["window"]
    n0, n1 = SH["den"]
    rows = SH["rows"].sort_values(["launch_s1", "launch_s0"])
    named = set(SH["gainers"]) | {SH["loser"]}
    en = S["sp_en"]
    hover = ((lambda y, n: f"<b>%{{y}}</b> {y}: %{{x:.1f}}% (%{{customdata}} of {n})<extra></extra>")
             if en else
             (lambda y, n: f"<b>%{{y}}</b> {y}年：%{{x:.1f}}%（{n}件中%{{customdata}}件）<extra></extra>"))
    fig = go.Figure()
    _dumbbell(fig, [S["sp_cat"][k] for k in rows.index], rows["launch_s0"], rows["launch_s1"],
              rows["launch_n0"], rows["launch_n1"], [k in named for k in rows.index],
              hover(y0, n0), hover(y1, n1))
    fig.update_layout(**{**_base(520), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["sp_s_x"], font=dict(size=11)),
                                 ticksuffix="%", rangemode="tozero"),
                      yaxis=_yax(automargin=True))
    return fig


def fig_supply_origin(M, S):
    """Share of core launch releases by issuer origin, each complete half-year;
    Korea in ink at the base, each origin labelled beside the last bar. A
    year's two halves stand side by side over one year label, which fits at
    phone width where nine half-year labels do not; hover names the half."""
    O = M["origin"]
    sh, ct, tot = O["shares"], O["counts"], O["total"]
    x = [int(h[:4]) + (0.28 if h.endswith("1") else 0.72) for h in sh.index]
    label = [S["sp_half"][h] for h in sh.index]
    years = sorted({int(h[:4]) for h in sh.index})
    ticks = [y + 0.5 for y in years]
    fig = go.Figure()
    for o in O["counts"].columns:
        name = S["sp_origin"][o]
        fig.add_trace(go.Bar(
            x=x, y=sh[o], name=name, width=0.4,
            marker=dict(color=_ORIGIN_COLOUR[o], line=dict(width=0)),
            customdata=list(zip(ct[o], tot, label)),
            hovertemplate=(f"{name} %{{customdata[2]}}: %{{y:.0f}}% (%{{customdata[0]}} of "
                           "%{customdata[1]})<extra></extra>" if S["sp_en"] else
                           f"{name} %{{customdata[2]}}：%{{y:.0f}}%（%{{customdata[1]}}件中"
                           "%{customdata[0]}件）<extra></extra>")))
    last, base = sh.iloc[-1], 0.0
    for o in O["counts"].columns:
        fig.add_annotation(x=1, xref="paper", y=base + last[o] / 2, text=S["sp_origin"][o],
                           showarrow=False, xanchor="left", xshift=6,
                           font=dict(size=11, color=C["ink"] if o == "KR" else C["muted"]))
        base += last[o]
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, barmode="stack",
                      showlegend=False, margin=dict(l=10, r=100, t=10, b=40),
                      xaxis=_xax(tickangle=0, tickvals=ticks, showgrid=False,
                                 ticktext=[str(y) if S["sp_en"] else f"{y}年" for y in years],
                                 range=[min(x) - 0.3, max(ticks) + 0.3]),
                      yaxis=_yax(S["sp_o_y"], suffix="%", range=[0, 100]))
    return fig


def fig_supply_groups(M, S):
    """12-month launch-release totals by category group; skincare and makeup in
    the pair's colours, the rest grey, each line labelled at its end."""
    roll = M["groups"]["roll"]
    x = pd.to_datetime(roll.index + "-01")
    colour = {"skincare": C["skin"], "makeup": C["cosm"], "other": _GREY, "none": _GREY}
    fig = go.Figure()
    ends = {}
    for g in LAUNCH_GROUPS:
        name = S["sp_group"][g]
        fig.add_trace(go.Scatter(
            x=x, y=roll[g], mode="lines", name=name,
            line=dict(color=colour[g], width=2.5 if g in ("skincare", "makeup") else 1.5,
                      dash="dash" if g == "none" else "solid"),
            hovertemplate=f"{name} %{{x|%Y-%m}}: %{{y:.0f}}<extra></extra>"))
        ends[g] = (x[-1], float(roll[g].iloc[-1]))
    _end_labels(fig, ends, S["sp_group"], ("skincare", "makeup"), float(roll.values.max()))
    fig.update_layout(**{**_base(360), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=20, r=150, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x[0] - pd.Timedelta(days=20), x[-1] + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["sp_g_y"], rangemode="tozero"))
    return fig


def fig_supply_ingredients(M, S):
    """Share of launch releases naming each tracked ingredient, the 12 months
    before and the latest 12, alphabetical top to bottom; the ingredient the
    title names in ink."""
    I = M["ingredients"]
    f = I["frame"]
    order = S["sp_ing_order"][::-1]               # Plotly draws the first category at the bottom
    en = S["sp_en"]
    hover = ((lambda w: f"<b>%{{y}}</b> {w}: %{{x:.1f}}% (%{{customdata}})<extra></extra>") if en
             else (lambda w: f"<b>%{{y}}</b> {w}：%{{x:.1f}}%（%{{customdata}}件）<extra></extra>"))
    fig = go.Figure()
    _dumbbell(fig, [S["sp_ing"][k] for k in order], f.loc[order, "s_p12"], f.loc[order, "s_l12"],
              f.loc[order, "n_p12"], f.loc[order, "n_l12"], [k == I["top"] for k in order],
              hover(S["sp_win_p12"]), hover(S["sp_win_l12"]))
    fig.update_layout(**{**_base(460), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["sp_i_x"], font=dict(size=11)),
                                 ticksuffix="%", rangemode="tozero"),
                      yaxis=_yax(automargin=True))
    return fig


def fig_supply_prices(M, S):
    """Median price among each Rakuten genre's most-reviewed items, highest at
    the top; the two genres the title names in ink."""
    P = M["prices"]
    f = P["frame"].sort_values("med_price")
    names = [S["sp_genre"][k] for k in f.index]
    en = S["sp_en"]
    fig = go.Figure(go.Bar(
        x=f["med_price"], y=names, orientation="h",
        marker=dict(color=[C["ink"] if k in (P["hi"], P["lo"]) else _GREY for k in f.index]),
        text=[f"¥{v:,.0f}" if en else f"{v:,.0f}円" for v in f["med_price"]],
        textposition="outside", cliponaxis=False, textfont=dict(size=11, color=C["muted"]),
        customdata=np.stack([f["avg_rating"], f["rated_share"], f["sku_count"]], axis=-1),
        hovertemplate=("<b>%{y}</b><br>Median price ¥%{x:,.0f}<br>Average rating "
                       "%{customdata[0]:.2f} (the %{customdata[1]:.0%} of items rated)<br>"
                       "Items: %{customdata[2]:,}<extra></extra>" if en else
                       "<b>%{y}</b><br>価格中央値 %{x:,.0f}円<br>平均評価 %{customdata[0]:.2f}"
                       "（評価のある%{customdata[1]:.0%}の商品）<br>商品数 %{customdata[2]:,}"
                       "<extra></extra>")))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["sp_r_x"], font=dict(size=11)),
                                 tickformat=",", tickprefix="¥" if en else "",
                                 ticksuffix="" if en else "円",
                                 range=[0, 1.3 * f["med_price"].max()]),
                      yaxis=_yax(automargin=True))
    return fig
