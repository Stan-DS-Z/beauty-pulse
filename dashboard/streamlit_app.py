"""
Beauty Pulse — Japanese Beauty Market Analytics Dashboard
streamlit_app.py  ·  single file  ·  Streamlit Community Cloud
"""

import html as _html
import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Beauty Pulse · Japanese Beauty Market",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ASSETS = Path(__file__).parent / "assets"
# Note: assets/ also ships signal_pulse_public.db (the stripped, queryable
# dataset) for anyone exploring the repo — the dashboard itself reads only
# the pre-computed CSV assets below.

C = {
    "bg":      "#FAFAF8",
    "card":    "#FFFFFF",
    "border":  "#E8E5E0",
    "text":    "#2D2D2D",
    "muted":   "#8E8E93",
    "grid":    "#F0EDE8",
    "skin":    "#4A90B8",
    "cosm":    "#C4627A",
    "ingr":    "#5B8C6E",
    "korean":  "#D4785C",
    "gold":    "#B8965A",
    "skin_lt": "#D6E8F5",
    "cosm_lt": "#F5DDE3",
}

@st.cache_data
def compute_headline():
    """Headline metrics — single source of truth, computed live from dashboard assets.

    All v1 review-volume and pooled-TF-IDF metrics were retired; the Google
    Trends comparison uses the anchored block_B, and convergence is the
    size-matched figure (see Analysis Revision History in README)."""
    # Rakuten SKU counts
    df_sku = pd.read_csv(ASSETS / "nb07_sku_treemap.csv")
    skin_skus = int(df_sku[df_sku["tier_group"] == "skincare"]["sku_count"].sum())
    cosm_skus = int(df_sku[df_sku["tier_group"] == "cosmetics"]["sku_count"].sum())
    sku_ratio = round(skin_skus / max(cosm_skus, 1), 1)

    # Google Trends — anchored block_B (the only cross-term-comparable block)
    df_tr = pd.read_csv(ASSETS / "nb07_trends_crossover.csv", parse_dates=["week_start"])
    df_tr["year"] = df_tr["week_start"].dt.year
    # Compare full calendar years only — the latest year is partial (Jan–Mar),
    # and cosmetics search is seasonal (December gifting), so a partial-year
    # endpoint biases the decline estimate.
    months_per_year = df_tr.groupby("year")["week_start"].nunique()
    full_years = months_per_year[months_per_year >= 12].index
    annual = df_tr.groupby(["year", "term"])["interest"].mean().unstack(fill_value=0)
    annual = annual.loc[annual.index.isin(full_years)]
    y0, y1 = annual.index.min(), annual.index.max()
    cosm_decline = int(round(100 * (annual.loc[y1, "化粧品"] - annual.loc[y0, "化粧品"])
                             / annual.loc[y0, "化粧品"]))
    ratio_0 = round(annual.loc[y0, "スキンケア"] / annual.loc[y0, "化粧品"], 2)
    ratio_1 = round(annual.loc[y1, "スキンケア"] / annual.loc[y1, "化粧品"], 2)

    # Vocabulary convergence — size-matched salvage (v1 figure was size-inflated)
    df_sv = pd.read_csv(ASSETS / "nb06_cosine_salvage.csv")
    sm = df_sv[df_sv["method"] == "size_matched"]["cosine"].tolist()
    v1 = df_sv[df_sv["method"] == "v1_full_data"]["cosine"].tolist()
    conv_lo, conv_hi = round(sm[0], 2), round(sm[1], 2)
    conv_delta = round(sm[1] - sm[0], 2)
    conv_v1 = round(v1[1] - v1[0], 2)
    v1_lo, v1_hi = round(v1[0], 2), round(v1[1], 2)
    _mn = df_sv[df_sv["method"] == "matched_n"]["cosine"]
    matched_n = int(_mn.iloc[0]) if len(_mn) else 249
    conv_share = round(100 * conv_delta / conv_v1) if conv_v1 else 0

    # Sample-size effect — identical data, cosine vs N
    df_cv = pd.read_csv(ASSETS / "nb06_cosine_sizecurve.csv")
    size_lo, size_hi = df_cv.iloc[0], df_cv.iloc[-1]

    # Ingredient search surge — niacinamide, pre- vs post-COVID
    df_ing = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
    df_ing["year"] = df_ing["week_start"].dt.year
    nia = df_ing[df_ing["term"] == "ナイアシンアミド"]
    nia_pre = int(round(nia[nia.year <= 2020]["interest"].mean()))
    nia_post = int(round(nia[nia.year >= 2023]["interest"].mean()))

    return {
        "sku_ratio":    sku_ratio,
        "skin_skus":    skin_skus,
        "cosm_skus":    cosm_skus,
        "cosm_decline": cosm_decline,
        "ratio_0":      ratio_0,
        "ratio_1":      ratio_1,
        "conv_lo":      conv_lo,
        "conv_hi":      conv_hi,
        "conv_delta":   conv_delta,
        "conv_v1":      conv_v1,
        "v1_lo":        v1_lo,
        "v1_hi":        v1_hi,
        "matched_n":    matched_n,
        "conv_share":   conv_share,
        "size_lo_n":    int(size_lo["sample_size"]),
        "size_lo_cos":  round(size_lo["cross_tier_cosine"], 2),
        "size_hi_n":    int(size_hi["sample_size"]),
        "size_hi_cos":  round(size_hi["cross_tier_cosine"], 2),
        "nia_pre":      nia_pre,
        "nia_post":     nia_post,
    }

