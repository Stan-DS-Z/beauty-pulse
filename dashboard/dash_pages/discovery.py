"""Discovery: YouTube channels and comments, and the review map."""

import dash
from dash import Input, Output, State, callback, dcc, html

import data_cache
import ui
from bp import figures
from bp.theme import C

PATH = "/discovery"
dash.register_page(__name__, path=PATH, name="Discovery", order=5,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def umap_count_caption(df_umap, year_filter):
    return ui.caption(f"{figures.umap_count(df_umap, year_filter):,} reviews")


def _youtube_channels(S, d):
    try:
        df_ch = d.frame("yt_channels")
    except FileNotFoundError:
        return [ui.info("nb07_yt_channels.csv not found — run the NB07 YouTube export "
                        "cells to generate it.")]
    return [
        ui.graph("dc-fig-yt-ch", figures.fig_yt_channels(df_ch)),
        ui.legend([(S["t3_umap_sk"], C["skin"]), (S["t3_umap_co"], C["cosm"]),
                   ("Korean", C["korean"])], shape="small"),
        ui.note(S["t3_ytgap"], S["t3_ytgapb"], "korean"),
    ]


def _youtube_terms(S, d):
    """The two top-30 lists side by side, rank by rank; a term in both lists
    is set in ink and bold, the rest in grey."""
    df = d.frame("vocab_overlap")
    cols = {src: g.set_index("rank") for src, g in df.groupby("source")}
    cell = lambda r: html.Td(r["term"], className="bp-vocab-shared" if r["in_both"]   # noqa: E731
                             else "bp-vocab-own")
    head = html.Thead(html.Tr([html.Th(h) for h in S["t3_vcols"]]))
    body = html.Tbody([html.Tr([html.Td(rank, className="num muted"),
                                cell(cols["cosme"].loc[rank]), cell(cols["youtube"].loc[rank])])
                       for rank in cols["cosme"].index])
    return [html.Div(html.Table([head, body], className="bp-table bp-vocab"),
                     className="bp-tablewrap"),
            ui.caption(S["t3_vkey"])]


def build(lang, d):
    S = d.S[lang]
    df_umap = d.frame("umap")
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        dcc.Store(id="dc-lang", data=lang),
        ui.header(S, lang, PATH),
        ui.intro(S["t3_intro"]),
        ui.row(
            ui.kpi_card(S["t3_m3"], f"{len(df_umap):,} reviews", S["t3_m3d"]),
            cls="cols-3 bp-kpis"),

        ui.panel_header(S["t3_p2"], S["t3_p2d"]),
        ui.chart_head(S["t3_ytch"], S["t3_ytche"]),
        *_youtube_channels(S, d),
        ui.chart_head(S["t3_yttfh"], S["t3_yttfe"]),
        *_youtube_terms(S, d),

        ui.chart_head(S["t3_umaph"], S["t3_umape"]),
        ui.row(
            html.Div(ui.graph("dc-fig-umap", figures.fig_umap(df_umap, "all", S))),
            html.Div([
                ui.pills("dc-umap-year",
                         [(v, figures.umap_year_label(v, lang)) for v in figures.umap_year_options()],
                         "all", label=S["t3_umap_yr"]),
                html.Div(className="bp-umap-key", children=[
                    ui.legend([(S["t3_umap_sk"], C["skin"]), (S["t3_umap_co"], C["cosm"])],
                              shape="dot"),
                    html.P(ui.rich(S["t3_umap_note"].replace(chr(10), "<br><br>")),
                           className="bp-umap-note"),
                ]),
                html.Div(umap_count_caption(df_umap, "all"), id="dc-umap-count"),
            ]),
            cls="cols-3-1"),
        ui.finding(S["f3_title"], S["f3_body"], "skin"),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]


@callback(Output("dc-fig-umap", "figure"), Input("dc-umap-year", "value"),
          State("dc-lang", "data"), prevent_initial_call=True)
def _umap(year_filter, lang):
    return ui.themed(figures.fig_umap(D.frame("umap"), year_filter or "all", D.S[lang]))


@callback(Output("dc-umap-count", "children"), Input("dc-umap-year", "value"),
          prevent_initial_call=True)
def _umap_count(year_filter):
    return umap_count_caption(D.frame("umap"), year_filter or "all")
