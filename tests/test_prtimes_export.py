"""The launch layer's public boundary, and the gate's measured accuracy.

PR TIMES releases are third-party text under private-use terms, and the repo is
public. The committed exports may carry metadata and computed tags only; the
whitelists below are written out here rather than imported from the build
script, so widening the export means editing this file on purpose.

The gate tests need the release store and the labelled samples, both
gitignored, so they run locally and skip in CI.
"""

import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "dashboard" / "assets"

LAUNCH_COLUMNS = [
    "release_id", "company_id", "issuer", "issuer_group", "role", "origin", "panel",
    "published", "month", "category", "category_group", "ingredients", "brand", "tier",
    "is_quasi_drug", "is_renewal", "is_edition", "url",
]
FEED_COLUMNS = ["company_id", "issuer_group", "panel", "feed_reach", "history_complete",
                "fetched"]
TERM_COLUMNS = ["canonical", "label_short_en", "label_ja", "trends_term"]


@pytest.fixture(scope="module")
def launches():
    path = ASSETS / "prtimes_launches.csv"
    if not path.exists():
        pytest.skip("launch export not built")
    return pd.read_csv(path, dtype=str).fillna("")


def test_exports_carry_only_the_whitelisted_columns(launches):
    assert list(launches.columns) == LAUNCH_COLUMNS
    assert list(pd.read_csv(ASSETS / "prtimes_feeds.csv").columns) == FEED_COLUMNS
    assert list(pd.read_csv(ASSETS / "prtimes_ingredient_terms.csv").columns) == TERM_COLUMNS


def test_no_cell_carries_release_prose(launches):
    """Titles run 40-120 characters; the longest legitimate cell is a URL or a
    pipe-joined tag list. A cell past 150 characters is text that leaked."""
    longest = launches.apply(lambda c: c.str.len().max()).max()
    assert longest < 150, f"a cell of {longest} characters is in the export"


def test_one_row_per_release_and_known_panels(launches):
    assert launches["release_id"].is_unique
    assert set(launches["panel"]) <= {"core", "present_forward"}
    for col in ("is_quasi_drug", "is_renewal", "is_edition"):
        assert set(launches[col]) <= {"0", "1"}


def test_release_store_is_gitignored():
    ignored = subprocess.run(["git", "check-ignore", "-q", "data/prtimes.db"], cwd=ROOT)
    assert ignored.returncode == 0, "data/prtimes.db holds release text and must stay untracked"


def test_discovery_tab_renders_without_the_export(tmp_path):
    """A clone without the launch export still renders every tab.

    st.cache_data keys on the function's source, not on the assets directory,
    so an earlier app run in this process would hand back its cached launch
    figures. The cache is cleared first."""
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_data.clear()
    app_dir = tmp_path / "dashboard"
    (app_dir / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "dashboard" / "streamlit_app.py", app_dir / "streamlit_app.py")
    for f in ASSETS.iterdir():
        if not f.name.startswith("prtimes_"):
            (app_dir / "assets" / f.name).symlink_to(f)
    at = AppTest.from_file(str(app_dir / "streamlit_app.py"), default_timeout=180).run()
    assert not at.exception, at.exception
    body = "\n".join(str(e.value) for e in at.markdown)
    assert "prtimes_launches.csv" in body, "the empty state line must render"


# ── Gate v2, frozen: the counts it scored when the vocabulary was fixed ──────

SAMPLES = {
    # labels, sample (title + excerpt), frozen (TP, FP, FN, TN)
    "design": ("recon/prtimes_launch_validation_labels.csv",
               "recon/2026-09-18_prtimes-validation-sample.csv", (98, 3, 4, 45)),
    "holdout": ("recon/prtimes_launch_holdout_labels.csv",
                "recon/2026-09-19_prtimes-holdout-sample.csv", (44, 6, 11, 39)),
}


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_gate_scores_what_it_scored_when_frozen(name):
    labels, sample, frozen = SAMPLES[name]
    if not ((ROOT / labels).exists() and (ROOT / sample).exists()):
        pytest.skip("labelled samples are gitignored")
    from src import prtimes as pt
    mt = pt.load_matchers()
    lab = pd.read_csv(ROOT / labels, dtype=str).fillna("")
    smp = pd.read_csv(ROOT / sample, dtype=str, encoding="utf-8-sig").fillna("")
    d = lab.merge(smp[["sample_id", "release_id", "title", "excerpt"]],
                  on=["sample_id", "release_id"])
    truth = (d["is_beauty"] == "1") & (d["is_launch"] == "1")
    pred = pd.Series([bool(pt.gate(t, e, mt)["is_launch"]) for t, e in
                      zip(d["title"], d["excerpt"])], index=d.index)
    got = (int((pred & truth).sum()), int((pred & ~truth).sum()),
           int((~pred & truth).sum()), int((~pred & ~truth).sum()))
    assert got == frozen, (
        f"{name}: gate now scores {got}, frozen at {frozen}. A vocabulary change "
        "re-opens the holdout as in-sample and needs a fresh sample.")
