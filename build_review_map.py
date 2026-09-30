"""Write dashboard/assets/review_map.csv: what the review map needs from the
review text, without the text.

    python build_review_map.py            # from data/signal_pulse.db

The review map (Consumer page) places each @cosme review in
umap_embedding.csv by its vocabulary; NB06 §8 builds that file. The public DB
carries no review text (see memory: public-repo-exposure), so a clone cannot
say which reviews use which words. This script reads the private DB and
exports, per review in the embedding:

  review_id  the embedding's review_id
  category   categories.normalized_name of the review's product category
  phrase     1 when the text contains プレゼント or 当選, else 0
  nn_phrase  how many of the review's NEIGHBOURS nearest reviews on the map
             (Euclidean, in umap_x/umap_y) have phrase = 1

The two phrases are the ones @cosme's own present campaigns use
(「@cosme様よりプレゼントでいただきました」, 「当選しました」). A review that names a
present from a friend matches too; the page names the phrases, never a
campaign.

Run it whenever NB06 rebuilds umap_embedding.csv. The app reads the output;
the suite checks it covers the embedding row for row (tests/test_consumer.py).
"""

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "dashboard" / "assets"
OUT = ASSETS / "review_map.csv"
DB = ROOT / "data" / "signal_pulse.db"

PHRASES = ("プレゼント", "当選")
NEIGHBOURS = 10


def build(db: Path) -> pd.DataFrame:
    emb = pd.read_csv(ASSETS / "umap_embedding.csv")
    with sqlite3.connect(db) as con:
        rev = pd.read_sql("SELECT r.review_id, r.review_text, c.normalized_name AS category "
                          "FROM reviews r JOIN categories c USING (category_id)", con)
    m = emb[["review_id", "umap_x", "umap_y"]].merge(rev, on="review_id", how="left")
    if m["category"].isna().any():
        raise SystemExit(f"{m['category'].isna().sum()} embedded reviews are not in {db}")
    phrase = m["review_text"].fillna("").str.contains("|".join(PHRASES)).to_numpy()
    xy = m[["umap_x", "umap_y"]].to_numpy()
    # The nearest point to each review is itself: ask for one more and drop it.
    _, idx = NearestNeighbors(n_neighbors=NEIGHBOURS + 1).fit(xy).kneighbors(xy)
    nn = phrase[idx[:, 1:]].sum(axis=1)
    return pd.DataFrame({"review_id": m["review_id"], "category": m["category"],
                         "phrase": phrase.astype(int), "nn_phrase": nn.astype(int)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    out = build(ap.parse_args().db)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out):,} reviews, "
          f"{out['phrase'].sum():,} with {' or '.join(PHRASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
