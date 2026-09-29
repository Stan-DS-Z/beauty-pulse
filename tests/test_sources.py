"""The source registry dates every exhibit, so it must read its dates from the data.

Three kinds of check. The registry is complete: every source is declared once,
dated, and used on real pages. Its dates are derived: cut the data short and the
dates move with it, with no edit to the code. And the export it reads for the
database-only sources is current: never older than the public DB, and equal to
this Mac's database when that is present.
"""

import shutil
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PRIVATE_DB = ROOT / "data" / "signal_pulse.db"


@pytest.fixture(scope="module")
def src():
    from bp import sources
    return sources


@pytest.fixture(scope="module")
def registry(src, app):
    return src.build_registry(app.ASSETS)


def test_every_declared_source_is_in_the_registry(src, registry):
    assert list(registry) == list(src.DECLARED)
    assert len(registry) == 9


def test_every_source_says_how_current_it_is(registry):
    """A series has a date and a cadence; a snapshot has a date. The one
    exception is the related-searches pull, which recorded no date."""
    for key, s in registry.items():
        assert s.kind in ("series", "snapshot"), key
        if key == "trends_related":
            assert s.data_to is None
            continue
        assert isinstance(s.data_to, pd.Timestamp), key
        assert s.precision in ("day", "month", "year"), key
        if s.kind == "series":
            assert s.cadence in ("weekly", "monthly", "annual", "per_release"), key


def test_used_on_names_real_pages(src, registry):
    for key, s in registry.items():
        assert set(s.used_on) <= set(src.PAGES), key
    # Collected, and used by no finding or chart (README, METHODOLOGY caveats 6
    # and 7; Revision 17).
    unused = ("amazon", "trends_related")
    assert all(registry[k].used_on == () for k in unused)
    assert all(s.used_on for k, s in registry.items() if k not in unused)


def test_no_source_is_dated_after_its_collection(registry):
    for key in ("trends", "prtimes"):
        s = registry[key]
        assert s.data_to <= s.collected, key


def test_meti_edition_is_the_release_holding_the_newest_month(registry):
    s = registry["meti"]
    assert s.edition == f"確報 {s.data_to:%Y%m}"


def test_the_trends_assets_reach_the_same_month(src, app):
    """If one Trends export were rebuilt and another not, the registry would
    date both by the older. They should not disagree at all."""
    ends = {f: pd.read_csv(app.ASSETS / f, parse_dates=["week_start"])["week_start"].max()
            for f in src.TRENDS_ASSETS}
    assert len(set(ends.values())) == 1, ends


# ── derived, not typed ──────────────────────────────────────────────────────

@pytest.fixture
def cut_assets(src, app, tmp_path):
    """A copy of the registry's inputs, each cut back to an earlier date."""
    names = ["estat_meti_cosmetics.csv", "estat_trade_hs3304.csv",
             "prtimes_launches.csv", "prtimes_feeds.csv", "source_dates.csv",
             *src.TRENDS_ASSETS]
    for n in names:
        shutil.copy(app.ASSETS / n, tmp_path / n)

    m = pd.read_csv(tmp_path / "estat_meti_cosmetics.csv")
    m[(m["year"] < 2026) | (m["month"] <= 3)].to_csv(tmp_path / "estat_meti_cosmetics.csv", index=False)
    t = pd.read_csv(tmp_path / "estat_trade_hs3304.csv")
    t[t["year"] <= 2023].to_csv(tmp_path / "estat_trade_hs3304.csv", index=False)
    for f in src.TRENDS_ASSETS:
        d = pd.read_csv(tmp_path / f)
        d[d["week_start"] < "2026-05-01"].to_csv(tmp_path / f, index=False)
    lc = pd.read_csv(tmp_path / "prtimes_launches.csv", dtype=str)
    lc[lc["published"] <= "2026-06-30"].to_csv(tmp_path / "prtimes_launches.csv", index=False)
    ex = pd.read_csv(tmp_path / "source_dates.csv", dtype=str)
    ex.loc[(ex["source"] == "rakuten") & (ex["date_kind"] == "data_to"), "value"] = "2026-07-05"
    ex.to_csv(tmp_path / "source_dates.csv", index=False)
    return tmp_path


def test_dates_move_with_the_data(src, cut_assets):
    r = src.build_registry(cut_assets)
    assert r["meti"].data_to == pd.Timestamp("2026-03-01")
    assert r["trade"].data_to.year == 2023
    assert r["trends"].data_to == pd.Timestamp("2026-04-01")
    assert r["prtimes"].data_to <= pd.Timestamp("2026-06-30")
    assert r["rakuten"].data_to == pd.Timestamp("2026-07-05")


# ── the source line ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("precision, en, ja", [
    ("day", "18 Sep 2026", "2026年9月18日"),
    ("month", "Sep 2026", "2026年9月"),
    ("year", "2026", "2026年"),
])
def test_date_labels(src, precision, en, ja):
    ts = pd.Timestamp("2026-09-18")
    assert src.date_label(ts, precision, "en") == en
    assert src.date_label(ts, precision, "ja") == ja


def test_source_line_lists_each_source_with_its_date(src, registry):
    line = src.source_line(["meti", "prtimes"], registry)
    meti, pt = registry["meti"], registry["prtimes"]
    assert line == (f"Source: METI 生産動態統計 (data to {src.date_label(meti.data_to, 'month')}); "
                    f"PR TIMES (data to {src.date_label(pt.data_to, 'day')}); "
                    "Beauty Pulse analysis")


def test_undated_source_says_so(src, registry):
    assert "(pull date not recorded)" in src.source_line(["trends_related"], registry)
    assert "取得日の記録なし" in src.source_line(["trends_related"], registry, "ja")


# ── the database export ─────────────────────────────────────────────────────

def _from_db(path):
    from build_source_dates import source_dates
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        return {(r.source, r.date_kind): r.value for r in source_dates(conn).itertuples()}


def _shipped(app):
    df = pd.read_csv(app.ASSETS / "source_dates.csv", dtype=str)
    return {(r.source, r.date_kind): r.value for r in df.itertuples()}


def test_export_is_not_older_than_the_public_db(app, public_db):
    """The public DB is rebuilt by hand and the export weekly, so the export may
    run ahead of it, never behind."""
    shipped, public = _shipped(app), _from_db(public_db)
    assert set(shipped) == set(public)
    for k, v in public.items():
        if k[1] == "collections":
            assert int(shipped[k]) >= int(v), k
        else:
            assert shipped[k] >= v, k


def test_export_matches_this_macs_database(app):
    if not PRIVATE_DB.exists():
        pytest.skip("private database not present")
    assert _shipped(app) == _from_db(PRIVATE_DB), "run build_source_dates.py"
