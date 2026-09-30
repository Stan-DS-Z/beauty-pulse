"""The Method page: its figures, the directions its copy states, the sources
table against the registry, the review-vocabulary record, and the page.

Method restates figures other pages compute (Market's January 2022 step,
Timing's chi-square tests) and the edition's own record of the withdrawn
convergence (build_convergence.py). These tests hold each figure the copy
states to the data it came from, so a rebuilt asset that turns one fails here.
"""

import json
import re

import pandas as pd
import pytest

from bp import data, market, method, seasonal, sources, strings, timing
from test_brief import EMOJI

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads


@pytest.fixture(scope="module")
def REG():
    return sources.build_registry(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def MK():
    return market.compute_market(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def TM():
    return timing.compute_timing(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def M(MK, TM, REG):
    return method.compute_method(E, sources.CUTOFF, MK, TM, REG)


def _S(lang, headline, M, REG):
    return strings.build_strings(lang, headline, None, A, None, REG, None, None, None, None,
                                 None, M)


# ── The sources table ───────────────────────────────────────────────────────

def test_every_declared_source_has_one_row_in_order(M):
    assert [r["key"] for r in M["sources"]] == list(sources.DECLARED)


def test_report_pages_are_the_registry_pages_in_report_order(M, REG):
    for r in M["sources"]:
        used = REG[r["key"]].used_on
        assert r["pages"] == [p for p in sources.REPORT_PAGES if p in used], r["key"]


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_every_row_carries_its_registry_date_and_pages(M, REG, headline, lang):
    S = _S(lang, headline, M, REG)
    code = "ja" if lang == "jp" else "en"
    for r, (name, _, coverage, pages) in zip(M["sources"], S["me_s_rows"]):
        src = REG[r["key"]]
        assert name == src.name(code)
        if src.data_to is None:
            assert coverage == sources.data_to_label(src, code)
        else:
            assert sources.date_label(src.data_to, src.precision, code) in coverage, r["key"]
        for p in r["pages"]:
            assert strings.STRINGS[lang][f"nav_{p}"] in pages


def test_the_title_counts_the_sources_no_report_page_uses(M, REG):
    unused = [k for k, s in REG.items() if not set(s.used_on) & set(sources.REPORT_PAGES)]
    assert unused == [r["key"] for r in M["sources"] if not r["pages"]]
    assert set(unused) == set(strings._UNUSED)


def test_rakutens_snapshot_postdates_the_cut_off(REG):
    """The reason the table gives for Rakuten."""
    end = pd.Timestamp(sources.CUTOFF + "-01") + pd.offsets.MonthEnd(0)
    assert REG["rakuten"].data_to > end


def test_the_counts_come_from_the_edition(M, MK):
    c = {r["key"]: r["counts"] for r in M["sources"]}
    assert c["meti"]["lines"] == MK["keys"]["n_items"]
    feeds = pd.read_csv(E / "prtimes_feeds.csv")
    core = feeds[feeds["panel"] == "core"]
    assert (c["prtimes"]["feeds"], c["prtimes"]["issuers"]) == (len(core),
                                                               core["issuer_group"].nunique())
    umap = data.load_umap(E)
    assert c["cosme"]["reviews"] == len(umap) == len(data.load_review_map(E))
    yt = pd.read_csv(E / "nb07_yt_channels.csv")
    assert c["youtube"]["videos"] == yt["video_count"].sum()
    assert c["youtube"]["queries"] == M["youtube"].sum()


# ── Series breaks ───────────────────────────────────────────────────────────

def test_yen_per_kg_steps_down_for_the_lines_the_title_names(M):
    """The title's changes are Market's, and each is a fall; the chart's
    monthly lines sit lower in the year after the break than the year before."""
    P = M["price"]
    y0, f = P["year"], P["frame"]
    for li in P["lines"]:
        assert P["drop"][li] < 0, li
        before = f.loc[f.index.year == y0 - 1, li].mean()
        after = f.loc[f.index.year == y0, li].mean()
        assert after < before, li


def test_the_break_note_matches_markets_ranges(M, MK):
    assert M["price"]["pre"] == MK["brk"]["pre"]
    assert M["price"]["drop"] == MK["brk"]["drop"]


def test_the_trade_code_is_in_the_import_file_from_its_first_year(M):
    tr = pd.read_csv(E / "estat_trade_hs3304.csv", dtype={"hs_code": str})
    years = sorted(tr.loc[(tr["flow"] == "import") & (tr["hs_code"] == "330499010"), "year"].unique())
    T = M["trade"]
    assert years[0] == T["first"] and T["year"] in years
    assert 0 < T["share"] < 100


# ── The seasonal method and the launch test ─────────────────────────────────

def test_the_anchor_example_is_sunscreen_searchs_peak_run(M, TM):
    Z = M["seasonal"]
    prof = TM["sun"]["search"]["profile"]
    a, b = Z["sun_run"]
    assert (a, b) == tuple(TM["sun"]["search"]["run"])
    assert Z["sun_values"] == [float(prof[m]) for m in range(a, b + 1)]
    # The months cannot be ranked: they sit within the pull spread of each other.
    from bp.brief import TRENDS_PULL_SPREAD
    assert max(Z["sun_values"]) - min(Z["sun_values"]) < TRENDS_PULL_SPREAD


def test_the_rules_are_the_seasonal_modules(M):
    Z = M["seasonal"]
    assert (Z["window"], Z["years"], Z["tolerance"], Z["run"], Z["swing"], Z["crit"]) == (
        seasonal.RATIO_WINDOW, seasonal.FULL_YEARS, seasonal.PEAK_TOLERANCE, seasonal.PEAK_RUN,
        seasonal.SEARCH_SWING, seasonal.CHI2_11_05)


def test_the_chi_square_table_is_timings_and_the_title_counts_it(M, TM):
    t = M["tests"]
    assert t.equals(TM["tests"])
    assert len(t) == 8                                       # eight side-years
    assert int(t["even"].sum()) == 7                          # "Seven of eight"
    odd = t[~t["even"]].iloc[0]
    assert (odd["side"], odd["year"], odd["top_month"]) == ("skincare", 2024, 8)
    assert (t["chi2"] < seasonal.CHI2_11_05).equals(t["even"])


# ── Coverage ────────────────────────────────────────────────────────────────

def test_the_review_counts_by_year_are_the_embeddings(M):
    rv = M["reviews"]
    pts = data.load_umap(E).merge(data.load_review_map(E), on="review_id")
    cat = pts[pts["category"] == method.COVERAGE_CATEGORY]
    y_lo = int(M["convergence"]["periods"][0][:4])
    assert rv.loc[method.COVERAGE_CATEGORY, y_lo] == (cat["review_year"] == y_lo).sum()
    late = rv.loc[method.LATE_CATEGORY]
    first = int(late[late > 0].index.min())
    assert late[late.index < first].sum() == 0                # "no review before"
    # "dated January – <newest review>": the newest year is the one the registry dates.
    assert int(rv.columns.max()) == M["cosme_to"].year


def test_youtube_search_categories_by_side(M):
    yt = M["youtube"]
    assert yt["skincare"] > yt["cosmetics"]


# ── The review-vocabulary record (Revision 20) ──────────────────────────────

def test_the_curve_reads_what_the_title_states(M):
    cv = M["convergence"]
    cur = cv["curve"].set_index("sample_size")["cosine"]
    assert cur.is_monotonic_increasing
    assert (round(cur.iloc[0], 2), round(cur.iloc[-1], 2)) == (0.28, 0.67)
    assert set(cv["curve"]["period"]) == {cv["periods"][1]} == {"2023–2025"}
    # The matched test is the curve's point at its size, by construction.
    assert cur.loc[cv["n"]] == cv["late"]
    assert (cv["curve"]["early_n"] == cv["n"]).all()


def test_product_matched_the_change_includes_zero(M):
    ck = M["convergence"]["checks"]
    pb = ck.loc["products_in_both"]
    assert pb["ci_lo"] <= 0 <= pb["ci_hi"]
    assert ck.loc["baseline", "ci_lo"] > 0
    assert list(ck.index) == list(method.CHECKS)


def test_products_per_period(M):
    per = M["convergence"]["per"]
    p0, p1 = M["convergence"]["periods"]
    assert (per.loc[("makeup", p0), "products"], per.loc[("makeup", p1), "products"]) == (3, 31)
    assert (per.loc[("skincare", p0), "products"], per.loc[("skincare", p1), "products"]) == (20, 72)


def test_the_withdrawal_line_is_the_one_the_exemption_covers(M, headline, REG):
    """Ruling 5: the line is caught by the convergence entry and exempt, not
    reworded. The exemption must be needed, and nothing else on the page
    names the convergence."""
    from retired_phrases import EXEMPT, RETIRED
    conv = next(pat for pat, why, *_ in RETIRED if "convergence" in why)
    assert EXEMPT == {"/method": ("me_cv_line",)}
    for lang in ("en", "jp"):
        S = _S(lang, headline, M, REG)
        assert re.search(conv, S["me_cv_line"], re.I), lang
        rest = " ".join(_flat(S[k]) for k in S if k.startswith("me_") and k != "me_cv_line")
        assert not re.search(conv, rest, re.I), lang


# ── The copy ────────────────────────────────────────────────────────────────

_LOOKUPS = ("me_kicker", "me_check", "me_side", "me_months", "me_q_month", "me_k_n", "me_k_ci",
            "me_period", "me_pk_hover", "me_v_hover", "me_src_meti", "me_src_prtimes",
            "me_src_cosme", "me_s_cols", "me_q_cols", "me_p_cols", "me_k_cols")


def _flat(v):
    if isinstance(v, dict):
        return " ".join(_flat(x) for x in v.values())
    return " ".join(_flat(x) for x in v) if isinstance(v, (list, tuple)) else str(v)


def test_the_japanese_method_page_is_complete_and_carries_the_same_figures(M, headline, REG):
    en, ja = _S("en", headline, M, REG), _S("jp", headline, M, REG)
    keys = [k for k in en if k.startswith("me_")]
    assert keys and all(k in ja for k in keys)
    num = re.compile(r"\d+(?:[.,]\d+)*")
    jp_chars = re.compile(r"[぀-ヿ一-鿿]")
    for k in keys:
        if k in _LOOKUPS:
            continue
        e, j = _flat(en[k]), _flat(ja[k])
        assert jp_chars.search(j), k
        assert set(num.findall(e)) <= set(num.findall(j)), (k, set(num.findall(e)) - set(num.findall(j)))


def test_japanese_titles_end_without_a_full_stop(M, headline, REG):
    ja = _S("jp", headline, M, REG)
    for k in ja:
        if k.startswith("me_") and k.endswith(("_h", "_t")):
            assert not ja[k].endswith("。"), k


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_every_exhibit_carries_a_source_line_from_the_registry(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    code = "ja" if lang == "jp" else "en"
    for key, src in (("me_src_meti", "meti"), ("me_src_prtimes", "prtimes"),
                     ("me_src_cosme", "cosme")):
        assert S[key] == sources.source_line([src], REG, code)
        assert "method" in REG[src].used_on


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_copy_names_no_page_and_no_removal_outside_the_record(M, headline, REG, lang):
    S = _S(lang, headline, M, REG)
    text = " ".join(_flat(S[k]) for k in S if k.startswith("me_") and k not in _LOOKUPS
                    and k != "me_cv_line")
    for tell in ("this page", "this tab", "here", "withdrawn", "no longer", "previously",
                 "retired", " pp", "このページ", "撤回", "以前"):
        assert tell not in text.lower(), tell


# ── The page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_json():
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/method")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_the_page_has_no_emoji_tile_rimmed_card_or_control(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js and "bp-pill" not in js, lang
        assert "bp-widewrap" not in js, lang


def test_the_page_uses_no_side_colour(page_json):
    """No title on the page sets skincare against makeup: grey and ink only."""
    from bp.theme import C
    for lang, js in page_json.items():
        assert C["skin"] not in js and C["cosm"] not in js, lang


def test_method_is_the_last_report_page_in_the_nav():
    import ui
    assert ui.NAV_PATHS[-2:] == ["/timing", "/method"]
