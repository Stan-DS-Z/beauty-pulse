"""genre_totals: Rakuten's own listing count per genre, captured weekly.

The pull keeps each genre's 3,000 most-reviewed items, so the only figure that
sizes a genre is the count the API reports for it. These tests pin how that
count is read from a snapshot file and from a run log.
"""

import json
import sqlite3

import pytest


@pytest.fixture(scope="module")
def ing():
    import ingest_rakuten_weekly
    return ingest_rakuten_weekly


@pytest.fixture
def conn(ing):
    c = sqlite3.connect(":memory:")
    for ddl in ing.DDL:
        c.execute(ddl)
    yield c
    c.close()


LOG = """\
PULLING  スキンケア (id=100944)
    Total available: 631,905 items across 100 pages
  SAVED 3,000 items → rakuten_products_100944_2026-09-20.json

SKIP  美容液                  (3,000 items already saved)

PULLING  韓国コスメ (id=564517)
    Total available: 30,039 items across 100 pages
  FAILED 韓国コスメ — page 4 failed after retries
"""


def test_a_log_gives_the_total_of_each_saved_genre(ing, conn, tmp_path):
    log = tmp_path / "update.log"
    log.write_text(LOG, encoding="utf-8")
    assert ing.totals_from_log(conn, log) == 1
    rows = conn.execute("SELECT snapshot_date, genre_id, genre_name, total_available, "
                        "recorded_from FROM genre_totals").fetchall()
    # A skipped genre printed no total; a failed one saved no file, so it has no date.
    assert rows == [("2026-09-20", "100944", "スキンケア", 631905, "run log")]


def test_a_snapshot_file_carries_its_total(ing, tmp_path):
    f = tmp_path / "rakuten_products_204233_2026-10-04.json"
    f.write_text(json.dumps({"genre_id": "204233", "genre_name": "ベースメイク・メイクアップ",
                             "item_count": 3000, "total_available": 402248, "items": []}),
                 encoding="utf-8")
    assert ing.read_total(f) == ("ベースメイク・メイクアップ", 402248)


def test_an_older_file_has_no_total(ing, tmp_path):
    f = tmp_path / "rakuten_products_204233_2026-09-13.json"
    f.write_text(json.dumps({"genre_id": "204233", "item_count": 3000, "items": []}),
                 encoding="utf-8")
    assert ing.read_total(f)[1] is None


def test_a_file_overrides_a_log_for_the_same_date(ing, conn):
    ing.store_total(conn, "2026-09-20", "100944", "スキンケア", 631905, "run log")
    ing.store_total(conn, "2026-09-20", "100944", "スキンケア", 631910, "snapshot file")
    assert conn.execute("SELECT total_available, recorded_from FROM genre_totals").fetchall() \
        == [(631910, "snapshot file")]


def test_the_genre_tree_file_fills_every_level(ing, conn, tmp_path, monkeypatch):
    monkeypatch.setattr(ing, "TOTALS_DIR", tmp_path)
    (tmp_path / "rakuten_genre_totals_2026-10-04.json").write_text(json.dumps({"genres": [
        {"genre_id": "100939", "name": "美容・コスメ・香水", "level": 1, "parent_id": None,
         "total_available": 3615664},
        {"genre_id": "204233", "name": "ベースメイク・メイクアップ", "level": 2,
         "parent_id": "100939", "total_available": 401292},
        {"genre_id": "210457", "name": "ファンデーション", "level": 3,
         "parent_id": "204233", "total_available": 67931},
    ]}), encoding="utf-8")
    assert ing.tree_totals(conn, "2026-10-04") == 3
    assert ing.tree_totals(conn, "2026-10-11") == 0      # no file for that date
    got = conn.execute("SELECT genre_id, level, parent_id, total_available, recorded_from "
                       "FROM genre_totals ORDER BY level").fetchall()
    assert got == [("100939", 1, None, 3615664, "genre tree"),
                   ("204233", 2, "100939", 401292, "genre tree"),
                   ("210457", 3, "204233", 67931, "genre tree")]


def test_an_older_table_gains_the_tree_columns(ing):
    c = sqlite3.connect(":memory:")
    c.execute("""CREATE TABLE genre_totals (snapshot_date TEXT NOT NULL, genre_id TEXT NOT NULL,
                 genre_name TEXT, total_available INTEGER NOT NULL, recorded_from TEXT NOT NULL,
                 PRIMARY KEY(snapshot_date, genre_id))""")
    ing.migrate(c)
    ing.migrate(c)                                         # a second run is a no-op
    cols = [r[1] for r in c.execute("PRAGMA table_info(genre_totals)")]
    assert cols[-2:] == ["level", "parent_id"]
