"""Google Trends related searches: one request per seed over one window, every raw
response stored with its request, a pull loaded whole into the private DB, and two
pulls compared seed by seed.

    ./venv/bin/python ingest_trends_related.py pull                  # fetch every seed; raw files only
    ./venv/bin/python ingest_trends_related.py pull --resume PULL_ID # fetch the seeds a pull is missing
    ./venv/bin/python ingest_trends_related.py load PULL_ID          # dry run: check the pull
    ./venv/bin/python ingest_trends_related.py load PULL_ID --apply  # back up the DB, then replace that pull
    ./venv/bin/python ingest_trends_related.py compare --out FILE    # queries in both of the last two pulls
    ./venv/bin/python ingest_trends_related.py smoke SEED --out DIR  # one request, written to DIR only

The design is recon/2026-09-29_design_trends-related-repull.md as the architect
amended it on 2026-09-30:

- Seeds and their sides are in config/trends_related_seeds.csv: five skincare, five
  makeup, sunscreen and 化粧品 in the category group, and the tracked actives in a
  separate ingredient group that is reported apart and never pooled with it.
- One window, WINDOW, full calendar years. Google reports each rising query's growth
  against the equal-length period before the window, 2018-2021 here: the widget
  request it returns names that period (trendinessSettings.compareTime), and a pull
  whose requests name another is refused.
- Results are per seed. Nothing here counts, sums or normalises across seeds.
- Two pulls at least MIN_GAP apart. A query is published only if it is in the same
  seed's list on both pulls (compare).
- The client is pytrends; its name and version are stored with every request. A
  request that still fails after RETRIES attempts stops the pull, and the pull waits.
  There is no fallback to scraping.

A pull is fetched into data/raw/trends/related/<pull_id>/, one JSON file per seed
holding the request (parameters, client, version, pulled_at in UTC, and the widget
request that fixes the window) and Google's response exactly as parsed from the wire.
data/raw/ is gitignored. `pull` writes only raw files: a fetched response is the
record, so it is kept even when the pull stops partway. The DB changes only with
`load --apply`, which replaces that pull's rows whole in one transaction.
"""

import argparse
import json
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "config" / "trends_related_seeds.csv"
RAW = ROOT / "data" / "raw" / "trends" / "related"
DB = ROOT / "data" / "signal_pulse.db"

WINDOW = ("2022-01-01", "2025-12-31")
TIMEFRAME = f"{WINDOW[0]} {WINDOW[1]}"
COMPARE_TIME = "2018-01-01 2021-12-31"      # Google's baseline for WINDOW
GEO, CAT, HL, TZ = "JP", 0, "ja-JP", -540
CLIENT = "pytrends"
MIN_GAP = timedelta(days=1)
PAUSE, RETRIES, RETRY_WAIT = 5.0, 3, 60.0
KINDS = ("top", "rising")          # Google's rankedList order
# Google marks growth above 5000% as "Breakout" rather than a percentage.
BREAKOUT_OVER = 5000

DDL = """
CREATE TABLE IF NOT EXISTS trends_related (
    pull_id         TEXT    NOT NULL,
    pulled_at       TEXT    NOT NULL,
    client          TEXT    NOT NULL,
    client_version  TEXT    NOT NULL,
    seed            TEXT    NOT NULL,
    seed_group      TEXT    NOT NULL,
    side            TEXT,
    window_start    TEXT    NOT NULL,
    window_end      TEXT    NOT NULL,
    compare_time    TEXT    NOT NULL,
    geo             TEXT    NOT NULL,
    kind            TEXT    NOT NULL CHECK (kind IN ('top', 'rising')),
    rank            INTEGER NOT NULL,
    query           TEXT    NOT NULL,
    value           INTEGER,
    formatted_value TEXT,
    breakout        INTEGER NOT NULL,
    UNIQUE (pull_id, seed, kind, rank)
)
"""


# ── Seeds ───────────────────────────────────────────────────────────────────

