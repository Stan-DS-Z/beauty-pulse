"""No report table or chart sets a year before the January 2022 METI break
against a year after it for a skincare line.

METI's skincare lines step down at January 2022 (data.METI_BREAK), so a
skincare change measured across it includes the step. Makeup lines have no
step, and the report sets them against earlier years. Every report page's
tree is read as the browser gets it, in both languages.
"""

import json
import re
import sys

import pytest

from bp.data import METI_BREAK, METI_SKIN
from bp.funnel import CATEGORIES
from bp.strings import LAUNCH_CAT, METI_LINE

REPORT_PATHS = ("/brief", "/market")
YEAR = re.compile(r"(?<!\d)(20[12]\d)(?!\d)")
# A change between two years: 2019→2025, 2019〜2025, 2019–2025, 2019-2025.
PAIR = re.compile(r"(?<!\d)(20[12]\d)\s*(?:→|〜|–|-|to)\s*(20[12]\d)(?!\d)")

# Every name a skincare line or category goes by on the report pages.
SKINCARE_NAMES = (set(METI_SKIN)
                  | {n for li in METI_SKIN for n in METI_LINE[li]}
                  | {n for k, (_, _, _, g) in CATEGORIES.items() if g == "skincare"
                     for n in LAUNCH_CAT[k]})


def crosses(a, b):
    return min(a, b) < METI_BREAK <= max(a, b)


@pytest.fixture(scope="module")
def trees():
    import dash
    import plotly.io.json as pjson
    import app  # noqa: F401  registers the pages
    mods = {p["path"]: sys.modules[m] for m, p in dash.page_registry.items()}
    return {(path, lang): json.loads(pjson.to_json_plotly(mods[path].TREES[lang]))
            for path in REPORT_PATHS for lang in ("en", "jp")}


def _walk(node, kind):
    """Every component of one type in a serialised tree."""
    if isinstance(node, list):
        for n in node:
            yield from _walk(n, kind)
    elif isinstance(node, dict):
        if node.get("type") == kind:
            yield node
        yield from _walk(node.get("props", {}).get("children"), kind)


def _text(node):
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(_text(n) for n in node)
    if isinstance(node, dict):
        return _text(node.get("props", {}).get("children"))
    return ""


def _flat(v):
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in _flat(x)]
    return [v] if isinstance(v, str) else []


def test_no_report_table_heads_a_column_across_the_break(trees):
    """Every report table carries skincare rows, so no column may pair years
    across the break."""
    for key, tree in trees.items():
        for table in _walk(tree, "Table"):
            for th in _walk(table, "Th"):
                for a, b in PAIR.findall(_text(th)):
                    assert not crosses(int(a), int(b)), (key, _text(th))


def test_no_report_chart_sets_a_skincare_line_against_a_pre_break_year(trees):
    """A chart point that names a skincare line carries no year before the
    break, in its own text or in its trace's hover template."""
    checked = 0
    for key, tree in trees.items():
        for graph in _walk(tree, "Graph"):
            for trace in graph["props"]["figure"]["data"]:
                n = max(len(trace.get(k) or []) for k in ("x", "y", "text", "customdata"))
                tmpl = trace.get("hovertemplate") or ""
                tmpl = tmpl if isinstance(tmpl, str) else " ".join(tmpl)
                for i in range(n):
                    point = []
                    for k in ("x", "y", "text", "customdata"):
                        v = trace.get(k)
                        if isinstance(v, list) and i < len(v):
                            point += _flat(v[i])
                    if not SKINCARE_NAMES & set(point):
                        continue
                    checked += 1
                    years = [int(y) for s in point + [tmpl] for y in YEAR.findall(s)]
                    assert all(y >= METI_BREAK for y in years), (key, point, tmpl)
    assert checked, "no chart point named a skincare line"
