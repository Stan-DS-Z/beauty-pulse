"""Every figure in the published prose must equal what compute_headline() renders.

This is the bug this project keeps hitting: a figure is hardcoded in README,
METHODOLOGY and the dashboard's string table, the pipeline is re-run, and the
surfaces drift apart. The SKU ratio went 4.1x -> 3.7x and the sweep missed
several sites; the ingredient window was reported on three different bases.
These tests fail when the prose and the computation disagree.
"""

import re


def test_sku_ratio_is_one_value_everywhere(docs, headline):
    """Any "N.N x/×/倍" in the docs is the SKU ratio and must match."""
    found = {m.group(1) for m in re.finditer(r"(\d+\.\d+)\s*[×x倍]", docs)}
    expected = f"{headline['sku_ratio']:.1f}"
    assert found == {expected}, (
        f"docs carry ratios {sorted(found)}; compute_headline says {expected}")


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


def test_dashboard_prose_carries_no_stale_ratio(app):
    """The EN/JP string table must not hardcode a ratio that disagrees."""
    blob = "\n".join(str(v) for lang in app.STRINGS.values() for v in lang.values())
    found = {m.group(1) for m in re.finditer(r"(\d+\.\d+)\s*[×x倍]", blob)}
    expected = f"{app.HEADLINE['sku_ratio']:.1f}"
    assert found <= {expected}, (
        f"dashboard strings carry ratios {sorted(found)}; expected {expected}")
