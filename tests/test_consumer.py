"""The Consumer page: its figures, the directions its copy states, the review
map's asset, and the page.

@cosme and YouTube are within-side instruments (METHODOLOGY, Source roles).
The copy compares vocabulary at equal sample sizes and says rose, more,
sit together and all ten; these tests hold the data to each, so a rebuilt
asset that turns one fails here instead of shipping wrong.
"""

import json
import re

import pytest

from bp import consumer, data, sources, strings
from test_brief import EMOJI

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads


@pytest.fixture(scope="module")
def M():
    return consumer.compute_consumer(E)


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, None, None, None, M)


# ── The directions the copy states ──────────────────────────────────────────

def test_size_matched_vocabulary_converged_and_the_interval_excludes_zero(M):
    c = M["conv"]
    assert c["hi"] > c["lo"]
    assert c["delta"] == pytest.approx(c["hi"] - c["lo"], abs=0.0015)
    assert 0 < c["ci_lo"] < c["delta"] < c["ci_hi"]


def test_the_size_curve_rises_with_the_sample(M):
    cv = M["curve"].sort_values("sample_size")
    assert cv["cross_tier_cosine"].is_monotonic_increasing
    assert M["size"]["c1"] > M["size"]["c0"]


def test_the_term_lists_hold_the_count_the_title_states(M):
    L = M["vocab"]["lists"]
    assert len(L["cosme"]) == len(L["youtube"]) == M["vocab"]["top"]
    shared = set(L["cosme"]["term"]) & set(L["youtube"]["term"])
    assert len(shared) == M["vocab"]["shared"]
    for src in ("cosme", "youtube"):
        assert set(L[src].loc[L[src]["in_both"], "term"]) == shared


def test_phrase_reviews_sit_together_and_span_every_category(M):
    ph = M["phrase"]
    assert ph["nn_phrase"] > ph["nn_other"]
    assert ph["cats"] == ph["n_cats"]    # the copy says "all ten"


# ── The review map's asset ──────────────────────────────────────────────────

def test_the_review_map_covers_the_embedding_row_for_row():
    for where in (A, E):
        rm, emb = data.load_review_map(where), data.load_umap(where)
        assert rm["review_id"].is_unique
        assert set(rm["review_id"]) == set(emb["review_id"])
        assert set(rm["phrase"]) <= {0, 1}
        assert rm["nn_phrase"].between(0, 10).all()


def test_the_review_map_carries_no_text():
    rm = data.load_review_map(E)
    assert list(rm.columns) == ["review_id", "category", "phrase", "nn_phrase"]
    assert set(rm["category"]) <= set(strings.REVIEW_CAT)


def test_the_neighbour_counts_match_the_map():
    """nn_phrase is what build_review_map computed on this embedding: check a
    sample of reviews by brute force."""
    import numpy as np
    emb = data.load_umap(E).merge(data.load_review_map(E), on="review_id")
    xy, ph = emb[["umap_x", "umap_y"]].to_numpy(), emb["phrase"].to_numpy()
    for i in np.random.default_rng(0).choice(len(emb), 50, replace=False):
        d = np.hypot(*(xy - xy[i]).T)
        d[i] = np.inf
        near = np.argsort(d, kind="stable")[:10]
        # A tie at the tenth distance can pick either review.
        assert abs(ph[near].sum() - emb["nn_phrase"].iloc[i]) <= 1, i


# ── The copy ────────────────────────────────────────────────────────────────

_LOOKUPS = ("cs_en", "cs_cat", "cs_kicker", "cs_c_hover", "cs_m_hover", "cs_m_label",
            "cs_vcols", "cs_src_cosme", "cs_src_both")


def _flat(v):
    if isinstance(v, dict):
        return " ".join(_flat(x) for x in v.values())
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def test_the_japanese_consumer_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("cs_")]
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
    assert S["cs_src_cosme"] == sources.source_line(["cosme"], REG, code)
    assert S["cs_src_both"] == sources.source_line(["cosme", "youtube"], REG, code)


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_names_no_removal_no_page_and_no_campaign(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    text = " ".join(_flat(S[k]) for k in S if k.startswith("cs_") and k not in _LOOKUPS)
    for tell in ("this page", "this tab", "here", "withdrawn", "no longer", "previously",
                 "giveaway", "campaign", "このタブ", "このページ", "撤回", "以前", "キャンペーン"):
        assert tell not in text.lower(), tell


def test_the_brief_and_the_page_carry_the_same_convergence(M, headline):
    c = M["conv"]
    assert (headline["conv_lo"], headline["conv_hi"]) == (round(c["lo"], 3), round(c["hi"], 3))
    assert (headline["conv_p0"], headline["conv_p1"]) == (c["p0"], c["p1"])


# ── The page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_json():
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/consumer")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_has_no_emoji_tile_rimmed_card_or_control(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js and "bp-pill" not in js, lang
        assert "bp-figs" in js, lang


def test_the_map_uses_no_side_colour(page_json):
    """The map's title is about the phrases, not skincare against makeup: grey
    and ink only (the colour ruling)."""
    from bp.theme import C
    for lang, js in page_json.items():
        assert C["skin"] not in js and C["cosm"] not in js, lang
