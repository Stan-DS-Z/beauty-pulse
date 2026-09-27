"""Write dashboard/assets/vocab_overlap.csv: shared skincare terms, @cosme against YouTube.

    python build_vocab_overlap.py

The Discovery page compares the 30 highest-weighted skincare terms in @cosme
reviews with the 30 in YouTube comments on skincare videos. Both lists are read
within one side (METHODOLOGY Source roles).

  @cosme   NB04's own method, run on the local database: its tokeniser (SudachiPy
           mode C, nouns and adjectives, NB04's stopwords), its review query, and
           its TF-IDF (fitted on skincare and cosmetics reviews together, mean
           weight within skincare, top 30). NB04's code is read from the notebook
           so the two cannot drift apart.
  YouTube  the skincare rows of dashboard/assets/nb07_yt_tfidf.csv, NB06 §6's top
           30 by mean TF-IDF.

One row per term in either list: term, source (cosme | youtube), rank, in_both.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.config import get_exclusion_terms  # noqa: E402,F401  (NB04's tokeniser cell calls it)
from src.schema import get_connection       # noqa: E402

NB04 = ROOT / "notebooks" / "NB04_consumer_voice.ipynb"
YT = ROOT / "dashboard" / "assets" / "nb07_yt_tfidf.csv"
OUT = ROOT / "dashboard" / "assets" / "vocab_overlap.csv"
TOP_N = 30


def nb04_cell(startswith: str) -> str:
    cells = json.loads(NB04.read_text(encoding="utf-8"))["cells"]
    hits = ["".join(c["source"]) for c in cells
            if c["cell_type"] == "code" and "".join(c["source"]).startswith(startswith)]
    if len(hits) != 1:
        raise SystemExit(f"NB04: expected one cell starting {startswith!r}, found {len(hits)}")
    return hits[0]


def cosme_skincare_terms(conn) -> list[str]:
    ns = {"get_exclusion_terms": get_exclusion_terms}
    # The tokeniser cell ends in a smoke test that prints; its definitions are what we need.
    exec(nb04_cell("import sudachipy"), ns)
    sql = nb04_cell("# ── Batch tokenise").split("'''")[1]
    df = pd.read_sql(sql, conn)
    df["tokens"] = df["review_text"].apply(ns["tokenise"])

    from sklearn.feature_extraction.text import TfidfVectorizer
    df = df[df["tokens"].apply(len) >= 3]
    vec = TfidfVectorizer(max_features=5000, min_df=5, max_df=0.85,
                          ngram_range=(1, 2), sublinear_tf=True)
    X = vec.fit_transform(df["tokens"].apply(" ".join))
    vocab = vec.get_feature_names_out()
    skin = np.asarray(X[(df["tier"] == "skincare").values].mean(axis=0)).ravel()
    return [vocab[i] for i in np.argsort(skin)[::-1][:TOP_N]]


def main() -> int:
    conn = get_connection()
    try:
        cosme = cosme_skincare_terms(conn)
    finally:
        conn.close()
    yt = (pd.read_csv(YT, encoding="utf-8-sig").query("tier == 'skincare'")
          .sort_values("tfidf", ascending=False)["term"].head(TOP_N).tolist())
    both = set(cosme) & set(yt)
    rows = ([{"term": t, "source": "cosme", "rank": i + 1, "in_both": t in both}
             for i, t in enumerate(cosme)]
            + [{"term": t, "source": "youtube", "rank": i + 1, "in_both": t in both}
               for i, t in enumerate(yt)])
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(both)} of {TOP_N} skincare terms in both lists")
    print("  shared:", "、".join(t for t in yt if t in both))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
