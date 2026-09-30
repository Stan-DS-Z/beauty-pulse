"""Vocabulary convergence and the sample-size curve, by one method, from the
local database.

    python build_convergence.py            # the checks, printed; nothing written
    python build_convergence.py --write    # also write the three assets below

NB06 §2 measures how alike skincare and makeup @cosme review vocabulary is:
the TF-IDF cosine between the pooled skincare reviews and the pooled makeup
reviews of one period. NB06 cannot be re-run here (its §8 rebuilds the public
DB), and it builds the size-matched figures and the size curve two ways: the
size-matched test subsamples all four period slices, the curve only the two
2023 slices. This script reproduces NB06's corpus, tokeniser, periods, TF-IDF
settings and bootstrap (40 draws, seed 42), and builds both on one design:

  slices    skincare / makeup x the four NB06 periods; every review in a slice
            joined into one document; TF-IDF (1-2 grams, 5,000 features,
            sublinear tf) fitted on all eight slice documents each draw
  matched   the four key slices (both sides, 2021-22 and the late period)
            each drawn without replacement to N = the smallest of the four
  curve     the same draws, with the late period's two slices drawn to each
            curve size instead of N; the 2021-22 slices stay at N. At the
            curve's N point the curve is the matched figure by construction.

It also runs the robustness checks the architect asked for on 30 Sep 2026:
  (a) reviews containing プレゼント or 当選 removed (build_review_map.PHRASES)
  (b) product-matched: only products with reviews in both periods

The published convergence (0.252 → 0.317 at 249 reviews per period) does not
hold under (b) and was withdrawn (METHODOLOGY Revision 20). The Method page
carries these files as the record of the test:

  convergence_curve.csv    sample_size, cosine: the late period's two slices
                           drawn to each size, the 2021-2022 slices at N
  convergence_checks.csv   check, n, early, late, delta, ci_lo, ci_hi
  convergence_periods.csv  side, period, reviews, products, with_phrase

NB06 labels its late period "2023–26" but defines it as 2023-2025; the files
say 2023–2025. Tokens are cached in data/interim/review_tokens.parquet
(private: derived from the text), because SudachiPy takes minutes.
"""

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "signal_pulse.db"
CACHE = ROOT / "data" / "interim" / "review_tokens.parquet"
ASSETS = ROOT / "dashboard" / "assets"

# NB06 cell 3 and cell 6, as run for the published figures.
SKIN_TIERS = {"skincare", "mass_skincare", "sensitive_skincare", "prestige_skincare",
              "sun_protection", "dermo_skincare"}
COSM_TIERS = {"cosmetics", "mass_cosmetics", "prestige_cosmetics", "base_makeup"}
CONTENT_POS = {"名詞", "動詞", "形容詞", "副詞"}
PERIODS = {"2019": (2019, 2019), "2020": (2020, 2020), "2021–22": (2021, 2022),
           "2023–25": (2023, 2025)}
EARLY, LATE = "2021–22", "2023–25"
TRIALS, SEED = 40, 42
CURVE_N = (150, 500, 1000, 2000, 4000, 6000)   # and the matched N (NB06 also drew 250)
PHRASES = ("プレゼント", "当選")
# The periods as the files name them: full years, which NB06's labels were not.
LABEL = {EARLY: "2021–2022", LATE: "2023–2025", "2026": "2026"}
SIDE = {"SK": "skincare", "CM": "makeup"}


def corpus(db: Path) -> pd.DataFrame:
    with sqlite3.connect(db) as con:
        df = pd.read_sql("""
            SELECT r.review_id, r.product_id, r.review_text, r.review_year, c.tier
            FROM reviews r JOIN categories c USING (category_id)
            WHERE r.review_text IS NOT NULL AND LENGTH(r.review_text) > 20
              AND r.review_year BETWEEN 2019 AND 2026""", con)
    df["side"] = np.where(df["tier"].isin(SKIN_TIERS), "SK",
                          np.where(df["tier"].isin(COSM_TIERS), "CM", ""))
    return df


def tokens(df: pd.DataFrame) -> pd.Series:
    """NB06's tokeniser: SudachiPy mode C, content words, dictionary form,
    longer than one character. Cached by review_id."""
    cached = pd.read_parquet(CACHE) if CACHE.exists() else pd.DataFrame(
        columns=["review_id", "tokens"])
    todo = df[~df["review_id"].isin(cached["review_id"])]
    if len(todo):
        from sudachipy import Dictionary, SplitMode
        tok = Dictionary().create()

        def one(text):
            return " ".join(m.dictionary_form() for m in tok.tokenize(text, SplitMode.C)
                            if m.part_of_speech()[0] in CONTENT_POS
                            and len(m.dictionary_form()) > 1)
        print(f"tokenising {len(todo):,} reviews…")
        new = pd.DataFrame({"review_id": todo["review_id"],
                            "tokens": todo["review_text"].map(one)})
        cached = pd.concat([cached, new], ignore_index=True)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        cached.to_parquet(CACHE, index=False)
    return df["review_id"].map(cached.set_index("review_id")["tokens"])


def slices(df: pd.DataFrame, periods=PERIODS) -> dict:
    out = {}
    for side in ("SK", "CM"):
        for p, (lo, hi) in periods.items():
            r = df.loc[(df["side"] == side) & df["review_year"].between(lo, hi), "tokens"].tolist()
            if len(r) >= 5:
                out[f"{side} {p}"] = r
    return out


def _cos(docs: dict, a, b):
    names = list(docs)
    v = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, min_df=1, sublinear_tf=True)
    M = cosine_similarity(v.fit_transform([docs[n] for n in names]))
    return M[names.index(a), names.index(b)]


