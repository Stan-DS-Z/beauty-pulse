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
from .theme import (AMBER, C, CHARCOAL, CONTEXT, ORIGIN, PURPLE, SIDE, SKIN_DEEP, SKIN_LIGHT,
                    TEAL, _SEQ, _base, _xax, _yax)


def _legend(**kw):
    """A horizontal legend above the plot; Plotly widens the top margin for it."""
    d = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
             bgcolor="rgba(0,0,0,0)", font=dict(size=11))
    d.update(kw)
    return d


def _key(fig, name, marker=None, line=None, mode="markers"):
    """A legend entry with no data: names a colour or a mark the traces use."""
    fig.add_trace(go.Scatter(x=[None], y=[None], mode=mode, name=name, marker=marker or {},
                             line=line or {}, hoverinfo="skip", showlegend=True))


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


# ── Brief ───────────────────────────────────────────────────────────────────
# Colour: each category in its own colour (theme.SIDE); the actives in green.
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
            marker=dict(size=1.1 * np.sqrt(g["value_y1"]), color=SIDE[group],
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
    # The actives the title names in full green, the rest lighter.
    opacity = [1.0 if k in named else 0.45 for k in A.index]
    fig = go.Figure(go.Scatter(
        x=A["d"], y=A["share"], mode="markers+text",
        text=[f"{name} ({n})" if S["b_namecol"] == "en" else f"{name}（{n}）"
              for name, n in zip(A[S["b_namecol"]], A["n"])],
        textposition="top center",
        textfont=dict(size=11, color=C["ink"]),
        marker=dict(size=14, color=C["ingr"], opacity=opacity, line=dict(color="#fff", width=2)),
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
# Product lines in their side's colour; import origins in theme's origin set.
IMPORT_COLOUR = {"大韓民国": C["korean"], "フランス": PURPLE, "アメリカ合衆国": CHARCOAL,
                 "中華人民共和国": TEAL}


def _side_keys(fig, S, groups):
    """One legend entry per side drawn, in the site's order."""
    for g in ("skincare", "makeup", "sunscreen"):
        if g in set(groups):
            _key(fig, S["ch_side"][g], marker=dict(color=SIDE[g], size=10, symbol="square"))


def fig_market_lines(M, S):
    """Each METI product line's shipped value in the last full year, in its
    side's colour; label: the change since the break year."""
    rows = M["rows"].sort_values("value_y1")
    y0, y1 = M["window"]
    names = S["mk_line"]
    vs = [S["mk_l_vs"].format(d=r["value_d"], y=y0) for _, r in rows.iterrows()]
    more = [v + (" · " + S["mk_l_vs"].format(d=r["base_d"], y=M["base"])
                 if r["group"] == "makeup" else "") for v, (_, r) in zip(vs, rows.iterrows())]
    fig = go.Figure(go.Bar(
        x=rows["value_y1"], y=[names[li] for li in rows.index], orientation="h",
        marker=dict(color=[SIDE[g] for g in rows["group"]]),
        text=[f"{d:+.0f}%" for d in rows["value_d"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=C["muted"]), showlegend=False,
        customdata=np.stack([list(rows.index), more], axis=-1),
        hovertemplate=(f"<b>%{{y}}</b> %{{customdata[0]}}<br>{S['mk_l_hover']} · "
                       "%{customdata[1]}<extra></extra>")))
    _side_keys(fig, S, rows["group"])
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["mk_l_x"], font=dict(size=11)),
                                 range=[0, 1.2 * rows["value_y1"].max()]),
                      yaxis=_yax(automargin=True))
    return fig


def fig_market_bridge(M, S):
    """Each line's change since the break year in units, value per unit and
    shipped value, largest value change at the top. Colour is the line's
    side; the mark's shape is the measure, and the legend names both."""
    rows = M["rows"].sort_values("value_d")
    y = [S["mk_line"][li] for li in rows.index]
    col = [SIDE[g] for g in rows["group"]]
    fig = go.Figure()
    shapes = (("units_d", "circle-open", 10, 1.5), ("vpu_d", "diamond", 10, 1),
              ("value_d", "line-ns", 16, 2.5))
    for (field, symbol, size, width), name in zip(shapes, S["mk_b_names"]):
        fig.add_trace(go.Scatter(
            x=rows[field], y=y, mode="markers", name=name, showlegend=False,
            marker=dict(color=col, size=size, symbol=symbol, line=dict(color=col, width=width)),
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:+.0f}}%<extra></extra>"
            if S["mk_en"] else
            f"<b>%{{y}}</b><br>{name}：%{{x:+.0f}}%<extra></extra>"))
    for (_, symbol, size, width), name in zip(shapes, S["mk_b_names"]):
        _key(fig, name, marker=dict(color=CONTEXT, size=size, symbol=symbol,
                                    line=dict(color=CONTEXT, width=width)))
    _side_keys(fig, S, rows["group"])
    fig.add_vline(x=0, line_width=1, line_color=C["border"])
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["mk_b_x"], font=dict(size=11)),
                                 ticksuffix="%", zeroline=False),
                      yaxis=_yax(automargin=True))
    return fig


