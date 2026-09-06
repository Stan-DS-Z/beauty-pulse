"""Every figure in the published prose must equal what compute_headline() renders.

This is the bug this project keeps hitting: a figure is hardcoded in README,
METHODOLOGY and the dashboard's string table, the pipeline is re-run, and the
surfaces drift apart. The SKU ratio went 4.1x -> 3.7x and the sweep missed
several sites; the ingredient window was reported on three different bases.
These tests fail when the prose and the computation disagree.
"""

import re

import pandas as pd


def test_every_sku_ratio_in_the_docs_is_a_computed_one(docs):
    """Any "N.N x/×/倍" in the docs must be a value build_sku_ratio.py produced.

    The ratio is deliberately published as a range now — 6.6x measured, 3.7x as
    Rakuten tags it, 9.7x and 10.7x under the other two treatments — so a single
    expected value no longer describes the docs. What must still hold is that
    every figure traces to the asset; a hand-typed or stale one fails.
    """
    from pathlib import Path
    ratios = pd.read_csv(
        Path(__file__).resolve().parent.parent / "dashboard" / "assets" / "nb07_sku_ratio.csv"
    )["ratio"]
    allowed = {f"{round(float(r), 1):.1f}" for r in ratios}

    found = {m.group(1) for m in re.finditer(r"(\d+\.\d+)\s*[×x倍]", docs)}
    stray = found - allowed
    assert not stray, (
        f"docs carry ratios {sorted(stray)} that build_sku_ratio.py does not "
        f"produce; it computes {sorted(allowed)}")


def test_ingredient_levels_match(docs, headline):
    """"A→B" level pairs must be the niacinamide and retinol endpoints."""
    # (?<![\d.]) / (?![\d.]) so "0.31→0.53" is not read as 31→0.
    pairs = {(int(a), int(b)) for a, b in
             re.findall(r"(?<![\d.])(\d+)\s*→\s*(\d+)(?![\d.])", docs)}
    expected = {
        (headline["nia_pre"], headline["nia_post"]),
        (headline["ret_pre"], headline["ret_post"]),
        (headline["ing_y0"], headline["ing_y1"]),   # the "2019→2025" window
    }
    assert pairs == expected, f"docs {sorted(pairs)} vs headline {sorted(expected)}"


def test_cosmetics_decline_matches(docs, headline):
    assert f"{abs(headline['cosm_decline'])}%" in docs


def test_convergence_figures_match(docs, headline):
    for value in (headline["conv_delta"], headline["conv_lo"], headline["conv_hi"]):
        assert f"{value:.3f}" in docs, f"{value:.3f} missing from the docs"
    # The CI is published as a bracketed pair; both bounds must appear.
    for bound in re.findall(r"\+(\d\.\d{3})", headline["conv_ci"]):
        assert bound in docs, f"CI bound {bound} missing from the docs"


# No docs assertion for ratio_0 / ratio_1: outside the revision log they are
# rendered only by the dashboard, computed live, so there is nothing to drift.


def test_dashboard_string_table_hardcodes_no_ratio(app):
    """Every ratio the page shows is rebuilt from HEADLINE, so none is stored.

    The static table is where stale figures used to hide: a heading that the
    live block overwrites is dead code, and one it does not overwrite silently
    disagrees with the KPI card.
    """
    blob = "\n".join(str(v) for lang in app.STRINGS.values() for v in lang.values())
    found = {m.group(1) for m in re.finditer(r"(\d+\.\d+)\s*[×x倍]", blob)}
    assert not found, f"STRINGS hardcodes ratios {sorted(found)}; build them from HEADLINE"
