"""The Timing page: its figures, the directions its copy states, and the page.

The copy names peak runs, a count of stable lines, the search terms with a
season and the launch test's result; the data decides each, so a rebuilt
edition that turns one fails here instead of shipping wrong.
"""

import json
import re

import pytest

from bp import data, seasonal, sources, strings, timing
from test_brief import EMOJI

A = data.ASSETS
E = sources.edition_assets(A)


@pytest.fixture(scope="module")
def M():
    return timing.compute_timing(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, None, None, None, None, M)


# ── The directions the copy states ──────────────────────────────────────────

def test_sunscreen_search_follows_shipments_by_the_same_offset_every_year(M):
    sun = M["sun"]
    for y in seasonal.FULL_YEARS:
        assert sun["search"]["year_runs"][y] == sun["search"]["run"]
        assert sun["ship"]["year_runs"][y] == sun["ship"]["run"]
    assert set(sun["offset"].values()) == {3}


def test_the_band_holds_the_average(M):
    for key in ("search", "ship"):
        st = M["sun"][key]
        assert (st["band"]["lo"] <= st["profile"] + 1e-9).all()
        assert (st["profile"] <= st["band"]["hi"] + 1e-9).all()


def test_the_heatmaps_are_ordered_by_peak_month(M):
    for g in (M["ship"], M["search"]):
        assert g["peak"].is_monotonic_increasing


def test_the_launch_title_counts_each_side(M):
    t = M["tests"].groupby("side")["even"].agg(["sum", "size"])
    assert (t.loc["makeup", "sum"], t.loc["skincare", "sum"]) == (4, 3)


def test_every_heatmap_row_has_a_name_in_both_languages(M, headline, REG):
    for lang in ("en", "jp"):
        S = _S(lang, headline, M, REG)
        assert set(S["tm_rows_ship"]) == set(M["ship"].index)
        assert set(S["tm_rows_search"]) == set(M["search"].index)


def test_the_counts_the_titles_state(M):
    assert int(M["ship"]["passes"].sum()) == 6 and len(M["ship"]) == 16
    assert set(M["search"].index[M["search"]["passes"]]) == {"日焼け止め", "乳液"}
    t = M["tests"]
    assert int(t["even"].sum()) == 7 and len(t) == 8


# ── The copy ────────────────────────────────────────────────────────────────

_LOOKUPS = ("tm_kicker", "tm_h_hover", "tm_l_side", "tm_l_hover", "tm_l_end",
            "tm_src_sun", "tm_src_meti", "tm_src_trends", "tm_src_prtimes", "tm_s_search",
            "tm_s_ship", "tm_rows_ship", "tm_rows_search", "tm_h_months", "tm_h2_swing")


def _flat(v):
    if isinstance(v, dict):
        return " ".join(_flat(x) for x in v.values())
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def test_the_japanese_timing_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("tm_")]
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
    assert S["tm_src_sun"] == sources.source_line(["trends", "meti"], REG, code)
    assert S["tm_src_prtimes"] == sources.source_line(["prtimes"], REG, code)


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_makes_no_causal_claim_and_names_no_page(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    text = " ".join(_flat(S[k]) for k in S if k.startswith("tm_") and k not in _LOOKUPS).lower()
    for tell in (r"\bdriver", r"\bbecause\b", r"\bahead of\b", r"\bdue to\b", r"\bcaused?\b",
                 r"\bthis page\b", r"\bhere\b", "要因", "ため、", "に先立", "このページ"):
        assert not re.search(tell, text), tell


# ── The page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_json():
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/timing")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_has_no_emoji_or_tile(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "bp-figs" in js, lang


def test_each_chart_carries_its_colours_and_a_key():
    """Sunscreen in its gold; each launch year in its side's colour, a
    different shade per year, with a legend; each heatmap on the blue scale."""
    import data_cache
    from bp import figures
    from bp.theme import C, _SEQ
    D = data_cache.load()
    S, T = D.S["en"], D.TIMING
    sun = figures.fig_timing_sun(T, S)
    assert {t.line.color for t in sun.data if t.mode == "lines+markers"} == {C["gold"]}
    assert sun.layout.showlegend
    launch = figures.fig_timing_launch(T, S)
    for side, axis in (("skincare", "y"), ("makeup", "y2")):
        shades = [t.line.color for t in launch.data if t.yaxis == axis]
        assert len(set(shades)) == len(shades) == len(T["counts"][side]), side
        assert C["skin" if side == "skincare" else "cosm"] in shades, side
    assert launch.layout.showlegend
    for fig in (figures.fig_timing_ship(T, S), figures.fig_timing_search(T, S)):
        heat = fig.data[0]
        assert [list(c) for c in heat.colorscale] == [list(c) for c in _SEQ]


def test_each_heatmap_has_its_colour_key_under_it(page_json):
    for lang, js in page_json.items():
        n = js.count("bp-scalekey-bar")
        assert n == 2, (lang, n)
