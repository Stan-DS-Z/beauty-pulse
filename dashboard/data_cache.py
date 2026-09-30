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
from bp import consumer as bp_consumer
from bp import data as bp_data
from bp import demand as bp_demand
from bp import market as bp_market
from bp import sources, strings
from bp import supply as bp_supply
from bp import timing as bp_timing

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
    MARKET: dict                   # market.compute_market at the cut-off
    DEMAND: dict                   # demand.compute_demand at the cut-off
    SUPPLY: dict | None            # supply.compute_supply at the cut-off, None without the launch export
    CONSUMER: dict                 # consumer.compute_consumer on the frozen edition
    TIMING: dict                   # timing.compute_timing at the cut-off
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
    market = bp_market.compute_market(frozen, sources.CUTOFF)
    demand = bp_demand.compute_demand(frozen, sources.CUTOFF)
    supply = bp_supply.compute_supply(frozen, sources.CUTOFF) if launch else None
    consumer = bp_consumer.compute_consumer(frozen)
    timing = bp_timing.compute_timing(frozen, sources.CUTOFF)
    return (brief, market, demand, supply, consumer, timing,
            sources.build_registry(frozen, sources.CUTOFF))


def build_data(assets: Path, launch: bool = True) -> Data:
    """A Data over `assets`. launch=False builds it as a clone without the
    launch export would see it."""
    headline = bp_data.compute_headline(assets)
    lau = bp_data.compute_launch_headline(assets) if launch else None
    brief, market, demand, supply, consumer, timing, report_registry = build_report(assets, launch)
    registry = sources.build_registry(assets)
    return Data(assets=assets, HEADLINE=headline, LAUNCH=lau, BRIEF=brief, MARKET=market,
                DEMAND=demand, SUPPLY=supply, CONSUMER=consumer, TIMING=timing,
                REGISTRY=registry,
                REPORT_REGISTRY=report_registry,
                S={lang: strings.build_strings(lang, headline, lau, assets, brief,
                                               report_registry, market, demand, supply,
                                               consumer, timing)
                   for lang in LANGS})


@lru_cache(maxsize=1)
def load() -> Data:
    return build_data(ASSETS)
