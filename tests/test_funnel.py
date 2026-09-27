"""The funnel matrix: sixteen categories, four stages, one window.

The matrix sets measures that count different things side by side, so what the
tests pin is that each column is its own measure, computed the way the rest of
the site computes it, on a window that never crosses the METI break.
"""

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def fn():
    from bp import funnel
    return funnel


@pytest.fixture(scope="module")
def m(fn, app):
    return fn.compute_funnel_matrix(app.ASSETS)


@pytest.fixture(scope="module")
def launches(app):
    d = pd.read_csv(app.ASSETS / "prtimes_launches.csv", dtype=str).fillna("")
    d = d[(d["panel"] == "core") & (d["category"] != "")]
    return d.assign(year=d["month"].str[:4].astype(int), tags=d["category"].str.split("|"))


def test_sixteen_categories_each_joined_to_every_source(fn, m, app, launches):
    rows = m["rows"]
    assert len(rows) == 16
    val, _ = app.load_meti_annual()
    att = pd.read_csv(app.ASSETS / "nb04b_attention_annual.csv")
    tags = {t for ts in launches["tags"] for t in ts}
    for key, (line, _join, term, _group) in fn.CATEGORIES.items():
        assert key in tags, key
        assert line in val.index, line
        assert term is None or term in set(att["term"]), term


def test_the_window_never_crosses_the_meti_break(m, app):
    y0, y1 = m["window"]
    assert y0 >= app.METI_BREAK
    assert y0 < y1


def test_the_window_holds_back_when_sources_start_earlier(fn, app):
    """Even when every source reaches back before 2022, the window starts at the break."""
    years = list(range(2015, 2026))
    val = pd.DataFrame(1.0, index=["x"], columns=years)
    att = pd.DataFrame(1.0, index=years, columns=["x"])
    launch = pd.DataFrame({"month": [f"{y}-12" for y in years]})
    y0, _ = fn.funnel_window(app.ASSETS, _launch=launch, _val=val, _att=att)
    assert y0 == app.METI_BREAK


def test_the_last_year_is_complete_in_every_source(m, app, launches):
    _, y1 = m["window"]
    meti = pd.read_csv(app.ASSETS / "estat_meti_cosmetics.csv")
    assert meti[(meti["year"] == y1) & (meti["month"] >= 1)]["month"].nunique() == 12
    assert f"{y1}-12" in set(launches["month"])
    att = pd.read_csv(app.ASSETS / "nb04b_attention_annual.csv")
    assert (att[att["year"] == y1]["n_months"] == 12).all()


def test_shipments_are_meti_value_over_the_window(m, app):
    val, _ = app.load_meti_annual()
    y0, y1 = m["window"]
    for key, r in m["rows"].iterrows():
        expect = 100 * (val.loc[r["meti_line"], y1] / val.loc[r["meti_line"], y0] - 1)
        assert r["ship_d"] == pytest.approx(expect), key
        assert r["value_y1"] == pytest.approx(val.loc[r["meti_line"], y1]), key


def test_launch_share_is_a_share_of_categorised_core_releases(m, launches):
    y0, y1 = m["window"]
    den0, den1 = (launches["year"] == y0).sum(), (launches["year"] == y1).sum()
    assert m["launch_den"] == (den0, den1)
    for key, r in m["rows"].iterrows():
        assert r["launch_s0"] == pytest.approx(100 * r["launch_n0"] / den0), key
        assert r["launch_s1"] == pytest.approx(100 * r["launch_n1"] / den1), key
        assert r["launch_d"] == pytest.approx(r["launch_s1"] - r["launch_s0"]), key


def test_search_is_the_terms_own_change(m, app):
    """block_A: each term against its own earlier year, in index points."""
    att = (pd.read_csv(app.ASSETS / "nb04b_attention_annual.csv")
           .pivot(index="year", columns="term", values="interest"))
    y0, y1 = m["window"]
    for key, r in m["rows"].iterrows():
        if pd.isna(r["term"]):
            assert pd.isna(r["search_d"]), key
        else:
            assert r["search_d"] == pytest.approx(att.loc[y1, r["term"]] - att.loc[y0, r["term"]]), key


def test_stages_run_company_to_consumer(fn):
    cols = [c for c, _n, _s in fn.STAGES]
    assert cols == ["launch", "social", "verification", "search", "shipments"]
    assert [n for _c, n, _s in fn.STAGES] == sorted(n for _c, n, _s in fn.STAGES)


def test_every_empty_cell_has_a_reason(fn, m):
    reasons, rows = m["reasons"], m["rows"]
    assert set(reasons.columns) == {c for c, _n, _s in fn.STAGES}
    assert set(reasons.values.ravel()) <= set(fn.REASONS) | {""}
    assert (reasons["social"] == "not_collected").all()
    assert (reasons["verification"] == "single_scrape").all()
    assert ((reasons["search"] == "term_not_tracked") == rows["term"].isna()).all()
    assert (reasons["shipments"] == "").all()


def test_colour_compares_within_one_column_only(m):
    rows, scale = m["rows"], m["scale"]
    assert scale["launch"] == pytest.approx(rows["launch_d"].abs().max())
    assert scale["search"] == pytest.approx(rows["search_d"].abs().max())
    assert scale["shipments"] == pytest.approx(rows["ship_d"].abs().max())


def test_display_order_groups_then_value(fn, m):
    rows = m["rows"]
    order = fn.display_order(rows)
    assert sorted(order) == sorted(rows.index)
    groups = list(rows.loc[order, "group"])
    assert groups == sorted(groups, key=fn.GROUPS.index)
    for g in fn.GROUPS:
        v = rows.loc[[k for k in order if rows.loc[k, "group"] == g], "value_y1"]
        assert v.is_monotonic_decreasing, g
