"""The Market page: its figures, the directions its copy states, and the page.

The Market copy says lead, grew, fell, rose, below and largest, and the data
decides each. These tests hold the data to every direction the copy states,
so a refresh that turns one fails here and the sentence is rewritten for the
new edition instead of shipping wrong.
"""

import json
import re

import pandas as pd
import pytest

from bp import data, market, sources, strings
from test_brief import EMOJI, _assets_copy

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads


@pytest.fixture(scope="module")
def M():
    return market.compute_market(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, M)


# ── The directions the copy states ──────────────────────────────────────────

def test_the_lead_lines_are_the_largest(M):
    rows = M["rows"]
    assert list(rows.index[:market.LEAD_LINES]) == M["lead"]          # "lead shipped value"
    assert list(rows["value_y1"]) == sorted(rows["value_y1"], reverse=True)


def test_the_bridge_title_holds(M):
    rows = M["rows"]
    # "grew through value per unit on fewer units"; the title names two, then three
    assert len(M["fewer_units"]) == market.FEWER_UNITS_NAMED
    assert len(M["by_units"]) == market.UNITS_NAMED
    for li in M["fewer_units"]:
        r = rows.loc[li]
        assert r["value_d"] > 0 and r["units_d"] < 0 and r["vpu_d"] > 0, li
    for li in M["by_units"]:                                           # "grew mostly through units"
        r = rows.loc[li]
        assert r["value_d"] > 0 and r["units_d"] > r["vpu_d"] and r["units_d"] > 0, li


def test_makeup_shipped_value_has_no_step_at_the_break(M):
    """The intro sets makeup against the base year because its shipped value
    rose across the break while the skincare lines stepped down."""
    y0 = M["window"][0]
    annual = M["monthly"].groupby(M["monthly"].index.year).sum()
    assert annual.loc[y0, "makeup"] > annual.loc[y0 - 1, "makeup"]


def test_the_import_title_holds(M):
    I = M["imports"]
    f = I["frame"]
    full = market.pd.read_csv(E / "estat_trade_hs3304.csv")
    imp = full[full["flow"] == "import"].groupby(["country", "year"])["value_1000jpy"].sum().unstack()
    for y in range(I["since"], I["y1"] + 1):                           # "largest … since"
        assert imp[y].idxmax() == I["leader"], y
    if I["since"] > I["y0"]:
        assert imp[I["since"] - 1].idxmax() != I["leader"]
    assert list(f.index[:2]) == [I["leader"], I["runner"]]
    assert f.loc[I["leader"], I["y1"]] == I["lead_y1"] > I["runner_y1"]


def test_the_break_footnote_holds(M):
    B = M["brk"]
    assert all(v < 0 for v in B["drop"].values())                       # "that price drops"
    for li in B["drop"]:
        assert B["jan"][li][2] < 0, li                                  # "shipped value fell"
    for li in market.BREAK_CONTROLS:
        assert B["jan"][li][2] > 0, li                                  # "while … rose"
    for li, (kg_d, val_d, ypk_d) in B["kg"].items():
        assert ypk_d < 0 and kg_d > 0 and val_d > 0, li                 # "also fall … rose … rose"
    for li, r in B["range"].items():
        assert not r["above"], li                                       # no line is above its range


def test_the_peak_caption_names_a_month_only_where_it_is_stable(M):
    """Makeup peaks in November in every full year of the seasonal window;
    skincare's highest month differs by year, so none is named."""
    from bp.seasonal import FULL_YEARS
    assert M["peaks"]["makeup"] == dict(month=11, years=list(FULL_YEARS))
    assert M["peaks"]["skincare"]["month"] is None


def test_no_skincare_yen_change_crosses_the_break(M, headline, REG):
    """Only makeup lines are set against the base year; every other change
    starts at the break."""
    fig = market_figures(M, _S("en", headline, M, REG))["lines"]
    base = str(M["base"])
    for li, extra in fig.data[0].customdata:
        crosses = base in extra
        assert crosses == (li in data.METI_MAKE), li
    assert M["window"][0] == data.METI_BREAK


