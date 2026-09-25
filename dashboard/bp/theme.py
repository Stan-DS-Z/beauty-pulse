"""Beauty Pulse palette and the Plotly layout helpers every chart shares."""

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
