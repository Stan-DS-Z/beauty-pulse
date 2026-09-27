"""Write dashboard/assets/vocab_overlap.csv: shared skincare terms, @cosme against YouTube.

    python build_vocab_overlap.py

The Discovery page compares the 30 highest-weighted skincare terms in @cosme
reviews with the 30 in YouTube comments on skincare videos. Both lists are read
within one side (METHODOLOGY Source roles), and both come from one method, NB04's,
run on the local database:

  tokeniser  SudachiPy mode C, nouns and adjectives, NB04's stopwords. NB04's code
             is read from the notebook so the two cannot drift apart.
  corpus     @cosme: NB04's review query. YouTube: Japanese comments of more than
             10 characters on videos from the skincare and makeup search
             categories (NB06 §6's split; 韓国コスメ and uncategorised searches
             are left out). Documents with fewer than 3 tokens are dropped.
  weights    TF-IDF fitted on each platform's skincare and makeup documents
             together; terms ranked by mean weight within skincare; top 30.

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
OUT = ROOT / "dashboard" / "assets" / "vocab_overlap.csv"
TOP_N = 30


def nb04_cell(startswith: str) -> str:
    cells = json.loads(NB04.read_text(encoding="utf-8"))["cells"]
    hits = ["".join(c["source"]) for c in cells
            if c["cell_type"] == "code" and "".join(c["source"]).startswith(startswith)]
    if len(hits) != 1:
        raise SystemExit(f"NB04: expected one cell starting {startswith!r}, found {len(hits)}")
    return hits[0]


YT_SKIN = {"美容液", "敏感肌・乾燥肌", "成分・知識", "化粧水", "乳液・クリーム",
           "エイジングケア", "日焼け止め", "洗顔料", "ニキビ・毛穴", "メンズ・プチプラ"}
YT_MAKE = {"ファンデーション", "アイシャドウ", "口紅・リップ", "その他メイク"}
YT_SQL = """
    SELECT c.comment_text AS text, v.search_category
    FROM yt_comments c
    JOIN yt_videos v USING (video_id)
    WHERE c.is_japanese = 1
      AND c.comment_text IS NOT NULL
      AND LENGTH(c.comment_text) > 10
"""


def nb04_tokeniser():
    ns = {"get_exclusion_terms": get_exclusion_terms}
    # The tokeniser cell ends in a smoke test that prints; its definitions are what we need.
    exec(nb04_cell("import sudachipy"), ns)
    return ns["tokenise"]


def skincare_terms(texts: pd.Series, is_skin: pd.Series, tokenise) -> tuple[list[str], int]:
    """NB04's TF-IDF: fit on both sides, rank by mean weight within skincare."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    tokens = texts.apply(tokenise)
    keep = tokens.apply(len) >= 3
    tokens, is_skin = tokens[keep], is_skin[keep]
    vec = TfidfVectorizer(max_features=5000, min_df=5, max_df=0.85,
                          ngram_range=(1, 2), sublinear_tf=True)
    X = vec.fit_transform(tokens.apply(" ".join))
    vocab = vec.get_feature_names_out()
    skin = np.asarray(X[is_skin.values].mean(axis=0)).ravel()
    return [vocab[i] for i in np.argsort(skin)[::-1][:TOP_N]], int(is_skin.sum())


def main() -> int:
    tokenise = nb04_tokeniser()
    conn = get_connection()
    try:
        rv = pd.read_sql(nb04_cell("# ── Batch tokenise").split("'''")[1], conn)
        yt = pd.read_sql(YT_SQL, conn)
    finally:
        conn.close()
    yt = yt[yt["search_category"].isin(YT_SKIN | YT_MAKE)].reset_index(drop=True)
    cosme, n_rv = skincare_terms(rv["review_text"], rv["tier"] == "skincare", tokenise)
    yt, n_yt = skincare_terms(yt["text"], yt["search_category"].isin(YT_SKIN), tokenise)
    print(f"skincare documents: {n_rv:,} @cosme reviews, {n_yt:,} YouTube comments")
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
