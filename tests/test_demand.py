"""The Demand page: its figures, the directions its copy states, and the page.

The Demand copy says rose, fell, narrowed, above, below and lowest, and the
data decides each. These tests hold the data to every
direction the copy states, so a refresh that turns one fails here and the
sentence is rewritten for the new edition instead of shipping wrong.
"""

import json
import re

import pandas as pd
import pytest

from bp import brief, data, demand, sources, strings
from test_brief import EMOJI, _assets_copy

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads
SPREAD = brief.TRENDS_PULL_SPREAD


@pytest.fixture(scope="module")
def M():
    return demand.compute_demand(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, None, M)


# ── The directions the copy states ──────────────────────────────────────────

def test_the_change_title_and_note_hold(M):
    C, ch = M["changes"], M["change"]
    act = ch[ch["kind"] == "active"]
    assert C["n_actives"] == len(act) and C["n_rose"] == len(C["rose"]) >= 1
    assert all(ch.loc[t, "d"] >= SPREAD for t in C["rose"])            # "rose"
    assert C["rose_lo"] >= SPREAD
    assert all(ch.loc[t, "d"] <= -SPREAD for t in C["words_down"])     # "fell"
    assert C["words_down"], "the title counts the category words that fell"
    assert all(abs(ch.loc[t, "d"]) < SPREAD for t in C["within"])      # "moved less than that"
    assert all(ch.loc[t, "d"] >= SPREAD for t in C["words_up"])        # "serum rose"
    assert C["within"] and C["words_up"]


def test_the_key_figures_rise(M):
    for _, _, _, v0, v1 in M["keys"].values():
        assert v1 > v0


def test_the_pair_holds(M):
    P = M["pair"]
    assert P["cosm_d"] < 0                                               # "fell"
    assert P["above_every_year"]                                         # "above … in every year"
    assert P["gap_d"] < 0 and 0 < P["cosm_share"] <= 100                 # "narrowed … of it from the fall"


def test_the_makeup_note_holds(M):
    MK = M["makeup"]
    a, last, rel = MK["annual"], MK["last"], MK["relaxed"].year
    for t in ("口紅", "ファンデーション"):                                 # "rose in 2023 and fell in 2024 and 2025"
        assert a.loc[rel, t] > a.loc[rel - 1, t], t
        assert a.loc[last - 1, t] < a.loc[rel, t] and a.loc[last, t] < a.loc[last - 1, t], t
    mask = a.loc[list(demand.MASK_YEARS), "口紅"]
    assert a.loc[last, "口紅"] < mask.min()                             # "below its 2021 mean, the lowest"
    eye = a["アイシャドウ"]
    assert all(eye[y] > 100 for y in demand.MASK_YEARS)                 # "above its 2019 level in 2020–2022"
    assert eye[last - 1] < 100 and eye[last] < 100                      # "below it in 2024–2025"
    assert last - rel == 2                                               # "two years after"


# ── Order and colour ────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_actives_are_never_ranked(M, headline, REG, lang):
    """The change chart lists each group alphabetically (五十音 in Japanese),
    never by the size of its change."""
    S = _S(lang, headline, M, REG)
    kind = M["change"]["kind"]
    for g in strings.DEMAND_GROUPS:
        group = [t for t in S["dm_order"] if kind[t] == g]
        assert group == strings._sorted_terms(group, M, lang), g
        if lang == "en":
            names = [S["dm_term"][t].lower() for t in group]
            assert names == sorted(names), g


def test_the_japanese_order_is_gojuon():
    M_ = demand.compute_demand(E, sources.CUTOFF)
    words = [t for t in M_["change"].index if M_["change"].loc[t, "kind"] == "category"]
    got = strings._sorted_terms(words, M_, "jp")
    assert got.index("口紅") < got.index("洗顔") < got.index("乳液") < got.index("日焼け止め")


def test_each_term_is_drawn_in_its_own_colour_with_a_legend(M, headline, REG):
    """Actives green, umbrella terms charcoal, a category word its side's
    colour; each line its own colour; every chart with two or more series
    carries a legend."""
    from bp import figures
    from bp.funnel import CATEGORIES
    from bp.theme import C, CHARCOAL, SIDE
    S = _S("en", headline, M, REG)
    fig = figures.fig_demand_change(M, S)
    side = {t: g for _, _, t, g in CATEGORIES.values() if t}
    want = {"active": lambda t: C["ingr"], "umbrella": lambda t: CHARCOAL,
            "category": lambda t: SIDE[side[t]]}
    bars = fig.data[0]
    for t, col in zip(bars.customdata[:, 0], bars.marker.color):
        assert col == want[M["change"].loc[t, "kind"]](t), t
    assert fig.layout.showlegend
    pair = {t.name: t.line.color for t in figures.fig_demand_pair(M, S).data}
    assert pair == {S["dm_p_names"]["スキンケア"]: C["skin"], S["dm_p_names"]["化粧品"]: CHARCOAL}
    for fig, named, colour in (
            (figures.fig_demand_ingredients(M, S), S["dm_term"][demand.LONG_ACTIVE], C["ingr"]),
            (figures.fig_demand_makeup(M, S), S["dm_m_names"]["口紅"], C["cosm"])):
        lines = {t.name: t.line.color for t in fig.data}
        assert lines[named] == colour
        assert len(set(lines.values())) == len(lines)
        assert fig.layout.showlegend


# ── The edition cut-off ─────────────────────────────────────────────────────

def test_no_demand_figure_uses_data_past_the_cut_off(tmp_path):
    cut = sources.CUTOFF
    base_dir = _assets_copy(tmp_path / "base", future=False)
    fut_dir = _assets_copy(tmp_path / "future", future=True)
    base = demand.compute_demand(base_dir, cut)
    fut = demand.compute_demand(fut_dir, cut)
    for key in ("change", "ing", "cross"):
        pd.testing.assert_frame_equal(base[key], fut[key])
    pd.testing.assert_frame_equal(base["makeup"]["annual"], fut["makeup"]["annual"])
    for key in ("changes", "pair", "keys", "window"):
        assert base[key] == fut[key], key
    for lang in ("en", "jp"):
        assert (strings.demand_strings(lang, base, sources.build_registry(base_dir, cut))
                == strings.demand_strings(lang, fut, sources.build_registry(fut_dir, cut)))


def test_the_page_carries_the_frozen_edition(M):
    import data_cache
    d = data_cache.load()
    pd.testing.assert_frame_equal(d.DEMAND["change"], M["change"])
    assert d.DEMAND["pair"] == M["pair"]


# ── Copy ────────────────────────────────────────────────────────────────────

_LOOKUPS = ("dm_en", "dm_term", "dm_order", "dm_c_hover", "dm_p_names",
            "dm_m_names", "dm_c_groups", "dm_kicker")


def _flat(v):
    if isinstance(v, dict):
        return " ".join(_flat(x) for x in v.values())
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def test_the_japanese_demand_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("dm_")]
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
    assert S["dm_src_trends"] == sources.source_line(["trends"], REG, code)


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_names_no_removal_and_no_page(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    text = " ".join(_flat(S[k]) for k in S if k.startswith("dm_") and k not in _LOOKUPS)
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
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/demand")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_has_no_emoji_tile_or_rimmed_card(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js, lang
        assert "bp-figs" in js, lang