def fig_market_imports(M, S):
    """HS 3304 imports by origin, the largest origins in the last year, each
    in its own colour and labelled at its end; the leading origin thicker."""
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
        colour = IMPORT_COLOUR.get(c, CONTEXT)
        fig.add_trace(go.Scatter(
            x=list(f.columns), y=row.values, mode="lines+markers", name=name,
            line=dict(color=colour, width=3 if lead else 2), marker=dict(size=5),
            hovertemplate=(f"{name} %{{x}}: ¥%{{y:,.0f}}億<extra></extra>" if en else
                           f"{name} %{{x}}年：%{{y:,.0f}}億円<extra></extra>")))
        fig.add_annotation(x=f.columns[-1], y=label_y[c], text=name, showarrow=False,
                           xanchor="left", xshift=8,
                           font=dict(size=11, color=C["ink"] if lead else C["muted"]))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=100, t=20, b=30),
                      xaxis=_xax(tickformat="d", tickangle=0,
                                 range=[f.columns[0] - 0.4, f.columns[-1] + 0.4]),
                      yaxis=_yax(S["mk_i_y"], rangemode="tozero"))
    return fig


# ── Demand ──────────────────────────────────────────────────────────────────
# Category words in their side's colour, actives green, the umbrella terms
# charcoal. Actives are never ranked against each other: the change chart
# lists each group of terms alphabetically (五十音 in Japanese), top to bottom.
def _term_colour(term, kind):
    """A search term's colour: actives green, umbrella terms charcoal, a
    category word its side's (funnel.CATEGORIES records each word's side)."""
    from .funnel import CATEGORIES
    if kind == "active":
        return C["ingr"]
    if kind == "umbrella":
        return CHARCOAL
    side = {t: g for _, _, t, g in CATEGORIES.values() if t}
    return SIDE[side[term]]


