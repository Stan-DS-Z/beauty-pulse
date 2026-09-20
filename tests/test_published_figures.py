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
        (headline["ing_y0"], headline["ing_y1"]),   # the attention window
        # The market layer's windows. METI ends in 2024, two years before
        # Trends, and it is split at the 2022 break — so the docs legitimately
        # name three more windows, and each must be one compute_headline uses.
        (headline["mkt_y0"], headline["mkt_y1"]),     # full METI span
        (headline["mkt_y0"], headline["mkt_pre1"]),   # before the break
        (headline["mkt_break"], headline["mkt_y1"]),  # after the break
    }
    stray = pairs - expected
    assert not stray, (
        f"docs carry windows {sorted(stray)} that compute_headline does not "
        f"define; it uses {sorted(expected)}")
    # The reverse guard, kept narrow: the README is an index now and does not
    # re-narrate every finding, but the ingredient endpoints are the one pair
    # the docs still assert outright, so they must not drift out of them.
    assert (headline["nia_pre"], headline["nia_post"]) in pairs, (
        "the niacinamide endpoints have left the docs — either restore them or "
        "drop this guard deliberately")


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


def test_size_curve_copy_uses_the_asset_window(app):
    """The size-curve explanation must name the window the CSV defines.

    It said 2023–25 while nb06_cosine_salvage.csv said 2023–26, understating it
    by the largest year in the corpus. Other windows on the page (word clouds,
    the tier comparison, the data subtitle) are different analyses with their
    own spans, so this checks only the string the cosine asset governs.
    """
    for lang in ("en", "jp"):
        assert not app.STRINGS[lang]["t2_curvee"] or "2023" not in app.STRINGS[lang]["t2_curvee"], (
            "t2_curvee hardcodes a window; it must be rebuilt from conv_p1")


def test_period_labels_match_the_asset(app):
    import pandas as pd
    from pathlib import Path
    sm = pd.read_csv(Path(__file__).resolve().parent.parent
                     / "dashboard" / "assets" / "nb06_cosine_salvage.csv")
    sm = sm[sm["method"] == "size_matched"]
    assert app.HEADLINE["conv_p0"] == str(sm["period"].iloc[0])
    assert app.HEADLINE["conv_p1"] == str(sm["period"].iloc[1])


def test_marked_doc_figures_are_generated_not_typed():
    """Every <!--f:key--> span in the docs equals what build_docs_figures computes.

    The reconciliation this replaces was manual and had to happen after every
    weekly pull, because the SKU ratio moves with the catalogue. A figure that
    drifts is now a failing test rather than a number nobody re-read.
    """
    import re
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    import build_docs_figures as bdf

    reg = bdf.build_registry()
    stale, unknown = [], []
    for name in bdf.DOCS:
        for key, shown in bdf.MARKER.findall((root / name).read_text(encoding="utf-8")):
            if key not in reg:
                unknown.append(f"{name}: {key}")
            elif shown != reg[key]:
                stale.append(f"{name}: {key} shows {shown!r}, computed {reg[key]!r}")

    assert not unknown, f"markers with no registry entry: {unknown}"
    assert not stale, (
        "docs carry figures that disagree with the computed assets:\n  "
        + "\n  ".join(stale) + "\nRun: python build_docs_figures.py")
