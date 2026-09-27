"""Market: METI shipments by product line and by group, and HS 3304 imports
by origin. A report page: no controls, one edition date, every exhibit a
result with its source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures
from bp.data import METI_BREAK

PATH = "/market"
dash.register_page(__name__, path=PATH, name="Market", order=1,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _exhibit(S, key, graph_id, figure, src):
    return html.Div([ui.chart_head(S[f"mk_{key}_h"], S[f"mk_{key}_e"]),
                     ui.graph(graph_id, figure), ui.source(S[src])])


def build(lang, d):
    S, M = d.S[lang], d.MARKET
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        ui.header(S, lang, PATH),
        ui.kicker(S["mk_kicker"]),
        ui.intro(S["mk_intro"]),
        ui.key_figures(S["mk_figs"]),

        ui.row(_exhibit(S, "l", "mk-fig-lines", figures.fig_market_lines(M, S), "mk_src_meti"),
               _exhibit(S, "b", "mk-fig-bridge", figures.fig_market_bridge(M, S),
                        "mk_src_meti")),

        ui.chart_head(S["mk_g_h"], S["mk_g_e"]),
        ui.graph("mk-fig-groups", figures.fig_meti_groups(
            M["monthly"], {"mkt_break": METI_BREAK}, lang)),
        ui.caption(S["mk_g_cap"]),
        ui.source(S["mk_src_meti"]),

        ui.chart_head(S["mk_i_h"], S["mk_i_e"]),
        ui.graph("mk-fig-imports", figures.fig_market_imports(M, S)),
        ui.source(S["mk_src_trade"]),

        ui.footnote(S["mk_fn_t"], S["mk_fn_b"]),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
