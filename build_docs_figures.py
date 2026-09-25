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

The registry has three sources, in order of authority:

  HEADLINE   dashboard/bp/data.py's compute_headline() — the exact values
             the deployed page renders, so docs and dashboard cannot diverge
  LAUNCH     compute_launch_headline() and prtimes_feeds.csv — the launch
             panel's feed counts
  nb07_sku_ratio.csv   the ratio treatments, which HEADLINE only spans
  the database         corpus sizes for the data-source tables

Not everything is derivable. Hand-label proportions, classifier scores and the
2022 break diagnostics are measurements recorded once, not recomputed per pull;
they stay as prose and --check ignores them.

Run it after NB07 and build_sku_ratio.py, which is where the assets it reads
are written. update_data.command does this.
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.schema import get_connection          # noqa: E402

DOCS = ["README.md", "METHODOLOGY.md"]
MARKER = re.compile(r"<!--f:([a-z0-9_]+)-->(.*?)<!--/f-->", re.DOTALL)


def headline() -> dict:
    """compute_headline() from the dashboard's bp package — the function the
    deployed page computes HEADLINE with, over the same shipped assets."""
    sys.path.insert(0, str(ROOT / "dashboard"))
    from bp import data
    return data.compute_headline(data.ASSETS)


def launch_feeds() -> dict:
    """The launch panel's feed counts: compute_launch_headline() for what the
    figures use, prtimes_feeds.csv for the panel each active feed is on."""
    sys.path.insert(0, str(ROOT / "dashboard"))
    from bp import data
    lau = data.compute_launch_headline(data.ASSETS)
    if lau is None:
        return {}
    feeds = pd.read_csv(data.ASSETS / "prtimes_feeds.csv")
    return {
        "launch_core_feeds": f"{lau['n_core_feeds']}",
        "launch_core_issuers": f"{lau['n_core']}",
        "launch_later_feeds": f"{int((feeds['panel'] == 'present_forward').sum())}",
        "launch_later_feeds_l12": f"{lau['n_pf_feeds']}",
    }


def ratios() -> pd.Series:
    return pd.read_csv(
        ROOT / "dashboard" / "assets" / "nb07_sku_ratio.csv"
    ).set_index("basis")["ratio"]


def corpus() -> dict:
    conn = get_connection()
    q = lambda sql: conn.execute(sql).fetchone()[0]          # noqa: E731
    out = {
        "rakuten_skus": q("SELECT COUNT(*) FROM products WHERE source_id = 1"),
        "weekly_rows": q("SELECT COUNT(*) FROM products_weekly"),
        "weekly_dates": q("SELECT COUNT(DISTINCT snapshot_date) FROM products_weekly"),
        "cosme_reviews": q("SELECT COUNT(*) FROM reviews r JOIN products p "
                           "ON r.product_id = p.product_id WHERE p.source_id = 2"),
        "amazon_asins": q("SELECT COUNT(*) FROM products WHERE source_id = 3"),
        "amazon_reviews": q("SELECT COUNT(*) FROM reviews r JOIN products p "
                            "ON r.product_id = p.product_id WHERE p.source_id = 3"),
        "trends_rows": q("SELECT COUNT(*) FROM trends_weekly"),
        "yt_videos": q("SELECT COUNT(*) FROM yt_videos"),
        "yt_comments": q("SELECT COUNT(*) FROM yt_comments"),
    }
    conn.close()
    return out


def build_registry() -> dict[str, str]:
    h, r, c = headline(), ratios(), corpus()

    def pct(x) -> str:
        """Signed percentages are written without the sign in prose that already
        says 'fell', so both spellings are registered."""
        return f"{abs(float(x)):.0f}"

    reg = {
        # ── corpus sizes ────────────────────────────────────────────────────
        **{k: f"{v:,}" for k, v in c.items()},

        # ── SKU ratio treatments ────────────────────────────────────────────
        "sku_as_tagged":      f"{r['as_labelled']:.1f}",
        "sku_564517_only":    f"{r['reclassified_564517_only']:.1f}",
        "sku_reclassified":   f"{r['reclassified']:.1f}",
        "sku_ci_lo":          f"{r['reclassified_lo']:.1f}",
        "sku_ci_hi":          f"{r['reclassified_hi']:.1f}",
        "sku_origin_dropped": f"{r['origin_genre_dropped']:.1f}",
        "sku_product_type":   f"{r['product_type_genres']:.1f}",
        "skin_skus":          f"{int(h['skin_skus']):,}",
        "cosm_skus":          f"{int(h['cosm_skus']):,}",

        # ── attention layer ─────────────────────────────────────────────────
        "cosm_decline":  pct(h["cosm_decline"]),
        "nia_pre":       f"{int(h['nia_pre'])}",
        "nia_post":      f"{int(h['nia_post'])}",
        "ing_y0":        f"{int(h['ing_y0'])}",
        "ing_y1":        f"{int(h['ing_y1'])}",

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
        "ytd_skin":        f"{float(h['ytd_skin']):.1f}",
        "ytd_make":        f"{abs(float(h['ytd_make'])):.1f}",

        # ── convergence ─────────────────────────────────────────────────────
        "conv_delta":  f"{float(h['conv_delta']):.3f}",
        "conv_lo":     f"{float(h['conv_lo']):.3f}",
        "conv_hi":     f"{float(h['conv_hi']):.3f}",
        "conv_ci":     str(h["conv_ci"]),
        "conv_ci_jp":  str(h["conv_ci_jp"]),

        # ── launch layer ────────────────────────────────────────────────────
        **launch_feeds(),
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
