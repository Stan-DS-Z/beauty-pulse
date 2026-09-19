"""WINDOW_START must be the month the window policy locates in the store.

The store (data/prtimes.db) and the feed-health record are gitignored, so this
runs locally and skips in CI. It fails if the constant and the data disagree:
after a gate change or a new first-run record, re-derive and date the revision.
The dashboard carries the same month as LAUNCH_WINDOW_START; both are checked.
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "prtimes.db"
HEALTH = ROOT / "data" / "interim" / "prtimes_feed_health_2026-09-18.json"


def test_window_start_matches_the_store(app):
    if not (DB.exists() and HEALTH.exists()):
        pytest.skip("PR TIMES store not present")
    from src import prtimes as pt
    rows = pd.DataFrame(json.loads(HEALTH.read_text(encoding="utf-8"))["rows"])
    health = rows[rows["error"] != "no_feed"]
    with sqlite3.connect(DB) as conn:
        rel = pd.read_sql("SELECT company_id, published_date, title, excerpt FROM releases", conn)
    mt = pt.load_matchers()
    rel["is_launch"] = [pt.gate(t, e, mt)["is_launch"] for t, e in zip(rel.title, rel.excerpt)]
    month, share = pt.core_window(health, rel, last_month="2026-08")
    assert month == pt.WINDOW_START == app.LAUNCH_WINDOW_START
    assert share >= pt.CORE_SHARE_MIN
