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


def test_app_renders_the_headline_ratio(rendered, headline):
    """The SKU ratio reaches the page, not just the computation."""
    body = "\n".join(str(e.value) for e in rendered.markdown) \
         + "\n".join(str(e.value) for e in rendered.metric)
    assert f"{headline['sku_ratio']:.1f}" in body
