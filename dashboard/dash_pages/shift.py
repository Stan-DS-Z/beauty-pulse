"""The shift: attention, market, and the two measured side by side."""

import dash
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

import data_cache
import ui
from bp import figures, strings
from bp.theme import C

PATH = "/shift"
dash.register_page(__name__, path=PATH, name="The shift", order=0,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _months(df_cross):
    """The slider's stops: every month in the Trends asset, in order."""
    return sorted(df_cross["week_start"].unique())


def _date_range(df_cross, lo, hi):
    """What the Streamlit slider hands the builder: two datetimes."""
    m = _months(df_cross)
    return (m[lo].to_pydatetime(), m[hi].to_pydatetime())


def _kr_text(kr, lang):
    if lang == "en":
        return (f"  — {int(kr['sku_count']):,} SKUs · "
                f"{kr['avg_reviews']:.1f} reviews per SKU, against {kr['all_rps']:.1f} "
                f"across all categories · ¥{int(kr['med_price']):,} median price")
    return (f"  — {int(kr['sku_count']):,} SKU · "
            f"SKUあたりレビュー{kr['avg_reviews']:.1f}件（全カテゴリ平均{kr['all_rps']:.1f}件） · "
            f"価格中央値 ¥{int(kr['med_price']):,}")


def _rak_prompt(lang):
    return ui.caption("Click any tile to see category detail" if lang == "en"
                      else "タイルをクリックするとカテゴリの詳細を表示")


def build(lang, d):
    S, H = d.S[lang], d.HEADLINE
    _mon_en = strings._MON_EN

    df_cross = d.frame("trends_crossover")
    months = _months(df_cross)
    last = len(months) - 1
    df_ing = d.frame("ingredient_surge")
    df_sku = d.frame("sku_treemap")
    lens = figures.lens_options(S)
    lens0 = next(iter(lens))
    df_grp, px_kg_m = d.frame("meti_monthly")
    val_all, _ = d.frame("meti_annual")
    att = d.frame("attention_annual")

    sub3 = (f"95% CI {H['sku_lo']}–{H['sku_hi']} · "
            f"{H['sku_span_lo']}–{H['sku_span_hi']} across genre treatments"
            if lang == "en" else
            f"95%CI {H['sku_lo']}〜{H['sku_hi']} · "
            f"ジャンル処理により{H['sku_span_lo']}〜{H['sku_span_hi']}倍")

    kr = figures.korean_callout(df_sku)
    kr_note = (ui.note("Korean cosmetics" if lang == "en" else "韓国コスメ",
                       _kr_text(kr, lang), "korean") if kr is not None else None)

    try:
        df_yt_vol = d.frame("yt_volume")
        yt_block = [
            ui.graph("sh-fig5", figures.fig_yt_volume(df_yt_vol)),
            ui.caption(S["t1_c5cap"].format(**figures.yt_volume_counts(df_yt_vol))),
        ]
    except FileNotFoundError:
        yt_block = [ui.info("nb07_yt_volume.csv not found — run the NB07 YouTube "
                            "export cells to generate it.")]

    m2_cap = (f"Monthly, January 2019 – {_mon_en[H['ytd_m']]} {H['ytd_y']} · solid = the three "
              "lines with the step · dotted = comparison lines · log scale: equal vertical "
              "distance = equal percentage change"
              if lang == "en" else
              f"月次、2019年1月〜{H['ytd_y']}年{H['ytd_m']}月 · 実線＝段差のある3品目 · "
              "点線＝比較品目 · 対数軸：縦方向の同じ距離＝同じ変化率")

    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        dcc.Store(id="sh-lang", data=lang),
        dcc.Store(id="sh-rak-sel", data=None),
        ui.header(S, lang, PATH),
        ui.intro(S["t1_intro"]),
        ui.row(
            ui.kpi_card(S["t1_m1"], f"{H['cosm_decline']}%", S["t1_m1d"], arrow=None),
            ui.kpi_card(S["t1_m2"], f"{H['nia_pre']} → {H['nia_post']}", S["t1_m2d"]),
            ui.kpi_card(S["t1_m3"], f"{H['sku_measured']}x", sub3),
            ui.kpi_card(S["t1_m4"], f"{H['found_d']}%", S["t1_m4d"], arrow=None),
            cls="cols-4 bp-kpis"),

        ui.panel_header(S["t1_p1"], S["t1_p1d"]),
        ui.chart_head(S["t1_c1h"], S["t1_c1e"]),
        html.Div(className="bp-control bp-slider", children=dcc.RangeSlider(
            id="sh-crossover", min=0, max=last, step=1, value=[0, last], allowCross=False,
            allow_direct_input=False,
            marks={i: m.strftime("%Y-%m") for i, m in enumerate(months)
                   if m.month == 1 or i == last})),
        ui.graph("sh-fig1", figures.fig_trends_crossover(
            df_cross, figures.crossover_bounds(df_cross), lang)),
        ui.chart_head(S["t1_c4h"], S["t1_c4e"]),
        ui.graph("sh-fig1b", figures.fig_makeup_rebound(d.frame("makeup_rebound"), lang)),
        ui.caption(S["t1_c4cap"]),
        ui.finding(S["f1b_title"], S["f1b_body"], "cosm"),

        ui.row(
            html.Div([
                ui.chart_head(S["t1_c2h"], S["t1_c2e"]),
                html.Div(className="bp-control", children=[
                    html.Label(S["t1_ingr_sel"], className="bp-control-label"),
                    dcc.Dropdown(id="sh-ingr", options=figures.ingredient_options(df_ing),
                                 value=figures.ingredient_default(), multi=True),
                ]),
                ui.graph("sh-fig2", figures.fig_ingredient_surge(
                    df_ing, figures.ingredient_default())),
                ui.caption(S["t1_c2cap"]),
            ]),
            html.Div([
                ui.chart_head(S["t1_c3h"], S["t1_c3e"]),
                html.Div(className="bp-control", children=[
                    html.Label(S["t1_lens"], className="bp-control-label"),
                    dcc.RadioItems(id="sh-lens", value=lens0, inline=True,
                                   options=[{"label": lab, "value": k} for k, lab in lens.items()],
                                   className="bp-radio"),
                ]),
                ui.graph("sh-fig3", figures.fig_sku_treemap(df_sku, lens0)),
                html.Div(className="bp-detail-row", children=[
                    html.Div(_rak_prompt(lang), id="sh-rak-detail", className="bp-detail-slot"),
                    html.Button("✕", id="sh-rak-clear", n_clicks=0, className="bp-clear hidden"),
                ]),
                kr_note,
            ]),
        ),

        ui.chart_head(S["t1_c5h"], S["t1_c5e"]),
        *yt_block,

        ui.panel_header(S["t1_p2"], S["t1_p2d"]),
        ui.chart_head(S["t1_mkh"], S["t1_mke"]),
        ui.graph("sh-figM1", figures.fig_meti_groups(df_grp, H, lang)),
        ui.caption(S["t1_mkcap"]),
        ui.chart_head(S["t1_brkh"]),
        ui.graph("sh-figM2", figures.fig_meti_price_per_kg(px_kg_m, H, lang)),
        ui.caption(m2_cap),
        ui.finding(S["t1_brkh"], S["t1_brkb"], "cosm"),
        ui.footnote(S["t1_brkfnh"], S["t1_brkfn"]),

        ui.panel_header(S["t1_p3"], S["t1_p3d"]),
        ui.chart_head(S["t1_dvh"], S["t1_dve"]),
        ui.row(*[ui.graph(f"sh-figD-{period}",
                          figures.fig_search_vs_value(val_all, att, H, period, lang, S))
                 for period in ("pre", "post")]),
        ui.finding(S["f1_title"], S["f1_body"], "skin"),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]


