"""Beauty Pulse palette, the Plotly layout helpers every chart shares, and the
chart template the Dash app applies."""

import plotly.graph_objects as go

C = {
    "bg":      "#FAFAF8",
    "card":    "#FFFFFF",
    "border":  "#E8E5E0",
    "text":    "#2D2D2D",
    "muted":   "#8E8E93",
    "grid":    "#F0EDE8",
    "skin":    "#4A90B8",
    "cosm":    "#C4627A",
    "ingr":    "#5B8C6E",
    "korean":  "#D4785C",
    "gold":    "#B8965A",
    "skin_lt": "#D6E8F5",
    "cosm_lt": "#F5DDE3",
    # The exhibit language (mockup v3): ink carries text and the one accent on
    # an exhibit whose title is not about skincare against makeup; rule draws
    # the hairlines; pos and neg mark direction in the funnel matrix and in-cell
    # bars only.
    "ink":     "#1F1F1F",
    "rule":    "#E2DFD9",
    "pos":     "#3E7CA6",
    "neg":     "#C4843A",
}

# ── Chart colours ───────────────────────────────────────────────────────────
# The category colours are the Streamlit app's, and each one belongs to its
# entity on every chart: skincare blue, makeup rose, sunscreen gold, actives
# green, Korea orange. Actives green and makeup rose are hard to tell apart
# with red-green colour blindness, and green sits close to skincare blue, so
# green marks the actives only in a block of their own.
SIDE = {"skincare": C["skin"], "makeup": C["cosm"], "sunscreen": C["gold"]}
# Series that are not a category take these. Every set drawn together was
# checked with the dataviz validator: each pair at least 15 apart for normal
# vision and 8 for colour-blind readers, or told apart by a dash and a label.
PURPLE, CHARCOAL, TEAL, AMBER = "#7B5EA7", "#37474F", "#4DB6AC", "#E0A93B"
SKIN_DEEP, SKIN_LIGHT = "#1F4E79", "#9CC3DC"
CONTEXT = C["muted"]          # context series: grey, and dashed where it sits beside a colour
ORIGIN = {"KR": C["korean"], "JP": CHARCOAL, "global": PURPLE, "CN": TEAL}


def _base(height=420):
    return dict(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", color=C["text"], size=12),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=C["card"], font_color=C["text"], font_size=12),
    )

def _xax(**kw):
    d = dict(gridcolor=C["grid"], linecolor=C["border"],
             zerolinecolor=C["border"], zerolinewidth=1)
    d.update(kw)
    return d

def _yax(title="", suffix="", **kw):
    d = dict(title=dict(text=title, font=dict(size=11)),
             gridcolor=C["grid"], linecolor=C["border"],
             zerolinecolor=C["border"], ticksuffix=suffix)
    d.update(kw)
    return d


# ── Chart template ──────────────────────────────────────────────────────────
# Streamlit's chart look: its placeholder template with the light theme's
# colours and fonts filled in, as its frontend resolved them at draw time
# (Streamlit 1.62, read from the browser), so that the Dash app drew the charts
# as the Streamlit app it replaced did. The builders set no template; the Dash
# app applies TEMPLATE figure by figure (dashboard/ui.py).
#
# Three departures. The font: Streamlit's is Source Sans, which the Dash page
# does not load, so FONT is the page's stack (style.css --font). Titles:
# Streamlit bolded them by wrapping title.text in <b>, which is outside the
# template, so the weight is set here instead. "transparent", which plotly.py
# rejects, is written rgba(0,0,0,0). Left out: Streamlit's settings for
# ternary plots and range selectors, which no chart has, and its trace
# defaults, which resolve as Plotly's own do for the traces drawn here.

FONT = ('system-ui, -apple-system, "Hiragino Sans", "Hiragino Kaku Gothic ProN", '
        '"Noto Sans JP", "Yu Gothic", Meiryo, sans-serif')

_ST_TEXT = "#808495"      # chart text: ticks, axis titles, colorbar, hover
_ST_HEAD = "#31333F"      # chart titles
_ST_LEGEND = "#262730"
_ST_LINE = "#e6eaf1"      # grid, zero line, ticks
_ST_BG = "#ffffff"
_ST_BORDER = "rgba(49, 51, 63, 0.2)"
_CLEAR = "rgba(0,0,0,0)"