def load_seeds(path: Path = SEEDS) -> pd.DataFrame:
    """The seed list, in config order, with its group and side."""
    s = pd.read_csv(path, dtype=str).fillna("")
    s["file"] = [f"{i:02d}_{seed.replace(' ', '_')}.json" for i, seed in enumerate(s["seed"], 1)]
    return s


# ── Fetch ───────────────────────────────────────────────────────────────────

def _client_version() -> str:
    from importlib.metadata import version
    return version(CLIENT)


def fetch_one(seed: str) -> dict:
    """One related-queries request for `seed` over WINDOW. Returns the request
    record and Google's response. pytrends is imported here, so the rest of this
    module runs where it is not installed (CI)."""
    from pytrends.request import TrendReq

    tr = TrendReq(hl=HL, tz=TZ, timeout=(10, 25))
    pulled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tr.build_payload([seed], cat=CAT, timeframe=TIMEFRAME, geo=GEO)
    raw = []
    get = tr._get_data

    def keep(url, *a, **k):           # the response as parsed from the wire, before pytrends reshapes it
        out = get(url, *a, **k)
        if url == TrendReq.RELATED_QUERIES_URL:
            raw.append(out)
        return out

    tr._get_data = keep
    tr.related_queries()
    if len(raw) != 1 or len(tr.related_queries_widget_list) != 1:
        raise RuntimeError(f"{seed}: expected one related-queries response, got {len(raw)}")
    return {"request": {"seed": seed, "timeframe": TIMEFRAME, "geo": GEO, "cat": CAT, "hl": HL,
                        "tz": TZ, "client": CLIENT, "client_version": _client_version(),
                        "pulled_at": pulled_at,
                        "widget": tr.related_queries_widget_list[0]["request"]},
            "response": raw[0]}


def fetch_with_retries(seed: str, fetch=fetch_one, sleep=time.sleep) -> dict:
    """fetch(seed), tried RETRIES times with a growing wait; the last failure
    is raised, and the pull stops there."""
    for attempt in range(1, RETRIES + 1):
        try:
            return fetch(seed)
        except Exception as e:            # noqa: BLE001  pytrends raises several types for a refused request
            if attempt == RETRIES:
                raise
            print(f"  {seed}: {type(e).__name__}: {e}; waiting {RETRY_WAIT * attempt:.0f} s")
            sleep(RETRY_WAIT * attempt)
    raise AssertionError("unreachable")


def pull(resume: str | None = None, fetch=fetch_one, sleep=time.sleep, raw_root: Path = RAW) -> str:
    """Fetch every seed not yet in the pull's folder. Returns the pull id."""
    seeds = load_seeds()
    pull_id = resume or datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    out = raw_root / pull_id
    if resume and not out.is_dir():
        sys.exit(f"no pull {resume} under {raw_root}")
    out.mkdir(parents=True, exist_ok=True)
    todo = seeds[[not (out / f).exists() for f in seeds["file"]]]
    print(f"pull {pull_id}: {len(todo)} of {len(seeds)} seeds to fetch, window {TIMEFRAME}")
    for i, r in enumerate(todo.itertuples()):
        if i:
            sleep(PAUSE)
        try:
            rec = fetch_with_retries(r.seed, fetch, sleep)
        except Exception as e:            # noqa: BLE001
            sys.exit(f"\nSTOP at {r.seed}: {type(e).__name__}: {e}\n"
                     f"{i} fetched this run. Resume later with: pull --resume {pull_id}")
        rec["request"].update(seed_group=r.seed_group, side=r.side)
        (out / r.file).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        rows = parse(rec)
        print(f"  {r.seed}: {sum(rows.kind == 'top')} top, {sum(rows.kind == 'rising')} rising")
    return pull_id


# ── Parse and check ─────────────────────────────────────────────────────────