def market_figures(M, S):
    from bp import figures
    return {"lines": figures.fig_market_lines(M, S), "bridge": figures.fig_market_bridge(M, S),
            "imports": figures.fig_market_imports(M, S)}


def test_each_exhibit_spends_its_one_accent_on_what_its_title_names(M, headline, REG):
    from bp.theme import C
    figs = market_figures(M, _S("en", headline, M, REG))
    bars = figs["lines"].data[0]
    ink = {li for li, col in zip(bars.customdata[:, 0], bars.marker.color) if col == C["ink"]}
    assert ink == set(M["lead"])
    lines = {t.name: t.line.color for t in figs["imports"].data}
    lead = strings.ORIGIN[M["imports"]["leader"]][0]
    assert [n for n, col in lines.items() if col == C["ink"]] == [lead]


# ── The edition cut-off ─────────────────────────────────────────────────────

def test_no_market_figure_uses_data_past_the_cut_off(tmp_path):
    cut = sources.CUTOFF
    base_dir = _assets_copy(tmp_path / "base", future=False)
    fut_dir = _assets_copy(tmp_path / "future", future=True)
    base = market.compute_market(base_dir, cut)
    fut = market.compute_market(fut_dir, cut)
    pd.testing.assert_frame_equal(base["rows"], fut["rows"])
    pd.testing.assert_frame_equal(base["monthly"], fut["monthly"])
    pd.testing.assert_frame_equal(base["imports"]["frame"], fut["imports"]["frame"])
    for key in ("keys", "ytd", "peaks", "brk", "lead", "fewer_units", "by_units", "last_month"):
        assert base[key] == fut[key], key
    for lang in ("en", "jp"):
        assert (strings.market_strings(lang, base, sources.build_registry(base_dir, cut))
                == strings.market_strings(lang, fut, sources.build_registry(fut_dir, cut)))


def test_the_page_carries_the_frozen_edition(M):
    import data_cache
    d = data_cache.load()
    pd.testing.assert_frame_equal(d.MARKET["rows"], M["rows"])
    assert d.MARKET["keys"] == M["keys"]


# ── Copy ────────────────────────────────────────────────────────────────────

_LOOKUPS = ("mk_en", "mk_line", "mk_origin", "mk_l_vs", "mk_l_hover", "mk_b_names", "mk_i_y",
            "mk_kicker")


def _flat(v):
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def test_the_japanese_market_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("mk_")]
    assert keys and all(k in ja for k in keys)
    num = re.compile(r"\d+(?:[.,]\d+)*")
    jp_chars = re.compile(r"[぀-ヿ一-鿿]")
    for k in keys:
        if k in _LOOKUPS:
            continue
        e, j = _flat(en[k]), _flat(ja[k])
        assert jp_chars.search(j), k
        assert set(num.findall(e)) <= set(num.findall(j)), (k, set(num.findall(e)) - set(num.findall(j)))


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_every_exhibit_carries_a_source_line_from_the_registry(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    code = "ja" if lang == "jp" else "en"
    assert S["mk_src_meti"] == sources.source_line(["meti"], REG, code)
    assert S["mk_src_trade"] == sources.source_line(["trade"], REG, code)


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_names_no_removal_and_no_page(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    text = " ".join(_flat(S[k]) for k in S if k.startswith("mk_") and k not in _LOOKUPS)
    for tell in ("this page", "this tab", "here", "withdrawn", "no longer", "previously",
                 "このタブ", "このページ", "撤回", "以前"):
        assert tell not in text.lower(), tell


# ── The page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_json():
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/market")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_has_no_emoji_tile_or_rimmed_card(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js, lang
        assert "bp-figs" in js, lang


def test_the_break_note_reads_the_market_figures():
    """The Market page words the break note from compute_market on the frozen
    edition, with one builder: no break figure is typed."""
    import data_cache
    d = data_cache.load()
    assert d.S["en"]["mk_fn_b"] == strings._break_note_en(d.MARKET)
    assert d.S["jp"]["mk_fn_b"] == strings._break_note_ja(d.MARKET)
    for li in market.BREAK_CONTROLS:                     # "rose" / "増加した"
        assert d.MARKET["brk"]["jan"][li][2] > 0, li