@callback(Output("sh-fig1", "figure"), Input("sh-crossover", "value"),
          State("sh-lang", "data"), prevent_initial_call=True)
def _crossover(value, lang):
    df = D.frame("trends_crossover")
    return figures.fig_trends_crossover(df, _date_range(df, value[0], value[1]), lang)


@callback(Output("sh-fig2", "figure"), Input("sh-ingr", "value"),
          State("sh-lang", "data"), prevent_initial_call=True)
def _ingredients(selected, lang):
    return figures.fig_ingredient_surge(D.frame("ingredient_surge"), selected or [])


@callback(Output("sh-fig3", "figure"), Input("sh-lens", "value"),
          State("sh-lang", "data"), prevent_initial_call=True)
def _lens(color_col, lang):
    return figures.fig_sku_treemap(D.frame("sku_treemap"), color_col)


@callback(Output("sh-rak-sel", "data"),
          Input("sh-fig3", "clickData"), Input("sh-rak-clear", "n_clicks"),
          State("sh-rak-sel", "data"), prevent_initial_call=True)
def _select_tile(click, _clear, current):
    """Clicking a tile selects it; clicking it again, or the ✕, clears it."""
    if ctx.triggered_id == "sh-rak-clear":
        return None
    label = ui.clicked_label(click)
    if label is None:
        return no_update
    return None if label == current else label


@callback(Output("sh-rak-detail", "children"), Output("sh-rak-clear", "className"),
          Input("sh-rak-sel", "data"), State("sh-lang", "data"), prevent_initial_call=True)
def _tile_detail(label, lang):
    row = figures.sku_detail(D.frame("sku_treemap"), label) if label else None
    if row is None:
        return _rak_prompt(lang), "bp-clear hidden"
    colour = C["skin"] if row["tier_group"] == "skincare" else C["cosm"]
    return ui.sku_panel(row, colour), "bp-clear"