def _end_labels(fig, series, names, accent, top, gap_frac=0.045):
    """A label at the end of each line, moved apart where lines end close
    together; `series` maps key -> (x, y) of the line's last point, and `top`
    is the highest value drawn, so the gap is a share of the axis. `accent` is
    the key whose label is set in ink, or a tuple of them; the others are
    muted, and the line's colour beside each label names it. Labels sit in the
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
    names = [S["dm_term"][t] for t in order]
    fig = go.Figure(go.Bar(
        x=ch.loc[order, "d"], y=names, orientation="h", showlegend=False,
        marker=dict(color=[_term_colour(t, ch.loc[t, "kind"]) for t in order]),
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
    sq = dict(size=10, symbol="square")
    _key(fig, S["dm_c_groups"]["active"], marker=dict(color=C["ingr"], **sq))
    for g in ("skincare", "makeup", "sunscreen"):
        _key(fig, S["ch_side"][g], marker=dict(color=SIDE[g], **sq))
    _key(fig, S["dm_c_groups"]["umbrella"], marker=dict(color=CHARCOAL, **sq))
    fig.update_layout(**{**_base(560), "hovermode": "closest"}, showlegend=True, legend=_legend(),
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
        fig.add_trace(go.Scatter(
            x=d["week_start"], y=d["interest"], mode="lines", name=S["dm_p_names"][term],
            line=dict(color=C["skin"] if term == "スキンケア" else CHARCOAL, width=2.5),
            hovertemplate=f"{S['dm_p_names'][term]} %{{x|%Y-%m}}: %{{y:.0f}}<extra></extra>"))
        ends[term] = (d["week_start"].iloc[-1], d["interest"].iloc[-1])
    _end_labels(fig, ends, S["dm_p_names"], "化粧品", cross["interest"].max())
    x0, x1 = cross["week_start"].min(), cross["week_start"].max()
    fig.update_layout(**{**_base(360), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=110, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x0 - pd.Timedelta(days=20), x1 + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["dm_p_y"], rangemode="tozero"))
    return fig


def fig_demand_ingredients(M, S):
    """Annual mean search for the ingredient lines, full years; the line the
    title names in the actives' green, the others in purple, charcoal and
    amber (a set checked to tell apart)."""
    from .demand import LONG_ACTIVE
    ing = M["ing"]
    others = iter((PURPLE, CHARCOAL, AMBER))
    colour = {t: C["ingr"] if t == LONG_ACTIVE else next(others, CONTEXT) for t in ing.columns}
    fig = go.Figure()
    ends = {}
    for term in ing.columns:
        accent = term == LONG_ACTIVE
        name = S["dm_term"][term]
        fig.add_trace(go.Scatter(
            x=list(ing.index), y=ing[term].round(1), mode="lines+markers", name=name,
            line=dict(color=colour[term], width=3 if accent else 2),
            marker=dict(size=5),
            hovertemplate=f"{name} %{{x}}: %{{y:.1f}}<extra></extra>"))
        ends[term] = (ing.index[-1], ing[term].iloc[-1])
    _end_labels(fig, ends, S["dm_term"], LONG_ACTIVE, float(ing.max().max()))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=120, t=20, b=40),
                      xaxis=_xax(tickformat="d", range=[ing.index[0] - 0.3, ing.index[-1] + 0.3]),
                      yaxis=_yax(S["dm_i_y"], rangemode="tozero"))
    return fig


def fig_demand_makeup(M, S):
    """Three makeup terms by month against each term's own 2019 mean; the
    term the title names in makeup rose, the others purple and charcoal."""
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
        colour = {"口紅": C["cosm"], "アイシャドウ": PURPLE, "ファンデーション": CHARCOAL}[term]
        fig.add_trace(go.Scatter(
            x=d["week_start"], y=d["smooth"], mode="lines", name=name,
            line=dict(color=colour, width=3 if accent else 2),
            hovertemplate=f"{name} %{{x|%Y-%m}}: %{{y:.0f}}<extra></extra>"))
        ends[term] = (d["week_start"].iloc[-1], d["smooth"].iloc[-1])
    _end_labels(fig, ends, {t: S["dm_term"].get(t, t) for t in ends}, "口紅", mk["smooth"].max())
    x0, x1 = mk["week_start"].min(), mk["week_start"].max()
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=110, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x0 - pd.Timedelta(days=20), x1 + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["dm_m_y"], rangemode="tozero"))
    return fig


# ── Supply ──────────────────────────────────────────────────────────────────
# Categories in their side's colour, ingredients in the actives' green, issuer
# origins in theme.ORIGIN. Hollow marks are the earlier year or window, filled
# marks the later one, and the legend says which. Ingredients are never
# ranked: they are listed alphabetically (五十音 in Japanese), top to bottom.


def _dumbbell(fig, names, x0, x1, n0, n1, colour, hover0, hover1, label0, label1):
    """One row per name: a rule from x0 to x1, a hollow mark at x0 and a filled
    mark at x1, each row in its colour; label0 and label1 name the two marks
    in the legend."""
    # The rules are line traces, one per colour with a break between rows: a
    # shape is drawn under the gridline that runs along its row.
    rules = {}
    for name, a, b, c in zip(names, x0, x1, colour):
        xs, ys = rules.setdefault(c, ([], []))
        xs += [a, b, None]
        ys += [name, name, None]
    for c, (xs, ys) in rules.items():
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=c, width=2),
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=list(x0), y=names, mode="markers", customdata=list(n0),
                             marker=dict(size=9, color=C["card"], line=dict(color=colour, width=2)),
                             cliponaxis=False, hovertemplate=hover0, showlegend=False))
    fig.add_trace(go.Scatter(x=list(x1), y=names, mode="markers", customdata=list(n1),
                             marker=dict(size=10, color=colour, line=dict(color=colour, width=1)),
                             cliponaxis=False, hovertemplate=hover1, showlegend=False))
    _key(fig, label0, marker=dict(size=9, color=C["card"], line=dict(color=CONTEXT, width=2)))
    _key(fig, label1, marker=dict(size=10, color=CONTEXT))
    # A category axis takes its order from the first trace, here the rules,
    # which are grouped by colour: hold the rows in the order given.
    fig.update_yaxes(categoryorder="array", categoryarray=list(names))


def fig_supply_share(M, S):
    """Each category's share of categorised core launch releases in the first
    and last year of the window, largest last-year share at the top, each row
    in its side's colour."""
    SH = M["share"]
    y0, y1 = M["window"]
    n0, n1 = SH["den"]
    rows = SH["rows"].sort_values(["launch_s1", "launch_s0"])
    en = S["sp_en"]
    hover = ((lambda y, n: f"<b>%{{y}}</b> {y}: %{{x:.1f}}% (%{{customdata}} of {n})<extra></extra>")
             if en else
             (lambda y, n: f"<b>%{{y}}</b> {y}年：%{{x:.1f}}%（{n}件中%{{customdata}}件）<extra></extra>"))
    fig = go.Figure()
    _dumbbell(fig, [S["sp_cat"][k] for k in rows.index], rows["launch_s0"], rows["launch_s1"],
              rows["launch_n0"], rows["launch_n1"], [SIDE[g] for g in rows["group"]],
              hover(y0, n0), hover(y1, n1), str(y0), str(y1))
    _side_keys(fig, S, rows["group"])
    fig.update_layout(**{**_base(520), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["sp_s_x"], font=dict(size=11)),
                                 ticksuffix="%", rangemode="tozero"),
                      yaxis=_yax(automargin=True))
    return fig


