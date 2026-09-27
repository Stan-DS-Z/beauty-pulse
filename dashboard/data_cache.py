"""Boot-once data for the Dash app.

Every frame is read through bp.data once per process and kept; HEADLINE, LAUNCH
and the string tables for both languages are computed once. Pages build their
trees from a Data at import, and callbacks read the same cached frames. The bp
builders copy any frame they add columns to, so the cached frames stay as read.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from bp import brief as bp_brief
from bp import data as bp_data
from bp import sources, strings

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
    BRIEF: dict | None             # brief.compute_brief at the cut-off, None without the launch export
    REGISTRY: dict                 # sources.build_registry, the latest data (monitor)
    REPORT_REGISTRY: dict          # the same, on the frozen edition (report pages)
    S: dict                        # lang -> string table

    def frame(self, name):
        """A loaded asset, e.g. frame("umap") -> load_umap(assets). Raises
        FileNotFoundError when the CSV is absent; the pages catch it and show a
        notice in the chart's place."""
        return _frame(self.assets, name)


def build_report(assets: Path, launch: bool = True):
    """The report pages' data: computed only on the issued edition's frozen
    files (sources.edition_assets), cut at sources.CUTOFF. The monitor reads
    `assets` itself."""
    frozen = sources.edition_assets(assets)
    if not frozen.is_dir():
        raise FileNotFoundError(f"{frozen} is missing: run issue_edition.py")
    headline = bp_data.compute_headline(frozen)
    brief = bp_brief.compute_brief(frozen, headline, sources.CUTOFF) if launch else None
    return brief, sources.build_registry(frozen, sources.CUTOFF)


def build_data(assets: Path, launch: bool = True) -> Data:
    """A Data over `assets`. launch=False builds it as a clone without the
    launch export would see it."""
    headline = bp_data.compute_headline(assets)
    lau = bp_data.compute_launch_headline(assets) if launch else None
    brief, report_registry = build_report(assets, launch)
    registry = sources.build_registry(assets)
    return Data(assets=assets, HEADLINE=headline, LAUNCH=lau, BRIEF=brief, REGISTRY=registry,
                REPORT_REGISTRY=report_registry,
                S={lang: strings.build_strings(lang, headline, lau, assets, brief, report_registry)
                   for lang in LANGS})


@lru_cache(maxsize=1)
def load() -> Data:
    return build_data(ASSETS)
