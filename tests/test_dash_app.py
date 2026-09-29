"""The Dash app, through Flask's test client: routes, language, callbacks, the
word-cloud route, the no-launch empty state, the stylesheet tokens and the text
renderer. No browser; the charts' JSON is what bp/figures.py builds, which
tests/test_figures.py covers, with bp.theme.TEMPLATE set, which is checked here.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = {"/brief": "brief", "/market": "market", "/demand": "demand", "/supply": "supply",
         "/language": "language", "/discovery": "discovery"}


@pytest.fixture(scope="module")
def dash_app():
    import app
    return app


@pytest.fixture(scope="module")
def client(dash_app):
    return dash_app.server.test_client()


@pytest.fixture(scope="module")
def pages(dash_app):
    import sys
    import dash
    return {p["path"]: sys.modules[m] for m, p in dash.page_registry.items()}


def _post(client, output, inputs, state=(), outputs=None):
    """One callback over the wire, the way the browser sends it. A callback with
    several outputs is addressed by all of them; `output` picks the one returned."""
    outs = outputs or [output]
    parsed = [dict(zip(("id", "property"), o.split("."))) for o in outs]
    body = {"output": outs[0] if len(outs) == 1 else ".." + "...".join(outs) + "..",
            "outputs": parsed[0] if len(outs) == 1 else parsed,
            "inputs": list(inputs), "state": list(state),
            "changedPropIds": [f"{i['id']}.{i['property']}" for i in inputs]}
    r = client.post("/_dash-update-component", data=json.dumps(body),
                    content_type="application/json")
    assert r.status_code == 200, r.data[:300]
    oid, prop = output.split(".")
    return json.loads(r.data)["response"][oid][prop]


def _in(id_, prop, value):
    return {"id": id_, "property": prop, "value": value}


def _text(node):
    """Every string in a serialised component tree."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(_text(n) for n in node)
    if isinstance(node, dict):
        return _text(node.get("props", {}).get("children"))
    return ""


def _tree(component):
    import plotly.io.json as pjson
    return json.loads(pjson.to_json_plotly(component))


# ── Pages and routes ────────────────────────────────────────────────────────

def test_registry_holds_the_pages_and_the_nav_matches_it(dash_app):
    import dash
    import ui
    registered = sorted(dash.page_registry.values(), key=lambda p: p["order"])
    assert [p["path"] for p in registered] == list(PAGES)
    assert ui.NAV_PATHS == [p["path"] for p in registered]


@pytest.mark.parametrize("path", list(PAGES))
@pytest.mark.parametrize("query", ["", "?lang=ja"])
def test_every_page_serves(client, path, query):
    assert client.get(path + query).status_code == 200


def test_root_redirects_to_the_first_page_and_keeps_the_language(client):
    r = client.get("/")
    assert r.status_code == 302 and r.headers["Location"] == "/brief"
    r = client.get("/?lang=ja")
    assert r.status_code == 302 and r.headers["Location"] == "/brief?lang=ja"


def test_a_retired_page_redirects_to_its_replacement_and_keeps_the_language(client, dash_app):
    for old, new in dash_app.RETIRED.items():
        r = client.get(old)
        assert r.status_code == 302 and r.headers["Location"] == new
        r = client.get(old + "?lang=ja")
        assert r.status_code == 302 and r.headers["Location"] == new + "?lang=ja"
        assert new in PAGES and old not in PAGES


@pytest.mark.parametrize("path", list(PAGES))
def test_layout_takes_the_language_from_the_query(pages, path):
    page = pages[path]
    assert page.layout(lang="ja") is page.TREES["jp"]
    assert page.layout() is page.TREES["en"]
    for junk in ("xx", "", "JA", "jp"):
        assert page.layout(lang=junk) is page.TREES["en"], junk


def test_importing_the_app_leaves_it_set_up():
    """gunicorn --preload imports app.py once and forks the workers from it. A
    worker must start with Dash's list of servable JS bundles already built, or
    parallel requests on a cold start race Dash's own setup and get 500s. A
    fresh interpreter, because this process has served requests already."""
    import subprocess
    import sys
    code = ("import app; import sys; "
            "sys.exit(0 if 'dcc/dash_core_components.js' in app.app.registered_paths['dash'] "
            "and app.app._got_first_request['setup_server'] else 1)")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "dashboard",
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]


def test_version_reports_the_build_and_the_data_months(client):
    r = client.get("/version")
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    body = r.get_json()
    assert set(body) == {"version", "trends_to", "launches_to"}
    assert re.fullmatch(r"\d{4}-\d{2}", body["trends_to"])


@pytest.mark.parametrize("path", list(PAGES))
@pytest.mark.parametrize("lang", ["en", "jp"])
def test_no_page_uses_a_retired_phrase(pages, path, lang):
    from retired_phrases import RETIRED
    text = _text(_tree(pages[path].TREES[lang]))
    hits = [(why, m.group(0)) for pat, why in RETIRED
            for m in re.finditer(pat, text, re.I)]
    assert not hits, hits


def test_discovery_lists_both_top_terms_with_the_shared_ones_marked(pages):
    import data_cache
    d = data_cache.load()
    df = d.frame("vocab_overlap")
    tree = json.dumps(_tree(pages["/discovery"].TREES["en"]), ensure_ascii=False)
    for _, r in df.iterrows():
        cls = "bp-vocab-shared" if r["in_both"] else "bp-vocab-own"
        assert f'"children": "{r["term"]}", "className": "{cls}"' in tree, r["term"]
    assert d.S["en"]["t3_yttfe"].startswith(f"{int(df[df.source == 'cosme'].in_both.sum())} of")


