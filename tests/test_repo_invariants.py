"""Invariants the repo asserts about itself, checked rather than trusted.

The privacy boundary and the "runs from a clone" claim are both promises the
README makes to a reader. The window check pairs the standalone chart export
with the dashboard, which is how they came apart in the first place.
"""

import re
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent


# ── The public/private boundary ───────────────────────────────────────────────

def test_public_db_drops_identifying_columns(public_db):
    conn = sqlite3.connect(f"file:{public_db}?mode=ro", uri=True)
    try:
        product_cols = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
        assert "product_name" not in product_cols
        assert "raw_json" not in product_cols

        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        assert "reviewers" not in tables, "reviewer table must not ship publicly"
    finally:
        conn.close()


def test_public_db_has_one_row_per_genre(public_db):
    """categories must not fan out on a join by source_cat_id.

    Every ingest used to append a fresh copy of each genre — 352 rows for 22
    genres. Products always pointed at the first copy, so joins on category_id
    stayed correct and nothing looked wrong, while any join on source_cat_id
    multiplied its result by 16.
    """
    conn = sqlite3.connect(f"file:{public_db}?mode=ro", uri=True)
    try:
        dupes = conn.execute("""
            SELECT source_id, source_cat_id, COUNT(*) n FROM categories
            GROUP BY 1, 2 HAVING n > 1
        """).fetchall()
        assert not dupes, f"duplicate genre rows: {dupes[:5]}"
    finally:
        conn.close()


def test_private_db_is_not_tracked():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    assert "data/signal_pulse.db" not in tracked
    assert "dashboard/assets/signal_pulse_public.db" not in tracked, (
        "the uncompressed public DB is over GitHub's 100 MB limit; ship the .gz")


# ── The dashboard's inputs ────────────────────────────────────────────────────

def test_every_asset_the_dashboard_reads_exists():
    source = (ROOT / "dashboard" / "streamlit_app.py").read_text(encoding="utf-8")
    names = set(re.findall(r'ASSETS\s*/\s*"([^"]+)"', source))
    assert names, "no asset references found — has the loader style changed?"
    missing = [n for n in sorted(names)
               if not (ROOT / "dashboard" / "assets" / n).exists()]
    assert not missing, f"assets referenced but absent: {missing}"


@pytest.mark.parametrize("name", sorted(
    re.findall(r'ASSETS\s*/\s*"([^"]+\.csv)"',
               (ROOT / "dashboard" / "streamlit_app.py").read_text(encoding="utf-8"))))
def test_each_asset_csv_parses_and_is_not_empty(name):
    df = pd.read_csv(ROOT / "dashboard" / "assets" / name)
    assert not df.empty, f"{name} is empty"


# ── One window, two surfaces ──────────────────────────────────────────────────

def test_chart_export_uses_the_dashboard_window(app):
    """export_ingredient_chart.py must plot the years the dashboard reports."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "export_chart", ROOT / "export_ingredient_chart.py")
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)

    df = pd.read_csv(export.ASSETS / "nb07_ingredient_surge.csv",
                     parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    years = sorted(int(y) for y in export.full_calendar_years(df))

    assert years[0] == app.HEADLINE["ing_y0"]
    assert years[-1] == app.HEADLINE["ing_y1"]


# ── House writing rule ────────────────────────────────────────────────────────

def test_no_pp_abbreviation():
    """"pp" is banned for both percentage points and pages (see memory/)."""
    files = subprocess.run(
        ["git", "ls-files", "*.md", "*.py", "*.txt", "*.yml"],
        cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    offenders = []
    this_file = str(Path(__file__).resolve().relative_to(ROOT))
    for rel in files:
        if rel == this_file:
            continue        # states the rule, so it necessarily contains it
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.split("\n"), 1):
            if re.search(r"(?<![A-Za-z])pp(?![A-Za-z])", line):
                offenders.append(f"{rel}:{n}: {line.strip()[:80]}")
    assert not offenders, "banned token 'pp':\n" + "\n".join(offenders)