HEADLINE = compute_headline()
STRINGS = {
    "en": {
        "tagline":       "Japanese beauty market intelligence",
        "subtitle":      "@cosme · Rakuten Ichiba · Google Trends JP · YouTube · 2019–2026 · 45,510 reviews · 39,436 SKUs",
        "tab1": "📈  The shift", "tab2": "🔤  The language", "tab3": "🔍  Discovery", "tab4": "💡  For brands",

        # ── TAB 1: The Shift ──────────────────────────────────────────────
        "t1_intro":  "Several independent data sources lean the same way: since COVID, Japanese consumers have shifted beauty priority toward skincare. The signal is real — but modest, and driven as much by cosmetics demand falling as by skincare rising. This dashboard shows the corrected picture, after an independent methodology audit (see the README's revision history).",

        "t1_m1": "Cosmetics search decline",  "t1_m1d": "化粧品 search interest, full years 2019→2025 (anchored Google Trends)",
        "t1_m2": "Ingredient search surge",   "t1_m2d": "niacinamide search interest, pre- vs post-COVID",
        "t1_m3": "Rakuten SKU ratio",
        "t1_m4": "Skincare-to-cosmetics search",  "t1_m4d": "the gap roughly halved — but cosmetics still leads",

        "t1_c1h": "Cosmetics search fell about a third; skincare held flat — no crossover",
        "t1_c1e": "Monthly Google search interest, 2019–2026 (2026 = Jan–Mar). This uses the *anchored* query block — the only one where スキンケア and 化粧品 share a single comparable scale. Cosmetics (化粧品) search has fallen steadily; skincare (スキンケア) is roughly flat. The gap is closing — but cosmetics still leads in every year. There is no crossover. (v1 reported a \'2020 crossover\' from unanchored data, where each term is normalised to its own peak and the two cannot be compared — that claim was retired.)",
        "t1_c2h": "Consumers now search ingredients by name — a 6–7× surge",
        "t1_c2e": "Consumers aren\'t just searching for \'skincare\' — they\'re searching for specific ingredients by name. Each line tracks one ingredient\'s search popularity over time. The post-COVID climb shows consumers becoming educated about what goes into their products. Each term is normalised to its own scale, so this reads as growth-over-time, not cross-ingredient ranking.",
        "t1_c2cap": "Dashed lines = ingredients already known pre-COVID  ·  Solid lines = ingredients that broke out after 2020  ·  2026 = Jan–Mar only",
        "t1_ingr_sel": "Select ingredients",
        "t1_c3h": "Rakuten shelf: skincare outnumbers cosmetics 4.1×",
        "t1_c3e": "Every rectangle is a product subcategory on Rakuten Ichiba (Japan\'s largest e-commerce platform). Size = number of products listed · colour = the lens you select below. Skincare dominates the shelf — though SKU count reflects catalog supply and scraping depth, not sales or demand. Ratings average *rated* SKUs only (an unreviewed listing is not a zero-star one); price is the median, since listings range from ¥1 junk to ¥300k+ outliers.",
        "t1_lens": "Colour by",
        "t1_lens_opts": {"Engagement": "avg_reviews", "Competition": "sku_count", "Price point": "med_price", "Quality": "avg_rating"},

        "t1_c4h": "The mask test: makeup search never came back after masks came off",
        "t1_c4e": "The strongest rival explanation for the cosmetics decline is masks — \'makeup search fell because faces were covered, and it returns once masks come off.\' This panel tests that directly. Each makeup-category term is indexed to its own scale (no cross-term comparison). Japan relaxed its mask guidance on 13 March 2023: a pure mask effect predicts a rebound to the 2019 baseline after that line. Instead, lipstick and foundation managed only a brief 2023 bump before resuming their decline — by 2025 lipstick search sat *below its COVID-era trough*. Eyeshadow is the control that proves masks mattered: it *rose* while masks emphasised eyes, then fell below its 2019 baseline once they came off. The mask effect was real — but what remains is structural.",
        "t1_c4cap": "Monthly search interest, each term normalised to its own peak · grey band = COVID emergency phase · dashed line = mask guidance relaxed (2023-03-13) · 2026 = Jan–Mar",
        "f1b_title": "Why this matters — the decline is structural, not cyclical",
        "f1b_body":  "Annual averages vs each term\'s own 2019 baseline: lipstick 100 → 42 (2021, masks) → 53 (2023, rebound) → 36 (2025). Foundation 100 → 77 → 86 → 69. Eyeshadow 100 → 128 (2022 peak — eyes above the mask) → 80 (2025). If masks were the whole story, all three should have returned toward 100 after March 2023. None did. This is the single strongest piece of evidence that the skincare shift is structural — stronger than the 化粧品 headline, which could partly reflect consumers simply searching more specific terms over time.",

        "t1_c5h": "YouTube: skincare comment volume outgrew cosmetics",
        "t1_c5e": "An independent platform check: YouTube comment volumes on Japanese beauty videos, split by skincare vs cosmetics. Separate platform, broadly the same direction — skincare discourse outgrows cosmetics over the period.",
        "t1_c5cap": "2022: cosmetics briefly edges skincare — the mask-off rebound is visible here too · by 2024 skincare comment volume is well ahead",

        "f1_title": "Finding 1 — The structural shift is supported, but modest",
        "f1_body":  "Search demand, commercial supply, ingredient curiosity and YouTube discourse all lean the same way. In anchored Google Trends, cosmetics search fell ~32% across full years 2019→2025 while skincare held roughly flat — the gap halved, though cosmetics still leads. Rakuten lists 4.1× more skincare SKUs (shelf share). Ingredient searches surged 6–7×. And the mask test above rules out the strongest rival explanation: makeup search did not recover when masks came off. The direction is clear; the magnitude is moderate — this is a real shift, not a dramatic one.",

        # ── TAB 2: The Language ───────────────────────────────────────────
        "t2_intro": "The shift shows up in the words consumers use too — but this tab is also where the data demanded the hardest correction. v1 reported a dramatic vocabulary convergence between skincare and cosmetics reviews. An independent audit showed most of that was a sample-size artifact. What honestly remains is a small, real convergence — and the correction itself is worth seeing.",

        "t2_m1": "Vocabulary convergence",  "t2_m1d": "size-matched Δ — small but statistically robust (95% CI excludes 0)",
        "t2_m2": "v1 figure — retired",     "t2_m2d": "roughly 80% of it was a sample-size artifact",
        "t2_m3": "Sample-size effect",       "t2_m3d": "identical data: cosine inflates as N grows 150→6,000",

        "t2_wch": "Consumer vocabulary by year",
        "t2_wce": "What words appear most frequently in beauty reviews each year? Larger words = used more often. Brand names and generic sentiment words are removed. Note: the mix of categories in the corpus varies by year, so read these as a descriptive snapshot of each year\'s reviews, not as a controlled trend.",
        "t2_wc_early": "2019–2021: makeup-application vocabulary is prominent — マスカラ (mascara), アイライナー (eyeliner), まつ毛 (eyelashes), ブラシ (brush)",
        "t2_wc_2022":  "2022: a mix — makeup and skincare terms both visible",
        "t2_wc_2023":  "2023: functional skincare terms gaining ground",
        "t2_wc_late":  "2024–2026: skincare vocabulary prominent — 乾燥 (dryness), 保湿 (moisture), 香り (scent), クリーム (cream), 洗顔 (face wash). 2026 is a partial, mid-year snapshot.",

        "t2_curveh": "The sample-size trap — why v1\'s convergence was overstated",
        "t2_curvee": "v1 measured vocabulary convergence as the cosine similarity between *pooled* skincare and cosmetics reviews. But that cosine rises mechanically with sample size — a bigger pool simply covers more vocabulary. This line uses the *identical* 2023–25 reviews, subsampled to different sizes: the similarity climbs from ~0.31 to ~0.66 with no change in the underlying language. v1\'s bootstrap resampled within fixed sizes and never detected this.",
        "t2_curvenote": "Size-matched — every period equalised to 249 reviews — a convergence still remains: 0.25 → 0.32, Δ +0.06 (bootstrap 95% CI excludes zero). Real, statistically robust, but roughly one-fifth the magnitude v1 claimed (Δ +0.31).",

        "f2_title": "Finding 2 — Vocabulary converged slightly; v1\'s headline was a sample-size artifact",
        "f2_body":  "v1 reported skincare and cosmetics review language converging from 0.39 to 0.70 and called it the project\'s strongest unsupervised finding. An independent audit showed TF-IDF cosine between pooled corpora inflates with sample size — and v1\'s bootstrap, which resampled within fixed sizes, could not see it. Under a properly size-matched comparison the convergence is real but small: Δ +0.06 (95% CI excludes zero). The honest version is less dramatic — the full correction is documented in the README\'s revision history.",

        # ── TAB 3: Discovery ──────────────────────────────────────────────
        "t3_intro": "Two discovery engines look at what\'s coming next. Google Trends surfaces what consumers search for before it shows up in reviews. The review map below shows the spatial shape of consumer vocabulary — a descriptive structure that, unlike the convergence metric, does not depend on sample size.",

        "t3_m1": "Strongest recent signal",  "t3_m1d": "Korean brand · across 6 independent search terms",
        "t3_m2": "COVID-era leader",          "t3_m2d": "ingredient · 5 search terms · consumers learning",
        "t3_m3": "Review corpus shape",       "t3_m3d": "~78% form one undifferentiated mass — a continuum, not segments",

        "t3_bch": "Search discovery — what are consumers searching for next?",
        "t3_bce": "Starting from 20+ beauty search terms (e.g. スキンケア, ナイアシンアミド, 口紅), Google identifies the fastest-accelerating related searches. When the same brand or ingredient appears across multiple independent starting points, that\'s a strong signal. Size = signal strength (mean normalised rising-search score × number of seed terms it surfaced from) · colour = signal type. Brand origins were verified against official sources — three Japanese brands with K-beauty-style positioning (unlabel, CERAMIAID, KITEN) were initially misclassified as Korean and have been corrected.",
        "t3_win_r": "Recent (2023–2025)", "t3_win_c": "COVID era (2020–2021)",
        "t3_sig_kr": "Korean brand", "t3_sig_in": "Ingredient", "t3_sig_ot": "Other",

        "f4r_title": "Finding 4 — Korean brands are harvesting Japanese demand",
        "f4r_body":  "During COVID, ingredient searches dominated — consumers were building knowledge (retinol appeared across 5 independent search terms, niacinamide across 4). In the recent window, Anua (アヌア, a Korean brand) is the single strongest signal, appearing across 6 independent search terms. The structural shift educated consumers. Korean brands captured them.",
        "f4c_title": "COVID era — consumers were learning ingredients, not searching for brands",
        "f4c_body":  "During 2020–2021, Japanese consumers weren\'t searching for brands — they were learning ingredients. Retinol (レチノール), niacinamide (ナイアシンアミド), and ceramide (セラミド) dominated the fastest-rising searches across multiple starting points. This ingredient literacy is the knowledge foundation that Korean brands later capitalised on.",

        "t3_ytch":  "YouTube content supply — top channels by category",
        "t3_ytche": "The top 15 YouTube beauty channels by total views, coloured by whether they focus on skincare or cosmetics. Notice the gap: Korean beauty (韓国コスメ) generates massive search demand (Finding 4), but has very little YouTube content covering it.",
        "t3_ytgap":  "Content supply gap — ",
        "t3_ytgapb": "Korean beauty (韓国コスメ) generates the strongest search signal (アヌア across 6 search terms) but has only 16 videos and 4.4M views in our dataset. Meanwhile かずのすけ (a science-focused beauty creator) dominates ingredient content with 71 videos and 43.4M views — ingredient education drives engagement. Korean brands have captured search and reviews; YouTube is still wide open.",

        "t3_yttfh": "YouTube comments — what are viewers actually saying?",
        "t3_yttfe": "The same text analysis applied to YouTube comments reveals a surprise: YouTube and @cosme are different conversations. Only 14 of the top 30 skincare terms overlap between the two platforms.",
        "t3_ytreg":  "Platform difference — ",
        "t3_ytregb": "動画 (video) · 参考 (reference) · 思う (think) dominate YouTube — viewers comment <em>on the video</em>, not on a product. @cosme = product-evaluation language (しっとり/moist texture · 毛穴/pores · 香り/scent). YouTube = social-reaction language. Two genuinely different conversations about the same products. <b>かずのすけ</b> appears as a top-3 skincare term on YouTube — more prominent than 化粧水 (toner).",
        "t3_ytdivtitle": "← Cosmetics YouTube language  ·  Skincare YouTube language →",
        "t3_ytdivax":    "How much more a term appears in skincare vs cosmetics comments",

        "t3_umaph": "Review map — the shape of consumer vocabulary",
        "t3_umape": "Every dot is one @cosme review, positioned by vocabulary similarity — reviews using similar words appear close together. This turns the full review corpus into a landscape you can explore. Colours: blue = skincare, rose = cosmetics.",
        "t3_umap_yr": "Filter by year",
        "t3_umap_sk": "Skincare", "t3_umap_co": "Cosmetics",
        "t3_umap_note": "Labels show the key vocabulary of each region.\n\nCompare 2019 vs 2025 — where rose (cosmetics) dots mix into blue (skincare) territory, consumer vocabulary overlaps.",

        "f3_title": "Finding 3 — The review map reveals structure that survives scrutiny",
        "f3_body":  "Unlike the convergence number, this is spatial structure — descriptive, and independent of sample size. The northeast zone is where skincare and cosmetics vocabulary overlap most: foundation reviews written in skincare language, cleansing reviews evaluated on moisture and texture.<br><br>More striking is the isolated top island: influencer and giveaway reviews (「プレゼント」/「当選」 template language) separated automatically from organic consumer reviews — without being told to. Brands measuring sentiment without filtering these populations are mixing two different signals. This is the most robust thing @cosme\'s text offers.",

        # ── TAB 4: For brands ─────────────────────────────────────────────
        "t4_intro": "What the four findings imply if you sit inside a beauty company. These are directional hypotheses from attention and shelf data — search, reviews, catalog, YouTube — not from sales. Each card names the evidence it rests on.",
        "t4_c1h": "Lead with the ingredient, not the brand",
        "t4_c1b": "Ingredient-name search grew 6–7× and never receded (Finding 1), and COVID-era discovery searches were dominated by actives, not brands (Finding 4). The most-watched skincare creator in the dataset is a chemistry educator — かずのすけ\'s ingredient content drew 43.4M views, and his name out-ranks 化粧水 as a search term in YouTube comments. Product naming, PDP copy and ad creative that lead with the active and its concentration meet consumers where their literacy now is.",
        "t4_c2h": "Take the K-brand threat seriously — and learn its trick",
        "t4_c2b": "Anua is the strongest rising-search signal in the recent window, surfacing from 6 independent seed terms (Finding 4). The pattern: Korean brands captured demand that Japanese consumers\' own ingredient education created. Tellingly, three *Japanese* brands (unlabel, CERAMIAID, KITEN) now position themselves so K-style that this analysis initially misclassified them as Korean. Meanwhile Korean beauty has just 16 videos · 4.4M views of YouTube supply against that search demand — the education-content lane is still open to whoever moves first.",
        "t4_c3h": "Don\'t plan for a makeup rebound that isn\'t coming",
        "t4_c3b": "Two years after Japan relaxed mask guidance (March 2023), lipstick search sits at 36% of its 2019 baseline — below its COVID trough — and even eyeshadow, which *benefited* from masks, is 20% under baseline (mask test, Tab 1). The recovery scenario has had its window and didn\'t arrive. The convergence zone on the review map points to where the energy went: base makeup evaluated in skincare language — 保湿, 乾燥, ツヤ. Skincare-hybrid makeup is the defensible position; a pure colour-led lineup is fighting the tide.",
        "t4_c4h": "Filter giveaway reviews before you measure anything",
        "t4_c4b": "Influencer/monitor reviews (「プレゼント」「当選」 template language) form their own island in vocabulary space, fully separated from organic consumer reviews (Finding 3). Any brand-health metric, sentiment tracker or VoC summary built on unfiltered @cosme data is averaging two different populations — one of which was paid in product. The template vocabulary makes them cheap to detect and exclude. This is the most immediately operational finding in the project.",
        "t4_note": "Attention and shelf data lead sales data — they do not replace it. Before acting on any of these, triangulate against sales: 家計調査 household spend per item (e-Stat), METI shipment statistics, and your own sell-through.",
    },
    "jp": {
        "tagline":        "日本の美容市場インテリジェンス",
        "subtitle":       "@cosme · 楽天市場 · Google Trends JP · YouTube · 2019–2026 · 45,510件レビュー · 39,436 SKU",
        "tab1": "📈  市場変化", "tab2": "🔤  消費者の言語", "tab3": "🔍  発見", "tab4": "💡  ブランドへの示唆",

        "t1_intro":  "複数の独立したデータソースが同じ方向を指している。コロナ禍以降、日本の消費者は美容の優先順位をスキンケアへと移した。このシグナルは実在するが、規模は控えめであり、スキンケアの上昇よりむしろ化粧品の需要低下に支えられている。本ダッシュボードは、独立した方法論監査を経た修正後の姿を示す（READMEの改訂履歴を参照）。",

        "t1_m1":     "化粧品の検索需要の低下",  "t1_m1d": "化粧品の検索関心度、暦年ベース2019→2025年（アンカー付きトレンド）",
        "t1_m2":     "成分検索の急増",          "t1_m2d": "ナイアシンアミドの検索関心度、コロナ前後",
        "t1_m3":     "楽天SKU比率",
        "t1_m4":     "スキンケア対化粧品 検索比",  "t1_m4d": "差は半減 —— ただし化粧品が依然上回る",

        "t1_c1h":    "化粧品の検索は約3分の1低下 — スキンケアは横ばい（逆転なし）",
        "t1_c1e":    "2019〜2026年の月次Google検索関心度（2026年は1〜3月）。「スキンケア」と「化粧品」が共通の比較可能なスケールに乗る唯一のクエリブロック（アンカー付き）を用いている。化粧品の検索は着実に低下し、スキンケアはほぼ横ばい。差は縮まっているが、化粧品が毎年上回り、「逆転」は起きていない。（初版は非アンカーのデータで「2020年の逆転」を報告したが、そこでは各語が自身のピークに正規化され両者を比較できない —— この主張は撤回した。）",
        "t1_c2h":    "消費者は成分を指名検索する — コロナ後6〜7倍に",
        "t1_c2e":    "消費者は「スキンケア」だけでなく、成分名を指名検索している。各線は1つの成分の検索人気を経時的に追跡。コロナ後の上昇は、消費者が製品の中身について学び始めたことを示す。各語は自身のスケールに正規化されているため、これは経時的な伸びを示すもので、成分間の順位比較ではない。",
        "t1_c2cap":  "点線 = コロナ前から認知されていた成分  ·  実線 = 2020年以降に急浮上した成分  ·  2026年は1〜3月のみ",
        "t1_ingr_sel": "成分を選択",
        "t1_c3h":    "楽天の棚：スキンケアSKUはコスメの4.1倍",
        "t1_c3e":    "各長方形は楽天市場（日本最大のECプラットフォーム）のサブカテゴリ。サイズ = 商品掲載数 · 色 = 選択レンズ。スキンケアが棚を支配している —— ただしSKU数はカタログ供給と取得の深さを反映し、売上や需要そのものではない。評価は「評価のあるSKU」のみの平均（未レビュー＝星ゼロではない）。価格は中央値（¥1のジャンク出品や¥30万超の外れ値があるため）。",
        "t1_lens":   "色分け基準",
        "t1_lens_opts": {"エンゲージメント": "avg_reviews", "競合状況": "sku_count", "価格帯": "med_price", "品質": "avg_rating"},

        "t1_c4h":    "マスク検証：マスク解禁後もメイク検索は戻らなかった",
        "t1_c4e":    "化粧品低下の最有力な対立仮説はマスクである —— 「顔が隠れたから検索が落ちた。マスクが外れれば戻る」。このパネルはそれを直接検証する。各メイク用語は自身のスケールに正規化（用語間の比較はしない）。日本は2023年3月13日にマスク着用ルールを緩和した：純粋なマスク効果なら、この線の後に2019年水準へ回帰するはずである。実際には、口紅とファンデーションは2023年に小幅な反発を見せた後、再び低下に転じた —— 2025年の口紅検索は*コロナ期の底すら下回る*。アイシャドウは「マスクが効いていた」ことを証明する対照群である：マスクが目元を強調した期間に*上昇*し、解禁後は2019年水準を下回った。マスク効果は実在した —— だが残ったものは構造的である。",
        "t1_c4cap":  "月次検索関心度、各語は自身のピークに正規化 · グレー帯 = コロナ緊急期 · 破線 = マスク緩和（2023-03-13） · 2026年は1〜3月",
        "f1b_title": "これが重要な理由 — 低下は構造的であり、循環的ではない",
        "f1b_body":  "各語自身の2019年を100とした年平均：口紅 100 → 42（2021年・マスク期）→ 53（2023年・反発）→ 36（2025年）。ファンデーション 100 → 77 → 86 → 69。アイシャドウ 100 → 128（2022年ピーク —— マスクの上の目元）→ 80（2025年）。マスクがすべての説明なら、3語とも2023年3月以降に100へ回帰するはずだった。どれも回帰しなかった。これはスキンケアシフトが構造的であることを示す最も強力な証拠である —— 「化粧品」の見出し指標より強い（あちらは消費者がより具体的な語を検索するようになった効果も含みうる）。",

        "t1_c5h":    "YouTube：スキンケアのコメント量がコスメを上回って成長",
        "t1_c5e":    "独立したプラットフォームでの確認：日本の美容動画へのYouTubeコメント量をスキンケア対コスメで分割。別のプラットフォームでも、おおむね同じ方向 —— 期間を通じてスキンケアの言論がコスメを上回って伸びる。",
        "t1_c5cap":  "2022年はコスメが一時的にスキンケアを上回る（マスク解禁効果はここでも可視）· 2024年にはスキンケアのコメント量が大きく先行",

        "f1_title":  "発見1 — 構造的変化は支持されるが、規模は控えめ",
        "f1_body":   "検索需要・商業的供給・成分への関心・YouTube言論が、いずれも同じ方向を指す。アンカー付きGoogleトレンドでは、化粧品の検索が暦年ベース2019→2025年で約32%低下した一方、スキンケアはほぼ横ばい —— 差は半減したが化粧品が依然上回る。楽天はスキンケアSKUを4.1倍掲載（棚シェア）。成分検索は6〜7倍に急増。さらに上のマスク検証が最有力の対立仮説を棄却する：マスク解禁後もメイク検索は回復しなかった。方向は明確だが規模は中程度 —— これは実在する変化であり、劇的な変化ではない。",

        "t2_intro":  "変化は消費者が使う「言葉」にも現れる —— だがこのタブは、データが最も厳しい修正を要求した場所でもある。初版は、スキンケアとコスメのレビュー語彙が劇的に収束したと報告した。独立した監査により、その大部分がサンプルサイズのアーティファクトであることが判明した。正直に残るのは、小さいが実在する収束 —— そしてその修正の過程自体が見るに値する。",

        "t2_m1":     "語彙収束",  "t2_m1d": "サンプル数を揃えたΔ —— 小さいが統計的に頑健（95%CIがゼロを除外）",
        "t2_m2":     "初版の値（撤回）", "t2_m2d": "そのうち約8割はサンプルサイズのアーティファクト",
        "t2_m3":     "サンプルサイズ効果", "t2_m3d": "同一データ：Nが150→6,000と増えるとコサインが上昇",

        "t2_wch":    "年別消費者語彙",
        "t2_wce":    "美容レビューで各年に最も頻出する語彙は何か？　 大きい語 = より頻繁に使用。ブランド名と汎用感情語は除外。注：コーパスのカテゴリ構成は年により変動するため、これは各年のレビューの記述的スナップショットであり、統制されたトレンドではない。",
        "t2_wc_early":  "2019–2021：メイクアップ語彙が目立つ — マスカラ、アイライナー、まつ毛、ブラシ",
        "t2_wc_2022":   "2022：混在期 — メイクとスキンケアの語彙が両方見える",
        "t2_wc_2023":   "2023：機能的なスキンケア語彙が台頭",
        "t2_wc_late":   "2024–2026：スキンケア語彙が目立つ — 乾燥、保湿、香り、クリーム、洗顔。2026年は途中集計（年央時点）。",

        "t2_curveh": "サンプルサイズの罠 — なぜ初版の収束は過大だったのか",
        "t2_curvee": "初版は語彙収束を、プールしたスキンケアレビューとコスメレビューの間のコサイン類似度として測定した。しかしこのコサインは、サンプル数とともに機械的に上昇する —— プールが大きいほど多くの語彙を被覆するためである。この線は同一の2023–25年レビューを異なるサイズにサブサンプルしたもの：基となる言語は何も変えていないのに、類似度は約0.31から約0.66まで上昇する。初版のブートストラップは固定サイズ内で再標本化しており、これを検出できなかった。",
        "t2_curvenote": "サンプル数を揃えると（各期間を249件に均一化）、収束は依然として残る：0.25 → 0.32、Δ +0.06（ブートストラップ95%CIはゼロを除外）。実在し統計的に頑健だが、初版の主張（Δ +0.31）の約5分の1の規模。",

        "f2_title":  "発見2 — 語彙はわずかに収束した。初版の見出しはサンプルサイズのアーティファクトだった",
        "f2_body":   "初版は、スキンケアとコスメのレビュー言語が0.39から0.70へ収束したと報告し、これをプロジェクト最強の教師なし発見と称した。独立した監査により、プールされたコーパス間のTF-IDFコサインはサンプル数とともに上昇すること、そして固定サイズ内で再標本化した初版のブートストラップではそれを検出できないことが判明した。サンプル数を適切に揃えた比較では、収束は実在するが小さい：Δ +0.06（95%CIはゼロを除外）。正直な姿はより地味である —— 修正の全容はREADMEの改訂履歴に記録されている。",

        "t3_intro":  "2つの発見エンジンが「次に来るもの」を見る。Googleトレンドはレビューに現れる前に消費者が検索しているものを浮かび上がらせる。下のレビューマップは消費者語彙の空間的形状を示す —— 収束指標とは異なり、この記述的構造はサンプルサイズに依存しない。",

        "t3_m1":     "直近の最強シグナル", "t3_m1d": "韓国ブランド · 6つの独立した検索語で出現",
        "t3_m2":     "COVID期リーダー",    "t3_m2d": "成分 · 5つの検索語 · 消費者が学習していた時期",
        "t3_m3":     "レビューコーパスの形状",  "t3_m3d": "約78%が単一の中心塊に集中 —— セグメントではなく連続体",

        "t3_bch":    "検索発見 — 消費者は次に何を検索しているか？",
        "t3_bce":    "20以上の美容検索語（スキンケア、ナイアシンアミド、口紅など）を起点に、Googleが最も急上昇する関連検索を抽出。同じブランドや成分が複数の異なる起点から浮上する場合、それは強いシグナルである。サイズ = シグナル強度（正規化済み急上昇スコアの平均 × 浮上した起点数）· 色 = シグナル種別。ブランドの原産国は公式情報で検証済み —— K-Beauty風のポジショニングを持つ日本ブランド3つ（アンレーベル・セラミエイド・キテン）を当初韓国と誤分類しており、修正した。",
        "t3_win_r":  "直近（2023–2025）", "t3_win_c": "COVID期（2020–2021）",
        "t3_sig_kr": "韓国ブランド", "t3_sig_in": "成分", "t3_sig_ot": "その他",

        "f4r_title": "発見4 — 韓国ブランドが日本の需要を取り込んでいる",
        "f4r_body":  "COVID期は成分検索が支配的だった — 消費者が知識を蓄積していた（レチノールが5つの独立検索語で出現、ナイアシンアミドが4つ）。直近では、アヌア（韓国ブランド）が6つの独立した検索語に登場する最強シグナルとなっている。構造的変化が消費者を教育した。韓国ブランドがその恩恵を受けている。",
        "f4c_title": "COVID期 — 消費者はブランドではなく成分を学んでいた",
        "f4c_body":  "2020–2021年、日本の消費者はブランドを検索していたのではなく、成分を学んでいた。レチノール、ナイアシンアミド、セラミドが複数の起点から急上昇検索を独占した。この成分リテラシーこそ、後に韓国ブランドが活用する知識基盤となった。",

        "t3_ytch":   "YouTubeコンテンツ供給 — カテゴリ別トップチャンネル",
        "t3_ytche":  "総視聴数上位15チャンネルをスキンケア/コスメ別に表示。注目すべきギャップ：韓国コスメは検索需要が巨大（発見4）にもかかわらず、YouTubeコンテンツがほとんどない。",
        "t3_ytgap":  "コンテンツ供給ギャップ — ",
        "t3_ytgapb": "韓国コスメは最強の検索シグナル（アヌアが6つの検索語で出現）を生成しているが、YouTube動画はわずか16本・視聴数440万。一方、かずのすけ（科学系美容クリエイター）は71本・4,340万回視聴で成分コンテンツを支配 —— 成分教育がエンゲージメントを駆動する。韓国ブランドは検索と@cosmeを掌握した。YouTubeはまだ開かれている。",

        "t3_yttfh":  "YouTubeコメント — 視聴者は実際に何を言っているのか？",
        "t3_yttfe":  "同じテキスト分析をYouTubeコメントに適用すると意外な発見がある。YouTubeと@cosmeは異なる会話空間である。スキンケア上位30語のうち、両プラットフォームで共通するのはわずか14語。",
        "t3_ytreg":  "プラットフォーム間の違い — ",
        "t3_ytregb": "動画・参考・思うがYouTubeを支配 — 視聴者は商品ではなく<em>動画に対して</em>コメントしている。@cosme = 商品評価言語（しっとり・毛穴・香り）。YouTube = 社会的反応言語。同じ製品についての2つの異なる会話空間。<b>かずのすけ</b>がスキンケア上位3語として登場 — 化粧水よりも上位。",
        "t3_ytdivtitle": "← コスメYouTube言語  ·  スキンケアYouTube言語 →",
        "t3_ytdivax":    "スキンケアのコメントでどれだけ多く登場するか（コスメとの差分）",

        "t3_umaph":  "レビューマップ — 消費者語彙の地形",
        "t3_umape":  "各点が@cosmeレビュー1件。似た語彙を使うレビューほど近くに配置される。全レビューコーパスを探索可能な地形図に変換。色：青 = スキンケア、ローズ = コスメ。",
        "t3_umap_yr":   "年でフィルタ",
        "t3_umap_sk":   "スキンケア", "t3_umap_co": "コスメ",
        "t3_umap_note": "ラベルは各領域の主要語彙を示す。\n\n2019年と2025年を比較 — コスメ（ローズ）の点がスキンケア（ブルー）領域に混在している箇所が、消費者語彙の重なり。",

        "f3_title":  "発見3 — レビューマップは精査に耐える構造を示す",
        "f3_body":   "収束の数値とは異なり、これは空間的構造 —— 記述的であり、サンプルサイズに依存しない。北東の領域はスキンケアとコスメの語彙が最も重なる場所：スキンケア言語で書かれたファンデーションレビュー、保湿とテクスチャーで評価されるクレンジングレビュー。<br><br>さらに顕著なのは上部の孤立アイランド：インフルエンサー・モニターレビュー（「プレゼント」「当選」テンプレート）が、指示なしにオーガニックレビューから自動的に分離された。この2集団を分けずにセンチメント測定を行うブランドは、2種類のシグナルを混在させている。これは@cosmeのテキストが提供する最も頑健な所見である。",

        # ── TAB 4: ブランドへの示唆 ────────────────────────────────────────
        "t4_intro": "4つの発見が、美容企業の中にいる人にとって何を意味するか。これらは検索・レビュー・カタログ・YouTubeという「注目と棚」のデータに基づく方向性の仮説であり、売上データではない。各カードは根拠とする発見を明記している。",
        "t4_c1h": "ブランドではなく、成分を主語にする",
        "t4_c1b": "成分の指名検索は6〜7倍に増え、その後も衰えていない（発見1）。コロナ期の発見的検索を支配したのはブランドではなく有効成分だった（発見4）。データセット中で最も視聴されたスキンケアクリエイターは化学の教育者 —— かずのすけの成分コンテンツは4,340万回視聴され、YouTubeコメントでは彼の名前が「化粧水」より上位の検索語になっている。製品名・商品ページ・広告クリエイティブは、有効成分とその濃度を主語にすることで、現在の消費者リテラシーに合流できる。",
        "t4_c2h": "韓国ブランドの脅威を直視し、その手法から学ぶ",
        "t4_c2b": "直近ウィンドウの最強急上昇シグナルはアヌアで、6つの独立した起点語から浮上した（発見4）。構図：日本の消費者自身の成分教育が生んだ需要を、韓国ブランドが刈り取っている。象徴的なのは、日本ブランド3つ（アンレーベル・セラミエイド・キテン）がK-Beauty風のポジショニングを取るあまり、本分析が当初韓国と誤分類したことである。一方、韓国コスメのYouTube供給は16本・440万回視聴に留まる —— 検索需要に対して教育コンテンツのレーンはまだ空いている。先に動いた者が取る。",
        "t4_c3h": "「メイクの揺り戻し」を計画に織り込まない",
        "t4_c3b": "マスク緩和（2023年3月）から2年、口紅検索は2019年比36% —— コロナ期の底を下回る水準にある。マスクの恩恵を受けたアイシャドウでさえ基準比80%（タブ1のマスク検証）。回復シナリオには十分な時間が与えられ、実現しなかった。エネルギーの行き先はレビューマップの収束ゾーンが示している：保湿・乾燥・ツヤというスキンケア言語で評価されるベースメイクである。スキンケア・ハイブリッドのメイクが守れるポジションであり、純粋な色物主導のラインナップは潮流に逆らうことになる。",
        "t4_c4h": "測定の前に、モニターレビューを除外する",
        "t4_c4b": "インフルエンサー・モニターレビュー（「プレゼント」「当選」テンプレート言語）は語彙空間で独自のアイランドを形成し、オーガニックレビューから完全に分離している（発見3）。未フィルタの@cosmeデータで構築されたブランドヘルス指標・センチメントトラッカー・VoCサマリーは、2つの異なる母集団 —— うち一方は商品で対価を得ている —— を平均している。テンプレート語彙のため検出と除外は容易である。本プロジェクトで最も即座に運用可能な発見。",
        "t4_note": "注目と棚のデータは売上データに先行するが、代替はしない。実行の前に売上側での三角測量を：家計調査の品目別支出（e-Stat）、経産省の出荷統計、そして自社のセルスルー。",
    },
}
def _base(height=420):
    return dict(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", color=C["text"], size=12),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=C["card"], font_color=C["text"], font_size=12),
    )

