"""Boot-once data for the Dash app.

Every frame is read through bp.data once per process and kept; HEADLINE, LAUNCH
and the string tables for both languages are computed once. Pages build their
trees from a Data at import, and callbacks read the same cached frames. The bp
builders copy any frame they add columns to, so the cached frames stay as read.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from bp import data as bp_data
from bp import strings

ASSETS = Path(__file__).parent / "assets"
LANGS = ("en", "jp")


@lru_cache(maxsize=None)
def _frame(assets: Path, name: str):
    return getattr(bp_data, f"load_{name}")(assets)


@dataclass(frozen=True)
class Data:
    assets: Path
    HEADLINE: dict
    LAUNCH: dict | None
    S: dict                        # lang -> string table

    def frame(self, name):
        """A loaded asset, e.g. frame("umap") -> load_umap(assets). Raises
        FileNotFoundError when the CSV is absent, as the Streamlit loaders do."""
        return _frame(self.assets, name)


def build_data(assets: Path, launch: bool = True) -> Data:
    """A Data over `assets`. launch=False builds it as a clone without the
    launch export would see it."""
    headline = bp_data.compute_headline(assets)
    lau = bp_data.compute_launch_headline(assets) if launch else None
    return Data(assets=assets, HEADLINE=headline, LAUNCH=lau,
                S={lang: strings.build_strings(lang, headline, lau, assets) for lang in LANGS})


@lru_cache(maxsize=1)
def load() -> Data:
    return build_data(ASSETS)
