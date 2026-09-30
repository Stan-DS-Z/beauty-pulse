"""Every chart builder returns a figure that survives a JSON round trip.

bp/figures.py builds each Plotly figure the dashboard shows, for whichever
frontend calls it. Each builder runs here in both languages with its default
controls, on the shipped assets, and a builder added without a case fails.
"""

import json

import plotly.graph_objects as go
import plotly.io as pio
import pytest

from bp import brief, consumer, data, demand, figures, market, sources, strings, supply

A = data.ASSETS
BUILDERS = sorted(n for n in vars(figures) if n.startswith("fig_"))
# The Brief rests on the launch export as much as the Supply page does.
LAUNCH_BUILDERS = {n for n in BUILDERS if n.startswith(("fig_supply_", "fig_brief_"))}


@pytest.fixture(scope="module")
def launch():
    return data.compute_launch_headline(A)


@pytest.fixture(scope="module")
def frames():
    df_grp, _ = data.load_meti_monthly(A)
    return dict(grp=df_grp)


def cases(f, H, L, lang, S, B=None, M=None, DM=None, SP=None, CS=None):
    """Builder name -> the figures it draws with default controls."""
    return {
        "fig_meti_groups": lambda: [figures.fig_meti_groups(f["grp"], H, lang)],
        "fig_brief_portfolio": lambda: [figures.fig_brief_portfolio(B, S)],
        "fig_brief_actives": lambda: [figures.fig_brief_actives(B, S)],
        "fig_market_lines": lambda: [figures.fig_market_lines(M, S)],
        "fig_market_bridge": lambda: [figures.fig_market_bridge(M, S)],
        "fig_market_imports": lambda: [figures.fig_market_imports(M, S)],
        "fig_demand_change": lambda: [figures.fig_demand_change(DM, S)],
        "fig_demand_pair": lambda: [figures.fig_demand_pair(DM, S)],
        "fig_demand_ingredients": lambda: [figures.fig_demand_ingredients(DM, S)],
        "fig_demand_makeup": lambda: [figures.fig_demand_makeup(DM, S)],
        "fig_supply_share": lambda: [figures.fig_supply_share(SP, S)],
        "fig_supply_origin": lambda: [figures.fig_supply_origin(SP, S)],
        "fig_supply_groups": lambda: [figures.fig_supply_groups(SP, S)],
        "fig_supply_ingredients": lambda: [figures.fig_supply_ingredients(SP, S)],
        "fig_consumer_curve": lambda: [figures.fig_consumer_curve(CS, S)],
        "fig_consumer_map": lambda: [figures.fig_consumer_map(CS, S)],
    }


@pytest.mark.parametrize("lang", ["en", "jp"])
@pytest.mark.parametrize("name", BUILDERS)
def test_builder_returns_a_figure_that_round_trips(name, lang, headline, launch, frames):
    if name in LAUNCH_BUILDERS and launch is None:
        pytest.skip("launch export not built")
    B = brief.compute_brief(A, headline, sources.CUTOFF)
    M = market.compute_market(A, sources.CUTOFF)
    DM = demand.compute_demand(A, sources.CUTOFF)
    SP = supply.compute_supply(A, sources.CUTOFF)
    CS = consumer.compute_consumer(A)
    S = strings.build_strings(lang, headline, launch, A, B, sources.build_registry(A), M, DM, SP,
                              CS)
    table = cases(frames, headline, launch, lang, S, B, M, DM, SP, CS)
    assert name in table, f"{name} has no case in tests/test_figures.py"
    for fig in table[name]():
        assert isinstance(fig, go.Figure)
        spec = fig.to_json()
        # Rebuilding reorders layout keys, so compare the parsed JSON.
        assert json.loads(pio.from_json(spec).to_json()) == json.loads(spec)


@pytest.mark.parametrize("name", BUILDERS)
def test_builder_leaves_the_template_to_the_frontend(name, headline, launch, frames):
    """A builder sets no template: the Dash app sets bp.theme.TEMPLATE on
    every figure itself (dashboard/ui.py), so it is set in one place."""
    if name in LAUNCH_BUILDERS and launch is None:
        pytest.skip("launch export not built")
    B = brief.compute_brief(A, headline, sources.CUTOFF)
    M = market.compute_market(A, sources.CUTOFF)
    DM = demand.compute_demand(A, sources.CUTOFF)
    SP = supply.compute_supply(A, sources.CUTOFF)
    CS = consumer.compute_consumer(A)
    S = strings.build_strings("en", headline, launch, A, B, sources.build_registry(A), M, DM, SP,
                              CS)
    default = pio.templates[pio.templates.default].to_plotly_json()
    for fig in cases(frames, headline, launch, "en", S, B, M, DM, SP, CS)[name]():
        assert fig.layout.template.to_plotly_json() == default
