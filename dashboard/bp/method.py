"""The Method page, the report's appendix: what each source measures and
covers, the series breaks with METI's yen per kg, the seasonal method and the
launch chi-square table, the launch classifier, coverage, and the record of
the review-vocabulary test behind Revision 20.

A report page: every figure is computed from the frozen edition, cut at the
edition's cut-off (sources.CUTOFF), or taken from the Market and Timing
figures, so the pages that use one figure cannot disagree on it. The
review-vocabulary record is build_convergence.py's three files, added to the
2026-09 edition on 30 September 2026. strings.py words these figures and
tests/test_method.py holds the data to each direction the copy states. Like
data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from .data import load_meti_monthly, load_review_map, load_umap
from .market import BREAK_CONTROLS, BREAK_LINES
from .sources import DECLARED, REPORT_PAGES

# The @cosme category whose reviews by year the coverage note names, and the
# category whose first reviewed year it names.
COVERAGE_CATEGORY = "serum_essence"
LATE_CATEGORY = "foundation"
# The convergence checks, in the order the table lists them.
CHECKS = ("baseline", "without_phrases", "products_in_both", "both")


def _sources(ASSETS: Path, registry: dict, market: dict) -> list:
    """One row per declared source: the registry's dates and pages, and the
    counts the edition's files hold."""
    umap, rmap = load_umap(ASSETS), load_review_map(ASSETS)
    yt = pd.read_csv(ASSETS / "nb07_yt_channels.csv")
    feeds = pd.read_csv(ASSETS / "prtimes_feeds.csv")
    core = feeds[feeds["panel"] == "core"]
    counts = {
        "meti": dict(lines=market["keys"]["n_items"]),
        "prtimes": dict(feeds=len(core), issuers=core["issuer_group"].nunique()),
        "cosme": dict(reviews=len(umap), categories=rmap["category"].nunique(),
                      first=int(umap["review_year"].min())),
        "youtube": dict(videos=int(yt["video_count"].sum()), channels=len(yt),
                        queries=yt["search_category"].nunique()),
    }
    rows = []
    for key in DECLARED:
        src = registry[key]
        rows.append(dict(key=key, src=src, counts=counts.get(key, {}),
                         pages=[p for p in REPORT_PAGES if p in src.used_on]))
    return rows


def _price_per_kg(ASSETS: Path, cutoff: str, market: dict) -> dict:
    """Yen per kg by month for the lines with the January 2022 step and the
    lines set against them; the step itself is Market's."""
    _, ypk = load_meti_monthly(ASSETS, cutoff)
    y0 = market["window"][0]
    return dict(frame=ypk[BREAK_LINES + BREAK_CONTROLS], lines=BREAK_LINES,
                controls=BREAK_CONTROLS, year=y0, drop=market["brk"]["drop"],
                range=market["brk"]["range"], pre=market["brk"]["pre"])


def _trade_code(ASSETS: Path, cutoff: str) -> dict:
    """HS 3304.99-010 in the import file: the years it carries and its value
    in the last of them (億円)."""
    tr = pd.read_csv(ASSETS / "estat_trade_hs3304.csv", dtype={"hs_code": str})
    # Whole years inside the cut, as the registry dates the source.
    tr = tr[(tr["flow"] == "import") & (tr["year"] * 100 + 12 <= int(cutoff.replace("-", "")))]
    code = tr[tr["hs_code"] == "330499010"].groupby("year")["value_1000jpy"].sum() / 1e5
    total = tr.groupby("year")["value_1000jpy"].sum() / 1e5
    y = int(code.index.max())
    return dict(first=int(code.index.min()), year=y, value=float(code[y]),
                share=float(100 * code[y] / total[y]))


def _youtube_queries(ASSETS: Path) -> pd.Series:
    """How many YouTube search categories each side's videos came from."""
    yt = pd.read_csv(ASSETS / "nb07_yt_channels.csv")
    return yt.groupby("tier_group")["search_category"].nunique()


def _reviews_by_year(ASSETS: Path) -> pd.DataFrame:
    """Embedded @cosme reviews by category and year."""
    pts = load_umap(ASSETS).merge(load_review_map(ASSETS), on="review_id", validate="one_to_one")
    return pts.groupby(["category", "review_year"]).size().unstack(fill_value=0)


def _convergence(ASSETS: Path) -> dict:
    """build_convergence.py's record: the size curve, the checks and the
    products behind each period's slices."""
    checks = pd.read_csv(ASSETS / "convergence_checks.csv").set_index("check").loc[list(CHECKS)]
    curve = pd.read_csv(ASSETS / "convergence_curve.csv")
    per = pd.read_csv(ASSETS / "convergence_periods.csv")
    base = checks.loc["baseline"]
    periods = (base["early_period"], base["late_period"])
    per = per[per["period"].isin(periods)].set_index(["side", "period"])
    return dict(checks=checks, curve=curve, periods=periods, per=per, n=int(base["n"]),
                early=float(base["early"]), late=float(base["late"]))


def compute_method(ASSETS: Path, cutoff: str, market: dict, timing: dict, registry: dict) -> dict:
    """The Method page's figures on data up to `cutoff` ("YYYY-MM"), with the
    Market and Timing figures (market.compute_market, timing.compute_timing)
    and the report's source registry on the same edition."""
    from . import seasonal
    sun = timing["sun"]["search"]
    a, b = sun["run"]
    run_months = [(a + k - 1) % 12 + 1 for k in range((b - a) % 12 + 1)]
    return dict(
        cutoff=cutoff,
        sources=_sources(ASSETS, registry, market),
        price=_price_per_kg(ASSETS, cutoff, market),
        trade=_trade_code(ASSETS, cutoff),
        seasonal=dict(window=seasonal.RATIO_WINDOW, years=seasonal.FULL_YEARS,
                      tolerance=seasonal.PEAK_TOLERANCE, run=seasonal.PEAK_RUN,
                      swing=seasonal.SEARCH_SWING, crit=seasonal.CHI2_11_05,
                      sun_term=timing["sun_term"], sun_run=(a, b),
                      sun_values=[float(sun["profile"][m]) for m in run_months]),
        tests=timing["tests"],
        youtube=_youtube_queries(ASSETS),
        reviews=_reviews_by_year(ASSETS),
        cosme_to=registry["cosme"].data_to,
        convergence=_convergence(ASSETS),
    )
