"""The Consumer page: the two top-30 skincare term lists (@cosme reviews and
YouTube comments), and the review map.

A report page: every figure is computed from the frozen edition. @cosme and
YouTube are within-side instruments (METHODOLOGY, Source roles): the page
compares no vocabulary, count, share or volume across sides or years. The
vocabulary convergence across periods was withdrawn (Revision 20); its test
is in build_convergence.py and goes to the Method page. The review map's
labels come from review_map.csv (build_review_map.py), added to the 2026-09
edition on 30 September 2026. strings.py words these figures and
tests/test_consumer.py holds the data to each direction the copy states.
Like data.py, nothing runs at import.
"""

from pathlib import Path

from .data import load_review_map, load_umap, load_vocab_overlap

# Each review category's side, for the map's colours.
REVIEW_SIDE = {"toner_lotion": "skincare", "emulsion": "skincare", "serum_essence": "skincare",
               "face_cream": "skincare", "face_wash": "skincare", "cleansing": "skincare",
               "foundation": "makeup", "lip_colour": "makeup", "eye_shadow": "makeup",
               "sun_protection": "sunscreen"}


def compute_consumer(ASSETS: Path) -> dict:
    """The Consumer page's figures. The @cosme and YouTube collections are
    single pulls dated before the cut-off, so no cut applies."""
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

    return dict(vocab=vocab, points=points, phrase=phrase)
