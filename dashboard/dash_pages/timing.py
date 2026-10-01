"""Timing: seasonality by stage on one method (bp/seasonal.py): sunscreen's
search and shipments, the METI lines, the search terms, and launch releases
by month. A report page: no controls, one edition date, every exhibit a
result with its source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures

PATH = "/timing"
dash.register_page(__name__, path=PATH, name="Timing", order=5,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _exhibit(S, key, graph_id, figure, src, key_under=None):
    return html.Div([ui.chart_head(S[f"tm_{key}_h"], S[f"tm_{key}_e"]),
                     ui.graph(graph_id, figure), *([key_under] if key_under else []),
                     ui.source(S[src])])


def build(lang, d):
    S, M = d.S[lang], d.TIMING
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        ui.header(S, lang, PATH),
        ui.kicker(S["tm_kicker"]),
        ui.intro(S["tm_intro"]),
        ui.key_figures(S["tm_figs"]),
        _exhibit(S, "s", "tm-fig-sun", figures.fig_timing_sun(M, S), "tm_src_sun"),
        ui.row(_exhibit(S, "h1", "tm-fig-ship", figures.fig_timing_ship(M, S), "tm_src_meti",
                        ui.scale_key(*figures.heat_key(S))),
               _exhibit(S, "h2", "tm-fig-search", figures.fig_timing_search(M, S), "tm_src_trends",
                        ui.scale_key(*figures.heat_key(S)))),
        _exhibit(S, "l", "tm-fig-launch", figures.fig_timing_launch(M, S), "tm_src_prtimes"),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
