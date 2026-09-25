"""Discovery: product launches, rising searches, YouTube, and the review map."""

import dash
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

import data_cache
import ui
from bp import figures, strings
from bp.theme import C

PATH = "/discovery"
dash.register_page(__name__, path=PATH, name="Discovery", order=2,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def finding_f4(window_key, S):
    if window_key == "recent":
        return ui.finding(S["f4r_title"], S["f4r_body"], "korean")
    return ui.finding(S["f4c_title"], S["f4c_body"], "skin")


def blockc_prompt():
    return ui.detail_prompt("Click any tile to see detail")


def umap_count_caption(df_umap, year_filter):
    return ui.caption(f"{figures.umap_count(df_umap, year_filter):,} reviews")


def _launch_panel(lang, d):
    S, L = d.S[lang], d.LAUNCH
    if L is None:
        return [html.P(S["t3_lempty"], className="expl")]
    opts = figures.launch_ingredient_options(L)
    df_ing = d.frame("ingredient_surge")
    return [
        ui.chart_head(S["t3_l1h"], S["t3_l1e"]),
        ui.row(
            html.Div(ui.graph("dc-fig-l1", figures.fig_launch_groups(L, S))),
            html.Div([ui.chart_head(S["t3_l2h"], S["t3_l2e"]),
                      ui.graph("dc-fig-l2", figures.fig_launch_categories(L, lang, S))]),
            cls="cols-3-2"),
        ui.chart_head(S["t3_l3h"], S["t3_l3e"]),
        ui.graph("dc-fig-l3", figures.fig_launch_roster(L, S)),
        ui.row(
            html.Div([ui.chart_head(S["t3_l4h"], S["t3_l4e"]),
                      ui.graph("dc-fig-l4", figures.fig_launch_ingredients(L, lang, S))]),
            html.Div([
                ui.chart_head(S["t3_l5h"], S["t3_l5e"]),
                html.Div(className="bp-control", children=dcc.Dropdown(
                    id="dc-launch-ing", value=opts[0], clearable=False,
                    options=[{"label": strings._ing_label(k, lang, L), "value": k}
                             for k in opts])),
                ui.graph("dc-fig-l5", figures.fig_launch_vs_search(L, df_ing, opts[0], S)),
            ]),
        ),
        ui.caption(S["t3_lcap"]),
    ]


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
    try:
        df = d.frame("yt_tfidf")
    except FileNotFoundError:
        return [ui.info("nb07_yt_tfidf.csv not found — run NB06 Section 6 to generate it.")]
    return [ui.graph("dc-fig-yt-div", figures.fig_yt_tfidf(df, S)),
            ui.note(S["t3_ytreg"], S["t3_ytregb"], "muted")]


def build(lang, d):
    S = d.S[lang]
    df_bc = d.frame("blockc")
    df_umap = d.frame("umap")
    windows = figures.blockc_window_options(S)
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        dcc.Store(id="dc-lang", data=lang),
        dcc.Store(id="dc-bc-sel", data=None),
        ui.header(S, lang, PATH),
        ui.intro(S["t3_intro"]),
        ui.row(
            ui.kpi_card(S["t3_m1"], "アヌア", S["t3_m1d"]),
            ui.kpi_card(S["t3_m2"], "レチノール", S["t3_m2d"]),
            ui.kpi_card(S["t3_m3"], f"{len(df_umap):,} reviews", S["t3_m3d"]),
            cls="cols-3 bp-kpis"),

        ui.panel_header(S["t3_lp"], S["t3_lpd"]),
        *_launch_panel(lang, d),

        ui.panel_header(S["t3_p2"], S["t3_p2d"]),
        ui.chart_head(S["t3_bch"], S["t3_bce"]),
        ui.pills("dc-bc-window", list(windows.items()), "recent", label="Window"),
        ui.graph("dc-fig-bc", figures.fig_blockc(df_bc, "recent", S)),
        html.Div(blockc_prompt(), id="dc-bc-detail"),
        ui.legend([("Korean brands", C["korean"]), ("Ingredients", C["skin"]),
                   ("Other", C["ingr"])]),
        html.Div(finding_f4("recent", S), id="dc-f4"),

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


@callback(Output("dc-fig-l5", "figure"), Input("dc-launch-ing", "value"),
          State("dc-lang", "data"), prevent_initial_call=True)
def _launch_ingredient(canon, lang):
    return ui.themed(figures.fig_launch_vs_search(D.LAUNCH, D.frame("ingredient_surge"), canon,
                                                  D.S[lang]))


@callback(Output("dc-fig-bc", "figure"), Input("dc-bc-window", "value"),
          State("dc-lang", "data"), prevent_initial_call=True)
def _blockc(window_key, lang):
    return ui.themed(figures.fig_blockc(D.frame("blockc"), window_key or "recent", D.S[lang]))


@callback(Output("dc-f4", "children"), Input("dc-bc-window", "value"),
          State("dc-lang", "data"), prevent_initial_call=True)
def _blockc_finding(window_key, lang):
    return finding_f4(window_key or "recent", D.S[lang])


@callback(Output("dc-bc-sel", "data"),
          Input("dc-fig-bc", "clickData"), Input("dc-bc-window", "value"),
          State("dc-bc-sel", "data"), prevent_initial_call=True)
def _select_search(click, _window, current):
    """Clicking a tile selects it, clicking it again clears it. A window switch
    clears it too: the other window's treemap may not hold that search."""
    if ctx.triggered_id == "dc-bc-window":
        return None
    label = ui.clicked_label(click)
    if label is None:
        return no_update
    return None if label == current else label


@callback(Output("dc-bc-detail", "children"), Input("dc-bc-sel", "data"),
          State("dc-bc-window", "value"), State("dc-lang", "data"), prevent_initial_call=True)
def _search_detail(root, window_key, lang):
    row = (figures.blockc_detail(D.frame("blockc"), window_key or "recent", root)
           if root else None)
    if row is None:
        return blockc_prompt()
    sig = figures.blockc_signal_labels(D.S[lang]).get(row["signal_type"], "Other")
    return ui.blockc_panel(row, sig, figures.SIG_COLORS.get(row["signal_type"], C["ingr"]))


@callback(Output("dc-fig-umap", "figure"), Input("dc-umap-year", "value"),
          State("dc-lang", "data"), prevent_initial_call=True)
def _umap(year_filter, lang):
    return ui.themed(figures.fig_umap(D.frame("umap"), year_filter or "all", D.S[lang]))


@callback(Output("dc-umap-count", "children"), Input("dc-umap-year", "value"),
          prevent_initial_call=True)
def _umap_count(year_filter):
    return umap_count_caption(D.frame("umap"), year_filter or "all")
