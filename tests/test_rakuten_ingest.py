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
    every = json.dumps({"availability": 0, "genreInformationFlag": 1, "hits": 1}, sort_keys=True)
    stock = json.dumps({"availability": 1, "genreInformationFlag": 1, "hits": 1}, sort_keys=True)
    (tmp_path / "rakuten_genre_totals_2026-10-04.json").write_text(json.dumps({"genres": [
        {"genre_id": "100939", "name": "美容・コスメ・香水", "level": 1, "parent_id": None,
         "total_available": 4782164, "request": every},
        {"genre_id": "564517", "name": "韓国コスメ", "level": 2,
         "parent_id": "100939", "total_available": 29392, "request": every},
        {"genre_id": "564517", "name": "韓国コスメ", "level": 2,
         "parent_id": "100939", "total_available": 24534, "request": stock},
    ]}), encoding="utf-8")
    assert ing.tree_totals(conn, "2026-10-04") == 3
    assert ing.tree_totals(conn, "2026-10-11") == 0      # no file for that date
    got = conn.execute("SELECT genre_id, level, parent_id, availability, total_available "
                       "FROM genre_totals ORDER BY genre_id, availability").fetchall()
    # The same genre on one date is two series: every listing, and in stock only.
    assert got == [("100939", 1, None, 0, 4782164),
                   ("564517", 2, "100939", 0, 29392),
                   ("564517", 2, "100939", 1, 24534)]


def test_an_older_table_is_rebuilt_with_availability(ing):
    c = sqlite3.connect(":memory:")
    c.execute("""CREATE TABLE genre_totals (snapshot_date TEXT NOT NULL, genre_id TEXT NOT NULL,
                 genre_name TEXT, total_available INTEGER NOT NULL, recorded_from TEXT NOT NULL,
                 PRIMARY KEY(snapshot_date, genre_id))""")
    c.execute("INSERT INTO genre_totals VALUES ('2026-09-20', '564517', '韓国コスメ', 30039, 'run log')")
    ing.migrate(c)
    ing.migrate(c)                                         # a second run is a no-op
    cols = [r[1] for r in c.execute("PRAGMA table_info(genre_totals)")]
    assert cols[-4:] == ["level", "parent_id", "availability", "request"]
    # Stored before 2026-09-27 from the API default: in stock only.
    row = c.execute("SELECT availability, request FROM genre_totals").fetchone()
    assert row[0] == 1 and json.loads(row[1])["availability"] == 1