def _xax(**kw):
    d = dict(gridcolor=C["grid"], linecolor=C["border"],
             zerolinecolor=C["border"], zerolinewidth=1)
    d.update(kw)
    return d

def _yax(title="", suffix="", **kw):
    d = dict(title=dict(text=title, font=dict(size=11)),
             gridcolor=C["grid"], linecolor=C["border"],
             zerolinecolor=C["border"], ticksuffix=suffix)
    d.update(kw)
    return d

@st.cache_data
def load_trends_crossover():
    return pd.read_csv(ASSETS / "nb07_trends_crossover.csv", parse_dates=["week_start"])

@st.cache_data
def load_ingredient_surge():
    df = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    return df

@st.cache_data
def load_sku_treemap():
    return pd.read_csv(ASSETS / "nb07_sku_treemap.csv")

@st.cache_data
def load_makeup_rebound():
    df = pd.read_csv(ASSETS / "nb07_makeup_rebound.csv", parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    return df

@st.cache_data
def load_review_slope():
    return pd.read_csv(ASSETS / "nb07_review_slope.csv")

@st.cache_data
def load_blockc():
    return pd.read_csv(ASSETS / "nb07_blockc.csv")

@st.cache_data
def load_umap():
    return pd.read_csv(ASSETS / "umap_embedding.csv")

@st.cache_data
def load_tfidf_delta():
    return pd.read_csv(ASSETS / "nb07_tfidf_delta.csv")

@st.cache_data
def load_cosine_sizecurve():
    return pd.read_csv(ASSETS / "nb06_cosine_sizecurve.csv")

@st.cache_data
def load_yt_volume():
    return pd.read_csv(ASSETS / "nb07_yt_volume.csv")

@st.cache_data
def load_yt_channels():
    return pd.read_csv(ASSETS / "nb07_yt_channels.csv")

@st.cache_data
def load_yt_tfidf():
    return pd.read_csv(ASSETS / "nb07_yt_tfidf.csv")

def kpi_card(label, value, subtitle, arrow="up"):
    """KPI metric card with a CSS tooltip on the truncated subtitle."""
    if arrow == "up":
        sub_color, prefix = "#21a550", "↑ "
    elif arrow == "down":
        sub_color, prefix = "#e05252", "↓ "
    else:
        sub_color, prefix = C["muted"], ""
    tip = _html.escape(subtitle)
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub" style="color:{sub_color}" data-tooltip="{tip}">'
        f'{prefix}{tip}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.markdown(f"""
<style>
.stApp {{ background-color:{C["bg"]}; }}
[data-testid="stToolbar"]    {{ display:none !important; }}
[data-testid="stDecoration"] {{ display:none !important; }}
.kpi-card {{
    background:{C["card"]}; border:1px solid {C["border"]};
    border-radius:10px; padding:14px 18px;
}}
.kpi-label {{ font-size:12px; color:{C["muted"]}; font-weight:500; margin-bottom:6px; }}
.kpi-value {{ font-size:28px; font-weight:700; color:{C["text"]}; line-height:1.1; margin-bottom:6px; }}
.kpi-sub {{
    font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    cursor:help; display:block;
}}
.stTabs [data-baseweb="tab-list"] {{ gap:8px; border-bottom:2px solid {C["border"]}; }}
.stTabs [data-baseweb="tab"] {{
    background:transparent; border-radius:6px 6px 0 0;
    color:{C["muted"]}; font-weight:500; padding:8px 20px;
}}
.stTabs [aria-selected="true"] {{
    background:{C["card"]}; color:{C["text"]};
    border-bottom:2px solid {C["skin"]};
}}
.expl {{ font-size:12px; color:{C["muted"]}; margin-top:2px; margin-bottom:10px; }}
</style>
""", unsafe_allow_html=True)

# st.markdown cannot execute <script> tags (React strips them).
# components.html runs inside an iframe where scripts execute; we reach
# the parent document via window.parent to attach the floating tooltip.
_components.html("""
<script>
var doc = window.parent.document;
if (!doc.getElementById('_kpi_tip')) {
    var tip = doc.createElement('div');
    tip.id = '_kpi_tip';
    tip.style.cssText = 'position:fixed;background:#1e1e1e;color:#fff;padding:7px 11px;'
        + 'border-radius:7px;font-size:12px;max-width:280px;line-height:1.5;z-index:99999;'
        + 'box-shadow:0 2px 10px rgba(0,0,0,.2);pointer-events:none;display:none;white-space:normal;';
    doc.body.appendChild(tip);
    doc.addEventListener('mouseover', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (el) { tip.textContent = el.getAttribute('data-tooltip'); tip.style.display = 'block'; }
    });
    doc.addEventListener('mouseout', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (el) tip.style.display = 'none';
    });
    doc.addEventListener('mousemove', function(e) {
        if (tip.style.display === 'block') {
            tip.style.left = Math.min(e.clientX + 14, window.parent.innerWidth - 300) + 'px';
            tip.style.top  = (e.clientY - 42) + 'px';
        }
    });
}
</script>
""", height=0)

_hdr_left, _hdr_right = st.columns([12, 1])
with _hdr_right:
    _lang = st.radio("lang", ["EN", "JA"], horizontal=True,
                     label_visibility="collapsed", key="lang_toggle")
lang = "jp" if _lang == "JA" else "en"
S = dict(STRINGS[lang])

# ── Convergence copy is rebuilt from live figures ─────────────────────────
# These numbers recompute whenever NB06 re-runs (corpus growth, re-scrape),
# so the prose is generated from HEADLINE rather than hardcoded — it can never
# drift out of sync with the KPI cards or the size-curve chart.
_h = HEADLINE
if lang == "en":
    S["t2_m2d"] = f"roughly {100 - _h['conv_share']}% of it was a sample-size artifact"
    S["t2_curvee"] = (
        "v1 measured vocabulary convergence as the cosine similarity between *pooled* "
        "skincare and cosmetics reviews. But that cosine rises mechanically with sample "
        "size — a bigger pool simply covers more vocabulary. This line uses the *identical* "
        f"2023–26 reviews, subsampled to different sizes: the similarity climbs from "
        f"~{_h['size_lo_cos']} to ~{_h['size_hi_cos']} with no change in the underlying "
        "language. v1's bootstrap resampled within fixed sizes and never detected this.")
    S["t2_curvenote"] = (
        f"Size-matched — every period equalised to {_h['matched_n']} reviews — a convergence "
        f"still remains: {_h['conv_lo']} → {_h['conv_hi']}, Δ +{_h['conv_delta']} (bootstrap "
        f"95% CI excludes zero). Real, statistically robust, but roughly {_h['conv_share']}% "
        f"of the magnitude v1 claimed (Δ +{_h['conv_v1']}).")
    S["f2_body"] = (
        f"v1 reported skincare and cosmetics review language converging from {_h['v1_lo']} to "
        f"{_h['v1_hi']} and called it the project's strongest unsupervised finding. An "
        "independent audit showed TF-IDF cosine between pooled corpora inflates with sample "
        "size — and v1's bootstrap, which resampled within fixed sizes, could not see it. "
        f"Under a properly size-matched comparison the convergence is real but small: "
        f"Δ +{_h['conv_delta']} (95% CI excludes zero). The honest version is less dramatic — "
        "the full correction is documented in the README's revision history.")
else:
    S["t2_m2d"] = f"そのうち約{100 - _h['conv_share']}%はサンプルサイズのアーティファクト"
    S["t2_curvee"] = (
        "初版は語彙収束を、プールしたスキンケアレビューとコスメレビューの間のコサイン類似度として測定した。"
        "しかしこのコサインは、サンプル数とともに機械的に上昇する —— プールが大きいほど多くの語彙を被覆"
        "するためである。この線は同一の2023–26年レビューを異なるサイズにサブサンプルしたもの：基となる言語は"
        f"何も変えていないのに、類似度は約{_h['size_lo_cos']}から約{_h['size_hi_cos']}まで上昇する。"
        "初版のブートストラップは固定サイズ内で再標本化しており、これを検出できなかった。")
    S["t2_curvenote"] = (
        f"サンプル数を揃えると（各期間を{_h['matched_n']}件に均一化）、収束は依然として残る："
        f"{_h['conv_lo']} → {_h['conv_hi']}、Δ +{_h['conv_delta']}（ブートストラップ95%CIはゼロを除外）。"
        f"実在し統計的に頑健だが、初版の主張（Δ +{_h['conv_v1']}）の約{_h['conv_share']}%の規模。")
    S["f2_body"] = (
        f"初版は、スキンケアとコスメのレビュー言語が{_h['v1_lo']}から{_h['v1_hi']}へ収束したと報告し、"
        "これをプロジェクト最強の教師なし発見と称した。独立した監査により、プールされたコーパス間のTF-IDF"
        "コサインはサンプル数とともに上昇すること、そして固定サイズ内で再標本化した初版のブートストラップでは"
        f"それを検出できないことが判明した。サンプル数を適切に揃えた比較では、収束は実在するが小さい："
        f"Δ +{_h['conv_delta']}（95%CIはゼロを除外）。正直な姿はより地味である —— 修正の全容はREADMEの"
        "改訂履歴に記録されている。")

with _hdr_left:
    st.markdown(f"""
