"""The related-searches re-pull: its seed list, its window, and the rules that a
pull is stored whole, refused when incomplete, and published only where two pulls
agree, seed by seed. Every Google response here is synthetic; nothing is fetched."""

import json
import sqlite3

import pandas as pd
import pytest

import ingest_trends_related as itr

A = itr.ROOT / "dashboard" / "assets"


def _rec(seed, top, rising, pulled_at, timeframe=itr.TIMEFRAME, compare=itr.COMPARE_TIME):
    """A stored request as `pull` writes it, with synthetic queries."""
    s = itr.load_seeds().set_index("seed").loc[seed]
    lst = lambda qs: {"rankedKeyword": [{"query": q, "value": v, "formattedValue": f"{v}"}  # noqa: E731
                                        for q, v in qs]}
    return {"request": {"seed": seed, "seed_group": s.seed_group, "side": s.side,
                        "timeframe": timeframe, "geo": "JP", "client": "pytrends",
                        "client_version": "4.9.2", "pulled_at": pulled_at,
                        "widget": {"trendinessSettings": {"compareTime": compare}}},
            "response": {"default": {"rankedList": [lst(top), lst(rising)]}}}


def _write_pull(root, pull_id, pulled_at, rising_for=lambda seed: [(f"{seed} 語A", 300)]):
    folder = root / pull_id
    folder.mkdir(parents=True)
    for r in itr.load_seeds().itertuples():
        rec = _rec(r.seed, [(r.seed, 100)], rising_for(r.seed), pulled_at)
        (folder / r.file).write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")


# ── The seed list and the window ────────────────────────────────────────────

def test_the_category_seeds_are_balanced_and_each_has_a_side():
    s = itr.load_seeds()
    assert not s["seed"].duplicated().any()
    cat = s[s["seed_group"] == "category"]
    assert cat["side"].value_counts().to_dict() == {"skincare": 5, "makeup": 5,
                                                    "sunscreen": 1, "umbrella": 1}
    assert set(s["seed_group"]) == {"category", "ingredient"}


def test_the_ingredient_seeds_are_the_tracked_actives_and_carry_no_side():
    s = itr.load_seeds()
    ing = s[s["seed_group"] == "ingredient"]
    terms = pd.read_csv(A / "prtimes_ingredient_terms.csv", dtype=str).fillna("")
    assert set(ing["seed"]) == set(terms.loc[terms["trends_term"] != "", "trends_term"])
    assert (ing["side"] == "").all()


def test_the_window_is_full_calendar_years_from_the_break():
    from bp.data import METI_BREAK
    start, end = (pd.Timestamp(d) for d in itr.WINDOW)
    assert (start.month, start.day, end.month, end.day) == (1, 1, 12, 31)
    assert start.year == METI_BREAK
    years = end.year - start.year + 1
    c0, c1 = (pd.Timestamp(d) for d in itr.COMPARE_TIME.split())
    assert (c0.year, c1.year) == (start.year - years, start.year - 1)   # the equal-length period before


# ── Parsing ─────────────────────────────────────────────────────────────────

def test_parse_ranks_each_list_and_flags_growth_above_5000_as_breakout():
    rows = itr.parse(_rec("化粧水", [("x", 100), ("y", 40)], [("p", 9000), ("q", 250)],
                          "2026-10-01T00:00:00+00:00"))
    top, rising = rows[rows.kind == "top"], rows[rows.kind == "rising"]
    assert list(top["rank"]) == [1, 2] and list(rising["rank"]) == [1, 2]
    assert list(rising["breakout"]) == [1, 0] and top["breakout"].sum() == 0
    assert (rows["seed_group"] == "category").all() and (rows["side"] == "skincare").all()


def test_a_seed_with_no_rising_list_parses_to_its_top_list_only():
    rec = _rec("化粧水", [("x", 100)], [], "2026-10-01T00:00:00+00:00")
    rec["response"]["default"]["rankedList"] = rec["response"]["default"]["rankedList"][:1]
    assert set(itr.parse(rec)["kind"]) == {"top"}


# ── A pull: stored as fetched, refused when incomplete ─────────────────────

def test_a_pull_stops_when_a_request_keeps_failing_and_resumes_where_it_stopped(tmp_path):
    seeds = itr.load_seeds()["seed"].tolist()
    stop_at = seeds[2]

    def fetch(seed):
        if seed == stop_at:
            raise RuntimeError("429")
        return _rec(seed, [(seed, 100)], [], "2026-10-01T00:00:00+00:00")

    with pytest.raises(SystemExit):
        itr.pull(fetch=fetch, sleep=lambda s: None, raw_root=tmp_path)
    (pid,) = itr.pull_ids(tmp_path)
    assert len(list((tmp_path / pid).iterdir())) == 2              # what was fetched is kept
    with pytest.raises(ValueError, match="not fetched"):
        itr.read_pull(pid, tmp_path)

    calls = []
    ok = lambda seed: calls.append(seed) or _rec(seed, [(seed, 100)], [],  # noqa: E731
                                                 "2026-10-01T00:05:00+00:00")
    itr.pull(resume=pid, fetch=ok, sleep=lambda s: None, raw_root=tmp_path)
    assert calls == seeds[2:]                                       # only the missing seeds
    reqs, _ = itr.read_pull(pid, tmp_path)
    assert len(reqs) == len(seeds)


