"""The Brief: its figures, the directions its copy states, and the page.

The Brief's sentences say rose, fell, below, gained and lost, and the data
decides each. These tests hold the data to every direction the copy states, so
a refresh that turns one fails here, and the sentence is rewritten for the new
edition instead of shipping wrong.
"""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from bp import brief, data, sources, strings

A = data.ASSETS
E = sources.edition_assets(A)            # the issued edition: what the report reads


@pytest.fixture(scope="module")
def launch():
    lau = data.compute_launch_headline(A)
    if lau is None:
        pytest.skip("launch export not built")
    return lau


@pytest.fixture(scope="module")
def B(launch):
    return brief.compute_brief(E, data.compute_headline(E), sources.CUTOFF)


@pytest.fixture(scope="module")
def S(headline, launch, B):
    return strings.build_strings("en", headline, launch, A, B,
                                 sources.build_registry(E, sources.CUTOFF))


# ── The directions the copy states ──────────────────────────────────────────

def test_market_line_holds(B):
    m = B["market"]
    assert m["skin_d"] > 0 and m["make_d"] > 0                     # "rose … in skincare and … makeup"
    assert m["make_vs_base"] < 0                                     # "makeup is still … below"
    assert m["serum_d"] > 0 and m["serum_vpu"] > 0 and m["serum_units"] < 0   # "from value per unit on fewer units"


def test_demand_line_holds(B):
    d, spread = B["demand"], brief.TRENDS_PULL_SPREAD
    assert d["n_rose"] >= 1 and d["rose_lo"] >= spread
    assert d["within"], "the line names the actives inside the spread"
    assert d["top3_lo"] >= spread
    assert d["words_down"] >= 1 and d["words_up"] and d["words_within"]


def test_supply_line_holds(B):
    s, rows = B["supply"], B["rows"]
    assert all(rows.loc[k, "launch_d"] > 0 for k in s["gainers"])  # "gained"
    assert s["loss"] < 0                                             # "lost"
    (k0, n0), (k1, n1) = s["kr_first"], s["kr_last"]
    assert n0 and n1 and k1 / n1 > k0 / n0                           # "from …%" (JA: から上昇)


def test_governing_thought_and_portfolio_title_hold(B):
    p, rows = B["portfolio"], B["rows"]
    assert p["risers"] and all(rows.loc[k, "ship_d"] >= brief.VALUE_RISE_NAMED for k in p["risers"])
    assert p["fell"], "the portfolio title names risers whose launch share fell"
    assert all(rows.loc[k, "launch_d"] < 0 for k in p["fell"])


# ── Windows and rules ───────────────────────────────────────────────────────

def test_korean_share_compares_complete_halves_inside_the_launch_window(B):
    s = B["supply"]
    months = pd.Series(data.compute_launch_headline(E, sources.CUTOFF)["months"])
    for h in (s["h_first"], s["h_last"]):
        y, half = int(h[:4]), int(h[-1])
        want = [f"{y}-{m:02d}" for m in (range(1, 7) if half == 1 else range(7, 13))]
        assert set(want) <= set(months), h


@pytest.mark.parametrize("lang", ["en", "jp"])
def test_the_top_actives_are_never_ranked(B, headline, launch, lang):
    """The three are named in alphabetical (EN) or 五十音 (JA) order, never by
    their rise."""
    S = strings.build_strings(lang, headline, launch, A, B,
                              sources.build_registry(E, sources.CUTOFF))
    col = S["b_namecol"]
    names = [B["actives"].loc[k, col] for k in B["demand"]["top3"]]
    names = [n.lower() for n in names] if lang == "en" else names
    for key in ("b_kf_demand", "b_a_h"):
        first = {n: S[key].index(n) for n in names}
        assert sorted(first, key=first.get) == sorted(names), key


