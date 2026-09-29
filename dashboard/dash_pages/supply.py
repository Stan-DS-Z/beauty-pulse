"""Supply: PR TIMES product-launch releases from the core issuers, by
category, issuer origin, category group and ingredient. A report page: no
controls, one edition date, every exhibit a result with its source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures

PATH = "/supply"
dash.register_page(__name__, path=PATH, name="Supply", order=3,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _exhibit(S, key, graph_id, figure):
    return html.Div([ui.chart_head(S[f"sp_{key}_h"], S[f"sp_{key}_e"]),
                     ui.graph(graph_id, figure), ui.source(S["sp_src_prtimes"])])


def build(lang, d):
    S, M = d.S[lang], d.SUPPLY
    kids = [ui.header(S, lang, PATH)]
    if M is None:
        return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en",
                        children=kids + [ui.info(S["launch_empty"])])
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=kids + [
        ui.kicker(S["sp_kicker"]),
        ui.intro(S["sp_intro"]),
        ui.key_figures(S["sp_figs"]),
        ui.row(_exhibit(S, "s", "sp-fig-share", figures.fig_supply_share(M, S)),
               _exhibit(S, "o", "sp-fig-origin", figures.fig_supply_origin(M, S))),
        ui.row(_exhibit(S, "g", "sp-fig-groups", figures.fig_supply_groups(M, S)),
               _exhibit(S, "i", "sp-fig-ingredients", figures.fig_supply_ingredients(M, S))),
        ui.caption(S["sp_cap"]),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
