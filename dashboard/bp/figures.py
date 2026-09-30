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


# ── Consumer ────────────────────────────────────────────────────────────────
# Grey, with the one accent in ink on what the title names: the reviews that
# contain the two phrases.

def fig_consumer_map(M, S):
    """The @cosme reviews placed by vocabulary; the reviews that contain the
    two phrases in ink, labelled once where most of them sit."""
    pts = M["points"]
    fig = go.Figure()
    for flag, colour, size, opacity in ((0, _GREY_LIGHT, 3, 0.45), (1, C["ink"], 3, 0.6)):
        d = pts[pts["phrase"] == flag]
        # Scattergl: 40k points render via WebGL; SVG Scatter is sluggish here.
        fig.add_trace(go.Scattergl(
            x=d["umap_x"], y=d["umap_y"], mode="markers",
            marker=dict(color=colour, size=size, opacity=opacity, line=dict(width=0)),
            customdata=d["category"].map(S["cs_cat"]),
            hovertemplate=S["cs_m_hover"][flag] + "<extra></extra>"))
    # The label points at the middle of the reviews most of whose neighbours
    # carry the phrases too, from the empty space to their left.
    core = pts[(pts["phrase"] == 1) & (pts["nn_phrase"] >= 8)]
    fig.add_annotation(x=core["umap_x"].median(), y=core["umap_y"].median(), text=S["cs_m_label"],
                       showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=C["ink"],
                       ax=-90, ay=-30, xanchor="right", font=dict(size=11, color=C["ink"]))
    fig.update_layout(**{**_base(520), "hovermode": "closest"}, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig
