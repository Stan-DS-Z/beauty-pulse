"""
Beauty Pulse — the Dash app, served at https://beautypulse.web.app.

    python dashboard/app.py                                   # local, port 8050
    gunicorn --chdir dashboard --preload app:server           # production
    /version                                                  # what is deployed

Deploy: Dockerfile and cloudbuild.yaml at the repo root; see DEPLOY.md.

The pages are in dash_pages/ (not pages/: a pages/ folder next to
streamlit_app.py would switch the Streamlit app into multipage mode): the Brief,
then the report pages built so far; the monitor pages follow.
The language is the URL's ?lang=ja; anything else is English. Each page builds
its English and Japanese trees once at import and its layout() hands back the
one the URL asks for. Numbers, copy, theme and figures come from bp/.
"""

import os
from pathlib import Path

from dash import Dash, Input, Output, clientside_callback, dcc, html, page_container
from flask import jsonify, redirect, request
from flask_compress import Compress

import data_cache
from bp import figures

HERE = Path(__file__).parent
ASSETS = HERE / "assets"          # the CSV data; Dash's own assets folder is static/
HOME = "/brief"
# Pages the report replaced -> the page that carries their exhibits now.
RETIRED = {"/shift": "/demand", "/language": "/consumer", "/discovery": "/consumer"}

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="dash_pages",
    assets_folder="static",
    suppress_callback_exceptions=True,
    update_title=None,
    title="Beauty Pulse · Japanese Beauty Market",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server
Compress(server)


@server.before_request
def _home():
    """"/" goes to the first page, and a retired page's path to the page that
    replaced it, each keeping the query, so /?lang=ja lands in Japanese.
    Dash's redirect_from cannot do this: it drops the query, answers 301
    (which browsers cache, and "/" is due to become its own page), and
    collides with Dash's own "/" route."""
    target = HOME if request.path == "/" else RETIRED.get(request.path.rstrip("/"))
    if target:
        qs = request.query_string.decode()
        return redirect(target + (f"?{qs}" if qs else ""), code=302)
    return None


@server.route("/version")
def _version():
    """The deployed commit and the months its data runs to. APP_VERSION is the
    short SHA Cloud Build bakes into the image; a local run says "dev"."""
    d = data_cache.load()
    resp = jsonify({
        "version": os.environ.get("APP_VERSION", "dev"),
        "trends_to": d.frame("trends_crossover")["week_start"].max().strftime("%Y-%m"),
        "launches_to": d.LAUNCH["last"] if d.LAUNCH else None,
    })
    resp.headers["Cache-Control"] = "no-store"
    return resp


app.layout = html.Div(className="bp-shell", children=[
    dcc.Location(id="shell-url"),
    dcc.Store(id="shell-lang-sink"),
    dcc.Store(id="shell-nav-sink"),
    page_container,
])

# <html lang> follows ?lang, so the browser picks Japanese glyphs for Japanese.
clientside_callback(
    """function (search) {
        var lang = new URLSearchParams(search || "").get("lang") === "ja" ? "ja" : "en";
        document.documentElement.lang = lang;
        return lang;
    }""",
    Output("shell-lang-sink", "data"),
    Input("shell-url", "search"),
)

# On a phone the nav scrolls sideways inside its own strip (the one element
# allowed to: no content scrolls sideways at 390 px). Once the page for this
# path has rendered, centre its entry in the strip, so a page far along the
# nav (Method) is not off-screen.
clientside_callback(
    """function (path) {
        var tries = 0;
        (function centre() {
            var a = document.querySelector(".bp-nav .bp-navlink.active");
            if (!a || (a.getAttribute("href") || "").split("?")[0] !== path) {
                if (tries++ < 120) { window.requestAnimationFrame(centre); }
                return;
            }
            var nav = a.parentElement, n = nav.getBoundingClientRect(), r = a.getBoundingClientRect();
            nav.scrollLeft += r.left - n.left - (n.width - r.width) / 2;
        })();
        return path;
    }""",
    Output("shell-nav-sink", "data"),
    Input("shell-url", "pathname"),
)

# Dash sets itself up on a process's first request, and marks that done before
# it is: a request on another thread meanwhile is checked against a half-built
# list of the JS bundles Dash serves, and gets a 500. On a cold start that broke
# the page. Made here, the first request runs in the gunicorn master before the
# workers fork (--preload), so every worker starts set up.
with server.test_client() as _client:
    _client.get(HOME)


if __name__ == "__main__":
    app.run(debug=False, port=8050)