def test_the_japanese_brief_is_complete_and_carries_the_same_figures(B, headline, launch):
    """Every Brief string exists in Japanese, and every number in an English
    line appears in its Japanese line."""
    reg = sources.build_registry(E, sources.CUTOFF)
    en = strings.build_strings("en", headline, launch, A, B, reg)
    ja = strings.build_strings("jp", headline, launch, A, B, reg)
    keys = [k for k in en if k.startswith("b_")]
    assert keys and all(k in ja for k in keys)
    num = re.compile(r"\d+(?:[.,]\d+)*")
    for k in keys:
        if isinstance(en[k], str) and k not in ("b_kicker", "b_namecol", "b_t_monsep"):
            assert re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", ja[k]), k
            en_text = re.sub(r"\bH[12]\b", "", en[k])       # 2026 H1 is 2026年上期
            assert set(num.findall(en_text)) <= set(num.findall(ja[k])), k


def test_the_table_holds_every_category_largest_value_first(B):
    rows = B["rows"]
    assert B["n_rows"] == 16 == len(rows)
    assert list(rows["value_y1"]) == sorted(rows["value_y1"], reverse=True)


# ── The edition cut-off ─────────────────────────────────────────────────────

def _later(ym, n):
    p = pd.Period(ym, freq="M") + n
    return p.year, p.month


def _assets_copy(dest, future):
    """The shipped assets under `dest`, linked, with the fetch dated long after
    the edition so every month up to the cut-off is complete. With `future`,
    rows dated after the cut-off are added to every dated asset the report
    reads, with values far from the real ones."""
    import shutil
    dest.mkdir()
    for f in A.iterdir():
        if f.is_file():
            (dest / f.name).symlink_to(f)
    def write(name, frame, **kw):
        (dest / name).unlink()
        frame.to_csv(dest / name, index=False, **kw)
    cut = sources.CUTOFF
    after = [_later(cut, n) for n in range(1, 16)]          # the next fifteen months

    feeds = pd.read_csv(A / "prtimes_feeds.csv", dtype=str)
    feeds["fetched"] = f"{after[-1][0] + 1}-01-15"
    write("prtimes_feeds.csv", feeds)
    if not future:
        return dest

    meti = pd.read_csv(A / "estat_meti_cosmetics.csv")
    src = meti[(meti["year"] == meti["year"].max() - 1) & (meti["month"] >= 1)]
    add = [src[src["month"] == m].assign(year=y, value=lambda x: x["value"] * 10)
           for y, m in after]
    add.append(src[src["month"] == 1].assign(year=after[-1][0] + 1, month=0))
    write("estat_meti_cosmetics.csv", pd.concat([meti, *add]))

    lau = pd.read_csv(A / "prtimes_launches.csv", dtype=str)
    core = lau[lau["panel"] == "core"].head(400)
    add = [core.assign(month=f"{y}-{m:02d}", published=f"{y}-{m:02d}-15",
                       origin="KR", category="toner_lotion", ingredients="アゼライン酸")
           for y, m in after]
    write("prtimes_launches.csv", pd.concat([lau, *add]))

    am = pd.read_csv(A / "nb04b_attention_monthly.csv")
    src = am[am["year"] == am["year"].max()]
    add = [src[src["month"] == m].assign(year=y, interest=100.0) for y, m in after]
    write("nb04b_attention_monthly.csv", pd.concat([am, *add]))
    an = pd.read_csv(A / "nb04b_attention_annual.csv")
    add = [an[an["year"] == an["year"].max()].assign(year=y, interest=100.0)
           for y in sorted({y for y, _ in after})]
    write("nb04b_attention_annual.csv", pd.concat([an, *add]))

    for name in sources.TRENDS_ASSETS:
        t = pd.read_csv(A / name, encoding="utf-8-sig")
        last = t[t["week_start"] == t["week_start"].max()]
        add = [last.assign(week_start=f"{y}-{m:02d}-01") for y, m in after]
        write(name, pd.concat([t, *add]), encoding="utf-8-sig")
    tr = pd.read_csv(A / "estat_trade_hs3304.csv")
    write("estat_trade_hs3304.csv",
          pd.concat([tr, tr[tr["year"] == tr["year"].max()].assign(year=after[-1][0] + 1)]))
    return dest


