"""A statistical code scheme can change under a series without raising anything.

Both e-Stat pulls filter on codes. When a scheme is revised, the old codes stop
and new ones start; if the new ones are not picked up, value leaves the series
silently. That happened to HS 3304 imports: on 2024-01-01 the import schedule
merged 3304.99-011/012/019 into 010, the e-Stat database never added 010, and
the 2024 import total read 25% low.

These tests only look at years where the set of codes changes, and ask whether
the total survived the change.
"""

from pathlib import Path

import pandas as pd

ASSETS = Path(__file__).resolve().parent.parent / "dashboard" / "assets"

# Checked on HS 6-digit groups, not 4-digit. Ordinary year-on-year moves are
# large at either level (6-digit, years with no code change: median 13%, 95th
# percentile 49%, largest 84%), so the tolerance cannot be symmetric. The
# failure being guarded against is value leaving the series, which shows as a
# fall. At 4-digit the lost 3304.99 lines were a -25% move, inside the ordinary
# range; at 6-digit they were -50%. The legitimate breaks on record: 3304.91 was
# re-coded in 2023 (-4%), and 3304.99 grew 20% across its 2024 re-code once 010
# is included. A rise above 50% at a break points to double counting.
MAX_FALL, MAX_RISE = -0.20, 0.50


def _trade_breaks() -> list[tuple]:
    d = pd.read_csv(ASSETS / "estat_trade_hs3304.csv", dtype={"hs_code": str})
    d["group"] = d["hs_code"].str[:6]
    codes = d.groupby(["flow", "group", "year"])["hs_code"].agg(frozenset)
    total = d.groupby(["flow", "group", "year"])["value_1000jpy"].sum()
    out = []
    for (flow, group), s in total.groupby(level=[0, 1]):
        years = sorted(s.index.get_level_values(2))
        for a, b in zip(years, years[1:]):
            if codes[flow, group, a] != codes[flow, group, b]:
                out.append((flow, group, a, b, s[flow, group, b] / s[flow, group, a] - 1,
                            sorted(codes[flow, group, a] ^ codes[flow, group, b])))
    return out


def test_trade_years_are_consecutive():
    """A missing year would hide a break between the years either side of it."""
    d = pd.read_csv(ASSETS / "estat_trade_hs3304.csv")
    for flow, g in d.groupby("flow"):
        years = sorted(g["year"].unique())
        assert years == list(range(years[0], years[-1] + 1)), f"{flow}: {years}"


def test_trade_totals_survive_code_changes():
    bad = [f"{fl} {g} {a}→{b}: {ch:+.0%} (codes changed: {', '.join(c)})"
           for fl, g, a, b, ch, c in _trade_breaks() if not MAX_FALL <= ch <= MAX_RISE]
    assert not bad, "value left or entered a series at a code change:\n" + "\n".join(bad)


def test_trade_breaks_on_record():
    """The known re-codes are still seen as breaks, so the test above is armed.

    If one disappears, the code sets were merged upstream and this list needs
    updating; if a new one appears, look at it before adding it here.
    """
    seen = {(fl, g, b) for fl, g, a, b, ch, c in _trade_breaks()}
    assert seen == {("import", "330491", 2023), ("import", "330499", 2024)}


def test_meti_component_lines_constant():
    """METI's 33 component lines are the same in every year.

    The 計 subtotal rows stop after 2020, which is why aggregates are summed from
    the components; a line added or dropped would move every group total.
    """
    m = pd.read_csv(ASSETS / "estat_meti_cosmetics.csv")
    m = m[(m["measure"] == "販売金額") & (m["month"] >= 1)]
    m = m[~m["item"].str.endswith("計") & (m["item"] != "化粧品合計")]
    lines = m.groupby("year")["item"].agg(frozenset)
    first = lines.iloc[0]
    changed = {y: (sorted(v - first), sorted(first - v)) for y, v in lines.items() if v != first}
    assert not changed, f"component lines added/dropped against {lines.index[0]}: {changed}"
    assert len(first) == 33
