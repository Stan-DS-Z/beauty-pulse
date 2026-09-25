"""The Dash app, through Flask's test client: routes, language, callbacks, the
word-cloud route, the no-launch empty state, the stylesheet tokens and the text
renderer. No browser; the charts' JSON is what bp/figures.py builds, and
tests/test_figures.py covers that.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = {"/shift": "shift", "/language": "language", "/discovery": "discovery"}


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

def test_registry_holds_the_three_pages_and_the_nav_matches_it(dash_app):
    import dash
    import ui
    registered = sorted(dash.page_registry.values(), key=lambda p: p["order"])
    assert [p["path"] for p in registered] == list(PAGES)
    assert [path for path, _ in ui.NAV] == [p["path"] for p in registered]


@pytest.mark.parametrize("path", list(PAGES))
@pytest.mark.parametrize("query", ["", "?lang=ja"])
def test_every_page_serves(client, path, query):
    assert client.get(path + query).status_code == 200


def test_root_redirects_to_the_first_page_and_keeps_the_language(client):
    r = client.get("/")
    assert r.status_code == 302 and r.headers["Location"] == "/shift"
    r = client.get("/?lang=ja")
    assert r.status_code == 302 and r.headers["Location"] == "/shift?lang=ja"


@pytest.mark.parametrize("path", list(PAGES))
def test_layout_takes_the_language_from_the_query(pages, path):
    page = pages[path]
    assert page.layout(lang="ja") is page.TREES["jp"]
    assert page.layout() is page.TREES["en"]
    for junk in ("xx", "", "JA", "jp"):
        assert page.layout(lang=junk) is page.TREES["en"], junk


def test_version_reports_the_build_and_the_data_months(client):
    r = client.get("/version")
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    body = r.get_json()
    assert set(body) == {"version", "trends_to", "launches_to"}
    assert re.fullmatch(r"\d{4}-\d{2}", body["trends_to"])


# ── One callback per control, with a non-default value ─────────────────────

def test_crossover_slider_sets_the_visible_range(client, pages):
    fig = _post(client, "sh-fig1.figure", [_in("sh-crossover", "value", [24, 60])],
                [_in("sh-lang", "data", "en")])
    months = pages["/shift"]._months(pages["/shift"].D.frame("trends_crossover"))
    assert fig["layout"]["xaxis"]["range"][0].startswith(months[24].strftime("%Y-%m-%d"))


def test_ingredient_dropdown_draws_the_selected_terms(client):
    fig = _post(client, "sh-fig2.figure", [_in("sh-ingr", "value", ["グルタチオン", "レチナール"])],
                [_in("sh-lang", "data", "en")])
    assert [t["name"] for t in fig["data"]] == ["グルタチオン", "レチナール"]


def test_lens_radio_recolours_the_treemap(client):
    fig = _post(client, "sh-fig3.figure", [_in("sh-lens", "value", "med_price")],
                [_in("sh-lang", "data", "jp")])
    assert fig["layout"]["coloraxis"]["colorbar"]["title"]["text"] == "Median price (¥)"


def test_rakuten_tile_click_selects_then_clears(client):
    click = {"points": [{"label": "All-in-one"}]}
    sel = _post(client, "sh-rak-sel.data",
                [_in("sh-fig3", "clickData", click), _in("sh-rak-clear", "n_clicks", 0)],
                [_in("sh-rak-sel", "data", None)])
    assert sel == "All-in-one"
    again = _post(client, "sh-rak-sel.data",
                  [_in("sh-fig3", "clickData", click), _in("sh-rak-clear", "n_clicks", 0)],
                  [_in("sh-rak-sel", "data", "All-in-one")])
    assert again is None
    detail = _post(client, "sh-rak-detail.children", [_in("sh-rak-sel", "data", "All-in-one")],
                   [_in("sh-lang", "data", "en")],
                   outputs=["sh-rak-detail.children", "sh-rak-clear.className"])
    assert "All-in-one" in _text(detail) and "Avg reviews / SKU" in _text(detail)


def test_wordcloud_pills_swap_the_image_and_note(client):
    img = _post(client, "lg-wc-img.children", [_in("lg-wc-year", "value", 2020)],
                [_in("lg-lang", "data", "en")],
                outputs=["lg-wc-img.children", "lg-wc-note.children"])
    assert img["props"]["src"] == "/wordcloud/2020.png"


def test_launch_ingredient_dropdown_redraws_the_pair(client, pages):
    from bp import figures
    D = pages["/discovery"].D
    if D.LAUNCH is None:
        pytest.skip("launch export not built")
    first, second = figures.launch_ingredient_options(D.LAUNCH)[:2]
    fig = _post(client, "dc-fig-l5.figure", [_in("dc-launch-ing", "value", second)],
                [_in("dc-lang", "data", "en")])
    default = figures.fig_launch_vs_search(D.LAUNCH, D.frame("ingredient_surge"), first, D.S["en"])
    assert fig["data"][0]["y"] != _tree(default)["data"][0]["y"]


def test_window_pills_switch_the_treemap_and_the_finding(client):
    fig = _post(client, "dc-fig-bc.figure", [_in("dc-bc-window", "value", "covid")],
                [_in("dc-lang", "data", "en")])
    assert fig["data"][0]["type"] == "treemap"
    finding = _post(client, "dc-f4.children", [_in("dc-bc-window", "value", "covid")],
                    [_in("dc-lang", "data", "en")])
    assert "2020–2021" in _text(finding)


def test_blockc_tile_click_opens_its_detail(client):
    sel = _post(client, "dc-bc-sel.data",
                [_in("dc-fig-bc", "clickData", {"points": [{"label": "アヌア"}]}),
                 _in("dc-bc-window", "value", "recent")],
                [_in("dc-bc-sel", "data", None)])
    assert sel == "アヌア"
    detail = _post(client, "dc-bc-detail.children", [_in("dc-bc-sel", "data", "アヌア")],
                   [_in("dc-bc-window", "value", "recent"), _in("dc-lang", "data", "jp")])
    assert "アヌア" in _text(detail) and "Seed queries" in _text(detail)


def test_umap_year_pills_filter_the_map_and_the_count(client):
    fig = _post(client, "dc-fig-umap.figure", [_in("dc-umap-year", "value", 2023)],
                [_in("dc-lang", "data", "en")])
    assert "— 2023" in fig["layout"]["title"]["text"]
    count = _post(client, "dc-umap-count.children", [_in("dc-umap-year", "value", 2023)])
    assert re.search(r"[\d,]+ reviews", _text(count))


def test_a_malformed_click_changes_nothing(client):
    r = client.post("/_dash-update-component", data=json.dumps({
        "output": "sh-rak-sel.data", "outputs": {"id": "sh-rak-sel", "property": "data"},
        "inputs": [_in("sh-fig3", "clickData", {"points": "junk"}),
                   _in("sh-rak-clear", "n_clicks", 0)],
        "state": [_in("sh-rak-sel", "data", "Emulsion")],
        "changedPropIds": ["sh-fig3.clickData"]}), content_type="application/json")
    # no_update: Dash 4 answers 200 with nothing in the response
    assert r.status_code == 200 and json.loads(r.data)["response"] == {}


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

def test_discovery_renders_its_empty_state_without_the_launch_export(pages):
    import data_cache
    d = data_cache.build_data(data_cache.ASSETS, launch=False)
    for lang in data_cache.LANGS:
        text = _text(_tree(pages["/discovery"].build(lang, d)))
        assert d.S[lang]["t3_lempty"] in text


def test_stylesheet_tokens_mirror_the_theme():
    from bp.theme import C
    css = (ROOT / "dashboard" / "static" / "style.css").read_text(encoding="utf-8")
    root = css[css.index(":root"):css.index("}", css.index(":root"))]
    tokens = dict(re.findall(r"--([a-z-]+):\s*(#[0-9A-Fa-f]{6})", root))
    for key, hexval in C.items():
        assert tokens.get(key.replace("_", "-"), "").upper() == hexval.upper(), key


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
