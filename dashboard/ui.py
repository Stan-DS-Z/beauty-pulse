"""Dash-side components for Beauty Pulse: header, nav, language link, the text
renderer, and one component per piece of page furniture (panel header, KPI
card, chart head, callouts, captions, legends, detail panels).

Page text comes from bp.strings and carries a little inline HTML. rich() turns
exactly the tags in RICH_TAGS into components and refuses anything else, so
copy can never inject markup; tests/test_dash_app.py checks every tag in the
string tables is one of them. No dcc.Markdown: markdown would reinterpret
characters in the copy.
"""

from html.parser import HTMLParser

from dash import dcc, html

from bp.theme import TEMPLATE, finish

# ── Language and routes ─────────────────────────────────────────────────────

def lang_of(value):
    """The URL's ?lang value -> bp's language code. Anything but "ja" is English."""
    return "jp" if value == "ja" else "en"


def href(path, lang):
    """A page URL that keeps the language: no query for English, ?lang=ja for Japanese."""
    return path + ("?lang=ja" if lang == "jp" else "")


# The nav, in order: groups of (path, string-table key of its label), each
# group under the label its key names. A static list, because
# dash.page_registry is incomplete while pages import; a test pins it to the
# registry. The Shift, Language and Discovery pages stay in the report group
# until the report and monitor pages that replace them are built.
NAV = [("nav_report", [("/brief", "nav_brief"), ("/market", "nav_market"),
                       ("/demand", "nav_demand"), ("/supply", "nav_supply"), ("/shift", "tab1"),
                       ("/language", "tab2"), ("/discovery", "tab3")])]
NAV_PATHS = [path for _, items in NAV for path, _ in items]

GRAPH_CONFIG = {"displaylogo": False, "displayModeBar": False, "responsive": True}


# ── Text ────────────────────────────────────────────────────────────────────

RICH_TAGS = {"b", "br"}


