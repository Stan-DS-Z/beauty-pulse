"""The Supply page: its figures, the directions its copy states, and the page.

The Supply copy says gained, lost, rose, held, from … to and ran from … to,
and the data decides each. These tests hold the data to every direction the
copy states, so a refresh that turns one fails here and the sentence is
rewritten for the new edition instead of shipping wrong.
"""

import json
import re

import pandas as pd
import pytest

from bp import brief, data, sources, strings, supply
from test_brief import EMOJI, _assets_copy

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads


@pytest.fixture(scope="module")
def M():
    m = supply.compute_supply(E, sources.CUTOFF)
    if m is None:
        pytest.skip("launch export not built")
    return m


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, None, None, M)


# ── The directions the copy states ──────────────────────────────────────────

def test_the_share_title_holds(M):
    SH = M["share"]
    d = SH["rows"]["launch_d"].dropna()
    assert SH["gainers"] == list(d.nlargest(2).index)
    assert SH["gain_lo"] > 0                                             # "gained"
    assert SH["loss"] < 0 and SH["loser"] == d.idxmin()                  # "lost"


def test_the_share_and_origin_figures_are_the_briefs(M, headline):
    B = brief.compute_brief(E, headline, sources.CUTOFF)["supply"]
    SH, O = M["share"], M["origin"]
    assert (SH["gainers"], SH["loser"]) == (B["gainers"], B["loser"])
    assert (SH["gain_lo"], SH["gain_hi"], SH["loss"]) == (B["gain_lo"], B["gain_hi"], B["loss"])
    assert (O["first"], O["last"]) == (B["h_first"], B["h_last"])
    assert (O["kr_first"], O["kr_last"]) == (B["kr_first"], B["kr_last"])


def test_the_origin_title_holds_on_complete_half_years(M):
    O = M["origin"]
    (k0, t0), (k1, t1) = O["kr_first"], O["kr_last"]
    assert k1 / t1 > k0 / t0                                             # "from … to"
    months = pd.Series(data.compute_launch_headline(E, sources.CUTOFF)["months"])
    per_half = months.map(brief._half).value_counts()
    assert all(per_half[h] == 6 for h in O["shares"].index)
    assert (O["total"] == O["counts"].sum(axis=1)).all()
    assert int(O["issuers"].sum()) == M["n_core"]                        # "13 Korean, 10 Japanese …"


def test_the_group_title_holds(M):
    G = M["groups"]
    l12, p12 = G["l12"], G["p12"]
    assert not strings._held(l12["skincare"], p12["skincare"])
    assert l12["skincare"] > p12["skincare"]                             # "rose"
    assert strings._held(l12["makeup"], p12["makeup"])                   # "held"
    assert (G["roll"].iloc[-1] == l12).all()                             # the lines end on the title's totals


def test_the_ingredient_title_holds(M):
    I = M["ingredients"]
    top = I["frame"].loc[I["top"]]
    assert top["s_l12"] > top["s_p12"]                                   # "from … a year earlier"
    assert 0 < I["any_n"] <= I["den_l12"]


# ── Order and colour ────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_ingredients_are_never_ranked(M, headline, REG, lang):
    """The ingredient chart lists them alphabetically (五十音 in Japanese),
    never by share."""
    S = _S(lang, headline, M, REG)
    order = S["sp_ing_order"]
    assert set(order) == set(M["ingredients"]["frame"].index)
    names = [S["sp_ing"][k] for k in order]
    if lang == "en":
        assert [n.lower() for n in names] == sorted(n.lower() for n in names)
    else:
        assert order == sorted(order, key=lambda k: strings._kana_key(k, S["sp_ing"][k]))


def test_the_japanese_ingredient_order_reads_pdrn_as_katakana(M, headline, REG):
    order = _S("jp", headline, M, REG)["sp_ing_order"]
    assert order.index("アスコルビン酸") < order.index("DNA-Na") < order.index("ペプチド")


def _filled(fig):
    """A dumbbell chart's later-year marks: the second marker trace that
    carries data (the first is the hollow earlier-year marks)."""
    return [t for t in fig.data if t.mode == "markers" and t.x[0] is not None][1]


