"""The Consumer page: @cosme review vocabulary measured at equal sample
sizes, the two top-30 skincare term lists (@cosme reviews and YouTube
comments), and the review map.

A report page: every figure is computed from the frozen edition. @cosme and
YouTube are within-side instruments (METHODOLOGY, Source roles): the page
compares vocabulary at equal sample sizes, as the source roles allow, and
states no count, share or volume across sides or years. The review map's
labels come from review_map.csv (build_review_map.py), added to the 2026-09
edition on 30 September 2026. strings.py words these figures and
tests/test_consumer.py holds the data to each direction the copy states.
Like data.py, nothing runs at import.
"""

from pathlib import Path

import pandas as pd

from .data import load_cosine_sizecurve, load_review_map, load_umap, load_vocab_overlap


def compute_consumer(ASSETS: Path) -> dict:
    """The Consumer page's figures. The @cosme and YouTube collections are
    single pulls dated before the cut-off, so no cut applies."""
    # ── Vocabulary at equal sample sizes (NB06 §2)
    sv = pd.read_csv(ASSETS / "nb06_cosine_salvage.csv")
    sm = sv[sv["method"] == "size_matched"].reset_index(drop=True)
    dl = sv[sv["method"] == "size_matched_delta"].iloc[0]
    conv = dict(p0=str(sm.loc[0, "period"]), p1=str(sm.loc[1, "period"]),
                lo=float(sm.loc[0, "cosine"]), hi=float(sm.loc[1, "cosine"]),
                delta=float(dl["cosine"]), ci_lo=float(dl["ci_lo"]), ci_hi=float(dl["ci_hi"]),
                n=int(sv.loc[sv["method"] == "matched_n", "cosine"].iloc[0]))

    # ── The same reviews, subsampled to growing sizes (NB06 §2)
    curve = load_cosine_sizecurve(ASSETS)
    size = dict(n0=int(curve["sample_size"].iloc[0]), n1=int(curve["sample_size"].iloc[-1]),
                c0=float(curve["cross_tier_cosine"].iloc[0]),
                c1=float(curve["cross_tier_cosine"].iloc[-1]))

    # ── The two top-N skincare term lists (build_vocab_overlap.py)
    vo = load_vocab_overlap(ASSETS)
    lists = {src: g.sort_values("rank").reset_index(drop=True) for src, g in vo.groupby("source")}
    vocab = dict(lists=lists, top=len(lists["cosme"]), shared=int(lists["cosme"]["in_both"].sum()))

    # ── The review map, with each review's category and phrase flag
    rm = load_review_map(ASSETS)
    emb = load_umap(ASSETS)[["review_id", "umap_x", "umap_y"]]
    points = emb.merge(rm, on="review_id", how="inner", validate="one_to_one")
    ph = points[points["phrase"] == 1]
    other = points[points["phrase"] == 0]
    k = 10  # build_review_map.NEIGHBOURS
    phrase = dict(n=len(ph), total=len(points), k=k,
                  nn_phrase=float(ph["nn_phrase"].mean()),
                  nn_other=float(other["nn_phrase"].mean()),
                  cats=int(ph["category"].nunique()), n_cats=int(points["category"].nunique()))

    return dict(conv=conv, curve=curve, size=size, vocab=vocab, points=points, phrase=phrase)
