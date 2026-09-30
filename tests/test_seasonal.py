"""The seasonal method (bp/seasonal.py) and the figures the architect's check
of 30 September 2026 reported on the 2026-09 edition. A rebuilt edition that
moves one of them fails here and is reported before any copy changes."""

import numpy as np
import pandas as pd
import pytest

from bp import brief, data, seasonal, sources
from bp.demand import UMBRELLA
from bp.funnel import CATEGORIES

E = sources.edition_assets(data.ASSETS)
MONTHS = pd.date_range("2019-01-01", "2026-08-01", freq="MS")


# ── The method ──────────────────────────────────────────────────────────────

def test_a_trend_alone_has_no_season():
    """A series falling steadily through every year: the calendar-year mean
    reads it as a January peak, the centred ratio reads it as flat."""
    s = pd.Series(np.linspace(200, 100, len(MONTHS)), index=MONTHS)
    f = s.groupby([s.index.year, s.index.month]).first().unstack()
    year_mean = (f.div(f.mean(axis=1), axis=0) * 100).mean()
    assert year_mean.idxmax() == 1 and year_mean.max() > 103
    prof = seasonal.profile(s)
    assert prof.max() - prof.min() < 1


def test_a_pure_season_is_found_and_stable():
    s = pd.Series([100 + (30 if m.month == 7 else 0) for m in MONTHS], index=MONTHS)
    a = seasonal.assess(s)
    assert a["peak"] == 7 and a["stable"] and set(a["year_peaks"].values()) == {7}


def test_the_ratio_is_centred_on_the_month():
    s = pd.Series(np.arange(len(MONTHS), dtype=float) + 100, index=MONTHS)
    r = seasonal.ratio(s)
    assert r.dropna().round(9).eq(100).all()          # a straight line is its own average


def test_the_even_spread_test():
    assert seasonal.chi2_even([10] * 12) == 0
    assert seasonal.chi2_even([10] * 11 + [40]) > seasonal.CHI2_11_05


# ── The architect's check on the 2026-09 edition ───────────────────────────

@pytest.fixture(scope="module")
def meti():
    return brief._meti_monthly_value(E, sources.CUTOFF)


@pytest.fixture(scope="module")
def search():
    tm = data.load_trends_monthly(E, sources.CUTOFF)
    return {t: seasonal.monthly(g, "interest") for t, g in tm.groupby("term")}


def test_six_of_sixteen_lines_have_a_stable_shipment_peak(meti):
    got = {k: (a["peak"], round(a["peak_ratio"]))
           for k, (li, *_) in CATEGORIES.items()
           for a in [seasonal.assess(meti[li])] if a["stable"]}
    assert got == {"sunscreen": (2, 160), "foundation": (3, 116), "lip_balm": (9, 154),
                   "lipstick": (10, 133), "powder": (11, 172), "cream": (12, 130)}


def test_sunscreen_search_swings_far_more_than_the_other_words(search):
    words = [t for _, _, t, _ in CATEGORIES.values() if t] + list(UMBRELLA)
    sw = {t: seasonal.assess(search[t]) for t in words}
    sun = CATEGORIES["sunscreen"][2]
    assert (round(sw[sun]["trough_ratio"]), round(sw[sun]["peak_ratio"])) == (32, 181)
    assert sw[sun]["swing"] > brief.SEARCH_SWING
    others = [a for t, a in sw.items() if t != sun]
    assert min(a["trough_ratio"] for a in others) > 80 and max(a["peak_ratio"] for a in others) < 120


def test_sunscreen_ships_feb_to_apr_and_is_searched_may_to_jul_every_year(meti, search):
    ship = seasonal.year_runs(meti[CATEGORIES["sunscreen"][0]])
    srch = seasonal.year_runs(search[CATEGORIES["sunscreen"][2]])
    assert set(ship.values()) == {(2, 4)} and set(srch.values()) == {(5, 7)}


def test_launch_months_are_even_in_seven_of_eight_side_years():
    core = brief._core(E, sources.CUTOFF)
    core["m"] = core["month"].str[5:7].astype(int)
    uneven = []
    for side in ("skincare", "makeup"):
        for y in (2022, 2023, 2024, 2025):
            c = (core[(core["category_group"] == side) & (core["year"] == y)]["m"]
                 .value_counts().reindex(range(1, 13), fill_value=0))
            if seasonal.chi2_even(c) >= seasonal.CHI2_11_05:
                uneven.append((side, y, int(c.idxmax()), int(c.max())))
    assert uneven == [("skincare", 2024, 8, 18)]