def fig_supply_origin(M, S):
    """Share of core launch releases by issuer origin, each complete half-year;
    Korea at the base, each origin in its colour and labelled beside the last
    bar. A
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
            marker=dict(color=ORIGIN[o], line=dict(color=C["bg"], width=1)),
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
                      showlegend=True, legend=_legend(traceorder="normal"),
                      margin=dict(l=10, r=100, t=10, b=40),
                      xaxis=_xax(tickangle=0, tickvals=ticks, showgrid=False,
                                 ticktext=[str(y) if S["sp_en"] else f"{y}年" for y in years],
                                 range=[min(x) - 0.3, max(ticks) + 0.3]),
                      yaxis=_yax(S["sp_o_y"], suffix="%", range=[0, 100]))
    return fig


def fig_supply_groups(M, S):
    """12-month launch-release totals by category group; skincare and makeup in
    their colours, the other two grey (one dashed), each line labelled at its
    end."""
    roll = M["groups"]["roll"]
    x = pd.to_datetime(roll.index + "-01")
    colour = {"skincare": C["skin"], "makeup": C["cosm"], "other": CONTEXT, "none": CONTEXT}
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
    fig.update_layout(**{**_base(360), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=150, t=20, b=40),
                      xaxis=_xax(tickformat="%Y", tickangle=0,
                                 range=[x[0] - pd.Timedelta(days=20), x[-1] + pd.Timedelta(days=20)]),
                      yaxis=_yax(S["sp_g_y"], rangemode="tozero"))
    return fig


def fig_supply_ingredients(M, S):
    """Share of launch releases naming each tracked ingredient, the 12 months
    before and the latest 12, alphabetical top to bottom, in the actives'
    green."""
    I = M["ingredients"]
    f = I["frame"]
    order = S["sp_ing_order"][::-1]               # Plotly draws the first category at the bottom
    en = S["sp_en"]
    hover = ((lambda w: f"<b>%{{y}}</b> {w}: %{{x:.1f}}% (%{{customdata}})<extra></extra>") if en
             else (lambda w: f"<b>%{{y}}</b> {w}：%{{x:.1f}}%（%{{customdata}}件）<extra></extra>"))
    fig = go.Figure()
    _dumbbell(fig, [S["sp_ing"][k] for k in order], f.loc[order, "s_p12"], f.loc[order, "s_l12"],
              f.loc[order, "n_p12"], f.loc[order, "n_l12"], [C["ingr"]] * len(order),
              hover(S["sp_win_p12"]), hover(S["sp_win_l12"]), S["sp_win_p12"], S["sp_win_l12"])
    fig.update_layout(**{**_base(460), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=10, t=10, b=40),
                      xaxis=_xax(title=dict(text=S["sp_i_x"], font=dict(size=11)),
                                 ticksuffix="%", rangemode="tozero"),
                      yaxis=_yax(automargin=True))
    return fig


# ── Consumer ────────────────────────────────────────────────────────────────
# Each review in its side's colour; the reviews that contain the two phrases
# drawn over them in a dark purple that none of the side colours is near.
PHRASE = "#4B1F6F"


def fig_consumer_map(M, S):
    """The @cosme reviews placed by vocabulary, each in its side's colour; the
    reviews that contain the two phrases drawn on top, labelled once where
    most of them sit."""
    from .consumer import REVIEW_SIDE
    pts = M["points"]
    side = pts["category"].map(REVIEW_SIDE)
    fig = go.Figure()
    layers = [(pts[(pts["phrase"] == 0) & (side == g)], SIDE[g], 0.35, S["cs_m_sides"][g], 0)
              for g in ("skincare", "makeup", "sunscreen")]
    layers.append((pts[pts["phrase"] == 1], PHRASE, 0.75, S["cs_m_leg"], 1))
    for d, colour, opacity, name, flag in layers:
        # Scattergl: 40k points render via WebGL; SVG Scatter is sluggish here.
        fig.add_trace(go.Scattergl(
            x=d["umap_x"], y=d["umap_y"], mode="markers", name=name, showlegend=False,
            marker=dict(color=colour, size=3, opacity=opacity, line=dict(width=0)),
            customdata=d["category"].map(S["cs_cat"]),
            hovertemplate=S["cs_m_hover"][flag] + "<extra></extra>"))
        # The legend swatch at full size and strength; a 3px dot at 35% is unreadable there.
        _key(fig, name, marker=dict(color=colour, size=10))
    # The label points at the middle of the reviews most of whose neighbours
    # carry the phrases too, from the empty space to their left.
    core = pts[(pts["phrase"] == 1) & (pts["nn_phrase"] >= 8)]
    fig.add_annotation(x=core["umap_x"].median(), y=core["umap_y"].median(), text=S["cs_m_label"],
                       showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=C["ink"],
                       ax=-90, ay=-30, xanchor="right", font=dict(size=11, color=C["ink"]))
    fig.update_layout(**{**_base(520), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


# ── Timing ──────────────────────────────────────────────────────────────────
# Seasonal ratios (bp/seasonal.py) on one Jan-Dec axis. Sunscreen in its gold,
# with the years' range as a band; heatmaps on the Streamlit app's blue scale,
# with its key; a row that fails its test is labelled in grey. Launch years in
# their side's colour, lighter for earlier years.
_GOLD_BAND, _GOLD_PEAK = "rgba(184,150,90,0.25)", "rgba(184,150,90,0.18)"
_YEAR_SHADES = {"skincare": [SKIN_LIGHT, "#6FA6CB", C["skin"], SKIN_DEEP],
                "makeup": ["#E9B3C1", "#D88BA0", C["cosm"], "#8A3550"]}


def _month_axis(S, **kw):
    return _xax(tickmode="array", tickvals=list(range(1, 13)), ticktext=S["tm_h_months"],
                tickangle=0, range=[0.5, 12.5], **kw)


def fig_timing_sun(M, S, stage):
    """Sunscreen's seasonal ratio at one stage, "search" or "ship", with its
    years' range and its 3-month peak run shaded. The page sets the two
    stages side by side, so both take the same y range."""
    st = M["sun"][stage]
    name = S["tm_s_search" if stage == "search" else "tm_s_ship"]
    top = max(max(float(np.max(M["sun"][k]["band"]["hi"])), float(np.max(M["sun"][k]["profile"])))
              for k in ("search", "ship"))
    months = list(range(1, 13))
    a, b = st["run"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months + months[::-1],
                             y=list(st["band"]["hi"]) + list(st["band"]["lo"])[::-1],
                             fill="toself", fillcolor=_GOLD_BAND,
                             line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=months, y=st["profile"].round(0), mode="lines+markers",
                             line=dict(color=C["gold"], width=2.5), marker=dict(size=5),
                             showlegend=False,
                             hovertemplate=f"{name} %{{x}}: %{{y:.0f}}<extra></extra>"))
    fig.add_hline(y=100, line_width=1, line_dash="dot", line_color=C["border"])
    fig.add_vrect(x0=a - 0.5, x1=b + 0.5, fillcolor=_GOLD_PEAK, opacity=1,
                  layer="below", line_width=0)
    avg, band, peak = S["tm_s_leg"]
    _key(fig, avg, line=dict(color=C["gold"], width=2.5), mode="lines")
    _key(fig, band, marker=dict(color=_GOLD_BAND, size=12, symbol="square"))
    _key(fig, peak, marker=dict(color=_GOLD_PEAK, size=12, symbol="square",
                                line=dict(color=C["gold"], width=1)))
    fig.update_layout(**{**_base(340), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=10, t=10, b=30), xaxis=_month_axis(S),
                      yaxis=_yax(S["tm_y"], range=[0, 1.08 * top]))
    return fig


def _heatmap(grid, S, rows, height, swing=False):
    """Rows by peak month (top first), labelled by name in the page's language
    (S[rows]), the METI line or search query in the hover; values printed,
    colour capped at timing.HEAT_RANGE. A row that fails its test is labelled
    in grey. swing=True prints each row's swing after December."""
    from .timing import HEAT_RANGE
    z = grid[list(range(1, 13))].round(0)
    labels = [S[rows][k] if ok else f"<span style='color:{C['muted']}'>{S[rows][k]}</span>"
              for k, ok in zip(grid.index, grid["passes"])]
    fig = go.Figure(go.Heatmap(
        # The key is HTML under the chart (ui.scale_key): at phone width a
        # horizontal Plotly colour bar draws no bar and drops the row names.
        z=z.values, x=list(range(1, 13)), y=labels, colorscale=_SEQ, showscale=False,
        zmin=HEAT_RANGE[0], zmax=HEAT_RANGE[1],
        customdata=[[src] * 12 for src in grid["name"]],
        texttemplate="%{z:.0f}", textfont=dict(size=9), xgap=1, ygap=1,
        hovertemplate=S["tm_h_hover"] + "<extra></extra>"))
    if swing:
        # Anchored to the plot's right edge: Plotly drops an annotation whose
        # data x falls outside the axis range.
        fig.add_annotation(xref="paper", x=1, xshift=4, yref="paper", y=1, yanchor="bottom",
                           text=S["tm_h2_swing"], showarrow=False, xanchor="left",
                           font=dict(size=9, color=C["muted"]))
        for lab, (k, r) in zip(labels, grid.iterrows()):
            fig.add_annotation(xref="paper", x=1, xshift=4, y=lab, text=f"{r['swing']:.1f}",
                               showarrow=False, xanchor="left",
                               font=dict(size=9, color=C["ink"] if r["passes"] else C["muted"]))
    fig.update_layout(**{**_base(height), "hovermode": "closest"},
                      margin=dict(l=4, r=34 if swing else 4, t=24, b=4),
                      xaxis=dict(side="top", showgrid=False, tickmode="array",
                                 tickvals=list(range(1, 13)), ticktext=S["tm_h_months"],
                                 tickangle=0, tickfont=dict(size=10), range=[0.5, 12.5]),
                      yaxis=dict(autorange="reversed", showgrid=False, automargin=True,
                                 tickfont=dict(color=C["ink"], size=11)))
    return fig