<div style="padding:28px 0 8px 0; border-bottom:1px solid {C['border']}; margin-bottom:20px;">
    <div style="display:flex; align-items:baseline; gap:12px;">
        <h1 style="margin:0; font-size:30px; font-weight:800; color:{C['text']};
                   letter-spacing:-1px; font-family:Georgia,serif;">Beauty Pulse</h1>
        <span style="font-size:13px; color:{C['muted']}; font-style:italic;">
            {S["tagline"]}
        </span>
    </div>
    <p style="margin:6px 0 0 0; font-size:13px; color:{C['muted']};">
        {S["subtitle"]}
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([S["tab1"], S["tab2"], S["tab3"], S["tab4"]])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1
# ═══════════════════════════════════════════════════════════════════════════
with tab1:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t1_intro"]}</p>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        kpi_card(S["t1_m1"], f"{HEADLINE['cosm_decline']}%", S["t1_m1d"], arrow=None)
    with m2:
        kpi_card(S["t1_m2"], f"{HEADLINE['nia_pre']} → {HEADLINE['nia_post']}", S["t1_m2d"])
    with m3:
        _sub3 = f"{HEADLINE['skin_skus']:,} vs {HEADLINE['cosm_skus']:,} {'SKUs' if lang == 'en' else 'SKU'}"
        kpi_card(S["t1_m3"], f"{HEADLINE['sku_ratio']}x", _sub3)
    with m4:
        kpi_card(S["t1_m4"], f"{HEADLINE['ratio_0']} → {HEADLINE['ratio_1']}", S["t1_m4d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Chart 1 — Trends crossover
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c1h"]}</h3><p class="expl">{S["t1_c1e"]}</p>', unsafe_allow_html=True)

    df_cross = load_trends_crossover()
    min_date = df_cross["week_start"].min().to_pydatetime()
    max_date = df_cross["week_start"].max().to_pydatetime()
    date_range = st.slider("dr", min_value=min_date, max_value=max_date,
                           value=(min_date, max_date), format="YYYY-MM",
                           label_visibility="collapsed", key="crossover_slider")

    # Always plot full dataset — slider controls xaxis.range (zoom not filter)
    fig1 = go.Figure()
    fig1.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                   opacity=0.6, layer="below", line_width=0,
                   annotation_text="COVID", annotation_position="top left",
                   annotation_font=dict(size=10, color=C["muted"]))
    for term, color, label in [("スキンケア", C["skin"], "スキンケア (skincare)"),
                                 ("化粧品", C["cosm"], "化粧品 (cosmetics)")]:
        d = df_cross[df_cross["term"] == term]
        fig1.add_trace(go.Scatter(x=d["week_start"], y=d["interest"],
                                   name=label, mode="lines",
                                   line=dict(color=color, width=2.5),
                                   hovertemplate="%{y:.0f}<extra></extra>"))
    fig1.add_annotation(x="2024-01-01", y=70,
                        text="gap halving — no crossover" if lang == "en" else "差は縮小 — 逆転はなし",
                        showarrow=False,
                        font=dict(size=10, color=C["muted"]), bgcolor=C["card"],
                        bordercolor=C["border"], borderwidth=1, borderpad=4)
    fig1.update_layout(**_base(height=360))
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                       legend=dict(orientation="h", yanchor="top", y=-0.12,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(range=[date_range[0], date_range[1]]),
                       yaxis=_yax(title="Search interest (0–100)"))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Chart 1b — The mask test: makeup-term rebound vs own 2019 baseline
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c4h"]}</h3><p class="expl">{S["t1_c4e"]}</p>', unsafe_allow_html=True)

    df_mk = load_makeup_rebound()
    # Index each term to its own 2019 mean = 100 — per-term own-baseline reads
    # are the only valid use of unanchored block_A data (no cross-term levels).
    base_2019 = df_mk[df_mk["year"] == 2019].groupby("term")["interest"].mean()
    df_mk = df_mk[df_mk["term"].isin(base_2019.index)].copy()
    df_mk["indexed"] = 100 * df_mk["interest"] / df_mk["term"].map(base_2019)
    # 3-month centred rolling mean per term for readability (monthly is noisy)
    df_mk["smooth"] = (df_mk.sort_values("week_start")
                       .groupby("term")["indexed"]
                       .transform(lambda s: s.rolling(3, center=True, min_periods=1).mean()))

    MAKEUP_META = {
        "口紅":           (C["cosm"],  "口紅 (lipstick)"),
        "ファンデーション": (C["gold"],  "ファンデーション (foundation)"),
        "アイシャドウ":     ("#7B5EA7", "アイシャドウ (eyeshadow)"),
    }
    fig1b = go.Figure()
    fig1b.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                    opacity=0.6, layer="below", line_width=0,
                    annotation_text="COVID", annotation_position="top left",
                    annotation_font=dict(size=10, color=C["muted"]))
    fig1b.add_vline(x="2023-03-13", line_dash="dash", line_color=C["muted"],
                    line_width=1.5)
    fig1b.add_annotation(x="2023-03-13", y=0.96, yref="paper",
                         text="マスク緩和<br>masks relaxed" if lang == "en" else "マスク着用ルール緩和",
                         showarrow=False, xanchor="left", xshift=4,
                         font=dict(size=9, color=C["muted"]))
    fig1b.add_hline(y=100, line_dash="dot", line_color=C["border"], line_width=1.5,
                    annotation_text="2019 baseline = 100",
                    annotation_position="bottom right",
                    annotation_font=dict(size=9, color=C["muted"]))
    for term, (color, label) in MAKEUP_META.items():
        d = df_mk[df_mk["term"] == term].sort_values("week_start")
        fig1b.add_trace(go.Scatter(
            x=d["week_start"], y=d["smooth"], name=label, mode="lines",
            line=dict(color=color, width=2.5),
            hovertemplate="%{y:.0f}<extra>" + label + "</extra>"))
    fig1b.update_layout(**_base(height=380))
    fig1b.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.12,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(),
                        yaxis=_yax(title="Search interest, own 2019 = 100"))
    st.plotly_chart(fig1b, use_container_width=True)
    st.caption(S["t1_c4cap"])
    st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["cosm"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f1b_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f1b_body"]}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    # Chart 2 — Ingredient surge
    with col_left:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c2h"]}</h3><p class="expl">{S["t1_c2e"]}</p>', unsafe_allow_html=True)
        df_ing = load_ingredient_surge()
        df_ing_yr = (df_ing[df_ing["year"] <= 2026]
                     .groupby(["year", "term"])["interest"].mean().reset_index())
        ESTABLISHED = ["ヒアルロン酸", "セラミド"]  # レチナール excluded: +11.4pp post-COVID, not pre-established
        INGR_COLORS = {
            "ナイアシンアミド": "#2E7D32", "レチノール": "#1565C0",
            "グルタチオン": "#6A1B9A", "ビタミンC 美容": "#E65100",
            "トラネキサム酸": "#00695C", "アゼライン酸": "#AD1457",
            "エクソソーム": "#4E342E", "ヒアルロン酸": C["skin"],
            "セラミド": C["muted"], "レチナール": "#78909C",
        }
        all_terms = sorted(df_ing_yr["term"].unique().tolist())
        selected = st.multiselect(S["t1_ingr_sel"], options=all_terms,
                                   default=["ナイアシンアミド", "レチノール", "ヒアルロン酸", "アゼライン酸"],
                                   key="ingr_select")
        fig2 = go.Figure()
        fig2.add_vrect(x0=2019.8, x1=2021.2, fillcolor=C["grid"],
                       opacity=0.6, layer="below", line_width=0)
        for term in selected:
            d = df_ing_yr[df_ing_yr["term"] == term]
            fig2.add_trace(go.Scatter(
                x=d["year"], y=d["interest"].round(1), name=term,
                mode="lines+markers",
                line=dict(color=INGR_COLORS.get(term, C["muted"]), width=2,
                          dash="dot" if term in ESTABLISHED else "solid"),
                marker=dict(size=6),
                hovertemplate="%{y:.1f}<extra></extra>"))
        fig2.update_layout(**_base(height=380))
        fig2.update_layout(margin=dict(l=20, r=20, t=20, b=90),
                           legend=dict(orientation="h", yanchor="top", y=-0.2,
                                       xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                       font=dict(size=10)),
                           xaxis=_xax(dtick=1, range=[2018.8, 2026.2]),
                           yaxis=_yax(title="Avg search interest (0–100)"))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(S["t1_c2cap"])

    # Chart 3 — Rakuten treemap
    with col_right:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c3h"]}</h3><p class="expl">{S["t1_c3e"]}</p>', unsafe_allow_html=True)
        df_sku = load_sku_treemap()
        CAT_LABELS = {
            "korean_cosmetics": "Korean cosmetics", "cosmetics": "Cosmetics",
            "sun_protection": "Sun protection", "face_cream": "Face cream",
            "all_in_one": "All-in-one", "face_wash": "Face wash",
            "emulsion": "Emulsion", "serum_essence": "Serum / essence",
            "toner_lotion": "Toner / lotion", "skincare": "Skincare (general)",
        }
        df_sku["cat_display"] = df_sku["category"].map(lambda x: CAT_LABELS.get(x, x))
        df_sku["tier_display"] = df_sku["tier_group"].str.capitalize()

        LENS_OPTIONS = S["t1_lens_opts"]
        COLOR_SCALES = {"sku_count": "RdPu", "avg_reviews": "Blues",
                        "med_price": "Oranges", "avg_rating": "Greens"}
        HOVER_LABELS = {"sku_count": "SKUs", "avg_reviews": "Avg reviews/SKU",
                        "med_price": "Median price (¥)", "avg_rating": "Avg rating (rated SKUs)"}

        lens_label = st.radio(S["t1_lens"], options=list(LENS_OPTIONS.keys()),
                               horizontal=True, key="treemap_lens")
        color_col = LENS_OPTIONS[lens_label]
        hover_lbl = HOVER_LABELS[color_col]

        # Build customdata array: [avg_reviews, med_price, avg_rating, tier, rated_share]
        df_sku["_cval"] = df_sku[color_col]
        CELL_LABELS = {
            "sku_count": "SKUs", "avg_reviews": "rev/SKU avg",
            "med_price": "median price", "avg_rating": "avg rating",
        }
        CELL_FMT = {
            "sku_count": lambda v: f"{v:,.0f}",
            "avg_reviews": lambda v: f"{v:.1f}",
            "med_price": lambda v: f"¥{v:,.0f}",
            "avg_rating": lambda v: f"{v:.2f} ★",
        }

        # px.treemap single level — flat, butter zoom preserved
        df_sku["_color"] = df_sku[color_col]
        treemap_path = ["cat_display"]
        fig3 = px.treemap(
            df_sku,
            path=treemap_path,
            values="sku_count",
            color=color_col,
            color_continuous_scale=COLOR_SCALES[color_col],
            custom_data=["avg_reviews", "med_price", "avg_rating", "tier_group", "rated_share"],
        )
        fig3.update_traces(
            texttemplate="<b>%{label}</b><br>%{value:,} SKUs",
            textfont=dict(size=10),
            marker_line=dict(width=2, color=C["bg"]),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "SKUs: %{value:,}<br>"
                "Avg reviews/SKU: %{customdata[0]:.1f}<br>"
                "Median price: ¥%{customdata[1]:,.0f}<br>"
                "Avg rating: %{customdata[2]:.2f} / 5.0 "
                "(across the %{customdata[4]:.0%} of SKUs with ratings)"
                "<extra>%{customdata[3]}</extra>"
            ),
        )
        fig3.update_layout(**_base(height=420))
        fig3.update_layout(
            margin=dict(l=0, r=55, t=10, b=0),
            coloraxis_colorbar=dict(
                thickness=10, len=0.5,
                title=dict(text=hover_lbl, font=dict(size=9), side="right"),
                tickfont=dict(size=9),
            ),
        )
        rak_sel = st.plotly_chart(
            fig3, use_container_width=True,
            on_select="rerun", key="rak_treemap",
        )

        # Detail panel on click
        detail_placeholder = st.empty()
        if rak_sel and rak_sel.selection and rak_sel.selection.get("points"):
            pt  = rak_sel.selection["points"][0]
            lbl = pt.get("label", "")
            match = df_sku[df_sku["cat_display"] == lbl]
            if not match.empty:
                row = match.iloc[0]
                tc  = C["skin"] if row["tier_group"] == "skincare" else C["cosm"]
                with detail_placeholder.container():
                    detail_col, btn_col = st.columns([10, 1])
                    with detail_col:
                        st.markdown(f"""
                        <div style="background:{C['card']};border:1px solid {C['border']};
                                    border-left:4px solid {tc};border-radius:0 8px 8px 0;
                                    padding:12px 20px;display:flex;gap:32px;align-items:center;">
                            <div style="min-width:110px;">
                                <p style="margin:0;font-size:12px;font-weight:700;
                                          color:{C['text']};white-space:nowrap;">{lbl}</p>
                                <p style="margin:2px 0 0;font-size:11px;
                                          color:{C['muted']};">{row['tier_group'].capitalize()}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};">SKUs</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{int(row['sku_count']):,}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};white-space:nowrap;">Avg reviews / SKU</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{row['avg_reviews']:.1f}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};">Median price</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">¥{int(row['med_price']):,}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};white-space:nowrap;">Avg rating (rated SKUs)</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{row['avg_rating']:.2f} ★ · {row['rated_share']:.0%} rated</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with btn_col:
                        if st.button("✕", key="rak_clear"):
                            st.rerun()
        else:
            detail_placeholder.caption("Click any tile to see category detail")

        # Korean-cosmetics callout — computed from the same CSV as the treemap
        # (a previous hardcoded version drifted out of sync with the data)
        _kr = df_sku[df_sku["category"] == "korean_cosmetics"]
        if not _kr.empty:
            _kr = _kr.iloc[0]
            if lang == "en":
                _kr_txt = (f"  — {int(_kr['sku_count']):,} SKUs · "
                           f"{_kr['avg_reviews']:.0f} avg reviews/SKU · "
                           f"¥{int(_kr['med_price']):,} median price. "
                           f"Large shelf presence, thin consumer engagement.")
            else:
                _kr_txt = (f"  — {int(_kr['sku_count']):,} SKU · "
                           f"平均レビュー{_kr['avg_reviews']:.0f}件/SKU · "
                           f"価格中央値 ¥{int(_kr['med_price']):,}。"
                           f"棚の存在感は大きいが、消費者エンゲージメントは薄い。")
            st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:3px solid {C["korean"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:8px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">Korean cosmetics</span><span style="font-size:12px;color:{C["muted"]};">{_kr_txt}</span></div>', unsafe_allow_html=True)


    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # Chart 4 — YouTube comment volume
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c5h"]}</h3><p class="expl">{S["t1_c5e"]}</p>', unsafe_allow_html=True)

    try:
        df_yt_vol = load_yt_volume()
        df_yt_sk  = df_yt_vol[df_yt_vol["tier_group"] == "skincare"]
        df_yt_co  = df_yt_vol[df_yt_vol["tier_group"] == "cosmetics"]

        fig5 = go.Figure()
        fig5.add_vrect(x0=2019.6, x1=2021.4, fillcolor=C["grid"],
                       opacity=0.6, layer="below", line_width=0,
                       annotation_text="COVID", annotation_position="top left",
                       annotation_font=dict(size=10, color=C["muted"]))
        fig5.add_trace(go.Bar(
            x=df_yt_sk["comment_year"], y=df_yt_sk["n_comments"],
            name="Skincare", marker_color=C["skin"],
            hovertemplate="Skincare: %{y:,} comments<extra></extra>",
        ))
        fig5.add_trace(go.Bar(
            x=df_yt_co["comment_year"], y=df_yt_co["n_comments"],
            name="Cosmetics", marker_color=C["cosm"],
            hovertemplate="Cosmetics: %{y:,} comments<extra></extra>",
        ))
        fig5.update_layout(**_base(height=280))
        fig5.update_layout(
            barmode="group",
            margin=dict(l=20, r=20, t=20, b=60),
            legend=dict(orientation="h", yanchor="top", y=-0.24,
                        xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
            xaxis=_xax(dtick=1, tickformat="d"),
            yaxis=_yax(title="Comment count"),
        )
        st.plotly_chart(fig5, use_container_width=True)
        st.caption(S["t1_c5cap"])
    except FileNotFoundError:
        st.info("nb07_yt_volume.csv not found — run the NB07 YouTube export cells to generate it.", icon="ℹ️")

    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f1_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f1_body"]}</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — THE LANGUAGE
# ═══════════════════════════════════════════════════════════════════════════
with tab2:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t2_intro"]}</p>', unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────────────────────────────
    t1, t2, t3 = st.columns(3)
    with t1:
        kpi_card(S["t2_m1"], f"+{HEADLINE['conv_delta']}", S["t2_m1d"])
    with t2:
        kpi_card(S["t2_m2"], f"+{HEADLINE['conv_v1']}", S["t2_m2d"])
    with t3:
        kpi_card(S["t2_m3"], f"{HEADLINE['size_lo_cos']} → {HEADLINE['size_hi_cos']}", S["t2_m3d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Row 1: Word clouds + Cosine similarity heatmap ────────────────────
    col_wc, col_cos = st.columns([1, 1])

    with col_wc:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_wch"]}</h3><p class="expl">{S["t2_wce"]}</p>', unsafe_allow_html=True)

        year = st.pills(
            "Year",
            options=[2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
            default=2025,
            key="wc_year_slider",
        )
        if year is None:
            year = 2025

        wc_path = ASSETS / f"wordcloud_{year}.png"
        if wc_path.exists():
            from PIL import Image as PILImage
            img = PILImage.open(wc_path)
            st.image(img, use_container_width=True)
        else:
            st.caption(f"wordcloud_{year}.png not found")

        if year <= 2021:
            note_text = S["t2_wc_early"]
            note_color = C["cosm_lt"]
            note_border = C["cosm"]
        elif year == 2022:
            note_text = S["t2_wc_2022"]
            note_color = C["grid"]
            note_border = C["muted"]
        elif year == 2023:
            note_text = S["t2_wc_2023"]
            note_color = C["grid"]
            note_border = C["gold"]
        else:
            note_text = S["t2_wc_late"]
            note_color = C["skin_lt"]
            note_border = C["skin"]

        st.markdown(f'<div style="background:{note_color};border-left:3px solid {note_border};border-radius:0 6px 6px 0;padding:8px 12px;margin-top:8px;"><span style="font-size:12px;color:{C["text"]};">{note_text}</span></div>', unsafe_allow_html=True)

    with col_cos:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_curveh"]}</h3><p class="expl">{S["t2_curvee"]}</p>', unsafe_allow_html=True)

        df_curve = load_cosine_sizecurve()

        fig_cv = go.Figure()
        fig_cv.add_trace(go.Scatter(
            x=df_curve["sample_size"], y=df_curve["cross_tier_cosine"],
            mode="lines+markers",
            line=dict(color=C["cosm"], width=2.5),
            marker=dict(size=8, color=C["cosm"]),
            hovertemplate="N=%{x:,} reviews<br>cosine = %{y:.2f}<extra></extra>",
        ))
        # v1 rode the top of this curve; the size-matched value sits near the bottom
        fig_cv.add_hline(
            y=HEADLINE["v1_hi"], line_dash="dot", line_color=C["muted"],
            annotation_text=f"v1 reported {HEADLINE['v1_hi']:.2f}",
            annotation_position="top left",
            annotation_font=dict(size=9, color=C["muted"]),
        )
        fig_cv.add_hline(
            y=HEADLINE["conv_lo"], line_dash="dot", line_color=C["skin"],
            annotation_text=f"size-matched ≈ {HEADLINE['conv_lo']:.2f}",
            annotation_position="bottom left",
            annotation_font=dict(size=9, color=C["skin"]),
        )
        fig_cv.update_layout(**_base(height=380))
        fig_cv.update_layout(
            margin=dict(l=20, r=20, t=20, b=50),
            showlegend=False,
            xaxis=_xax(title=dict(text="Reviews per slice (subsample size)",
                                  font=dict(size=11))),
            yaxis=_yax(title="Skincare ↔ cosmetics cosine",
                       range=[0, max(0.8, HEADLINE["v1_hi"] + 0.08)]),
        )
        st.plotly_chart(fig_cv, use_container_width=True)

        st.markdown(f'<div style="background:{C["skin_lt"]};border-left:3px solid {C["skin"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">+{HEADLINE["conv_delta"]}</span><span style="font-size:12px;color:{C["muted"]};">  — {S["t2_curvenote"]}</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Finding 2 callout ─────────────────────────────────────────────────
    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f2_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f2_body"]}</p></div>', unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════
with tab3:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t3_intro"]}</p>', unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────────────────────────────
    d1, d2, d3 = st.columns(3)
    with d1:
        kpi_card(S["t3_m1"], "アヌア", S["t3_m1d"])
    with d2:
        kpi_card(S["t3_m2"], "レチノール", S["t3_m2d"])
    with d3:
        kpi_card(S["t3_m3"], f"{len(load_umap()):,} reviews", S["t3_m3d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Block C treemap ───────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_bch"]}</h3><p class="expl">{S["t3_bce"]}</p>', unsafe_allow_html=True)

    df_bc = load_blockc()

    window_choice = st.pills(
        "Window",
        options=[S["t3_win_r"], S["t3_win_c"]],
        default=S["t3_win_r"],
        key="blockc_window",
    )
    if window_choice is None:
        window_choice = "Recent (2023–2025)"

    window_key = "recent" if window_choice == S["t3_win_r"] else "covid"
    df_window = df_bc[df_bc["window"] == window_key].copy()
    df_window = df_window[df_window["metric"] > 0].sort_values(
        "metric", ascending=False
    ).head(20).reset_index(drop=True)

    # Grammar + signal display setup
    df_window["seed_label"] = df_window["seed_count"].apply(
        lambda n: f"{n} seed" if n == 1 else f"{n} seeds"
    )
    SIG_DISPLAY = {
        "korean_brand": S["t3_sig_kr"],
        "ingredient":   S["t3_sig_in"],
        "other":        S["t3_sig_ot"],
    }
    SIG_COLORS = {
        "korean_brand": C["korean"],
        "ingredient":   C["skin"],
        "other":        C["ingr"],
    }
    df_window["sig_display"] = df_window["signal_type"].map(SIG_DISPLAY).fillna("Other")
    df_window["color"] = df_window["signal_type"].map(SIG_COLORS).fillna(C["ingr"])

    # px.treemap single level — flat, butter zoom, colour by signal type
    df_window["_color_val"] = df_window["signal_type"].map({
        "korean_brand": 0,
        "ingredient":   1,
        "other":        2,
    }).fillna(2)

    fig_bc = px.treemap(
        df_window,
        path=["root"],
        values="metric",
        color="signal_type",
        color_discrete_map={
            "korean_brand": C["korean"],
            "ingredient":   C["skin"],
            "other":        C["ingr"],
        },
        custom_data=["metric", "seed_count", "sig_display", "seeds", "seed_label"],
    )
    fig_bc.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[4]}",
        textfont=dict(size=11),
        marker_line=dict(width=2, color=C["bg"]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Signal strength: %{customdata[0]:.3f}<br>"
            "Found via %{customdata[4]}<br>"
            "Type: %{customdata[2]}<br>"
            "Search entry points: %{customdata[3]}"
            "<extra></extra>"
        ),
    )
    fig_bc.update_layout(**_base(height=400))
    fig_bc.update_layout(margin=dict(l=0, r=0, t=10, b=0))

    bc_selection = st.plotly_chart(
        fig_bc,
        use_container_width=True,
        on_select="rerun",
        key="bc_treemap",
    )

    # Detail panel — auto-populates on click
    if (bc_selection and
        hasattr(bc_selection, "selection") and
        bc_selection.selection and
        bc_selection.selection.get("points")):

        pt = bc_selection.selection["points"][0]
        clicked_label = pt.get("label", "")
        match = df_window[df_window["root"] == clicked_label]

        if not match.empty:
            row = match.iloc[0]
            border_color = SIG_COLORS.get(row["signal_type"], C["ingr"])
            sig_label = SIG_DISPLAY.get(row["signal_type"], "Other")
            seed_word = "seed" if row["seed_count"] == 1 else "seeds"
            seeds_str = row.get("seeds", "—")

            st.markdown(f"""
            <div style="background:{C["card"]};
                        border:1px solid {C["border"]};
                        border-left:4px solid {border_color};
                        border-radius:0 8px 8px 0;
                        padding:16px 20px;margin-top:12px;">
                <div style="display:flex;align-items:baseline;gap:12px;">
                    <span style="font-size:18px;font-weight:700;color:{C["text"]};">
                        {row["root"]}
                    </span>
                    <span style="font-size:12px;color:{border_color};font-weight:600;">
                        {sig_label}
                    </span>
                </div>
                <div style="margin-top:8px;display:flex;gap:24px;">
                    <div>
                        <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                    letter-spacing:1px;">Signal strength</div>
                        <div style="font-size:13px;font-weight:700;color:{C["text"]};">
                            {row["metric"]:.3f}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                    letter-spacing:1px;">Seed queries</div>
                        <div style="font-size:13px;font-weight:700;color:{C["text"]};">
                            {row["seed_count"]} {seed_word}
                        </div>
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:4px;">Appears in searches for</div>
                    <div style="font-size:13px;color:{C["text"]};">
                        {seeds_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{C["grid"]};border-radius:8px;
                    padding:12px 20px;margin-top:12px;text-align:center;">
            <span style="font-size:12px;color:{C["muted"]};font-style:italic;">
                Click any tile to see detail
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Legend
    leg1, leg2, leg3, _ = st.columns([1, 1, 1, 3])
    with leg1:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["korean"]};"></div><span style="font-size:12px;color:{C["text"]};">Korean brands</span></div>', unsafe_allow_html=True)
    with leg2:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["skin"]};"></div><span style="font-size:12px;color:{C["text"]};">Ingredients</span></div>', unsafe_allow_html=True)
    with leg3:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["ingr"]};"></div><span style="font-size:12px;color:{C["text"]};">Other</span></div>', unsafe_allow_html=True)

    if window_key == "recent":
        st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["korean"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:12px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f4r_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f4r_body"]}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:12px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f4c_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f4c_body"]}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── YouTube content supply ─────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_ytch"]}</h3><p class="expl">{S["t3_ytche"]}</p>', unsafe_allow_html=True)

    TIER_COLOURS = {
        "skincare":  C["skin"],
        "cosmetics": C["cosm"],
        "korean":    C["korean"],
        "other":     C["muted"],
    }

    try:
        df_ch = load_yt_channels()

        # Aggregate by channel — primary tier = category with highest total_views
        df_agg = (df_ch.groupby("channel_name")
                  .agg(total_views=("total_views", "sum"),
                       video_count=("video_count", "sum"),
                       total_comments=("total_comments", "sum"))
                  .reset_index())
        primary = (df_ch.sort_values("total_views", ascending=False)
                   .groupby("channel_name").first()[["tier_group", "search_category"]]
                   .reset_index())
        df_agg = df_agg.merge(primary, on="channel_name")
        df_agg = df_agg.sort_values("total_views", ascending=True).tail(15).copy()
        df_agg["colour"]  = df_agg["tier_group"].map(TIER_COLOURS).fillna(C["muted"])
        df_agg["views_M"] = (df_agg["total_views"] / 1_000_000).round(1)

        fig_yt_ch = go.Figure()
        fig_yt_ch.add_trace(go.Bar(
            x=df_agg["total_views"],
            y=df_agg["channel_name"],
            orientation="h",
            marker_color=df_agg["colour"].tolist(),
            marker_line=dict(width=0),
            customdata=np.stack([
                df_agg["views_M"],
                df_agg["video_count"],
                df_agg["total_comments"],
                df_agg["search_category"],
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{customdata[0]:.1f}M views · "
                "%{customdata[1]:.0f} videos · "
                "%{customdata[2]:,.0f} comments<br>"
                "Category: %{customdata[3]}"
                "<extra></extra>"
            ),
        ))
        fig_yt_ch.update_layout(**_base(height=380))
        fig_yt_ch.update_layout(
            margin=dict(l=10, r=20, t=10, b=50),
            xaxis=dict(
                title=dict(text="Total views", font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"],
                zerolinecolor=C["border"], tickformat=".2s",
            ),
            yaxis=dict(
                autorange=True,
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_yt_ch, use_container_width=True)

        yt_leg1, yt_leg2, yt_leg3, _ = st.columns([1, 1, 1, 3])
        for col, (lbl, clr) in zip([yt_leg1, yt_leg2, yt_leg3],
                                    [(S["t3_umap_sk"], C["skin"]),
                                     (S["t3_umap_co"], C["cosm"]),
                                     ("Korean", C["korean"])]):
            with col:
                st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:2px;background:{clr};"></div><span style="font-size:12px;color:{C["text"]};">{lbl}</span></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:3px solid {C["korean"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:10px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{S["t3_ytgap"]}</span><span style="font-size:12px;color:{C["muted"]};">{S["t3_ytgapb"]}</span></div>', unsafe_allow_html=True)

    except FileNotFoundError:
        st.info("nb07_yt_channels.csv not found — run the NB07 YouTube export cells to generate it.", icon="ℹ️")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── YouTube TF-IDF — what are they actually saying? ───────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_yttfh"]}</h3><p class="expl">{S["t3_yttfe"]}</p>', unsafe_allow_html=True)

    try:
        df_yt_tfidf = load_yt_tfidf()

        # ── Diverging view: terms that distinguish registers ───────────────
        # Raw top-15 per tier is dominated by shared generic verbs (使う, 動画).
        # The insight is what differs between skincare and cosmetics YouTube.
        # Compute TF-IDF delta: skincare score minus cosmetics score per term.
        # Positive = skews skincare · Negative = skews cosmetics.
        sk_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "skincare"].set_index("term")["tfidf"]
        co_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "cosmetics"].set_index("term")["tfidf"]
        all_terms_yt = sk_tf.index.union(co_tf.index)
        df_div = pd.DataFrame({
            "skin": sk_tf.reindex(all_terms_yt, fill_value=0),
            "cosm": co_tf.reindex(all_terms_yt, fill_value=0),
        })
        df_div["delta"] = df_div["skin"] - df_div["cosm"]
        # Exclude generic Japanese verbs that appear in all YouTube comments
        # regardless of topic — these are not register-specific signals
        YT_EXCL = {'使う', '思う', 'する', 'なる', 'いる', 'ある', 'くれる', 'もらう'}
        df_div = df_div[~df_div.index.isin(YT_EXCL)]
        # Take top 12 each direction, exclude near-zero shared terms
        skin_terms = df_div[df_div["delta"] > 0].nlargest(12, "delta")
        cosm_terms = df_div[df_div["delta"] < 0].nsmallest(12, "delta")
        df_diverge = pd.concat([
            skin_terms.assign(label="skincare"),
            cosm_terms.assign(label="cosmetics"),
        ]).sort_values("delta")

        colors = [C["skin"] if r.label == "skincare" else C["cosm"]
                  for _, r in df_diverge.iterrows()]

        fig_yt_div = go.Figure()
        fig_yt_div.add_trace(go.Bar(
            x=df_diverge["delta"],
            y=df_diverge.index,
            orientation="h",
            marker_color=colors,
            marker_line=dict(width=0),
            customdata=np.stack([
                df_diverge["skin"].round(4),
                df_diverge["cosm"].round(4),
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Skincare TF-IDF: %{customdata[0]:.4f}<br>"
                "Cosmetics TF-IDF: %{customdata[1]:.4f}<br>"
                "Delta: %{x:+.4f}"
                "<extra></extra>"
            ),
        ))
        fig_yt_div.add_vline(x=0, line_color=C["border"], line_width=1.5)
        fig_yt_div.update_layout(**_base(height=420))
        fig_yt_div.update_layout(
            margin=dict(l=10, r=20, t=30, b=40),
            title=dict(
                text=S["t3_ytdivtitle"],
                font=dict(size=11, color=C["muted"]), x=0.5, xanchor="center",
            ),
            xaxis=dict(
                title=dict(text=S["t3_ytdivax"], font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"], zerolinecolor=C["border"],
            ),
            yaxis=dict(
                tickfont=dict(size=11),
                gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_yt_div, use_container_width=True)

        st.markdown(f'<div style="background:{C["grid"]};border-left:3px solid {C["muted"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{S["t3_ytreg"]}</span><span style="font-size:12px;color:{C["muted"]};">{S["t3_ytregb"]}</span></div>', unsafe_allow_html=True)

    except FileNotFoundError:
        st.info("nb07_yt_tfidf.csv not found — run NB06 Section 6 to generate it.", icon="ℹ️")

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── UMAP scatter ──────────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_umaph"]}</h3><p class="expl">{S["t3_umape"]}</p>', unsafe_allow_html=True)

    df_umap = load_umap()

    # Topic labels mapped from NB06 Cell 13
    TOPIC_LABELS = {
        "Skin T1": "Cleansing & face wash",
        "Skin T2": "Moisturising routine",
        "Skin T3": "Makeup (miscategorised)",
        "Skin T4": "Eye makeup & liner",
        "Skin T5": "Sun protection & base",
        "Cosm T1": "Foot care (noise)",
        "Cosm T2": "Foundation as skincare ★",
        "Cosm T3": "Eyebrow pencil",
        "Cosm T4": "Powder & colour",
    }
    df_umap["topic_label"] = df_umap["dominant_topic"].map(TOPIC_LABELS).fillna("Unknown")

    umap_col1, umap_col2 = st.columns([3, 1])

    with umap_col2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Year filter — reverse chronological
        year_filter = st.pills(
            S["t3_umap_yr"],
            options=["全" if lang=="jp" else "All", 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019],
            default="全" if lang=="jp" else "All",
            key="umap_year",
        )
        if year_filter is None:
            year_filter = "全" if lang == "jp" else "All"

        st.markdown(f"""
        <div style="margin-top:16px;">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                <div style="width:10px;height:10px;border-radius:50%;
                            background:{C['skin']};opacity:0.8;"></div>
                <span style="font-size:12px;color:{C['text']};">{S["t3_umap_sk"]}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:16px;">
                <div style="width:10px;height:10px;border-radius:50%;
                            background:{C['cosm']};opacity:0.8;"></div>
                <span style="font-size:12px;color:{C['text']};">{S["t3_umap_co"]}</span>
            </div>
            <p style="font-size:11px;color:{C['muted']};line-height:1.6;margin:0;">
                {S["t3_umap_note"].replace(chr(10), "<br><br>")}
            </p>
        </div>
        """, unsafe_allow_html=True)

        n_shown = len(df_umap) if year_filter in ("All", "全") else \
                  len(df_umap[df_umap.review_year == int(year_filter)])
        st.caption(f"{n_shown:,} reviews")

    with umap_col1:
        # Vocabulary centroid keywords — always visible regardless of year
        TOPIC_KEYWORDS = {
            "Cleansing & face wash":     "洗顔 · 洗い上がり · 毛穴",
            "Moisturising routine":      "香り · 乾燥 · 保湿 · 化粧水",
            "Makeup (miscategorised)":   "メイク · 描く · 発色",
            "Eye makeup & liner":        "アイライナー · ライン · コットン",
            "Sun protection & base":     "日焼け止め · トーンアップ · 下地",
            "Foot care (noise)":         "⚠ 靴下 · 暖かい",
            "Foundation as skincare ★": "乾燥 · しっとり · 毛穴 · ツヤ ★",
            "Eyebrow pencil":            "細い · 眉毛 · コスパ",
            "Powder & colour":           "パウダー · 香り · 発色",
        }
        TOPIC_ANNOT_COLORS = {
            "Cleansing & face wash":     "#4A90B8",
            "Moisturising routine":      "#5B8C6E",
            "Makeup (miscategorised)":   "#78909C",
            "Eye makeup & liner":        "#C4627A",
            "Sun protection & base":     "#B8965A",
            "Foot care (noise)":         "#B0BEC5",
            "Foundation as skincare ★": "#D4785C",
            "Eyebrow pencil":            "#9C4E8A",
            "Powder & colour":           "#C4627A",
        }

        # Filter by year only
        df_u = df_umap.copy()
        if year_filter not in ("All", "全"):
            df_u = df_u[df_u["review_year"] == int(year_filter)]

        fig_umap = go.Figure()

        # Plot Tier — skincare and cosmetics always coloured the same
        for tier, color, name in [
            ("skincare",  C["skin"], S["t3_umap_sk"]),
            ("cosmetics", C["cosm"], S["t3_umap_co"]),
        ]:
            d = df_u[df_u["tier_group"] == tier]
            if len(d) == 0:
                continue
            # Scattergl: 21k points render via WebGL — SVG Scatter is sluggish here
            fig_umap.add_trace(go.Scattergl(
                x=d["umap_x"], y=d["umap_y"],
                mode="markers", name=S["t3_umap_sk"] if tier=="skincare" else S["t3_umap_co"],
                marker=dict(color=color, size=3, opacity=0.5,
                            line=dict(width=0)),
                customdata=np.stack([
                    d["review_year"].astype(int),
                    d["topic_label"],
                ], axis=-1),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Year: %{customdata[0]}<br>"
                    "Topic: %{customdata[1]}"
                    "<extra></extra>"
                ),
            ))

        # Centroid annotations — fixed coordinates from NB06 corpus analysis
        # Positions computed from full corpus so labels stay stable across year filters
        # Standard topic centroids from corpus median positions
        for topic, kw in TOPIC_KEYWORDS.items():
            color = TOPIC_ANNOT_COLORS.get(topic, C["muted"])
            d_full = df_umap[df_umap["topic_label"] == topic]
            if len(d_full) < 10:
                continue
            cx = d_full["umap_x"].median()
            cy = d_full["umap_y"].median()
            fig_umap.add_annotation(
                x=cx, y=cy,
                text=f"<b>{kw}</b>",
                showarrow=False,
                font=dict(size=9.5, color=color, family="sans-serif"),
                bgcolor="rgba(255,255,255,0.82)",
                borderpad=3,
                bordercolor=color,
                borderwidth=1,
            )

        # ── Manual island annotations ─────────────────────────────────────
        # Top island: influencer/monitor reviews — template vocabulary
        fig_umap.add_annotation(
            x=-1.72, y=9.47,
            text="<b>⚠ インフルエンサー · モニター</b><br>organic consumer とは語彙が分離",
            showarrow=True, arrowhead=2, arrowcolor=C["gold"],
            ax=60, ay=30,
            font=dict(size=9, color=C["gold"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["gold"],
            borderwidth=1.5,
        )

        # Right satellite: tone-up SPF — cosmetic SPF sub-category
        fig_umap.add_annotation(
            x=8.60, y=2.38,
            text="<b>トーンアップ · ファンデ · 伸び</b><br>Tone-up SPF as base makeup",
            showarrow=True, arrowhead=2, arrowcolor=C["ingr"],
            ax=-70, ay=-30,
            font=dict(size=9, color=C["ingr"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["ingr"],
            borderwidth=1.5,
        )

        # Northeast convergence zone
        fig_umap.add_annotation(
            x=3.41, y=7.22,
            text="<b>保湿 · 洗顔 · 乾燥</b><br>★ 収束点 — vocabulary already merged",
            showarrow=True, arrowhead=2, arrowcolor=C["skin"],
            ax=-80, ay=20,
            font=dict(size=9, color=C["skin"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["skin"],
            borderwidth=1.5,
        )

        suffix = f" — {year_filter}" if year_filter not in ("All", "全") else " — all years"
        fig_umap.update_layout(**_base(height=520))
        fig_umap.update_layout(
            margin=dict(l=10, r=10, t=30, b=20),
            title=dict(
                text=f"UMAP embedding{suffix} · {n_shown:,} reviews",
                font=dict(size=12, color=C["muted"]),
                x=0,
            ),
            legend=dict(
                orientation="v", yanchor="top", y=1,
                xanchor="left", x=1.01,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=10),
            ),
            xaxis=dict(showgrid=False, showticklabels=False,
                       linecolor="rgba(0,0,0,0)", zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False,
                       linecolor="rgba(0,0,0,0)", zeroline=False),
        )
        st.plotly_chart(fig_umap, use_container_width=True)

    # Finding callout
    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f3_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f3_body"]}</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — FOR BRANDS
# ═══════════════════════════════════════════════════════════════════════════
with tab4:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t4_intro"]}</p>', unsafe_allow_html=True)

    def implication_card(title, body, accent):
        st.markdown(f"""
        <div style="background:{C['card']};border:1px solid {C['border']};
                    border-top:3px solid {accent};border-radius:8px;
                    padding:18px 20px;margin-bottom:16px;min-height:230px;">
            <p style="margin:0;font-size:14px;font-weight:700;color:{C['text']};">{title}</p>
            <p style="margin:10px 0 0 0;font-size:12.5px;color:{C['muted']};line-height:1.7;">{body}</p>
        </div>
        """, unsafe_allow_html=True)

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        implication_card(S["t4_c1h"], S["t4_c1b"], C["ingr"])
    with r1c2:
        implication_card(S["t4_c2h"], S["t4_c2b"], C["korean"])
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        implication_card(S["t4_c3h"], S["t4_c3b"], C["cosm"])
    with r2c2:
        implication_card(S["t4_c4h"], S["t4_c4b"], C["gold"])

    st.markdown(f'<div style="background:{C["grid"]};border-left:3px solid {C["muted"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["muted"]};font-style:italic;">{S["t4_note"]}</span></div>', unsafe_allow_html=True)