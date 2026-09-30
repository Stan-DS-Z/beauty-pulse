"""The Timing page: seasonality by stage, on one method (bp/seasonal.py).

A report page: every figure is computed from the frozen edition, cut at the
edition's cut-off (sources.CUTOFF). Shipments are METI's 16 product lines
(funnel.CATEGORIES), search is block_A's eight category words and two
umbrella terms (trends_monthly.csv), and launches are the PR TIMES core
panel. Seasonal ratios run over seasonal.RATIO_WINDOW for every series.
strings.py words these figures and tests/test_timing.py holds the data to
each direction the copy states. Like data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from . import seasonal
from .brief import _core, _meti_monthly_value
from .data import load_trends_monthly
from .demand import UMBRELLA
from .funnel import CATEGORIES

# The launch sides tested, and the years whose twelve months are all inside
# the launch window and the cut-off.
LAUNCH_SIDES = ("skincare", "makeup")
LAUNCH_YEARS = (2022, 2023, 2024, 2025)


def _band(series: pd.Series) -> pd.DataFrame:
    """Each calendar month's lowest and highest yearly ratio in the window."""
    r = seasonal.window(seasonal.ratio(series))
    g = r.groupby(r.index.month)
    return pd.DataFrame({"lo": g.min(), "hi": g.max()})


def _stage(series: pd.Series) -> dict:
    a = seasonal.assess(series)
    return dict(profile=a["profile"], band=_band(series), run=a["run"][:2],
                year_runs=seasonal.year_runs(series), peak=a["peak"], stable=a["stable"])


def _grid(series: dict, names: dict, rule) -> pd.DataFrame:
    """One row per series: its profile by month, peak month, and whether it
    passes `rule`; ordered by peak month."""
    rows = []
    for key, s in series.items():
        a = seasonal.assess(s)
        row = dict(key=key, name=names[key], peak=a["peak"], stable=a["stable"],
                   swing=a["swing"], passes=rule(a), lo=a["trough_ratio"], hi=a["peak_ratio"])
        row.update({m: float(a["profile"][m]) for m in range(1, 13)})
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["peak", "hi"], ascending=[True, False]).set_index("key")


def compute_timing(ASSETS: Path, cutoff: str) -> dict:
    """The Timing page's figures on data up to `cutoff` ("YYYY-MM")."""
    mv = _meti_monthly_value(ASSETS, cutoff)
    tm = load_trends_monthly(ASSETS, cutoff)
    search = {t: seasonal.monthly(g, "interest") for t, g in tm.groupby("term")}
    sun_line, _, sun_term, _ = CATEGORIES["sunscreen"]

    # ── Sunscreen by stage, in funnel order: search, then shipments
    sun = dict(search=_stage(search[sun_term]), ship=_stage(mv[sun_line]))
    sun["offset"] = {y: sun["search"]["year_runs"][y][0] - sun["ship"]["year_runs"][y][0]
                     for y in seasonal.FULL_YEARS}

    # ── Shipments: the 16 lines; a line passes when its peak is stable
    ship = _grid({k: mv[li] for k, (li, *_) in CATEGORIES.items()},
                 {k: li for k, (li, *_) in CATEGORIES.items()}, lambda a: a["stable"])

    # ── Search: the category words and the umbrella terms; a term passes when
    # its peak is stable and it swings more than SEARCH_SWING index points
    words = {k: t for k, (_, _, t, _) in CATEGORIES.items() if t}
    words.update({t: t for t in UMBRELLA})
    srch = _grid({k: search[t] for k, t in words.items()}, words,
                 lambda a: a["stable"] and a["swing"] > seasonal.SEARCH_SWING)

    # ── Launch releases by month, per side and year, against an even spread
    core = _core(ASSETS, cutoff)
    core = core[core["year"].isin(LAUNCH_YEARS)].assign(m=lambda d: d["month"].str[5:7].astype(int))
    counts = {side: (core[core["category_group"] == side].groupby(["year", "m"]).size()
                     .unstack(fill_value=0).reindex(index=list(LAUNCH_YEARS),
                                                    columns=range(1, 13), fill_value=0))
              for side in LAUNCH_SIDES}
    tests = pd.DataFrame([dict(side=side, year=y, n=int(c.loc[y].sum()),
                               chi2=seasonal.chi2_even(c.loc[y]),
                               top_month=int(c.loc[y].idxmax()), top_n=int(c.loc[y].max()))
                          for side, c in counts.items() for y in LAUNCH_YEARS])
    tests["even"] = tests["chi2"] < seasonal.CHI2_11_05
    sun_launch = (core[core["category"].str.split("|").apply(lambda t: "sunscreen" in t)]
                  .groupby("year").size().reindex(list(LAUNCH_YEARS), fill_value=0))

    return dict(cutoff=cutoff, sun=sun, ship=ship, search=srch, sun_term=sun_term,
                counts=counts, tests=tests, sun_launch=sun_launch)