def test_retries_wait_longer_each_time_then_give_up():
    waits = []

    def fetch(seed):
        raise RuntimeError("429")

    with pytest.raises(RuntimeError):
        itr.fetch_with_retries("化粧水", fetch, waits.append)
    assert waits == [itr.RETRY_WAIT * k for k in range(1, itr.RETRIES)]


@pytest.mark.parametrize("bad", ["timeframe", "compare", "client"])
def test_a_pull_off_the_window_or_without_its_client_is_refused(tmp_path, bad):
    _write_pull(tmp_path, "p1", "2026-10-01T00:00:00+00:00")
    f = next((tmp_path / "p1").iterdir())
    rec = json.loads(f.read_text(encoding="utf-8"))
    if bad == "timeframe":
        rec["request"]["timeframe"] = "2020-01-01 2022-12-31"
    elif bad == "compare":
        rec["request"]["widget"]["trendinessSettings"]["compareTime"] = "2014-01-01 2017-12-31"
    else:
        rec["request"]["client_version"] = ""
    f.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        itr.read_pull("p1", tmp_path)


def test_loading_a_pull_replaces_it_whole_and_leaves_other_pulls(tmp_path):
    raw, db = tmp_path / "raw", tmp_path / "t.db"
    sqlite3.connect(db).close()
    _write_pull(raw, "p1", "2026-10-01T00:00:00+00:00")
    _write_pull(raw, "p2", "2026-10-02T06:00:00+00:00")
    n1 = itr.load("p1", apply=True, raw_root=raw, db=db)
    itr.load("p2", apply=True, raw_root=raw, db=db)
    itr.load("p1", apply=True, raw_root=raw, db=db)                  # again: replaced, not appended
    con = sqlite3.connect(db)
    got = dict(con.execute("SELECT pull_id, COUNT(*) FROM trends_related GROUP BY pull_id"))
    cols = {r[1] for r in con.execute("PRAGMA table_info(trends_related)")}
    con.close()
    assert got == {"p1": n1, "p2": n1}
    assert {"pulled_at", "client", "client_version", "window_start", "window_end",
            "compare_time", "seed_group", "side"} <= cols


def test_a_dry_run_load_writes_nothing(tmp_path):
    raw, db = tmp_path / "raw", tmp_path / "t.db"
    sqlite3.connect(db).close()
    _write_pull(raw, "p1", "2026-10-01T00:00:00+00:00")
    itr.load("p1", apply=False, raw_root=raw, db=db)
    con = sqlite3.connect(db)
    assert con.execute("SELECT name FROM sqlite_master WHERE name = 'trends_related'").fetchall() == []
    con.close()
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".db"] == ["t.db"]   # no backup either


# ── Two pulls: published only where both agree, seed by seed ────────────────

def test_a_query_is_kept_only_if_the_same_seed_returned_it_on_both_pulls(tmp_path):
    seeds = itr.load_seeds()["seed"].tolist()
    a, b = seeds[0], seeds[1]
    first = {a: [("q1", 300), ("q2", 200)], b: [("q3", 150)]}
    second = {a: [("q2", 180)], b: [("q1", 400), ("q3", 120)]}
    _write_pull(tmp_path, "p1", "2026-10-01T00:00:00+00:00", lambda s: first.get(s, []))
    _write_pull(tmp_path, "p2", "2026-10-02T06:00:00+00:00", lambda s: second.get(s, []))
    s = itr.stable("p1", "p2", tmp_path)
    rising = s[s.kind == "rising"]
    assert set(zip(rising["seed"], rising["query"])) == {(a, "q2"), (b, "q3")}   # q1 changed seed
    row = rising[rising["query"] == "q2"].iloc[0]
    assert (row["rank_1"], row["rank_2"], row["value_1"], row["value_2"]) == (2, 1, 200, 180)
    assert s["seed"].notna().all()                                  # every row belongs to one seed


def test_two_pulls_less_than_a_day_apart_are_refused(tmp_path):
    _write_pull(tmp_path, "p1", "2026-10-01T00:00:00+00:00")
    _write_pull(tmp_path, "p2", "2026-10-01T20:00:00+00:00")
    with pytest.raises(ValueError, match="apart"):
        itr.stable("p1", "p2", tmp_path)
