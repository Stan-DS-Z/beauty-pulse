"""Method: the report's appendix. What each source measures and covers, the
series breaks with METI's yen per kg, the seasonal method and the launch
chi-square table, the launch classifier, coverage, and the review-vocabulary
record (Revision 20).
A report page: no controls, one edition date, every exhibit a result with its
source line."""

import dash
from dash import html

import data_cache
import ui
from bp import figures

PATH = "/method"
dash.register_page(__name__, path=PATH, name="Method", order=6,
                   title="Beauty Pulse · Japanese Beauty Market")

D = data_cache.load()


def _table(head, rows, cls=""):
    """A table whose cells wrap; rows are lists of cells, each a string or a
    (text, className) pair."""
    cell = lambda c: html.Td(c[0], className=c[1]) if isinstance(c, tuple) else html.Td(c)  # noqa: E731
    return html.Div(html.Table([html.Thead(html.Tr([html.Th(h) for h in head])),
                                html.Tbody([html.Tr([cell(c) for c in r]) for r in rows])],
                               className=f"bp-table wrap {cls}".strip()),
                    className="bp-tablewrap")


def _sources(S, M):
    rows = [[(name, "bp-src-name"), measures, coverage,
             (pages, "" if r["pages"] else "muted")]
            for r, (name, measures, coverage, pages) in zip(M["sources"], S["me_s_rows"])]
    return _table(S["me_s_cols"], rows, "stack")


def _chi(S, M):
    rows = []
    for _, r in M["tests"].iterrows():
        ink = "" if r["even"] else "bp-ink"
        rows.append([(S["me_side"][r["side"]], ink), (str(r["year"]), ink),
                     (f"{r['n']}", f"num {ink}".strip()), (f"{r['chi2']:.1f}", f"num {ink}".strip()),
                     (S["me_q_month"].format(m=S["me_months"][r["top_month"] - 1], n=r["top_n"]),
                      ink)])
    return _table(S["me_q_cols"], rows)


def _checks(S, M):
    cv = M["convergence"]
    rows = []
    for key, r in cv["checks"].iterrows():
        label = [S["me_check"][key], html.Br(),
                 html.Span(S["me_k_n"].format(n=int(r["n"])), className="muted")]
        rows.append([(label, "bp-ink" if key == "products_in_both" else ""),
                     (f"{r['early']:.3f}", "num"), (f"{r['late']:.3f}", "num"),
                     ([f"{r['delta']:+.3f}", html.Br(),
                       html.Span(S["me_k_ci"].format(lo=r["ci_lo"], hi=r["ci_hi"]),
                                 className="muted")], "num")])
    return _table(S["me_k_cols"], rows)


def _periods(S, M):
    per = M["convergence"]["per"]
    rows = [[S["me_side"][side], S["me_period"][period], (f"{r['products']}", "num"),
             (f"{r['reviews']:,}", "num")] for (side, period), r in per.iterrows()]
    return _table(S["me_p_cols"], rows)


def _exhibit(S, key, body, src):
    return html.Div([ui.chart_head(S[f"me_{key}_h"], S[f"me_{key}_e"]), body, ui.source(S[src])])


def build(lang, d):
    S, M = d.S[lang], d.METHOD
    return html.Div(className="bp-page", lang="ja" if lang == "jp" else "en", children=[
        ui.header(S, lang, PATH),
        ui.kicker(S["me_kicker"]),
        ui.intro(S["me_intro"]),
        html.Div([ui.chart_head(S["me_s_h"], S["me_s_e"]), _sources(S, M)]),
        ui.row(ui.section(S["me_b_t"], [S["me_b_meti"], S["me_b_trends"], S["me_b_trade"]]),
               _exhibit(S, "pk", ui.graph("me-fig-price", figures.fig_method_price_kg(M, S)),
                        "me_src_meti")),
        ui.row(ui.section(S["me_z_t"], [S["me_z_ratio"], S["me_z_peak"], S["me_z_swing"],
                                        S["me_z_chi"]]),
               _exhibit(S, "q", _chi(S, M), "me_src_prtimes")),
        ui.row(ui.section(S["me_l_t"], [S["me_l_b"]]),
               ui.section(S["me_c_t"], [S["me_c_pr"], S["me_c_cosme"], S["me_c_yt"]])),
        ui.section(S["me_v_t"], [S["me_cv_line"]]),
        _exhibit(S, "v", ui.graph("me-fig-curve", figures.fig_method_curve(M, S)), "me_src_cosme"),
        ui.row(_exhibit(S, "k", _checks(S, M), "me_src_cosme"),
               _exhibit(S, "p", _periods(S, M), "me_src_cosme")),
    ])


TREES = {lang: build(lang, D) for lang in data_cache.LANGS}


def layout(lang="en", **_):
    return TREES[ui.lang_of(lang)]