def measure(df: pd.DataFrame, late=LATE, curve=True, periods=PERIODS) -> dict:
    """The matched figures and, with curve=True, the curve on the same design."""
    s = slices(df, periods)
    key = [f"SK {EARLY}", f"CM {EARLY}", f"SK {late}", f"CM {late}"]
    N = min(len(s[k]) for k in key)
    rng = np.random.default_rng(SEED)
    full = {n: " ".join(v) for n, v in s.items()}

    def draw(sizes):
        docs = dict(full)
        for k, n in sizes.items():
            idx = rng.choice(len(s[k]), size=n, replace=False)
            docs[k] = " ".join(s[k][j] for j in idx)
        return docs

    e, l_ = [], []
    for _ in range(TRIALS):
        d = draw({k: N for k in key})
        e.append(_cos(d, key[0], key[1]))
        l_.append(_cos(d, key[2], key[3]))
    e, l_ = np.array(e), np.array(l_)
    dl = l_ - e
    res = dict(N=N, early=e.mean(), late=l_.mean(), delta=dl.mean(),
               ci=(np.percentile(dl, 2.5), np.percentile(dl, 97.5)),
               early_ci=(np.percentile(e, 2.5), np.percentile(e, 97.5)),
               late_ci=(np.percentile(l_, 2.5), np.percentile(l_, 97.5)),
               sizes={k: len(s[k]) for k in key})
    if curve:
        pts = []
        cap = min(len(s[key[2]]), len(s[key[3]]))
        for n in sorted(set(CURVE_N) | {N}):
            if n > cap:
                break
            if n == N:
                # At N the curve is the matched test: its own draws, not new ones.
                pts.append((n, float(l_.mean())))
                continue
            vals = [_cos(draw({key[0]: N, key[1]: N, key[2]: n, key[3]: n}), key[2], key[3])
                    for _ in range(20)]
            pts.append((n, float(np.mean(vals))))
        res["curve"] = pts
    return res


def show(label, r):
    lo, hi = r["ci"]
    print(f"{label:<44} N={r['N']:>4}  {r['early']:.3f} → {r['late']:.3f}  "
          f"Δ {r['delta']:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  slices {r['sizes']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    df = corpus(args.db)
    df["tokens"] = tokens(df)
    df = df[df["tokens"].str.len() > 0].copy()
    df["phrase"] = df["review_text"].str.contains("|".join(PHRASES))

    # Each period's share of reviews with the phrases, by side
    per = df[df["side"] != ""].assign(
        period=lambda x: np.select([x["review_year"].between(*PERIODS[EARLY]),
                                    x["review_year"].between(*PERIODS[LATE]),
                                    x["review_year"] == 2026],
                                   [EARLY, LATE, "2026"], ""))
    per = per[per["period"] != ""]
    share = (per.groupby(["side", "period"])
             .agg(n=("phrase", "size"), products=("product_id", "nunique"),
                  with_phrase=("phrase", "sum"), share=("phrase", "mean")))
    print("\nReviews containing プレゼント or 当選, by side and period")
    print(share.assign(share=lambda x: (100 * x["share"]).round(1)).to_string())

    print("\nConvergence (TF-IDF cosine, skincare vs makeup), NB06 design")
    base = measure(df)
    show("baseline (NB06 reproduced)", base)
    a = measure(df[~df["phrase"]], curve=False)
    show("(a) without プレゼント / 当選", a)
    both = set(df.loc[df["review_year"].between(*PERIODS[EARLY]), "product_id"]) & \
        set(df.loc[df["review_year"].between(*PERIODS[LATE]), "product_id"])
    b = measure(df[df["product_id"].isin(both)], curve=False)
    show(f"(b) products in both periods ({len(both)})", b)
    ab = measure(df[df["product_id"].isin(both) & ~df["phrase"]], curve=False)
    show("(a)+(b)", ab)
    p26 = {**PERIODS, "2023–26": (2023, 2026)}
    del p26[LATE]
    w26 = measure(df, late="2023–26", curve=False, periods=p26)
    show("late period with 2026 (2023–26)", w26)

    print("\n(c) size curve on the matched design (late period drawn to n)")
    for n, c in base["curve"]:
        mark = "  ← matched N" if n == base["N"] else ""
        print(f"  n={n:>5}  {c:.3f}{mark}")

    if args.write:
        checks = {"baseline": base, "without_phrases": a, "products_in_both": b, "both": ab}
        pd.DataFrame([dict(check=k, n=r["N"], early=round(r["early"], 3),
                           late=round(r["late"], 3), delta=round(r["delta"], 3),
                           ci_lo=round(r["ci"][0], 3), ci_hi=round(r["ci"][1], 3),
                           early_period=LABEL[EARLY], late_period=LABEL[LATE])
                      for k, r in checks.items()]).to_csv(
            ASSETS / "convergence_checks.csv", index=False)
        pd.DataFrame([dict(sample_size=n, cosine=round(c, 3), period=LABEL[LATE],
                           early_n=base["N"]) for n, c in base["curve"]]).to_csv(
            ASSETS / "convergence_curve.csv", index=False)
        (share.reset_index()
         .assign(side=lambda x: x["side"].map(SIDE), period=lambda x: x["period"].map(LABEL))
         .rename(columns={"n": "reviews"})[["side", "period", "reviews", "products", "with_phrase"]]
         .to_csv(ASSETS / "convergence_periods.csv", index=False))
        print("\nwrote convergence_checks.csv, convergence_curve.csv, convergence_periods.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
