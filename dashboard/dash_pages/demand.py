"""Demand: Google Trends search for the actives, the category words and the
umbrella terms; 化粧品 against スキンケア on one scale; the ingredient and
makeup series; and the rising related searches. A report page: no controls,
one edition date, every exhibit a result with its source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures

PATH = "/demand"
dash.register_page(__name__, path=PATH, name="Demand", order=2,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _exhibit(S, key, graph_id, figure, src="dm_src_trends"):
    return html.Div([ui.chart_head(S[f"dm_{key}_h"], S[f"dm_{key}_e"]),
                     ui.graph(graph_id, figure), ui.source(S[src])])


def build(lang, d):
    S, M = d.S[lang], d.DEMAND
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        ui.header(S, lang, PATH),
        ui.kicker(S["dm_kicker"]),
        ui.intro(S["dm_intro"]),
        ui.key_figures(S["dm_figs"]),
        _exhibit(S, "c", "dm-fig-change", figures.fig_demand_change(M, S)),
        _exhibit(S, "p", "dm-fig-pair", figures.fig_demand_pair(M, S)),
        ui.row(_exhibit(S, "i", "dm-fig-ingredients", figures.fig_demand_ingredients(M, S)),
               _exhibit(S, "m", "dm-fig-makeup", figures.fig_demand_makeup(M, S))),
        _exhibit(S, "r", "dm-fig-related", figures.fig_demand_related(M, S), "dm_src_related"),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
