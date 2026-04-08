"""
signal_pulse/src/viz.py
────────────────────────
Shared visualisation helpers for Signal/Pulse notebooks.
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np


# ── Palette ───────────────────────────────────────────────────────────────────

PALETTE = {
    'skincare':          '#1565C0',
    'cosmetics':         '#C62828',
    'skincare_light':    '#BBDEFB',
    'cosmetics_light':   '#FFCDD2',
    'pre_covid':         '#78909C',
    'post_covid':        '#1B5E20',
    'bg':                '#FAFAFA',
    'grid':              '#E0E0E0',
    'text':              '#212121',
    'text_secondary':    '#757575',
    'neutral':           '#546E7A',
    'border':            '#BDBDBD',
}


# ── Style helpers ─────────────────────────────────────────────────────────────

def apply_style():
    import matplotlib.font_manager as fm

    JP_FONT_PRIORITY = [
        "Noto Sans CJK JP", "Hiragino Sans", "Yu Gothic",
        "BIZ UDGothic", "Meiryo", "IPAexGothic",
        "IPAGothic", "TakaoGothic", "MS Gothic",
    ]
    available_names = {f.name for f in fm.fontManager.ttflist}
    jp_font = next((f for f in JP_FONT_PRIORITY if f in available_names), None)

    if jp_font:
        plt.rcParams["font.family"] = jp_font
        print(f"Font: {jp_font} ✓")
    else:
        print("Warning: no Japanese font found — text may render as boxes.")

    try:
        import seaborn as sns
        sns.set_style('whitegrid', {'grid.color': PALETTE['grid'], 'axes.facecolor': PALETTE['bg']})
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
    if jp_font:
        plt.rcParams["font.family"] = jp_font


def fig_ax(w=10, h=5, nrows=1, ncols=1, **kwargs):
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
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        print(f"Saved → {path}")


def annotate_covid(ax, x=2019.5, label="COVID\n2020",
                   color='#90A4AE', fontsize=8.5):
    ymin, ymax = ax.get_ylim()
    ax.axvline(x, color=color, linewidth=1.2, linestyle='--', alpha=0.7, zorder=1)
    ax.text(x + 0.05, ymax * 0.96, label,
            fontsize=fontsize, color=color, va='top', ha='left', linespacing=1.4)


def check_nlp_deps():
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
        print("Missing packages:")
        print("  pip install sudachipy sudachidict-core scikit-learn wordcloud")


# ── Word cloud ────────────────────────────────────────────────────────────────

def wordcloud_jp(freq_dict, title="", colormap="Blues",
                 output_path=None, width=1200, height=600,
                 background_color='white',
                 max_words=40, min_font_size=14):
    """
    Render a publication-quality word cloud from a {term: score} dict.

    Parameters
    ----------
    freq_dict        : dict  {term: weight}
    title            : str   chart title
    colormap         : str   matplotlib colormap name
    output_path      : str   save path (None = don't save)
    width / height   : int   canvas size in pixels (default 1200×600)
    max_words        : int   maximum terms to render (default 40 for note.com quality)
    min_font_size    : int   smallest font in the cloud (default 14)
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("wordcloud not installed. Run: pip install wordcloud")
        return

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
        max_words=max_words,
        min_font_size=min_font_size,
        prefer_horizontal=0.85,
        collocations=False,
        margin=6,
    ).generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(width / 100, height / 100))
    fig.patch.set_facecolor('white')
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12,
                     color=PALETTE['text'])
    plt.tight_layout(pad=0.5)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Saved → {output_path}")
    plt.show()
