"""Shared fixtures.

The dashboard's numbers and copy come from its bp package, which imports no UI
framework, so the tests read HEADLINE and STRINGS — the values the deployed
page renders — from bp directly, without Streamlit or a server.
"""

import gzip
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))


@pytest.fixture(scope="session")
def headline():
    from bp import data
    return data.compute_headline(data.ASSETS)


@pytest.fixture(scope="session")
def app(headline):
    """The names the tests read from the dashboard, served from bp.

    bp computes nothing at import and its loaders take the assets directory,
    so HEADLINE is computed once above and the loader is bound here to the
    shipped assets, the way the app binds it."""
    from bp import data, strings
    return SimpleNamespace(
        ASSETS=data.ASSETS,
        HEADLINE=headline,
        STRINGS=strings.STRINGS,
        METI_SKIN=data.METI_SKIN,
        METI_MAKE=data.METI_MAKE,
        METI_BREAK=data.METI_BREAK,
        LAUNCH_WINDOW_START=data.LAUNCH_WINDOW_START,
        load_meti_annual=lambda: data.load_meti_annual(data.ASSETS),
    )


def _rendered(path):
    """The doc as GitHub shows it: figure markers stripped.

    build_docs_figures.py wraps every generated figure in
    <!--f:key-->value<!--/f-->. HTML comments are invisible when rendered, so
    the published claim is the text without them — and that is what these tests
    are about. Leaving them in breaks any check that reads across a figure,
    such as the "A→B" window pairs.
    """
    import re
    return re.sub(r"<!--/?f:?[a-z0-9_]*-->", "",
                  path.read_text(encoding="utf-8"))


REVISION_LOG_HEADING = "## \u5206\u6790\u306e\u6539\u8a02\u5c65\u6b74 / Analysis Revision History"


@pytest.fixture(scope="session")
def docs():
    """README + METHODOLOGY as one string — the live published claims.

    METHODOLOGY's revision log is excluded on purpose: its entries quote the
    superseded figure alongside the correction ("2019→2026 (−35%) ... recomputed
    on 2019→2025"), so it is the one place where an old number is correct.
    Reconciliation applies to what the docs currently assert, not to the record
    of what they used to.
    """
    readme = _rendered(ROOT / "README.md")
    method = _rendered(ROOT / "METHODOLOGY.md")

    start = method.index(REVISION_LOG_HEADING)
    end = method.index("\n## ", start + len(REVISION_LOG_HEADING))
    method = method[:start] + method[end:]

    return readme + "\n" + method


@pytest.fixture(scope="session")
def public_db(tmp_path_factory):
    """Path to the shipped public DB, extracting the archive if needed."""
    extracted = ROOT / "data" / "signal_pulse_public.db"
    if extracted.exists():
        return extracted
    gz = ROOT / "dashboard" / "assets" / "signal_pulse_public.db.gz"
    if not gz.exists():
        pytest.skip("public DB archive not present")
    out = tmp_path_factory.mktemp("db") / "signal_pulse_public.db"
    with gzip.open(gz, "rb") as src, open(out, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return out
