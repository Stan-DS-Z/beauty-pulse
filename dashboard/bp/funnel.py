"""The funnel matrix: sixteen categories across the funnel's stages.

Rows are the categories that both PR TIMES launch releases and a METI product
line name. Columns are the stages from company to consumer, each on its own
measure:

  ① launch      share of categorised core-panel launch releases, change in points
  ② social      not collected
  ③ verification  @cosme reviews: no change over time by category (see below)
  ④ search      Google Trends block_A annual mean, change in index points
  ④ shipments   METI shipped value, change in %

The stages count different things and no conversion between them was measured,
so nothing here relates one column to another. Each column's colour scale is
that column's own largest change.

Every column is measured over one window. It starts no earlier than the METI
break (data.METI_BREAK) and on the first full year the launch core panel
covers, and ends on the latest year every source holds in full. On the
September 2026 assets that is 2022→2025.

Like data.py, this computes nothing at import. Labels live in strings.py.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from .data import (LAUNCH_WINDOW_START, METI_BREAK, load_attention_annual,
                   load_meti_annual)

# launch tag: (METI product line, how well it matches, Trends term or None, group)
# "partial": the METI line covers part of the category — クレンジングクリーム is
# one form of cleansing, モイスチャークリーム one kind of cream. Eye makeup is
# searched as アイシャドウ, one product in it.
CATEGORIES = {
    "serum":        ("美容液", "1:1", "美容液", "skincare"),
    "toner_lotion": ("化粧水", "1:1", "化粧水", "skincare"),
    "face_wash":    ("洗顔クリーム・フォーム", "1:1", "洗顔", "skincare"),
    "cleansing":    ("クレンジングクリーム", "partial", None, "skincare"),
    "cream":        ("モイスチャークリーム", "partial", None, "skincare"),
    "emulsion":     ("乳液", "1:1", "乳液", "skincare"),
    "mask":         ("パック", "1:1", None, "skincare"),
    "sunscreen":    ("日やけ止め及び日やけ用化粧品", "1:1", "日焼け止め", "sunscreen"),
    "foundation":   ("ファンデーション", "1:1", "ファンデーション", "makeup"),
    "powder":       ("おしろい", "1:1", None, "makeup"),
    "lash_brow":    ("まゆ墨・まつ毛化粧料", "1:1", None, "makeup"),
    "eye_makeup":   ("アイメークアップ", "1:1", "アイシャドウ", "makeup"),
    "lipstick":     ("口紅", "1:1", "口紅", "makeup"),
    "lip_balm":     ("リップクリーム", "1:1", None, "makeup"),
    "blush":        ("ほほ紅", "1:1", None, "makeup"),
    "nail":         ("つめ化粧料(除光液を含む)", "1:1", None, "makeup"),
}
GROUPS = ("skincare", "sunscreen", "makeup")

# Funnel order, company to consumer. (column, stage number, source key in
# sources.DECLARED, or None where nothing was collected)
STAGES = (("launch", 1, "prtimes"), ("social", 2, None), ("verification", 3, "cosme"),
          ("search", 4, "trends"), ("shipments", 4, "meti"))

# Why a cell is empty. strings.py turns each code into the hover text.
#   not_collected     no Instagram, TikTok or X data was collected
#   single_scrape     @cosme was scraped once, and review dates follow which
#                     products were sampled, so reviews show no change over time
#                     by category
#   term_not_tracked  the category word has no Google Trends series
#   no_releases       no categorised core launch release names the category
#                     in either year
REASONS = ("not_collected", "single_scrape", "term_not_tracked", "no_releases")


def _core_categorised(ASSETS: Path, cutoff=None):
    d = pd.read_csv(ASSETS / "prtimes_launches.csv", dtype=str,
                    usecols=["panel", "month", "category"]).fillna("")
    d = d[(d["panel"] == "core") & (d["category"] != "")
          & ((d["month"] <= cutoff) if cutoff else True)].copy()
    d["year"] = d["month"].str[:4].astype(int)
    d["tags"] = d["category"].str.split("|")
    return d


def funnel_window(ASSETS: Path, *, cutoff=None, _launch=None, _val=None, _att=None):
    """(first year, last year) that every stage holds in full."""
    launch = _core_categorised(ASSETS, cutoff) if _launch is None else _launch
    val = load_meti_annual(ASSETS, cutoff)[0] if _val is None else _val
    att = load_attention_annual(ASSETS, cutoff) if _att is None else _att

    # The launch panel starts mid-year; its first full year is the next one if
    # the start month is not January. Its last full year is the last with a
    # December release month present.
    ws_y, ws_m = int(LAUNCH_WINDOW_START[:4]), int(LAUNCH_WINDOW_START[5:7])
    launch_first = ws_y if ws_m == 1 else ws_y + 1
    months = launch["month"].unique()
    launch_last = max(int(m[:4]) for m in months if m.endswith("-12"))

    y0 = max(METI_BREAK, launch_first, int(att.index.min()), int(val.columns.min()))
    y1 = min(launch_last, int(att.index.max()), int(val.columns.max()))
    if y0 >= y1:
        raise ValueError(f"no common window: {y0}→{y1}")
    return y0, y1


def compute_funnel_matrix(ASSETS: Path, cutoff=None):
    """The matrix, one row per category, with each cell's counts for hover.
    With a cutoff ("YYYY-MM"), it is computed on data dated up to that month.

    Returns a dict:
      window   (y0, y1)
      rows     DataFrame indexed by launch tag, in CATEGORIES order, with
               group, meti_line, join, term,
               launch_s0/s1 (share %), launch_n0/n1 (releases naming it),
               launch_d (s1 - s0, points),
               search_0/1 (annual mean index), search_d (points),
               ship_v0/v1 (億円), ship_d (%), value_y1 (億円, the last year)
      reasons  DataFrame of the same shape as the stage columns: a REASONS code
               where the cell is empty, "" where it holds a value
      scale    {stage column: its largest absolute change}, for colour within
               that column only
      launch_den  (categorised core releases in y0, in y1)
    """
    launch = _core_categorised(ASSETS, cutoff)
    val, _ = load_meti_annual(ASSETS, cutoff)
    att = load_attention_annual(ASSETS, cutoff)
    y0, y1 = funnel_window(ASSETS, _launch=launch, _val=val, _att=att)

    c0, c1 = launch[launch["year"] == y0], launch[launch["year"] == y1]
    rows, reasons = [], []
    for key, (line, join, term, group) in CATEGORIES.items():
        n0 = int(c0["tags"].apply(lambda t: key in t).sum())
        n1 = int(c1["tags"].apply(lambda t: key in t).sum())
        s0, s1 = 100 * n0 / len(c0), 100 * n1 / len(c1)
        v0, v1 = float(val.loc[line, y0]), float(val.loc[line, y1])
        a0 = float(att.loc[y0, term]) if term else np.nan
        a1 = float(att.loc[y1, term]) if term else np.nan
        rows.append(dict(
            key=key, group=group, meti_line=line, join=join, term=term,
            launch_n0=n0, launch_n1=n1, launch_s0=s0, launch_s1=s1,
            launch_d=(s1 - s0) if n0 or n1 else np.nan,
            search_0=a0, search_1=a1, search_d=a1 - a0,
            ship_v0=v0, ship_v1=v1, ship_d=100 * (v1 / v0 - 1), value_y1=v1))
        reasons.append(dict(
            key=key,
            launch="" if n0 or n1 else "no_releases",
            social="not_collected",
            verification="single_scrape",
            search="" if term else "term_not_tracked",
            shipments=""))

    rows = pd.DataFrame(rows).set_index("key")
    reasons = pd.DataFrame(reasons).set_index("key")
    scale = {"launch": float(rows["launch_d"].abs().max()),
             "search": float(rows["search_d"].abs().max()),
             "shipments": float(rows["ship_d"].abs().max())}
    return {"window": (y0, y1), "rows": rows, "reasons": reasons, "scale": scale,
            "launch_den": (len(c0), len(c1))}


def display_order(rows: pd.DataFrame):
    """Category keys grouped skincare, sunscreen, makeup; largest value first."""
    return [k for g in GROUPS
            for k in rows[rows["group"] == g].sort_values("value_y1", ascending=False).index]