# ── One callback per control, with a non-default value ─────────────────────

def test_wordcloud_pills_swap_the_image_and_note(client):
    img = _post(client, "lg-wc-img.children", [_in("lg-wc-year", "value", 2020)],
                [_in("lg-lang", "data", "en")],
                outputs=["lg-wc-img.children", "lg-wc-note.children"])
    assert img["props"]["src"] == "/wordcloud/2020.png"


def test_umap_year_pills_filter_the_map_and_the_count(client):
    fig = _post(client, "dc-fig-umap.figure", [_in("dc-umap-year", "value", 2023)],
                [_in("dc-lang", "data", "en")])
    assert "— 2023" in fig["layout"]["title"]["text"]
    count = _post(client, "dc-umap-count.children", [_in("dc-umap-year", "value", 2023)])
    assert re.search(r"[\d,]+ reviews", _text(count))


# ── Chart template ──────────────────────────────────────────────────────────

# Each callback that returns a figure: graph -> (control, a non-default value,
# the page's language store).
FIGURE_CALLBACKS = {
    "dc-fig-umap": ("dc-umap-year", 2023, "dc-lang"),
}


def _figures(node):
    """Every dcc.Graph figure in a serialised tree."""
    if isinstance(node, list):
        return [f for n in node for f in _figures(n)]
    if not isinstance(node, dict):
        return []
    props = node.get("props", {})
    if node.get("type") == "Graph":
        return [props["figure"]]
    return _figures(props.get("children"))


@pytest.mark.parametrize("path", list(PAGES))
@pytest.mark.parametrize("lang", ["en", "jp"])
def test_every_chart_on_a_page_carries_the_template(pages, path, lang):
    from bp.theme import TEMPLATE
    figs = _figures(_tree(pages[path].TREES[lang]))
    assert figs
    for fig in figs:
        assert fig["layout"]["template"] == _tree(TEMPLATE)


@pytest.mark.parametrize("graph", list(FIGURE_CALLBACKS))
def test_every_figure_callback_returns_the_template(client, pages, graph):
    from bp.theme import TEMPLATE
    control, value, lang_store = FIGURE_CALLBACKS[graph]
    fig = _post(client, f"{graph}.figure", [_in(control, "value", value)],
                [_in(lang_store, "data", "jp")])
    assert fig["layout"]["template"] == _tree(TEMPLATE)


def test_the_template_cases_cover_every_figure_callback(client, dash_app):
    client.get("/discovery")        # page callbacks register on the first request
    graphs = {k.split(".")[0] for k in dash_app.app.callback_map if k.endswith(".figure")}
    assert graphs == set(FIGURE_CALLBACKS)


# ── Word clouds ─────────────────────────────────────────────────────────────

def test_wordcloud_route_serves_listed_years_only(client):
    from bp import figures
    year = figures.wordcloud_years()[-2]
    r = client.get(f"/wordcloud/{year}.png")
    assert r.status_code == 200 and r.mimetype == "image/png"
    assert client.get("/wordcloud/2018.png").status_code == 404
    # a path that is not /wordcloud/<int>.png never reaches the file route
    assert client.get("/wordcloud/..%2Fsecret.png").mimetype != "image/png"


# ── Empty state, stylesheet, text ───────────────────────────────────────────

def test_supply_renders_its_empty_state_without_the_launch_export(pages):
    import data_cache
    d = data_cache.build_data(data_cache.ASSETS, launch=False)
    for lang in data_cache.LANGS:
        text = _text(_tree(pages["/supply"].build(lang, d)))
        assert d.S[lang]["launch_empty"] in text


def test_stylesheet_tokens_mirror_the_theme():
    from bp.theme import C
    css = (ROOT / "dashboard" / "static" / "style.css").read_text(encoding="utf-8")
    root = css[css.index(":root"):css.index("}", css.index(":root"))]
    tokens = dict(re.findall(r"--([a-z-]+):\s*(#[0-9A-Fa-f]{6})", root))
    for key, hexval in C.items():
        assert tokens.get(key.replace("_", "-"), "").upper() == hexval.upper(), key
    from bp.theme import FONT
    assert " ".join(re.search(r"--font:\s*([^;]+);", root).group(1).split()) == FONT


@pytest.mark.parametrize("path", list(PAGES))
@pytest.mark.parametrize("lang", ["en", "jp"])
def test_no_page_shows_rising_related_searches(pages, path, lang):
    """The related-search pull records no date and no window, and its count
    across seed terms follows the seed list (METHODOLOGY Revision 17); no page
    shows it until a dated re-pull brings it back."""
    text = json.dumps(_tree(pages[path].TREES[lang]), ensure_ascii=False)
    for tell in ("seed term", "起点語", "rising related", "rising search", "急上昇",
                 "related search", "関連検索", "アヌア"):
        assert tell.lower() not in text.lower(), (path, lang, tell)
    assert not re.search(r"\bAnua\b", text), (path, lang)


def test_every_tag_in_the_string_tables_is_one_the_renderer_supports(dash_app):
    import data_cache
    import ui
    D = data_cache.load()
    for lang, S in D.S.items():
        for key, value in S.items():
            if not isinstance(value, str):
                continue
            tags = {t.lower() for t in re.findall(r"</?\s*([a-zA-Z0-9]+)", value)}
            assert tags <= ui.RICH_TAGS, f"{lang}.{key} uses {tags - ui.RICH_TAGS}"
            ui.rich(value)                            # and it renders
    with pytest.raises(ValueError):
        ui.rich("a <script>x</script>")
