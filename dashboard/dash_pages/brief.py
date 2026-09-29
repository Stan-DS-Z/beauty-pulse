"""The Brief: the report's governing thought, five key findings, and three
exhibits. A report page: no controls, one edition date, every exhibit a
result with its source line."""

import dash
import numpy as np
from dash import html

import data_cache
import ui
from bp import figures
from bp.figures import GROUP_COLOUR
from bp.strings import BRIEF_LINKS, LAUNCH_CAT

PATH = "/brief"
dash.register_page(__name__, path=PATH, name="Brief", order=0,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()
FINDINGS = ("market", "demand", "supply", "consumer", "timing")


def _findings(S, lang):
    items = []
    for key in FINDINGS:
        link = BRIEF_LINKS[key]
        items.append((S["b_kf_labels"][key], S[f"b_kf_{key}"],
                      ui.href(link[0], lang) if link else None,
                      f"{S[link[1]]} →" if link else ""))
    return ui.key_findings(items)


def _signed(x, suffix="%"):
    """+12%, -3%, and 0% with no sign when it rounds to zero; — when absent."""
    if np.isnan(x):
        return "—"
    return f"0{suffix}" if round(x) == 0 else f"{x:+.0f}{suffix}"


def category_table(B, S):
    """The categories, largest shipped value first: value and its change as
    in-cell bars on each column's shared scale, then the other measures."""
    rows = B["rows"]
    vmax, dmax = rows["value_y1"].max(), rows["ship_d"].abs().max()
    mon = S["b_t_months"]
    head = html.Thead(html.Tr([html.Th([name, html.Span(sub)]) for name, sub in S["b_t_cols"]]))
    body = []
    for key, r in rows.iterrows():
        tag = [html.Span(S["b_t_partial"], className="bp-tag")] if r["join"] == "partial" else []
        body.append(html.Tr([
            html.Td([html.Span(className="bp-swatch",
                               style={"background": GROUP_COLOUR[r["group"]]}),
                     LAUNCH_CAT[key][S["b_catix"]]]),
            html.Td([r["meti_line"], *tag], className="bp-jp"),
            html.Td(ui.cell_bar(r["value_y1"] / vmax, f"{r['value_y1']:,.0f}"),
                    className="num barcell"),
            html.Td(ui.div_bar(r["ship_d"] / dmax, _signed(r["ship_d"])), className="num barcell"),
            html.Td(_signed(r["units_d"]), className="num"),
            html.Td(_signed(r["vpu_d"]), className="num"),
            html.Td(_signed(r["search_d"], ""), className="num"),
            html.Td(f"{r['launch_s0']:.1f} → {r['launch_s1']:.1f}%", className="num"),
            html.Td([f"{r['kr_s']:.0f}% " if r["kr_n"] else "— ",
                     html.Span(f"({r['kr_n']})", className="muted")], className="num"),
            html.Td(S["b_t_monsep"].join(mon[m] for m in r["peak"])),
        ]))
    return html.Div(html.Table([head, html.Tbody(body)], className="bp-table"),
                    className="bp-tablewrap")


def build(lang, d):
    S, B = d.S[lang], d.BRIEF
    kids = [ui.header(S, lang, PATH)]
    if B is None:
        return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en",
                        children=kids + [ui.info(S["launch_empty"])])
    kids += [
        ui.kicker(S["b_kicker"]),
        ui.governing(S["b_governing"]),
        _findings(S, lang),

        ui.chart_head(S["b_p_h"], S["b_p_e"]),
        ui.graph("br-fig-portfolio", figures.fig_brief_portfolio(B, S)),
        ui.source(S["b_p_src"]),

        ui.chart_head(S["b_a_h"], S["b_a_e"]),
        ui.graph("br-fig-actives", figures.fig_brief_actives(B, S)),
        ui.source(S["b_a_src"]),

        ui.chart_head(S["b_t_h"], S["b_t_e"]),
        category_table(B, S),
        ui.source(S["b_t_src"]),
        ui.footnote(S["b_fn_t"], S["b_fn_b"]),
    ]
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=kids)


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