def test_no_report_figure_uses_data_past_the_cut_off(tmp_path, headline):
    """Data dated after the cut-off month changes nothing on the Brief: not a
    figure, not a sentence, not a source line. The baseline has the same late
    fetch, so the months up to the cut-off are complete in both."""
    cut = sources.CUTOFF
    base_dir = _assets_copy(tmp_path / "base", future=False)
    fut_dir = _assets_copy(tmp_path / "future", future=True)
    base = brief.compute_brief(base_dir, headline, cut)
    fut = brief.compute_brief(fut_dir, headline, cut)
    pd.testing.assert_frame_equal(base["rows"], fut["rows"])
    pd.testing.assert_frame_equal(base["actives"], fut["actives"])
    for lang in ("en", "jp"):
        assert (strings.brief_strings(lang, base, base["H"], sources.build_registry(base_dir, cut))
                == strings.brief_strings(lang, fut, fut["H"], sources.build_registry(fut_dir, cut)))
    # and the added data is really there for the monitor to read
    assert (sources.build_registry(fut_dir)["meti"].data_to
            > sources.build_registry(base_dir)["meti"].data_to)


# ── The frozen edition ──────────────────────────────────────────────────────

def test_the_frozen_edition_matches_its_manifest():
    """Every file issue_edition.py froze is unchanged, and nothing was added."""
    import hashlib
    import json
    m = json.loads((E / "manifest.json").read_text(encoding="utf-8"))
    assert (m["edition"], m["cutoff"]) == (sources.EDITION, sources.CUTOFF)
    assert {f.name for f in E.iterdir()} == set(m["files"]) | {"manifest.json"}
    for name, digest in m["files"].items():
        assert hashlib.sha256((E / name).read_bytes()).hexdigest() == digest, name


def test_the_report_opens_no_live_asset(monkeypatch):
    """Building the report's data opens files under the frozen edition only."""
    import builtins
    import data_cache
    opened, real_open = [], builtins.open
    def spy(file, *a, **kw):
        opened.append(Path(file).resolve() if isinstance(file, (str, Path)) else file)
        return real_open(file, *a, **kw)
    monkeypatch.setattr(builtins, "open", spy)
    data_cache.build_report(A)
    under = [p for p in opened if isinstance(p, Path) and A.resolve() in p.parents]
    assert under, "the spy saw no asset read"
    live = [p for p in under if E.resolve() not in p.parents]
    assert not live, live


def test_the_page_carries_the_frozen_edition():
    import data_cache
    d = data_cache.load()
    assert d.BRIEF["rows"].equals(brief.compute_brief(E, data.compute_headline(E),
                                                      sources.CUTOFF)["rows"])


def test_the_edition_and_its_cut_off_are_months_in_order():
    for ym in (sources.EDITION, sources.CUTOFF):
        assert re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym), ym
    assert sources.CUTOFF < sources.EDITION


# ── The page ────────────────────────────────────────────────────────────────

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿ℹ️]")


@pytest.fixture(scope="module")
def page_json():
    """Each language's Brief tree as JSON text, non-ASCII left readable."""
    import sys
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mod = next(sys.modules[m] for m, p in dash.page_registry.items() if p["path"] == "/brief")
    return {lang: json.dumps(json.loads(pjson.to_json_plotly(tree)), ensure_ascii=False)
            for lang, tree in mod.TREES.items()}


def test_every_exhibit_carries_a_source_line_from_the_registry(S):
    reg = sources.build_registry(E, sources.CUTOFF)
    for key, srcs in (("b_p_src", ["meti", "prtimes"]), ("b_a_src", ["trends", "prtimes"]),
                      ("b_t_src", ["meti", "trends", "prtimes"])):
        assert S[key] == sources.source_line(srcs, reg)


def test_the_page_has_no_emoji_tile_or_rimmed_card(page_json):
    for lang, js in page_json.items():
        assert not EMOJI.search(js), lang
        assert "kpi-card" not in js and "bp-finding" not in js and "bp-note" not in js, lang
        assert "borderLeft" not in js, lang


def test_the_nav_has_no_emoji(headline, launch, B):
    for lang in ("en", "jp"):
        S = strings.build_strings(lang, headline, launch, A, B,
                                  sources.build_registry(E, sources.CUTOFF))
        for key in ("nav_report", "nav_brief", "nav_market", "nav_demand", "nav_supply",
                    "nav_consumer"):
            assert not EMOJI.search(S[key]), (lang, key)
