"""Shared fixtures.

The dashboard module is imported directly rather than through Streamlit's
script runner: outside a run context the st.* calls are no-ops, so importing it
gives us HEADLINE and STRINGS — the values the deployed page actually renders —
without standing up a server.
"""

import gzip
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def app():
    spec = importlib.util.spec_from_file_location(
        "dash_app", ROOT / "dashboard" / "streamlit_app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def headline(app):
    return app.HEADLINE


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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    method = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")

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