def parse(rec: dict) -> pd.DataFrame:
    """One stored request -> one row per returned query, ranked within its list."""
    q = rec["request"]
    lists = rec["response"].get("default", {}).get("rankedList", [])
    rows = []
    for kind, lst in zip(KINDS, lists):
        for rank, kw in enumerate(lst.get("rankedKeyword", []), 1):
            value = kw.get("value")
            fmt = kw.get("formattedValue")
            rows.append(dict(
                seed=q["seed"], seed_group=q.get("seed_group", ""), side=q.get("side", ""),
                kind=kind, rank=rank, query=kw["query"], value=value, formatted_value=fmt,
                breakout=int(kind == "rising" and value is not None and value > BREAKOUT_OVER)))
    cols = ["seed", "seed_group", "side", "kind", "rank", "query", "value", "formatted_value",
            "breakout"]
    return pd.DataFrame(rows, columns=cols)


def read_pull(pull_id: str, raw_root: Path = RAW) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(requests, rows) for a stored pull, checked complete and on WINDOW."""
    seeds = load_seeds()
    folder = raw_root / pull_id
    reqs, frames, problems = [], [], []
    for r in seeds.itertuples():
        f = folder / r.file
        if not f.exists():
            problems.append(f"{r.seed}: not fetched")
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        q = rec["request"]
        if q["timeframe"] != TIMEFRAME:
            problems.append(f"{r.seed}: timeframe {q['timeframe']}, not {TIMEFRAME}")
        if q.get("seed_group") != r.seed_group or q.get("side", "") != r.side:
            problems.append(f"{r.seed}: group or side differs from config")
        if not q.get("client") or not q.get("client_version") or not q.get("pulled_at"):
            problems.append(f"{r.seed}: client, version or pull time not recorded")
        compare = q.get("widget", {}).get("trendinessSettings", {}).get("compareTime")
        if compare != COMPARE_TIME:
            problems.append(f"{r.seed}: Google's comparison period is {compare}, not {COMPARE_TIME}")
        reqs.append({k: q.get(k) for k in ("seed", "seed_group", "side", "timeframe", "geo",
                                            "client", "client_version", "pulled_at")})
        frames.append(parse(rec))
    if problems:
        raise ValueError(f"pull {pull_id} is not loadable:\n  " + "\n  ".join(problems))
    return pd.DataFrame(reqs), pd.concat(frames, ignore_index=True)


def load(pull_id: str, apply: bool = False, raw_root: Path = RAW, db: Path = DB) -> int:
    """Check a pull; with apply, back up the DB and replace that pull's rows."""
    reqs, rows = read_pull(pull_id, raw_root)
    started = reqs["pulled_at"].min()
    rows = rows.merge(reqs[["seed", "pulled_at", "client", "client_version", "geo"]], on="seed")
    rows.insert(0, "pull_id", pull_id)
    rows["window_start"], rows["window_end"] = WINDOW
    rows["compare_time"] = COMPARE_TIME
    empty = sorted(set(reqs["seed"]) - set(rows.loc[rows.kind == "rising", "seed"]))
    print(f"pull {pull_id}: {len(reqs)} seeds from {started}, {len(rows)} rows "
          f"({(rows.kind == 'rising').sum()} rising); client "
          f"{', '.join(sorted(set(reqs.client + ' ' + reqs.client_version)))}")
    if empty:
        print(f"  no rising list for: {', '.join(empty)}")
    if not apply:
        print("Dry run: checks passed, nothing written. Re-run with --apply.")
        return len(rows)
    backup = db.with_name(f"{db.stem}_{datetime.now():%Y-%m-%d_%H%M%S}_pre-trends-related.db")
    shutil.copy2(db, backup)
    print(f"backup -> {backup.name}")
    cols = ["pull_id", "pulled_at", "client", "client_version", "seed", "seed_group", "side",
            "window_start", "window_end", "compare_time", "geo", "kind", "rank", "query", "value",
            "formatted_value", "breakout"]
    con = sqlite3.connect(db)
    try:
        con.execute("BEGIN")
        con.execute(DDL)
        con.execute("DELETE FROM trends_related WHERE pull_id = ?", (pull_id,))
        con.executemany(f"INSERT INTO trends_related ({', '.join(cols)}) "
                        f"VALUES ({', '.join('?' * len(cols))})",
                        rows[cols].astype(object).where(rows[cols].notna(), None).values.tolist())
        n = con.execute("SELECT COUNT(*) FROM trends_related WHERE pull_id = ?",
                        (pull_id,)).fetchone()[0]
        if n != len(rows):
            raise RuntimeError(f"{n} rows stored, {len(rows)} expected")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    print(f"loaded {len(rows)} rows for pull {pull_id}")
    return len(rows)


