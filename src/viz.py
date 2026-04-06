"""
signal_pulse/src/viz.py
────────────────────────
Shared visualisation helpers for Signal/Pulse notebooks.
Import at the top of any NB04+ notebook:

    from src.viz import (
        PALETTE, fig_ax, tight, annotate_covid,
        apply_style, check_nlp_deps, wordcloud_jp
    )
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np


# ── Palette ───────────────────────────────────────────────────────────────────

PALETTE = {
    # Tier colours
    'skincare':          '#1565C0',
    'cosmetics':         '#C62828',
    'skincare_light':    '#BBDEFB',
    'cosmetics_light':   '#FFCDD2',
    # Period colours
    'pre_covid':         '#78909C',
    'post_covid':        '#1B5E20',
    # Chart chrome
    'bg':                '#FAFAFA',
    'grid':              '#E0E0E0',
    'text':              '#212121',
    'text_secondary':    '#757575',
    'neutral':           '#546E7A',
    'border':            '#BDBDBD',
}


# ── Style helpers ─────────────────────────────────────────────────────────────

def apply_style():
    """
    Apply consistent rcParams and activate Japanese font.
    Uses the same font detection approach as the Masstige project.
    Call once at notebook start (Cell 4).
    """
    import matplotlib.font_manager as fm

    # ── Japanese font — check what's actually available in the system ─────
    # Priority order: Windows system fonts first (always present),
    # then common Linux/Mac alternatives, then pip-installed fallbacks
    JP_FONT_PRIORITY = [
        "Noto Sans CJK JP",   # pip install mplfonts → mplfonts init (preferred)
        "Hiragino Sans",      # macOS built-in — clean and modern
        "Yu Gothic",          # Windows 8.1+ built-in — modern
        "BIZ UDGothic",       # Windows 10+ built-in — clean
        "Meiryo",             # Windows built-in
        "IPAexGothic",        # pip install japanize-matplotlib
        "IPAGothic",          # Linux
        "TakaoGothic",        # Ubuntu
        "MS Gothic",          # Windows fallback — functional but less elegant
    ]

    available_names = {f.name for f in fm.fontManager.ttflist}
    jp_font = None
    for font in JP_FONT_PRIORITY:
        if font in available_names:
            jp_font = font
            break

    if jp_font:
        plt.rcParams["font.family"] = jp_font
        print(f"Font: {jp_font} ✓")
    else:
        print("Warning: no Japanese font found — text may render as boxes.")
        print(f"Available fonts with CJK in name: "
              f"{[f for f in available_names if any(x in f for x in ['Gothic','Mincho','CJK','IPA'])]}")

    # ── Chart style ───────────────────────────────────────────────────────
    try:
        import seaborn as sns
        sns.set_style('whitegrid', {
            'grid.color': PALETTE['grid'],
            'axes.facecolor': PALETTE['bg'],
        })
    except ImportError:
        pass

    plt.rcParams.update({
        'figure.facecolor':   'white',
        'axes.facecolor':     PALETTE['bg'],
        'axes.spines.top':    False,
        'axes.spines.right':  False,
        'axes.edgecolor':     PALETTE['border'],
        'grid.color':         PALETTE['grid'],
        'grid.linewidth':     0.7,
        'xtick.color':        '#424242',
        'ytick.color':        '#424242',
        'axes.labelcolor':    PALETTE['text'],
        'axes.titlecolor':    PALETTE['text'],
        'axes.titleweight':   'bold',
        'axes.titlesize':     13,
        'axes.labelsize':     11,
        'legend.framealpha':  0.9,
        'legend.edgecolor':   PALETTE['grid'],
        'figure.dpi':         120,
    })

    # Re-apply font after rcParams.update (which can reset it)
    if jp_font:
        plt.rcParams["font.family"] = jp_font


def fig_ax(w=10, h=5, nrows=1, ncols=1, **kwargs):
    """
    Return (fig, ax) or (fig, axes) with Signal/Pulse styling.
    Drop-in replacement for plt.subplots().
    """
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), **kwargs)
    fig.patch.set_facecolor('white')

    ax_list = np.array(axes).flatten() if nrows * ncols > 1 else [axes]
    for ax in ax_list:
        ax.set_facecolor(PALETTE['bg'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(PALETTE['border'])
        ax.spines['bottom'].set_color(PALETTE['border'])
        ax.tick_params(colors='#424242')
        ax.grid(axis='y', color=PALETTE['grid'], linewidth=0.7, alpha=0.8)

    return fig, axes


def tight(fig, path=None, dpi=150):
    """
    fig.tight_layout() + optional save to disk.

    Usage:
        tight(fig)                         # just tighten
        tight(fig, "../outputs/foo.png")   # tighten + save
    """
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        print(f"Saved → {path}")


def annotate_covid(ax, x=2019.5, label="COVID\n2020",
                   color='#90A4AE', fontsize=8.5):
    """
    Draw a vertical dashed line at the COVID inflection point
    with a label. Call after plotting data, before tight().

    Parameters
    ----------
    ax    : matplotlib Axes
    x     : float  x-position of the line (default 2019.5)
    label : str    annotation text
    """
    ymin, ymax = ax.get_ylim()
    ax.axvline(x, color=color, linewidth=1.2,
               linestyle='--', alpha=0.7, zorder=1)
    ax.text(x + 0.05, ymax * 0.96, label,
            fontsize=fontsize, color=color,
            va='top', ha='left', linespacing=1.4)


# ── Dependency check ──────────────────────────────────────────────────────────

def check_nlp_deps():
    """Print status of all NB04 NLP dependencies."""
    deps = [
        ('sudachipy',           'SudachiPy tokeniser'),
        ('sudachidict_core',    'Sudachi dictionary (core)'),
        ('sklearn',             'scikit-learn (TF-IDF)'),
        ('japanize_matplotlib', 'Japanese font helper'),
        ('wordcloud',           'WordCloud (optional, Section 7)'),
    ]
    print("NB04 — NLP dependency check")
    print("-" * 44)
    all_ok = True
    for module, label in deps:
        try:
            m = __import__(module)
            ver = getattr(m, '__version__', '✓')
            print(f"  ✓  {label:<35} {ver}")
        except ImportError:
            print(f"  ✗  {label:<35} NOT INSTALLED")
            all_ok = False
    print()
    if all_ok:
        print("All dependencies satisfied. ✓")
    else:
        print("Missing packages. In your terminal:")
        print("  conda activate beauty-pulse")
        print("  pip install sudachipy sudachidict-core scikit-learn")
        print("  pip install japanize-matplotlib wordcloud")


# ── Word cloud ────────────────────────────────────────────────────────────────

def wordcloud_jp(freq_dict, title="", colormap="Blues",
                 output_path=None, width=900, height=500,
                 background_color='white'):
    """
    Render a word cloud from a {term: score} dict.
    Requires: pip install wordcloud

    Parameters
    ----------
    freq_dict    : dict  {term: weight}
    title        : str   chart title (Japanese OK with japanize_matplotlib)
    colormap     : str   matplotlib colormap name
    output_path  : str   save path, e.g. "../outputs/wc.png" (None = don't save)
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("wordcloud not installed. Run: pip install wordcloud")
        return

    # Find a Japanese-capable font bundled with japanize_matplotlib
    font_path = None
    try:
        font_path = fm.findfont(
            fm.FontProperties(family='IPAexGothic'), fallback_to_default=False
        )
    except Exception:
        pass

    wc = WordCloud(
        width=width,
        height=height,
        background_color=background_color,
        colormap=colormap,
        font_path=font_path,
        max_words=80,
        prefer_horizontal=0.7,
        collocations=False,
        margin=4,
    ).generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(width / 100, height / 100))
    fig.patch.set_facecolor('white')
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10,
                     color=PALETTE['text'])
    plt.tight_layout(pad=0.5)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor='white')
        print(f"Saved → {output_path}")
    plt.show()
