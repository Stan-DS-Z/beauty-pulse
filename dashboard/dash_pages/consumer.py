"""Consumer: @cosme review vocabulary at equal sample sizes, the two top-30
skincare term lists (@cosme reviews and YouTube comments), and the review map.
A report page: no controls, one edition date, every exhibit a result with its
source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures

PATH = "/consumer"
dash.register_page(__name__, path=PATH, name="Consumer", order=4,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _term_lists(S, M):
    """The two top-30 lists side by side, rank by rank; a term in both lists
    is set in ink, the rest in grey."""
    cols = M["vocab"]["lists"]
    cell = lambda r: html.Td(r["term"], className="bp-vocab-shared" if r["in_both"]   # noqa: E731
                             else "bp-vocab-own")
    head = html.Thead(html.Tr([html.Th(h) for h in S["cs_vcols"]]))
    body = html.Tbody([html.Tr([html.Td(int(c["rank"]), className="num muted"), cell(c), cell(y)])
                       for (_, c), (_, y) in zip(cols["cosme"].iterrows(),
                                                 cols["youtube"].iterrows())])
    return html.Div(html.Table([head, body], className="bp-table bp-vocab"),
                    className="bp-tablewrap")


def build(lang, d):
    S, M = d.S[lang], d.CONSUMER
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        ui.header(S, lang, PATH),
        ui.kicker(S["cs_kicker"]),
        ui.intro(S["cs_intro"]),
        ui.key_figures(S["cs_figs"]),
        html.Div([ui.chart_head(S["cs_c_h"], S["cs_c_e"]),
                  ui.graph("cs-fig-curve", figures.fig_consumer_curve(M, S)),
                  ui.source(S["cs_src_cosme"])]),
        html.Div([ui.chart_head(S["cs_v_h"], S["cs_v_e"]),
                  _term_lists(S, M),
                  ui.source(S["cs_src_both"])]),
        html.Div([ui.chart_head(S["cs_m_h"], S["cs_m_e"]),
                  ui.graph("cs-fig-map", figures.fig_consumer_map(M, S)),
                  ui.source(S["cs_src_cosme"])]),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
