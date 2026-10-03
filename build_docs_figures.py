"""Inject computed figures into README.md and METHODOLOGY.md.

    python build_docs_figures.py            # rewrite the marked spans
    python build_docs_figures.py --check    # verify only; non-zero if stale
    python build_docs_figures.py --list     # print the registry

Every figure the docs assert used to be hand-typed, which is how the SKU ratio
drifted from the dashboard and why the ratio moves again on every weekly pull.
The dashboard already solved this for itself: figure-bearing entries in STRINGS
are left empty and rebuilt from HEADLINE, so a stale number cannot ship. This
does the same for the two markdown files.

A figure in the prose is wrapped in a marker naming its registry key:

    46,193 SKUs      ->  <!--f:rakuten_skus-->47,374<!--/f--> SKUs

HTML comments render as nothing on GitHub, so the published page is unchanged.
Running this rewrites whatever sits between the markers, so the docs cannot
disagree with the assets they are quoting.

The registry reads the issued edition, as the report pages do
(dashboard/data_cache.build_report: the frozen files, cut at sources.CUTOFF):

  HEADLINE   compute_headline() on the edition's files: the values the report
             pages render, so docs and site cannot diverge
  LAUNCH     compute_launch_headline() and prtimes_feeds.csv, on the edition
  the site   whole sentences and tables from the report's own string tables
             (the Brief's findings, the Demand titles, the Method page's
             sources table), turned into markdown

A span may hold a sentence or a table as well as a number. Counts that only
the database holds (reviews stored, SKUs pulled) are not published: the
README states what the edition holds.

Not everything is derivable. Hand-label proportions, classifier scores and the
2022 break diagnostics are measurements recorded once, not recomputed per pull;
they stay as prose and --check ignores them.

Run it after NB07 and the weekly asset builds, which write the assets it reads.
update_data.command does this.
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dashboard"))
SITE = "https://beautypulse.web.app"

DOCS = ["README.md", "METHODOLOGY.md"]
MARKER = re.compile(r"<!--f:([a-z0-9_]+)-->(.*?)<!--/f-->", re.DOTALL)


def headline() -> dict:
    """compute_headline() on the issued edition's frozen files: the function
    and the files the report pages compute HEADLINE with."""
    from bp import data, sources
    return data.compute_headline(sources.edition_assets(data.ASSETS))


def launch_feeds() -> dict:
    """The launch panel's feed counts on the edition, cut at CUTOFF:
    compute_launch_headline() for what the figures use, prtimes_feeds.csv for
    the panel each active feed is on."""
    from bp import data, sources
    E = sources.edition_assets(data.ASSETS)
    lau = data.compute_launch_headline(E, sources.CUTOFF)
    if lau is None:
        return {}
    feeds = pd.read_csv(E / "prtimes_feeds.csv")
    return {
        "launch_core_feeds": f"{lau['n_core_feeds']}",
        "launch_core_issuers": f"{lau['n_core']}",
        "launch_later_feeds": f"{int((feeds['panel'] == 'present_forward').sum())}",
        "launch_later_feeds_l12": f"{lau['n_pf_feeds']}",
    }


# ── Text from the site ──────────────────────────────────────────────────────
# The sources on the Method page, by source role (METHODOLOGY, Source roles).
# A source no report page uses is listed last whatever its role.
ROLES = (("market", ("meti", "trade", "trends", "prtimes")),
         ("within", ("cosme", "youtube")))
SOURCE_COLS = ("ソース / Source", "測るもの / Measures", "収録範囲 / Coverage",
               "掲載ページ / Report pages")


def _md(text: str) -> str:
    """Page text for markdown: <b> kept as HTML, which GitHub renders. "**"
    does not open bold between two characters that are not spaces, such as
    が**+11%, so Japanese would show the asterisks. <br> becomes a space."""
    return text.replace("<br>", " ")


def _cell(text: str) -> str:
    return _md(text).replace("|", "\\|")


def _table(head, rows) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return _block(lines)


def _block(lines) -> str:
    """A block-level span: blank lines inside the markers, so the markdown
    around the comments parses as its own block."""
    return "\n\n" + "\n".join(lines) + "\n\n"


def site_text() -> dict:
    """Sentences and tables from the report's string tables, as the site
    renders them for the edition."""
    import data_cache
    from bp import sources
    d = data_cache.build_data(data_cache.ASSETS)
    en, ja = d.S["en"], d.S["jp"]
    out = {
        "lead_search_en": _md(en["dm_p_h"]),
        "lead_search_ja": _md(ja["dm_p_h"]),
        # スキンケア search over the same years, as the Demand page's note has it
        "skin_search_d": f"{abs(d.DEMAND['pair']['skin_d']):.0f}",
        "skin_search_dir_en": "rose" if d.DEMAND["pair"]["skin_d"] >= 0 else "fell",
        "skin_search_dir_ja": "上昇" if d.DEMAND["pair"]["skin_d"] >= 0 else "低下",
        "lead_mask_en": _md(en["dm_m_h"]),
        "lead_mask_ja": _md(ja["dm_m_h"]),
    }
    # The Brief: its governing thought and one line per finding, each linking
    # to its page, as the Brief's key findings do.
    from bp.strings import BRIEF_LINKS
    for code, S, q in (("en", en, ""), ("ja", ja, "?lang=ja")):
        lines = [f"> {_md(S['b_governing'])}", ""]
        for key, (path, _) in BRIEF_LINKS.items():
            lines.append(f"- **[{S['b_kf_labels'][key]}]({SITE}{path}{q})** — "
                         f"{_md(S[f'b_kf_{key}'])}")
        out[f"brief_{code}"] = _block(lines)
    # The Method page's sources table, split by source role.
    rows = dict(zip((r["key"] for r in d.METHOD["sources"]), en["me_s_rows"]))
    used = {r["key"] for r in d.METHOD["sources"] if r["pages"]}
    listed = [k for _, keys in ROLES for k in keys]
    assert set(listed) | (set(rows) - used) == set(rows), "a source has no role"
    for role, keys in ROLES:
        out[f"sources_{role}"] = _table(SOURCE_COLS, [rows[k] for k in keys if k in used])
    out["sources_unused"] = _table(SOURCE_COLS, [rows[k] for k in rows if k not in used])
    cut = pd.Timestamp(sources.CUTOFF + "-01")
    out["cutoff_en"] = f"{cut:%B %Y}"
    out["cutoff_ja"] = f"{cut.year}年{cut.month}月"
    return out


def build_registry() -> dict[str, str]:
    h = headline()

    def pct(x) -> str:
        """Signed percentages are written without the sign in prose that already
        says 'fell', so both spellings are registered."""
        return f"{abs(float(x)):.0f}"

    reg = {
        # ── attention layer ─────────────────────────────────────────────────
        "cosm_decline":  pct(h["cosm_decline"]),

        # ── market layer ────────────────────────────────────────────────────
        "found_d":         pct(h["found_d"]),
        "lip_d":           pct(h["lip_d"]),
        "serum_val_span":  pct(h["serum_val_span"]),
        "serum_val_post":  pct(h["serum_val_post"]),
        "mkt_y0":          f"{int(h['mkt_y0'])}",
        "mkt_y1":          f"{int(h['mkt_y1'])}",
        "mkt_break":       f"{int(h['mkt_break'])}",
        "mkt_pre1":        f"{int(h['mkt_pre1'])}",
        "ytd_y":           f"{int(h['ytd_y'])}",
        "ytd_m":           f"{int(h['ytd_m'])}",
        "ytd_m_en":        pd.Timestamp(2000, int(h["ytd_m"]), 1).strftime("%B"),
        "ytd_skin":        f"{float(h['ytd_skin']):.1f}",
        "ytd_make":        f"{abs(float(h['ytd_make'])):.1f}",

        # ── consumer layer ──────────────────────────────────────────────────
        "vocab_shared":  f"{int(h['vocab_shared'])}",
        "vocab_top":     f"{int(h['vocab_top'])}",

        # ── launch layer ────────────────────────────────────────────────────
        **launch_feeds(),

        # ── text from the site ──────────────────────────────────────────────
        **site_text(),
    }
    return reg


def apply(reg: dict[str, str], check: bool) -> int:
    stale, unknown, seen = [], [], set()

    for name in DOCS:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")

        def sub(match: re.Match) -> str:
            key, current = match.group(1), match.group(2)
            seen.add(key)
            if key not in reg:
                unknown.append(f"{name}: <!--f:{key}--> has no registry entry")
                return match.group(0)
            want = reg[key]
            if current != want:
                stale.append(f"{name}: {key}  {current!r} -> {want!r}")
            return f"<!--f:{key}-->{want}<!--/f-->"

        new = MARKER.sub(sub, text)
        n = len(MARKER.findall(text))
        if not check and new != text:
            path.write_text(new, encoding="utf-8")
        print(f"  {name:<16} {n} marked figures"
              + ("" if check else ("  (rewritten)" if new != text else "  (already current)")))

    if unknown:
        print("\nUNKNOWN KEYS:", file=sys.stderr)
        for u in unknown:
            print(f"  {u}", file=sys.stderr)
        return 2

    unused = sorted(set(reg) - seen)
    if unused:
        print(f"\n  registry entries not used in the docs ({len(unused)}): "
              + ", ".join(unused))

    if stale:
        print(f"\n{'STALE' if check else 'UPDATED'} ({len(stale)}):")
        for s in stale:
            print(f"  {s}")
        if check:
            print("\nRun: python build_docs_figures.py", file=sys.stderr)
            return 1
    elif check:
        print("\n  all marked figures match the computed assets")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="verify without writing; non-zero exit if stale")
    ap.add_argument("--list", action="store_true", help="print the registry and exit")
    args = ap.parse_args()

    reg = build_registry()
    if args.list:
        for k in sorted(reg):
            print(f"  {k:<20} {reg[k]}")
        return 0
    return apply(reg, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
