"""The language: review vocabulary by year, and the size-matched convergence."""

import dash
from dash import Input, Output, State, callback, dcc, html

import data_cache
import ui
from bp import figures
from bp.theme import C

PATH = "/language"
dash.register_page(__name__, path=PATH, name="The language", order=1,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()
WC_DEFAULT = 2025


def wordcloud_image(year, assets):
    """The year's word cloud, or the caption Streamlit shows when it is missing."""
    if not (assets / f"wordcloud_{year}.png").exists():
        return ui.caption(f"wordcloud_{year}.png not found")
    return html.Img(src=f"/wordcloud/{year}.png", className="bp-wordcloud",
                    alt=f"wordcloud {year}")


def wordcloud_note(year, S):
    key, bg, rule = figures.wordcloud_note(year)
    return html.Div(html.Span(ui.rich(S[key])), className="bp-note bp-wc-note",
                    style={"background": C[bg], "borderLeftColor": C[rule]})


def build(lang, d):
    S, H = d.S[lang], d.HEADLINE
    years = figures.wordcloud_years()
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        dcc.Store(id="lg-lang", data=lang),
        ui.header(S, lang, PATH),
        ui.intro(S["t2_intro"]),
        ui.row(
            ui.kpi_card(S["t2_m1"], f"+{H['conv_delta']}", S["t2_m1d"]),
            ui.kpi_card(S["t2_m2"], f"{H['conv_lo']} → {H['conv_hi']}", S["t2_m2d"]),
            ui.kpi_card(S["t2_m3"], f"{H['size_lo_cos']} → {H['size_hi_cos']}", S["t2_m3d"]),
            cls="cols-3 bp-kpis"),
        ui.row(
            html.Div([
                ui.chart_head(S["t2_wch"], S["t2_wce"]),
                ui.pills("lg-wc-year", [(y, str(y)) for y in years], WC_DEFAULT, label="Year"),
                html.Div(wordcloud_image(WC_DEFAULT, d.assets), id="lg-wc-img"),
                html.Div(wordcloud_note(WC_DEFAULT, S), id="lg-wc-note"),
            ]),
            html.Div([
                ui.chart_head(S["t2_curveh"], S["t2_curvee"]),
                ui.graph("lg-fig-cv", figures.fig_cosine_sizecurve(
                    d.frame("cosine_sizecurve"), H)),
                ui.note(f"+{H['conv_delta']}", "  — " + S["t2_curvenote"], "skin"),
            ]),
        ),
        ui.finding(S["f2_title"], S["f2_body"], "skin"),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]


@callback(Output("lg-wc-img", "children"), Output("lg-wc-note", "children"),
          Input("lg-wc-year", "value"), State("lg-lang", "data"), prevent_initial_call=True)
def _wordcloud(year, lang):
    year = year if year in figures.wordcloud_years() else WC_DEFAULT
    return wordcloud_image(year, D.assets), wordcloud_note(year, D.S[lang])