def _scale(colours):
    """Ten colours at even steps, as Streamlit spaces its scales."""
    return [[i / 9, c] for i, c in enumerate(colours)]


_SEQ = _scale(["#e4f5ff", "#c7ebff", "#a6dcff", "#83c9ff", "#60b4ff",
               "#3d9df3", "#1c83e1", "#0068c9", "#0054a3", "#004280"])
_DIV = _scale(["#7d353b", "#bd4043", "#ff4b4b", "#ff8c8c", "#ffc7c7",
               "#a6dcff", "#60b4ff", "#1c83e1", "#0054a3", "#004280"])
_TICKS = dict(color=_ST_TEXT, size=12)
_AXIS_TITLE = dict(color=_ST_TEXT, size=14)

TEMPLATE = go.layout.Template(layout=dict(
    font=dict(color=_ST_TEXT, family=FONT, size=12, weight=400),
    title=dict(font=dict(family=FONT, size=16, color=_ST_HEAD, weight=700),
               pad=dict(l=4), xanchor="left", x=0),
    legend=dict(title=dict(font=dict(size=12, color=_ST_TEXT), side="top"), valign="top",
                bordercolor=_CLEAR, borderwidth=0, font=dict(size=12, color=_ST_LEGEND)),
    paper_bgcolor=_ST_BG,
    plot_bgcolor=_ST_BG,
    xaxis=dict(showgrid=False, gridcolor=_ST_LINE, zeroline=False, zerolinecolor=_ST_LINE,
               tickcolor=_ST_LINE, tickfont=_TICKS, minor=dict(gridcolor=_ST_LINE),
               title=dict(font=_AXIS_TITLE, standoff=20), automargin=True),
    yaxis=dict(gridcolor=_ST_LINE, zerolinecolor=_ST_LINE, ticklabelposition="outside",
               tickcolor=_ST_LINE, tickfont=_TICKS, minor=dict(gridcolor=_ST_LINE),
               title=dict(font=_AXIS_TITLE, standoff=24), automargin=True),
    margin=dict(pad=8, r=0, l=0),
    hoverlabel=dict(bgcolor=_ST_BG, bordercolor=_ST_BORDER,
                    font=dict(color=_ST_TEXT, family=FONT, size=12)),
    coloraxis=dict(colorscale=_SEQ, colorbar=dict(
        thickness=16, len=0.75, y=0.5745, xpad=24, ticklabelposition="outside",
        outlinecolor=_CLEAR, outlinewidth=8, tickfont=_TICKS,
        title=dict(font=_AXIS_TITLE))),
    colorscale=dict(sequential=_SEQ, sequentialminus=_SEQ, diverging=_DIV),
    colorway=["#0068c9", "#83c9ff", "#ff2b2b", "#ffabab", "#29b09d",
              "#7defa1", "#ff8700", "#ffd16a", "#6d3fc0", "#d5dae5"],
))


# ── Exhibit finish ──────────────────────────────────────────────────────────
# Mockup v3 finished every chart the same way over the template: a clear
# background, the page's ink for text, and quieter grid and axis lines. The
# builders set their own axis colours, which a template cannot override, so
# this is applied to the figure after them (ui.themed).
_FINISH_TEXT = "#3A3A3A"
_FINISH_GRID = "#ECEAE5"
_FINISH_LINE = "#D9D6D0"


def finish(figure):
    """The figure with v3's finish on its background, text and every axis."""
    figure.update_layout(paper_bgcolor=_CLEAR, plot_bgcolor=_CLEAR,
                         font=dict(family=FONT, color=_FINISH_TEXT))
    figure.update_xaxes(gridcolor=_FINISH_GRID, zerolinecolor=_FINISH_LINE,
                        linecolor=_FINISH_LINE)
    figure.update_yaxes(gridcolor=_FINISH_GRID, zerolinecolor=_FINISH_LINE,
                        linecolor=_FINISH_LINE)
    return figure