def heat_key(S):
    """The heatmaps' key for ui.scale_key: title, colour scale and the ticks
    at its two ends and centre."""
    from .timing import HEAT_RANGE
    lo, hi = HEAT_RANGE
    return S["tm_y"], _SEQ, [f"≤{lo}", f"{(lo + hi) / 2:.0f}", f"≥{hi}"]


def fig_timing_ship(M, S):
    """The 16 METI lines' seasonal profiles."""
    return _heatmap(M["ship"], S, "tm_rows_ship", 40 + 24 * len(M["ship"]))


def fig_timing_search(M, S):
    """The category words' and umbrella terms' seasonal profiles, each with
    its swing."""
    return _heatmap(M["search"], S, "tm_rows_search", 40 + 24 * len(M["search"]), swing=True)


def fig_timing_launch(M, S, side):
    """Core launch releases by month for one side, one line per year in the
    side's colour, lighter for earlier years; the year that departs from an
    even spread thicker, and each year's count at the line's end. The page
    sets the two sides side by side, so both take the same y range."""
    tests = M["tests"].set_index(["side", "year"])
    odd = set(tests.index[~tests["even"]])
    top = max(int(c.values.max()) for c in M["counts"].values())
    c = M["counts"][side]
    shade = dict(zip(sorted(c.index), _YEAR_SHADES[side][-len(c.index):]))
    fig = go.Figure()
    ends = {}
    for y, vals in c.iterrows():
        ink = (side, y) in odd
        fig.add_trace(go.Scatter(
            x=list(range(1, 13)), y=vals.values, mode="lines", name=str(y),
            line=dict(color=shade[y], width=3.5 if ink else 2),
            hovertemplate=S["tm_l_hover"].format(y=y) + "<extra></extra>"))
        ends[y] = float(vals.values[-1])
    gap, placed = 0.08 * top, {}
    for y, v in sorted(ends.items(), key=lambda kv: kv[1]):
        placed[y] = max(v, max(placed.values(), default=-gap) + gap)
    for y in ends:
        ink = (side, y) in odd
        fig.add_annotation(x=12, y=placed[y], showarrow=False, xanchor="left", xshift=6,
                           text=S["tm_l_end"].format(y=y, n=int(tests.loc[(side, y), "n"])),
                           font=dict(size=10, color=C["ink"] if ink else C["muted"]))
    fig.update_layout(**{**_base(340), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=20, r=64, t=10, b=30), xaxis=_month_axis(S),
                      yaxis=_yax(S["tm_l_y"], range=[0, 1.12 * top]))
    return fig


