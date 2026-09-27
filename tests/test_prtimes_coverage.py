"""A feed's panel is set by what the store holds, not by what the feed serves today.

A capped PR TIMES feed returns its newest 200 releases, so its reach moves
forward each time the issuer publishes. Judged on the latest fetch, a core feed
would turn present-forward and take its whole history out of every historical
figure. src/prtimes.coverage reads every fetch instead: the first fetch's reach
is where the stored history starts, and a later fetch in which every item was
new is a gap.

src/prtimes imports requests, which CI does not install, so the module is
imported lazily and these tests skip there. The store test also needs the
gitignored data/prtimes.db.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "prtimes.db"


@pytest.fixture(scope="module")
def pt():
    return pytest.importorskip("src.prtimes")


def _log(rows):
    cols = ["run_date", "company_id", "http_status", "items", "new_items",
            "feed_reach", "newest", "history_complete"]
    return pd.DataFrame(rows, columns=cols)


def test_a_capped_feed_keeps_its_first_reach(pt):
    cov = pt.coverage(_log([
        ("2026-09-18", "1", 200, 200, 200, "2021-09-14", "2026-09-14", 0),
        ("2026-09-27", "1", 200, 200, 3, "2021-10-02", "2026-09-26", 0),
    ])).set_index("company_id")
    assert cov.loc["1", "feed_reach"] == "2021-09-14"
    assert cov.loc["1", "fetched"] == "2026-09-27"
    assert cov.loc["1", "gaps"] == []


def test_a_fetch_with_nothing_already_stored_is_a_gap(pt):
    cov = pt.coverage(_log([
        ("2026-09-18", "1", 200, 200, 200, "2021-09-14", "2026-09-14", 0),
        ("2027-06-01", "1", 200, 200, 200, "2026-10-20", "2027-05-30", 0),
    ])).set_index("company_id")
    assert cov.loc["1", "gaps"] == ["2027-06-01"]


def test_complete_feeds_and_failed_fetches(pt):
    cov = pt.coverage(_log([
        ("2026-09-18", "2", None, 0, 0, "", "", 0),            # failed: ignored
        ("2026-09-20", "2", 200, 40, 40, "2015-01-05", "2026-09-19", 1),
        ("2026-09-27", "2", 200, 41, 1, "2015-01-05", "2026-09-26", 1),
    ])).set_index("company_id")
    assert cov.loc["2", "feed_reach"] == "2015-01-05"
    assert bool(cov.loc["2", "history_complete"]) is True
    assert cov.loc["2", "gaps"] == []


def test_the_store_has_no_gaps(pt):
    if not DB.exists():
        pytest.skip("PR TIMES store not present")
    with sqlite3.connect(DB) as conn:
        cov = pt.coverage(pd.read_sql("SELECT * FROM fetch_log", conn))
    assert not cov["gaps"].str.len().any(), cov[cov["gaps"].str.len() > 0]
