"""The dashboard renders end to end without raising.

The direct import in conftest gets HEADLINE without a script run context, so
st.* is a no-op there and a rendering bug would go unseen. AppTest executes the
real Streamlit path.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def rendered():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(
        str(ROOT / "dashboard" / "streamlit_app.py"), default_timeout=180).run()


def test_app_renders_without_exception(rendered):
    assert not rendered.exception, rendered.exception


def test_app_renders_the_measured_ratio_and_its_range(rendered, headline):
    """The reclassified figure and its sensitivity both reach the page."""
    body = "\n".join(str(e.value) for e in rendered.markdown) \
         + "\n".join(str(e.value) for e in rendered.metric)
    assert f"{headline['sku_measured']:.1f}" in body
    assert f"{headline['sku_lo']:.1f}" in body, "the CI must be shown, not just the point"
    assert f"{headline['sku_span_hi']:.1f}" in body, "the sensitivity span must be shown"