# ── Method ──────────────────────────────────────────────────────────────────
# The three skincare lines with the step in blues (the Streamlit app's), the
# comparison lines grey, one dashed and one dotted; the review-similarity
# curve in purple.
_STEP_COLOUR = {"化粧水": C["skin"], "美容液": SKIN_DEEP, "乳液": SKIN_LIGHT}

def fig_method_price_kg(M, S):
    """METI yen per kg by month: the lines with the January 2022 step in
    blues, the comparison lines grey and dashed, each labelled at its end;
    log scale."""
    P = M["price"]
    f = P["frame"].dropna(how="all")
    brk = pd.Timestamp(P["year"], 1, 1) - pd.Timedelta(days=15)
    fig = go.Figure()
    pattern = dict(zip(P["controls"], ("dash", "dot")))
    for li in P["controls"] + P["lines"]:
        ink = li in P["lines"]
        fig.add_trace(go.Scatter(
            x=f.index, y=f[li], mode="lines", name=S["me_pk_names"][li],
            line=dict(color=_STEP_COLOUR.get(li, CONTEXT), width=2.2 if ink else 1.4,
                      dash=pattern.get(li, "solid")),
            hovertemplate=f"{li} {S['me_pk_hover']}<extra></extra>"))
    # End labels on the log axis: spaced in log10 units.
    last = f.index.max()
    ends = {li: (last, float(np.log10(f[li].dropna().iloc[-1]))) for li in f.columns}
    lo, hi = np.log10(f.min().min()), np.log10(f.max().max())
    gap, placed = 0.06 * (hi - lo), {}
    for k, (_, y) in sorted(ends.items(), key=lambda kv: kv[1][1]):
        placed[k] = max(y, max(placed.values(), default=-np.inf) + gap)
    for k, y in placed.items():
        fig.add_annotation(x=last, y=y, text=S["me_pk_names"][k], showarrow=False, xanchor="left",
                           xshift=6,
                           font=dict(size=11, color=C["ink"] if k in P["lines"] else C["muted"]))
    fig.add_vline(x=brk, line_width=1, line_dash="dot", line_color=C["muted"])
    fig.add_annotation(x=brk, y=1, yref="paper", text=S["me_pk_brk"], showarrow=False,
                       xanchor="left", yanchor="top", xshift=4, font=dict(size=10, color=C["muted"]))
    fig.update_layout(**{**_base(380), "hovermode": "closest"}, showlegend=True, legend=_legend(),
                      margin=dict(l=10, r=118, t=10, b=30),
                      xaxis=_xax(dtick="M24", tickformat="%Y", tickangle=0,
                                 range=[f.index.min(), last]),
                      yaxis=_yax(S["me_pk_y"], type="log", tickformat=",.0f"))
    return fig


