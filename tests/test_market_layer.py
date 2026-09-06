"""The market layer must reconcile to the official published aggregates.

The 皮膚用/仕上用 grouping is the load-bearing assumption of the whole panel:
METI stopped shipping the 計 subtotal rows after 2020, so the aggregates are
rebuilt from 33 component lines and a single line assigned to the wrong group
moves every money figure on the page. Two independent checks pin it — the
subtotal years it must reproduce exactly, and JCIA's published shares for the
latest year.

The break tests exist because measuring across it silently reverses the sign
of the skincare figures. They fail if anyone widens a window back over 2022.
"""

import pandas as pd
import pytest

# 日本化粧品工業会, 化粧品出荷 — published shares of 2024 shipped value.
JCIA_2024 = {"skincare": 44.5, "makeup": 20.9, "total_oku": 13745}


@pytest.fixture(scope="module")
def meti(app):
    val, units = app.load_meti_annual()
    return val, units


def test_grouping_reproduces_the_subtotal_rows(app, meti):
    """2019 and 2020 are the only years carrying 計 rows — hit them exactly."""
    val, _ = meti
    for year in (2019, 2020):
        for group, subtotal in (("METI_SKIN", "皮膚用化粧品計"),
                                ("METI_MAKE", "仕上用化粧品計")):
            summed = val.loc[getattr(app, group), year].sum()
            published = val.loc[subtotal, year]
            assert summed == pytest.approx(published, rel=1e-6), (
                f"{group} in {year} sums to {summed:.1f} 億円 but METI's "
                f"{subtotal} row says {published:.1f} — a line is in the wrong group")


def test_grouping_matches_jcia_published_shares(app, headline):
    """An external check: JCIA publishes the same split we compute."""
    assert headline["mkt_total_y1"] == JCIA_2024["total_oku"]
    assert headline["skin_share_y1"] == pytest.approx(JCIA_2024["skincare"], abs=0.05)
    assert headline["make_share_y1"] == pytest.approx(JCIA_2024["makeup"], abs=0.05)


def test_no_line_is_counted_twice_or_dropped(app, meti):
    """The four groups plus 香水 must partition the component lines."""
    val, _ = meti
    components = {i for i in val.index
                  if not str(i).endswith("計") and i != "化粧品合計"}
    grouped = app.METI_SKIN + app.METI_MAKE
    assert len(grouped) == len(set(grouped)), "a line appears in both groups"
    assert set(grouped) <= components, (
        f"grouped lines that are not component rows: {set(grouped) - components}")


def test_the_break_reverses_the_serum_sign(headline):
    """The reason nothing is measured across 2021/2022, asserted as a fact.

    If this ever stops holding the break has been revised away upstream and the
    whole two-regime treatment should be revisited — deliberately, not silently.
    """
    assert headline["serum_val_span"] < 0 < headline["serum_val_post"]
    assert headline["serum_ppu_span"] < 0 < headline["serum_ppu_post"]


def test_makeup_figures_do_not_span_the_break_by_accident(app, meti, headline):
    """Makeup is publishable across the window only because the break misses it.

    Its yen-per-unit must not step the way the skincare lines do — that is what
    licenses the -42% headline on a 2019->2024 window.
    """
    val, units = meti
    brk = headline["mkt_break"]
    for item in ("ファンデーション", "口紅"):
        ppu = (val.loc[item] / units.loc[item])
        step = abs(ppu[brk] / ppu[brk - 1] - 1)
        assert step < 0.15, (
            f"{item} yen-per-unit moved {step:.0%} across the break; it can no "
            "longer be reported on a window that spans 2022")


def test_broken_lines_are_the_ones_we_say_they_are(app, meti):
    """化粧水/美容液/乳液 step at 2022; the controls do not.

    Tested on shipped *value*, which is what separates them. Yen per kg is the
    wrong discriminator: 口紅's yen per kg also falls 40% in 2022, but because
    its volume rose 149% — a mix move, not a break.
    """
    val, _ = meti
    for item in ("化粧水", "美容液", "乳液"):
        step = val.loc[item, 2022] / val.loc[item, 2021] - 1
        assert step < -0.20, f"{item} no longer steps down at 2022 ({step:+.0%})"
    for item in ("モイスチャークリーム", "ファンデーション", "クレンジングクリーム"):
        step = abs(val.loc[item, 2022] / val.loc[item, 2021] - 1)
        assert step < 0.10, f"{item} now steps at 2022 ({step:+.0%}) — it was a control"


def test_the_break_is_a_price_move_not_a_volume_move(app, meti):
    """What makes it a break rather than demand: the kilograms did not follow."""
    val, _ = meti
    d = pd.read_csv(app.ASSETS / "estat_meti_cosmetics.csv")
    d = d[(d["month"] >= 1) & (d["measure"] == "販売数量")]
    vol = d.groupby(["item", "year"])["value"].sum().unstack()
    for item in ("化粧水", "美容液", "乳液"):
        d_val = val.loc[item, 2022] / val.loc[item, 2021] - 1
        d_vol = vol.loc[item, 2022] / vol.loc[item, 2021] - 1
        assert d_vol > d_val + 0.10, (
            f"{item}: value {d_val:+.0%} and volume {d_vol:+.0%} now move together, "
            "which would make 2022 look like demand rather than a reporting step")


def test_attention_asset_has_whole_years_only(app):
    """The week_year column mislabels Januaries; the asset must not inherit it."""
    d = pd.read_csv(app.ASSETS / "nb04b_attention_annual.csv")
    assert set(d["n_months"]) == {12}, (
        "a partial year reached the attention asset — check that "
        "build_attention_annual.py still derives the year from week_start")
