"""
signal_pulse/src/config.py
──────────────────────────
Configuration loader for Signal/Pulse.
All notebooks import from here — never hardcode brands, categories, or keywords.

Usage:
    from src.config import load_brands, load_categories, load_keywords, PROJECT

    brands = load_brands()                    # active group, all brands
    targets = load_brands(target_only=True)   # is_target == 1 only
    kao = load_brands(group='kao')            # specific group

To retarget the project (e.g. L'Oréal Japan):
    1. Edit config/project.yml → target.active_group: "loreal_japan"
    2. Edit config/brands.xlsx → set is_target=1 for desired brands
    3. Rerun NB02 ingestion
"""

import yaml
import pandas as pd
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


# ── Project config ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_project_config() -> dict:
    """Load project.yml. Cached — reads once per session."""
    path = CONFIG_DIR / "project.yml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class _AttrDict(dict):
    """Dot-access wrapper for nested dicts."""
    def __getattr__(self, key):
        try:
            val = self[key]
            return _AttrDict(val) if isinstance(val, dict) else val
        except KeyError:
            raise AttributeError(key)


def get_project() -> _AttrDict:
    return _AttrDict(load_project_config())


PROJECT = get_project()


# ── Brands ─────────────────────────────────────────────────────────────────

def load_brands(
    group: str | None = None,
    target_only: bool = False,
    tier: str | None = None,
) -> pd.DataFrame:
    """
    Load brand list from config/brands.xlsx.

    Parameters
    ----------
    group       : filter by brand_group ('kao', 'shiseido', 'kose', 'rohto',
                  'loreal_japan', 'jp_indie', 'estee_lauder', 'lvmh_beauty', 'all')
                  defaults to active_group from project.yml
    target_only : if True, return only rows where is_target == 1
    tier        : filter by tier string (e.g. 'skincare', 'mass_skincare',
                  'sensitive_skincare', 'cosmetics', 'haircare', etc.)
    """
    df = pd.read_excel(CONFIG_DIR / "brands.xlsx", sheet_name="brands", dtype=str)
    df["is_target"] = df["is_target"].astype(int)

    # Drop metadata columns not needed downstream
    drop_cols = [c for c in ["status"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    if group is None:
        group = PROJECT.lens.active_group

    if group and group != "all":
        df = df[df["brand_group"] == group]

    if target_only:
        df = df[df["is_target"] == 1]

    if tier:
        df = df[df["tier"] == tier]

    return df.reset_index(drop=True)


def load_all_target_brands() -> pd.DataFrame:
    """
    Return all target brands across active lens group AND benchmark groups.
    Used in NB04+ analysis and NB07 dashboard — NOT for ingestion.
    """
    active = PROJECT.lens.active_group
    benchmarks = PROJECT.lens.benchmark_groups or []
    groups = [active] + list(benchmarks)

    frames = []
    for g in groups:
        df = load_brands(group=g, target_only=True)
        frames.append(df)

    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["brand_name_jp"]
    )


def load_brand_groups() -> pd.DataFrame:
    """Load brand group definitions."""
    return pd.read_excel(
        CONFIG_DIR / "brands.xlsx", sheet_name="brand_groups", dtype=str
    )


def get_cosme_brand_ids(group: str | None = None) -> dict[str, str]:
    """
    Return {brand_name_jp: cosme_brand_id} for brands with confirmed @cosme IDs.
    Post-hoc lens helper — used in NB04+ to JOIN discovered products to brands.
    """
    df = load_brands(group=group)
    df = df[df["cosme_brand_id"].notna() & (df["cosme_brand_id"].str.strip() != "")]
    return dict(zip(df["brand_name_jp"], df["cosme_brand_id"]))


# ── Categories ─────────────────────────────────────────────────────────────

def load_cosme_categories(
    layer1: bool | None = None,
    layer2: bool | None = None,
) -> pd.DataFrame:
    """
    Load @cosme category list from config/categories.xlsx.

    Parameters
    ----------
    layer1 : if True, return only categories where layer1_metadata == 1
    layer2 : if True, return only categories where layer2_reviews == 1
    Pass neither to return all categories.
    """
    df = pd.read_excel(
        CONFIG_DIR / "categories.xlsx", sheet_name="cosme_categories", dtype=str
    )
    df["layer1_metadata"] = df["layer1_metadata"].astype(int)
    df["layer2_reviews"]  = df["layer2_reviews"].astype(int)
    if layer1 is not None:
        df = df[df["layer1_metadata"] == int(layer1)]
    if layer2 is not None:
        df = df[df["layer2_reviews"] == int(layer2)]
    return df.reset_index(drop=True)


def load_rakuten_genres(
    layer1: bool | None = None,
    layer2: bool | None = None,
) -> pd.DataFrame:
    """
    Load Rakuten genre list from config/categories.xlsx.
    Same layer1/layer2 parameter semantics as load_cosme_categories.
    """
    df = pd.read_excel(
        CONFIG_DIR / "categories.xlsx", sheet_name="rakuten_genres", dtype=str
    )
    df["layer1_metadata"] = df["layer1_metadata"].astype(int)
    df["layer2_reviews"]  = df["layer2_reviews"].astype(int)
    if layer1 is not None:
        df = df[df["layer1_metadata"] == int(layer1)]
    if layer2 is not None:
        df = df[df["layer2_reviews"] == int(layer2)]
    return df.reset_index(drop=True)


def get_cosme_category_ids(tier: str | None = None, layer2: bool = True) -> dict[str, str]:
    """
    Return {category_name_jp: cosme_category_id}.
    Defaults to layer2=True — categories with a full review corpus.
    """
    df = load_cosme_categories(layer2=True if layer2 else None)
    if tier:
        df = df[df["tier"] == tier]
    return dict(zip(df["category_name_jp"], df["cosme_category_id"]))


def get_rakuten_genre_ids(tier: str | None = None, layer1: bool = True) -> dict[str, str]:
    """
    Return {genre_name_jp: rakuten_genre_id}.
    Defaults to layer1=True — all genres in the metadata sweep.
    """
    df = load_rakuten_genres(layer1=True if layer1 else None)
    if tier:
        df = df[df["tier"] == tier]
    return dict(zip(df["genre_name_jp"], df["rakuten_genre_id"]))


# ── Keywords ───────────────────────────────────────────────────────────────

def load_seed_terms(
    group: str | None = None,
    in_trends: bool | None = None,
    in_nlp: bool | None = None,
    max_priority: int = 3,
) -> pd.DataFrame:
    """Load keyword seed terms from config/keywords.xlsx."""
    df = pd.read_excel(
        CONFIG_DIR / "keywords.xlsx", sheet_name="seed_terms", dtype=str
    )
    df["in_trends"] = df["in_trends"].astype(int)
    df["in_nlp"] = df["in_nlp"].astype(int)
    df["priority"] = df["priority"].astype(int)

    if group:
        df = df[df["group"] == group]
    if in_trends is not None:
        df = df[df["in_trends"] == int(in_trends)]
    if in_nlp is not None:
        df = df[df["in_nlp"] == int(in_nlp)]

    return df[df["priority"] <= max_priority].reset_index(drop=True)


def get_trends_terms(group: str | None = None, max_priority: int = 2) -> list[str]:
    """
    Return list of terms for Google Trends pulls.
    Anchor term (スキンケア) is always first.
    """
    anchor = PROJECT.google_trends.anchor_term
    df = load_seed_terms(group=group, in_trends=True, max_priority=max_priority)
    terms = [t for t in df["term"].tolist() if t != anchor]
    return [anchor] + terms


def load_exclusions() -> pd.DataFrame:
    """Load exclusion list — terms to filter from NLP analysis."""
    return pd.read_excel(
        CONFIG_DIR / "keywords.xlsx", sheet_name="exclusions", dtype=str
    )


def get_exclusion_terms() -> list[str]:
    """Return flat list of terms to exclude from NLP corpus."""
    return load_exclusions()["term"].tolist()


def load_stopwords() -> list[str]:
    """Load JP NLP stopword list."""
    df = pd.read_excel(
        CONFIG_DIR / "keywords.xlsx", sheet_name="nlp_stopwords", dtype=str
    )
    return df["term"].tolist()


# ── Config summaries ───────────────────────────────────────────────────────
#
# Two functions with clearly separated concerns:
#
#   print_ingestion_summary()  — NB01–NB03 (public notebooks)
#                                Brand-agnostic. Shows what data is being
#                                collected and how the pipeline is configured.
#                                Safe for a public GitHub repo.
#
#   print_lens_summary()       — NB04+ (private/gitignored notebooks)
#                                Company-specific. Shows which brands and
#                                groups are active in the analysis lens.
#                                Never called in ingestion notebooks.

def print_ingestion_summary() -> None:
    """
    Print ingestion scope — brand-agnostic.
    Call at the top of NB01–NB03.
    """
    cfg = PROJECT
    cats_l1 = load_cosme_categories(layer1=True)
    cats_l2 = load_cosme_categories(layer2=True)
    seeds   = load_seed_terms(in_trends=True, max_priority=2)

    print("SIGNAL/PULSE — INGESTION SCOPE")
    print("=" * 52)
    print(f"  Project        : {cfg.project.name} v{cfg.project.version}")
    print(f"  Time range     : {cfg.time_range.start} → {cfg.time_range.end}")
    print(f"  Baseline       : {cfg.time_range.baseline_start} (pre-COVID)")
    print(f"  Anchor term    : {cfg.google_trends.anchor_term}")
    print(f"  Layer 2 top N  : {cfg.ingestion.layer2_top_n} products per category")
    print()
    print(f"  @cosme — Layer 1 sweep  : {len(cats_l1)} categories")
    print(f"  @cosme — Layer 2 corpus : {len(cats_l2)} categories")
    print(f"  Trend seed terms        : {len(seeds)}")
    print(f"  Exclusions              : {len(get_exclusion_terms())} terms flagged")


def print_lens_summary() -> None:
    """
    Print active company lens — company-specific.
    Call at the top of NB04+. Never call in NB01–NB03.
    """
    cfg = PROJECT
    active_group = cfg.lens.active_group
    benchmarks   = cfg.lens.benchmark_groups or []

    targets     = load_brands(target_only=True)
    all_targets = load_all_target_brands()

    # Human-readable company names from brand_groups sheet
    groups_df = load_brand_groups()
    name_map  = dict(zip(groups_df["group_key"], groups_df["group_display_name"]))

    active_name     = name_map.get(active_group, active_group)
    benchmark_names = [name_map.get(g, g) for g in benchmarks]

    print("SIGNAL/PULSE — ACTIVE LENS")
    print("=" * 52)
    print(f"  Company focus  : {active_name}")
    print(f"  Comparisons    : {', '.join(benchmark_names)}")
    print()
    print(f"  {active_name} target brands ({len(targets)}):")
    for _, row in targets.iterrows():
        print(f"    {row['brand_name_jp']:<18} {row['brand_name_en']:<22} [{row['tier']}]")
    print()
    print(f"  Total brands in lens (focus + comparisons): {len(all_targets)}")