def fig_method_curve(M, S):
    """Cosine similarity of the late period's skincare and makeup reviews by
    sample size, with the early period's matched value dotted; log x."""
    cv = M["convergence"]
    cur = cv["curve"]
    fig = go.Figure(go.Scatter(
        x=cur["sample_size"], y=cur["cosine"], mode="lines+markers",
        line=dict(color=PURPLE, width=2.5), marker=dict(size=7, color=PURPLE),
        hovertemplate=S["me_v_hover"] + "<extra></extra>"))
    fig.add_hline(y=cv["early"], line_width=1.5, line_dash="dot", line_color=CONTEXT)
    fig.add_annotation(x=1, xref="x domain", y=cv["early"], text=S["me_v_dot"], showarrow=False,
                       xanchor="right", yanchor="top", font=dict(size=11, color=C["muted"]))
    fig.update_layout(**{**_base(360), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=20, t=10, b=40),
                      xaxis=_xax(type="log", title=dict(text=S["me_v_x"], font=dict(size=11)),
                                 tickvals=list(cur["sample_size"]), tickangle=0,
                                 ticktext=[f"{n / 1000:g}k" if n >= 1000 else str(n)
                                           for n in cur["sample_size"]]),
                      yaxis=_yax(S["me_v_y"], range=[0, 0.8]))
    return fig
