"""Every chart builder returns a figure that survives a JSON round trip.

bp/figures.py builds each Plotly figure the dashboard shows, for whichever
frontend calls it. Each builder runs here in both languages with its default
controls, on the shipped assets, and a builder added without a case fails.
"""

import json

import plotly.graph_objects as go
import plotly.io as pio
import pytest

from bp import data, figures, strings

A = data.ASSETS
BUILDERS = sorted(n for n in vars(figures) if n.startswith("fig_"))
LAUNCH_BUILDERS = {n for n in BUILDERS if n.startswith("fig_launch_")}


@pytest.fixture(scope="module")
def launch():
    return data.compute_launch_headline(A)


@pytest.fixture(scope="module")
def frames():
    df_grp, px_kg = data.load_meti_monthly(A)
    val_all, _ = data.load_meti_annual(A)
    return dict(
        cross=data.load_trends_crossover(A), mk=data.load_makeup_rebound(A),
        ing=data.load_ingredient_surge(A), sku=data.load_sku_treemap(A),
        yt_vol=data.load_yt_volume(A), grp=df_grp, px_kg=px_kg, val_all=val_all,
        att=data.load_attention_annual(A), curve=data.load_cosine_sizecurve(A),
        bc=data.load_blockc(A), ch=data.load_yt_channels(A), tfidf=data.load_yt_tfidf(A),
        umap=data.load_umap(A))


def cases(f, H, L, lang, S):
    """Builder name -> the figures it draws with default controls."""
    return {
        "fig_trends_crossover": lambda: [figures.fig_trends_crossover(
            f["cross"], figures.crossover_bounds(f["cross"]), lang)],
        "fig_makeup_rebound": lambda: [figures.fig_makeup_rebound(f["mk"], lang)],
        "fig_ingredient_surge": lambda: [figures.fig_ingredient_surge(
            f["ing"], figures.ingredient_default())],
        "fig_sku_treemap": lambda: [figures.fig_sku_treemap(
            f["sku"], next(iter(figures.lens_options(S))))],
        "fig_yt_volume": lambda: [figures.fig_yt_volume(f["yt_vol"])],
        "fig_meti_groups": lambda: [figures.fig_meti_groups(f["grp"], H, lang)],
        "fig_meti_price_per_kg": lambda: [figures.fig_meti_price_per_kg(f["px_kg"], H, lang)],
        "fig_search_vs_value": lambda: [figures.fig_search_vs_value(
            f["val_all"], f["att"], H, period, lang, S) for period in ("pre", "post")],
        "fig_cosine_sizecurve": lambda: [figures.fig_cosine_sizecurve(f["curve"], H)],
        "fig_launch_groups": lambda: [figures.fig_launch_groups(L, S)],
        "fig_launch_categories": lambda: [figures.fig_launch_categories(L, lang, S)],
        "fig_launch_roster": lambda: [figures.fig_launch_roster(L, S)],
        "fig_launch_ingredients": lambda: [figures.fig_launch_ingredients(L, lang, S)],
        "fig_launch_vs_search": lambda: [figures.fig_launch_vs_search(
            L, f["ing"], figures.launch_ingredient_options(L)[0], S)],
        "fig_blockc": lambda: [figures.fig_blockc(
            f["bc"], next(iter(figures.blockc_window_options(S))), S)],
        "fig_yt_channels": lambda: [figures.fig_yt_channels(f["ch"])],
        "fig_yt_tfidf": lambda: [figures.fig_yt_tfidf(f["tfidf"], S)],
        "fig_umap": lambda: [figures.fig_umap(f["umap"], figures.umap_year_options()[0], S)],
    }


@pytest.mark.parametrize("lang", ["en", "jp"])
@pytest.mark.parametrize("name", BUILDERS)
def test_builder_returns_a_figure_that_round_trips(name, lang, headline, launch, frames):
    if name in LAUNCH_BUILDERS and launch is None:
        pytest.skip("launch export not built")
    S = strings.build_strings(lang, headline, launch, A)
    table = cases(frames, headline, launch, lang, S)
    assert name in table, f"{name} has no case in tests/test_figures.py"
    for fig in table[name]():
        assert isinstance(fig, go.Figure)
        spec = fig.to_json()
        # Rebuilding reorders layout keys, so compare the parsed JSON.
        assert json.loads(pio.from_json(spec).to_json()) == json.loads(spec)


@pytest.mark.parametrize("name", BUILDERS)
def test_builder_leaves_the_template_to_the_frontend(name, headline, launch, frames):
    """A builder sets no template: Streamlit's own applies to what it draws,
    and the Dash app sets bp.theme.TEMPLATE itself (dashboard/ui.py)."""
    if name in LAUNCH_BUILDERS and launch is None:
        pytest.skip("launch export not built")
    S = strings.build_strings("en", headline, launch, A)
    default = pio.templates[pio.templates.default].to_plotly_json()
    for fig in cases(frames, headline, launch, "en", S)[name]():
        assert fig.layout.template.to_plotly_json() == default
