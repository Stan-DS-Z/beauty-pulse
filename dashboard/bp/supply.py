"""The Supply page: PR TIMES product-launch releases from the core panel, and
median prices among each Rakuten genre's most-reviewed items.

A report page: every figure is computed from the frozen edition, cut at the
edition's cut-off (sources.CUTOFF). Launch figures use the core panel only
(data.compute_launch_headline). Totals and ingredient shares are 12-month
windows against the 12 months before; category shares run over the report's
aligned window (funnel.funnel_window, 2022→2025 on the September 2026
edition); issuer origin runs over the complete half-years in the launch
window. The category and origin figures are the Brief's (brief.compute_brief),
built with its helpers. The Rakuten measures are per item, from one weekly
snapshot. strings.py words these figures and tests/test_supply.py holds the
data to each direction the copy states. Like data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from .brief import _core, _half
from .data import compute_launch_headline, load_sku_treemap
from .funnel import compute_funnel_matrix

# A 12-month total within this many percent of the 12 months before "held".
HELD_PCT = 3
# The category v3's key figure names, with its share of the last year's
# categorised releases.
KEY_CATEGORY = "serum"
# Issuer origins, in stacking order from the base: the one the title names first.
ORIGINS = ("KR", "JP", "global", "CN")


def compute_supply(ASSETS: Path, cutoff: str):
    """The Supply page's figures on data up to `cutoff` ("YYYY-MM"), or None
    without the launch export."""
    L = compute_launch_headline(ASSETS, cutoff)
    if L is None:
        return None

    # ── Launch share by category over the aligned window
    fm = compute_funnel_matrix(ASSETS, cutoff)
    y0, y1 = fm["window"]
    rows = fm["rows"][["group", "launch_n0", "launch_n1", "launch_s0", "launch_s1", "launch_d"]]
    ld = rows["launch_d"].dropna()
    gainers = ld.nlargest(2)
    share = dict(rows=rows, den=fm["launch_den"], gainers=list(gainers.index),
                 gain_lo=float(gainers.min()), gain_hi=float(gainers.max()),
                 loser=ld.idxmin(), loss=float(ld.min()))

    # ── Issuer origin by complete half-year inside the launch window
    core = _core(ASSETS, cutoff)
    inwin = core[core["month"].isin(L["months"])].assign(h=lambda x: x["month"].map(_half))
    n_months = pd.Series(L["months"]).map(_half).value_counts()
    halves = sorted(h for h, n in n_months.items() if n == 6)
    counts = (inwin[inwin["h"].isin(halves)].groupby(["h", "origin"]).size()
              .unstack(fill_value=0).reindex(index=halves, columns=list(ORIGINS), fill_value=0))
    total = counts.sum(axis=1)
    issuers = (inwin.groupby("origin")["issuer_group"].nunique()
               .reindex(list(ORIGINS), fill_value=0))
    origin = dict(counts=counts, total=total, shares=100 * counts.div(total, axis=0),
                  issuers=issuers,
                  first=halves[0], last=halves[-1],
                  kr_first=(int(counts.loc[halves[0], "KR"]), int(total[halves[0]])),
                  kr_last=(int(counts.loc[halves[-1], "KR"]), int(total[halves[-1]])))

    # ── 12-month totals by category group
    gl, gp = L["grp_l12"], L["grp_p12"]
    groups = dict(roll=L["roll"], l12=gl, p12=gp,
                  change={g: 100 * (gl[g] / gp[g] - 1) for g in gl.index if gp[g]})

    # ── Ingredient shares: every tracked ingredient named in either window
    ingredients = dict(frame=L["ing"], den_l12=L["den_l12"], den_p12=L["den_p12"],
                       any_share=L["any_ing_share"], any_n=L["any_ing_n"],
                       n_terms=len(L["terms"]), top=L["top_ing"])

    # ── Rakuten: per-item measures from one weekly snapshot
    sku = load_sku_treemap(ASSETS).set_index("category")
    prices = dict(frame=sku, snapshot=pd.Timestamp(sku["snapshot_date"].iloc[0]),
                  hi=sku["med_price"].idxmax(), lo=sku["med_price"].idxmin())

    return dict(cutoff=cutoff, window=(y0, y1), l12=L["l12"], p12=L["p12"], last=L["last"],
                tot_l12=L["tot_l12"], tot_p12=L["tot_p12"], n_core=L["n_core"],
                share=share, origin=origin, groups=groups, ingredients=ingredients,
                prices=prices, terms=L["terms"])