def test_each_category_origin_and_ingredient_is_drawn_in_its_colour(M, headline, REG):
    """Categories in their side's colour, origins in theme.ORIGIN, the other
    launch groups grey, ingredients green; every chart carries a legend."""
    from bp import figures
    from bp.theme import C, CONTEXT, ORIGIN, SIDE
    S = _S("en", headline, M, REG)
    SH = M["share"]
    fig = figures.fig_supply_share(M, S)
    name_side = {S["sp_cat"][k]: g for k, g in SH["rows"]["group"].items()}
    filled = _filled(fig)
    for y, col in zip(filled.y, filled.marker.color):
        assert col == SIDE[name_side[y]], y
    assert fig.layout.showlegend

    fig = figures.fig_supply_origin(M, S)
    assert {t.name: t.marker.color for t in fig.data} == {
        S["sp_origin"][o]: ORIGIN[o] for o in M["origin"]["counts"].columns}
    assert fig.layout.showlegend

    fig = figures.fig_supply_groups(M, S)
    colours = {t.name: t.line.color for t in fig.data}
    assert colours[S["sp_group"]["skincare"]] == C["skin"]
    assert colours[S["sp_group"]["makeup"]] == C["cosm"]
    assert {colours[S["sp_group"][g]] for g in ("other", "none")} == {CONTEXT}
    assert fig.layout.showlegend

    fig = figures.fig_supply_ingredients(M, S)
    assert set(_filled(fig).marker.color) == {C["ingr"]}
    assert fig.layout.showlegend


# ── The edition cut-off ─────────────────────────────────────────────────────

def test_no_supply_figure_uses_data_past_the_cut_off(tmp_path):
    cut = sources.CUTOFF
    base_dir = _assets_copy(tmp_path / "base", future=False)
    fut_dir = _assets_copy(tmp_path / "future", future=True)
    base = supply.compute_supply(base_dir, cut)
    fut = supply.compute_supply(fut_dir, cut)
    for key in ("share", "origin", "groups", "ingredients"):
        for k, v in base[key].items():
            if isinstance(v, (pd.DataFrame, pd.Series)):
                (pd.testing.assert_frame_equal if isinstance(v, pd.DataFrame)
                 else pd.testing.assert_series_equal)(v, fut[key][k])
            else:
                assert v == fut[key][k], (key, k)
    for key in ("window", "l12", "p12", "last", "tot_l12", "tot_p12"):
        assert base[key] == fut[key], key
    for lang in ("en", "jp"):
        assert (strings.supply_strings(lang, base, sources.build_registry(base_dir, cut))
                == strings.supply_strings(lang, fut, sources.build_registry(fut_dir, cut)))


def test_the_page_carries_the_frozen_edition(M):
    import data_cache
    d = data_cache.load()
    pd.testing.assert_frame_equal(d.SUPPLY["share"]["rows"], M["share"]["rows"])
    pd.testing.assert_frame_equal(d.SUPPLY["origin"]["counts"], M["origin"]["counts"])
    assert d.SUPPLY["tot_l12"] == M["tot_l12"]


# ── Copy ────────────────────────────────────────────────────────────────────

_LOOKUPS = ("sp_en", "sp_cat", "sp_origin", "sp_half", "sp_group", "sp_ing",
            "sp_ing_order", "sp_win_l12", "sp_win_p12", "sp_kicker")


def _flat(v):
    if isinstance(v, dict):
        return " ".join(_flat(x) for x in v.values())
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def _copy(S):
    return " ".join(_flat(S[k]) for k in S if k.startswith("sp_") and k not in _LOOKUPS)


def test_the_japanese_supply_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("sp_")]
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
    assert S["sp_src_prtimes"] == sources.source_line(["prtimes"], REG, code)


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_launch_shares_in_titles_carry_their_counts(M, headline, REG, lang):
    """A share in a launch title carries its count: '49% (141 of 289)'."""
    S = _S(lang, headline, M, REG)
    of = r"\d+ of \d+" if lang == "en" else r"\d+件中\d+件"
    for k in ("sp_s_h", "sp_o_h", "sp_i_h"):
        assert re.search(of, S[k]), k


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_publishes_no_rakuten_ratio_and_names_no_removal(M, headline, REG, lang):
    text = _copy(_S(lang, headline, M, REG)).lower()
    for tell in ("×", "ratio", "shelf", "lists", "sells", "倍",
                 "this page", "this tab", "here", "withdrawn", "no longer", "previously",
                 "このタブ", "このページ", "撤回", "以前"):
        assert tell not in text, tell


def test_the_brief_links_its_supply_finding_to_the_page():
    assert strings.BRIEF_LINKS["supply"] == ("/supply", "nav_supply")


# ── The page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_json():
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/supply")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_shows_no_multiplier_and_no_rakuten_data(page_json):
    """No Rakuten SKU ratio is published (METHODOLOGY Revision 11), and no
    Rakuten exhibit is in this edition: its snapshot postdates the cut-off
    (Revision 18)."""
    for lang, js in page_json.items():
        assert not re.search(r"\d+\.\d+\s*[x×倍]", js), lang
        assert "Rakuten" not in js and "楽天" not in js, lang


def test_the_page_has_no_emoji_tile_or_rimmed_card(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js, lang
        assert "bp-figs" in js, lang
