"""Seasonality: one method for every page that shows a season.

A month's seasonal ratio is its value divided by the centred 12-month moving
average around it (a 2x12 average: the two 12-month averages that straddle
the month, averaged), x 100. Dividing by the calendar year's mean instead
reads a trend inside the year as a season: a series falling through the year
looks highest in January. Ratios are taken from July 2022 to January 2026
(RATIO_WINDOW) for every series, so no METI skincare average reaches back
across the January 2022 break and every stage averages the same months.

A series has a seasonal peak only when its highest month in every full year
of the window (2023-2025) is within one month of the peak of its average
profile. A search term must also swing more than brief.SEARCH_SWING index
points from its profile's peak to its trough, the top of the spread between
repeat Google Trends pulls. Launch releases are tested for an even spread across
the months of each year (chi-square, 11 degrees of freedom, 5%).

Nothing here reads a file: callers pass monthly series indexed by the first
of the month. Like data.py, nothing runs at import.
"""

import numpy as np
import pandas as pd

# The months whose ratios are averaged. The centred average needs six months
# either side, so the series must run January 2022 - July 2026.
RATIO_WINDOW = ("2022-07-01", "2026-01-01")
FULL_YEARS = (2023, 2024, 2025)
# A stable peak: the year's highest month within this many months of the
# profile's peak, in every full year.
PEAK_TOLERANCE = 1
# Chi-square critical value, 11 degrees of freedom, 5%.
CHI2_11_05 = 19.675
PEAK_RUN = 3


def ratio(series: pd.Series) -> pd.Series:
    """Month / centred 2x12 moving average x 100, NaN where the average
    cannot be centred."""
    s = series.sort_index().astype(float)
    ma = s.rolling(12).mean().rolling(2).mean().shift(-6)
    return 100 * s / ma


def window(r: pd.Series) -> pd.Series:
    lo, hi = (pd.Timestamp(t) for t in RATIO_WINDOW)
    return r[(r.index >= lo) & (r.index <= hi)]


def profile(series: pd.Series) -> pd.Series:
    """Mean seasonal ratio by calendar month (1-12) over RATIO_WINDOW."""
    r = window(ratio(series))
    if r.isna().any() or len(r) != 43:
        raise ValueError("the series does not cover January 2022 - July 2026")
    return r.groupby(r.index.month).mean()


def _gap(a: int, b: int) -> int:
    d = abs(a - b) % 12
    return min(d, 12 - d)


def year_peaks(series: pd.Series) -> dict:
    """Each full year's highest-ratio month."""
    r = window(ratio(series))
    return {y: int(r[r.index.year == y].idxmax().month) for y in FULL_YEARS}


def peak_run(prof: pd.Series, run: int = PEAK_RUN):
    """The `run` consecutive months (December wraps into January) with the
    highest mean ratio: (first month, last month, lowest ratio, highest)."""
    best = max(range(12), key=lambda i: np.mean([prof[(i + k) % 12 + 1] for k in range(run)]))
    got = [prof[(best + k) % 12 + 1] for k in range(run)]
    return best + 1, (best + run - 1) % 12 + 1, min(got), max(got)


def assess(series: pd.Series) -> dict:
    """A series' profile, its peak month, each full year's peak, whether the
    peak is stable, and the swing in the series' own units: the profile's
    range times the series' mean over the window, / 100."""
    prof = profile(series)
    peak = int(prof.idxmax())
    yp = year_peaks(series)
    lo, hi = (pd.Timestamp(t) for t in RATIO_WINDOW)
    level = series[(series.index >= lo) & (series.index <= hi)].mean()
    return dict(profile=prof, peak=peak, peak_ratio=float(prof.max()),
                trough_ratio=float(prof.min()), year_peaks=yp,
                stable=all(_gap(m, peak) <= PEAK_TOLERANCE for m in yp.values()),
                swing=float((prof.max() - prof.min()) * level / 100),
                run=peak_run(prof))


def year_runs(series: pd.Series, run: int = PEAK_RUN) -> dict:
    """Each full year's `run` consecutive months (inside the calendar year)
    with the highest mean ratio: {year: (first month, last month)}."""
    r = window(ratio(series))
    out = {}
    for y in FULL_YEARS:
        v = r[r.index.year == y].to_numpy()
        i = max(range(12 - run + 1), key=lambda i: v[i:i + run].mean())
        out[y] = (i + 1, i + run)
    return out


def monthly(frame: pd.DataFrame, value: str = "value") -> pd.Series:
    """A (year, month, value) frame as a series indexed by the month's first
    day, summed where a month has several rows."""
    s = frame.groupby(["year", "month"])[value].sum()
    s.index = pd.to_datetime([f"{y}-{m:02d}-01" for y, m in s.index])
    return s


def chi2_even(counts) -> float:
    """Chi-square statistic of monthly counts against an even spread."""
    c = np.asarray(counts, dtype=float)
    if c.sum() == 0:
        raise ValueError("no releases to test")
    e = c.sum() / len(c)
    return float(((c - e) ** 2 / e).sum())