class _Rich(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.bold = [], None

    def handle_starttag(self, tag, attrs):
        if tag not in RICH_TAGS:
            raise ValueError(f"unsupported tag <{tag}> in page text")
        if tag == "br":
            self.out.append(html.Br())
        elif self.bold is not None:
            raise ValueError("nested <b> in page text")
        else:
            self.bold = []

    def handle_endtag(self, tag):
        if tag not in RICH_TAGS:
            raise ValueError(f"unsupported tag </{tag}> in page text")
        if tag == "b" and self.bold is not None:
            self.out.append(html.B("".join(self.bold)))
            self.bold = None

    def handle_data(self, data):
        (self.bold if self.bold is not None else self.out).append(data)


def rich(text):
    """Page text with <b> and <br> as components; a plain string passes through."""
    if "<" not in text:
        return text
    p = _Rich()
    p.feed(text)
    p.close()
    return p.out


# ── Shell ───────────────────────────────────────────────────────────────────

def header(S, lang, path):
    """Title, subtitle, page nav and the EN/JA link, in the page's language."""
    nav = []
    for i, (group, items) in enumerate(NAV):
        if i:
            nav.append(html.Span(className="bp-navsep"))
        nav.append(html.Span(S[group], className="bp-navgroup"))
        nav += [dcc.Link(S[key], href=href(p, lang),
                         className="bp-navlink" + (" active" if p == path else ""))
                for p, key in items]
    switch = html.Div(className="bp-lang", children=[
        html.Span("EN", className="bp-lang-current") if lang == "en"
        else dcc.Link("EN", href=href(path, "en"), className="bp-lang-link"),
        html.Span("·", className="bp-lang-sep"),
        html.Span("JA", className="bp-lang-current") if lang == "jp"
        else dcc.Link("JA", href=href(path, "jp"), className="bp-lang-link"),
    ])
    return html.Header(className="bp-header", children=[
        html.Div(className="bp-titlerow", children=[
            html.Div(className="bp-brand", children=[
                html.H1("Beauty Pulse", className="bp-title"),
                html.Span(S["tagline"], className="bp-tagline"),
            ]),
            switch,
        ]),
        html.P(S["subtitle"], className="bp-subtitle"),
        html.Nav(nav, className="bp-nav"),
    ])


# ── Furniture ───────────────────────────────────────────────────────────────

def intro(text):
    return html.P(rich(text), className="bp-intro")


def panel_header(title, note):
    """Section rule inside a page — marks which measurement the panel below is."""
    return html.Div(className="bp-panel-head", children=[
        html.P(title, className="bp-panel-title"),
        html.P(rich(note), className="bp-panel-note"),
    ])


def chart_head(h, e=None):
    kids = [html.H3(rich(h), className="bp-h3")]
    if e is not None:
        kids.append(html.P(rich(e), className="expl"))
    return html.Div(kids, className="bp-chart-head")


def kpi_card(label, value, subtitle, arrow="up"):
    """KPI card; the subtitle is truncated and shown whole in a tooltip."""
    prefix, tone = {"up": ("↑ ", "up"), "down": ("↓ ", "down")}.get(arrow, ("", "flat"))
    return html.Div(className="kpi-card", children=[
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value"),
        html.Div(prefix + subtitle, className=f"kpi-sub {tone}",
                 **{"data-tooltip": subtitle}),
    ])


# ── Report front matter and exhibits ───────────────────────────────────────

def kicker(text):
    return html.P(text, className="bp-kicker")


def governing(text):
    """The page's governing thought, the one sentence the page argues."""
    return html.H2(rich(text), className="bp-governing")


def key_findings(items):
    """One line per finding: (label, text, link path or None, link label).
    A finding whose page is not built yet carries no link."""
    lines = []
    for label, text, link, go in items:
        kids = [html.Span(label, className="bp-kf-label"),
                html.Span(rich(text), className="bp-kf-text"),
                html.Span(go if link else "", className="bp-kf-go")]
        lines.append(dcc.Link(kids, href=link, className="bp-kf") if link
                     else html.Div(kids, className="bp-kf"))
    return html.Div(lines, className="bp-kfs")


def key_figures(items):
    """A row of key figures set as type: (label, figure, one line under it)."""
    return html.Div([html.Div([html.Div(label, className="bp-fig-label"),
                               html.Div(value, className="bp-fig-value"),
                               html.Div(sub, className="bp-fig-sub")])
                     for label, value, sub in items],
                    className=f"bp-figs cols-{len(items)}")


def source(text):
    """An exhibit's source line; it is also the exhibit's freshness stamp."""
    return html.P(text, className="bp-source")


def cell_bar(share, text):
    """An in-cell bar on the column's shared scale: share of the column's
    largest value, 0-1."""
    return [html.Span(html.Span(className="cellbar-fill", style={"width": f"{100 * share:.0f}%"}),
                      className="cellbar"),
            html.Span(text, className="cellnum")]


def div_bar(share, text):
    """A diverging in-cell bar around a centre line: share is signed, -1-1, of
    the column's largest absolute change. Direction is --pos or --neg."""
    half = 50 * min(abs(share), 1)
    style = ({"left": "50%", "width": f"{half:.0f}%"} if share >= 0
             else {"left": f"{50 - half:.0f}%", "width": f"{half:.0f}%"})
    return [html.Span([html.Span(className="divbar-mid"),
                       html.Span(className="divbar-fill " + ("pos" if share >= 0 else "neg"),
                                 style=style)], className="divbar"),
            html.Span(text, className="cellnum")]


def row(*children, cls="cols-2"):
    return html.Div(list(children), className=f"bp-row {cls}")


def caption(text):
    return html.P(rich(text), className="bp-caption")


def info(text):
    return html.Div(text, className="bp-info")


def finding(title, body, tone):
    """Finding box: tone is "skin" or "cosm"."""
    return html.Div(className=f"bp-finding tone-{tone}", children=[
        html.P(rich(title), className="bp-finding-title"),
        html.P(rich(body), className="bp-finding-body"),
    ])


def footnote(title, body):
    return html.Div(className="bp-footnote", children=[
        html.P(rich(title), className="bp-footnote-title"),
        html.P(rich(body), className="bp-footnote-body"),
    ])


def note(strong, text, tone):
    """One-line callout: a bold lead and muted text. tone: korean, skin, muted,
    or a wordcloud tone (see WC_TONES)."""
    kids = [html.Span(rich(strong), className="bp-note-lead")] if strong else []
    kids.append(html.Span(rich(text), className="bp-note-text"))
    return html.Div(kids, className=f"bp-note tone-{tone}")


def legend(items, shape="square"):
    """Swatch legend: items are (label, colour)."""
    return html.Div(className="bp-legend", children=[
        html.Div(className="bp-legend-item", children=[
            html.Span(className=f"bp-swatch {shape}", style={"background": colour}),
            html.Span(label),
        ]) for label, colour in items])


def themed(figure):
    """The figure with bp's chart template, replacing whatever template it was
    built with, and v3's finish over it (theme.finish). Every figure the Dash app shows passes through here: graph()
    for the page trees, and each callback that returns a figure."""
    figure.layout.template = TEMPLATE
    return finish(figure)


def graph(id_, figure):
    """A chart whose box is the figure's own height. With responsive on, Plotly
    fills its container, and a container with no height of its own collapses
    under a tall figure, which then overlaps whatever follows."""
    figure = themed(figure)
    height = figure.layout.height
    return dcc.Graph(id=id_, figure=figure, config=GRAPH_CONFIG, className="bp-graph",
                     style={"height": f"{height}px"} if height else None)


def pills(id_, options, value, label=None):
    """Single-choice pills: options are (value, label)."""
    kids = [html.Label(label, className="bp-control-label")] if label else []
    kids.append(dcc.RadioItems(
        id=id_, options=[{"label": lab, "value": v} for v, lab in options], value=value,
        className="bp-pills", inputClassName="bp-pill-input", labelClassName="bp-pill"))
    return html.Div(kids, className="bp-control")


# ── Treemap clicks ──────────────────────────────────────────────────────────

def clicked_label(click):
    """The label of a clicked treemap tile, or None. A treemap point always
    carries one; a hand-built request need not, so anything else is None."""
    points = click.get("points") if isinstance(click, dict) else None
    if not points or not isinstance(points, list) or not isinstance(points[0], dict):
        return None
    return points[0].get("label") or None


# ── Detail panels ───────────────────────────────────────────────────────────

def _stat(label, value, colour):
    return html.Div(className="bp-stat", children=[
        html.P(label, className="bp-stat-label"),
        html.P(value, className="bp-stat-value", style={"color": colour}),
    ])


def sku_panel(row_, colour):
    """The Rakuten tile detail, from bp.figures.sku_detail()."""
    return html.Div(className="bp-detail", style={"borderLeftColor": colour}, children=[
        html.Div(className="bp-detail-name", children=[
            html.P(row_["label"], className="bp-detail-title"),
            html.P(row_["tier_group"].capitalize(), className="bp-detail-sub"),
        ]),
        _stat("Items in pull", f"{int(row_['sku_count']):,}", colour),
        _stat("Median price", f"¥{int(row_['med_price']):,}", colour),
        _stat("Avg rating (rated SKUs)",
              f"{row_['avg_rating']:.2f} ★ · {row_['rated_share']:.0%} rated", colour),
    ])


def detail_prompt(text):
    return html.Div(html.Span(text), className="bp-detail-prompt")