# ── Compare two pulls ───────────────────────────────────────────────────────

def pull_ids(raw_root: Path = RAW) -> list:
    return sorted(p.name for p in raw_root.iterdir() if p.is_dir()) if raw_root.is_dir() else []


def stable(pull_1: str, pull_2: str, raw_root: Path = RAW) -> pd.DataFrame:
    """The queries in the same seed's list, of the same kind, on both pulls, with
    each pull's rank and value. One row per seed, kind and query: nothing is
    counted or combined across seeds."""
    (r1, a), (r2, b) = read_pull(pull_1, raw_root), read_pull(pull_2, raw_root)
    gap = pd.Timestamp(r2["pulled_at"].min()) - pd.Timestamp(r1["pulled_at"].max())
    if gap < MIN_GAP:
        raise ValueError(f"pulls {pull_1} and {pull_2} are {gap} apart; they must be at "
                         f"least {MIN_GAP} apart")
    keys = ["seed", "seed_group", "side", "kind", "query"]
    both = a.merge(b, on=keys, suffixes=("_1", "_2"))
    both = both[keys + ["rank_1", "value_1", "formatted_value_1", "breakout_1",
                        "rank_2", "value_2", "formatted_value_2", "breakout_2"]]
    order = {s: i for i, s in enumerate(load_seeds()["seed"])}
    return (both.assign(_o=both["seed"].map(order))
            .sort_values(["_o", "kind", "rank_1"]).drop(columns="_o").reset_index(drop=True))


def compare(pull_1=None, pull_2=None, out: Path | None = None, raw_root: Path = RAW):
    ids = pull_ids(raw_root)
    if pull_1 is None:
        if len(ids) < 2:
            sys.exit(f"{len(ids)} pull(s) stored; two are needed")
        pull_1, pull_2 = ids[-2], ids[-1]
    s = stable(pull_1, pull_2, raw_root)
    print(f"pulls {pull_1} and {pull_2}: queries in both, per seed")
    for (seed, kind), g in s.groupby(["seed", "kind"], sort=False):
        print(f"  {seed} {kind}: {', '.join(g['query'].head(5))}")
    if out:
        s.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"-> {out}")
    return s


# ── Command line ────────────────────────────────────────────────────────────

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--resume")
    p = sub.add_parser("load")
    p.add_argument("pull_id")
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("compare")
    p.add_argument("pulls", nargs="*")
    p.add_argument("--out", type=Path)
    p = sub.add_parser("smoke")
    p.add_argument("seed")
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)

    if a.cmd == "pull":
        pid = pull(a.resume)
        print(f"\nfetched pull {pid}. Next: load {pid}, then --apply")
    elif a.cmd == "load":
        load(a.pull_id, a.apply)
    elif a.cmd == "compare":
        if len(a.pulls) not in (0, 2):
            sys.exit("compare takes no pull ids or two")
        compare(*(a.pulls or (None, None)), out=a.out)
    elif a.cmd == "smoke":
        if a.out.resolve().is_relative_to(ROOT / "data"):
            sys.exit("smoke writes outside data/: it is a client check, never a pull")
        a.out.mkdir(parents=True, exist_ok=True)
        rec = fetch_one(a.seed)
        f = a.out / f"smoke_{a.seed.replace(' ', '_')}.json"
        f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        rows = parse(rec)
        print(f"{a.seed}: client {rec['request']['client']} {rec['request']['client_version']}, "
              f"{sum(rows.kind == 'top')} top, {sum(rows.kind == 'rising')} rising -> {f}")
        print(rows.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
