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
}


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
# colours and fonts filled in, as its frontend resolves them at draw time
# (Streamlit 1.62, read from the browser). The builders set no template, so
# Streamlit's own applies to what Streamlit draws: importing Streamlit makes
# it Plotly's process-wide default. A template set in _base would replace it
# there too, so only the Dash app applies TEMPLATE, figure by figure
# (dashboard/ui.py).
#
# Three departures. The font: Streamlit's is Source Sans, which the Dash page
# does not load, so FONT is the page's stack (style.css --font). Titles:
# Streamlit bolds them by wrapping title.text in <b>, which is outside the
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
