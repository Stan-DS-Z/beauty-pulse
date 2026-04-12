"""
Beauty Pulse — Japanese Beauty Market Analytics Dashboard
streamlit_app.py  ·  single file  ·  Streamlit Community Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
from pathlib import Path

st.set_page_config(
    page_title="Beauty Pulse · Japanese Beauty Market",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ASSETS  = Path(__file__).parent / "assets"
DB_PATH = ASSETS / "signal_pulse_public.db"

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
    """Compute headline metrics from DB + CSVs — single source of truth."""
    db = sqlite3.connect(str(DB_PATH), check_same_thread=False)

    # Review share by year
    df_slope = pd.read_csv(ASSETS / "nb07_review_slope.csv")
    skin = df_slope[df_slope["tier_group"] == "skincare"].set_index("review_year")["share_pct"]
    skin_2019 = round(skin.get(2019, 0), 1)
    skin_2025 = round(skin.get(2025, skin.iloc[-1]), 1)

    # COVID inflection — YoY skincare volume 2019→2020
    vol = df_slope.groupby("review_year")["review_count"].sum()
    covid_jump = round(100 * (vol.get(2020, 0) - vol.get(2019, 1)) / max(vol.get(2019, 1), 1), 1)

    # Rakuten SKU counts
    df_sku = pd.read_csv(ASSETS / "nb07_sku_treemap.csv")
    skin_skus = int(df_sku[df_sku["tier"] == "skincare"]["sku_count"].sum())
    cosm_skus = int(df_sku[df_sku["tier"] == "cosmetics"]["sku_count"].sum())
    sku_ratio = round(skin_skus / max(cosm_skus, 1), 1)

    # Google Trends crossover year
    df_tr = pd.read_csv(ASSETS / "nb07_trends_crossover.csv", parse_dates=["week_start"])
    df_tr["year"] = df_tr["week_start"].dt.year
    annual = df_tr.groupby(["year", "term"])["interest"].mean().unstack(fill_value=0)
    if "スキンケア" in annual.columns and "化粧品" in annual.columns:
        cross = annual[annual["スキンケア"] >= annual["化粧品"]].index
        crossover_year = int(cross[0]) if len(cross) else 2020
    else:
        crossover_year = 2020

    # Cosine similarity
    df_cos = pd.read_csv(ASSETS / "nb07_cosine_sim.csv", index_col=0)
    sk19 = [c for c in df_cos.index if "Skincare" in c and "2019" in c]
    cm19 = [c for c in df_cos.index if "Cosmetics" in c and "2019" in c]
    sk25 = [c for c in df_cos.index if "Skincare" in c and "2023" in c]
    cm25 = [c for c in df_cos.index if "Cosmetics" in c and "2023" in c]
    cosine_2019 = round(df_cos.loc[sk19[0], cm19[0]], 2) if sk19 and cm19 else 0.38
    cosine_2025 = round(df_cos.loc[sk25[0], cm25[0]], 2) if sk25 and cm25 else 0.81

    db.close()

    return {
        "skin_share_2019": skin_2019,
        "skin_share_2025": skin_2025,
        "covid_jump":      covid_jump,
        "sku_ratio":       sku_ratio,
        "crossover_year":  crossover_year,
        "skin_skus":       skin_skus,
        "cosm_skus":       cosm_skus,
        "cosine_2019":     cosine_2019,
        "cosine_2025":     cosine_2025,
    }

HEADLINE = compute_headline()
STRINGS = {
    "en": {
        "tagline":       "Japanese beauty market intelligence",
        "subtitle":      "@cosme reviews · Rakuten Ichiba · Google Trends JP · YouTube · 2019–2026 · 22,451 reviews · 31,202 SKUs",
        "tab1": "📈  The shift", "tab2": "🔤  The language", "tab3": "🔍  Discovery",

        # ── TAB 1: The Shift ──────────────────────────────────────────────
        "t1_intro":  "Five independent data sources all point in the same direction: since COVID, Japanese consumers have made skincare — not makeup — their top beauty priority. This wasn't a temporary pandemic effect. It's a permanent restructuring.",

        "t1_m1": "Skincare review share",
        "t1_m2": "COVID surge",              "t1_m2d": "skincare reviews jumped +152% in one year",
        "t1_m3": "Rakuten SKU ratio",
        "t1_m4": "Google Trends crossover",  "t1_m4d": "skincare overtakes cosmetics in search",

        "t1_c1h": "Search demand — スキンケア vs 化粧品",
        "t1_c1e": "How often do Japanese consumers search for \'skincare\' vs \'cosmetics\'? This chart tracks weekly Google search interest from 2019 to 2026. The crossover point — where skincare permanently overtakes cosmetics — is the structural shift made visible.",
        "t1_c2h": "Ingredient search surge",
        "t1_c2e": "Consumers aren\'t just searching for \'skincare\' — they\'re searching for specific ingredients by name. Each line tracks a single ingredient\'s search popularity over time. The explosion post-COVID shows consumers becoming educated about what goes into their products.",
        "t1_c2cap": "Dashed lines = ingredients already known pre-COVID  ·  Solid lines = ingredients that broke out after 2020",
        "t1_ingr_sel": "Select ingredients",
        "t1_c3h": "Rakuten catalog — what the market is actually selling",
        "t1_c3e": "Every rectangle is a product subcategory on Rakuten Ichiba (Japan\'s largest e-commerce platform). Size = number of products listed · colour = the lens you select below. This is what commercial supply looks like — and skincare dominates the shelf.",
        "t1_lens": "Colour by",
        "t1_lens_opts": {"Competition": "sku_count", "Engagement": "avg_reviews", "Price point": "avg_price", "Quality": "avg_rating"},
        "t1_c4h": "Review share by year — @cosme corpus",
        "t1_c4e": "What percentage of consumer reviews are about skincare vs cosmetics, year by year? This is the core evidence: skincare\'s share is structurally dominant. Note: 2019 has a thin sample (n=168) — the hollow markers flag this. The 2022 cosmetics bump was real (Japan lifted mask mandates) but temporary.",
        "t1_c5h": "YouTube beauty discourse — comment volume by year",
        "t1_c5e": "A fifth, independent confirmation: YouTube comment volumes on Japanese beauty videos, split by skincare vs cosmetics. This data comes from a completely separate platform — yet it tells the same story.",
        "t1_c5cap": "559 comments (2019) → 17,645 (2024) for skincare + cosmetics · 2022: cosmetics briefly edges skincare — the mask-off rebound is visible on a third platform · by 2024 skincare comment volume is 3× cosmetics",

        "f1_title": "Finding 1 — The structural shift is confirmed across five independent sources",
        "f1_body":  "Review corpus · search demand · commercial supply · ingredient search · YouTube discourse. The 2022 cosmetics rebound (+20pp) was temporary — by 2025 cosmetics retreated to 12.7%, their lowest share in the dataset. Five sources, same direction.",

        # ── TAB 2: The Language ───────────────────────────────────────────
        "t2_intro": "The shift isn\'t just visible in numbers — it\'s visible in the words consumers use. Six years of @cosme reviews show the vocabularies of skincare and cosmetics converging. Makeup products are increasingly evaluated by how they feel on skin, not how they look.",

        "t2_m1": "Vocabulary convergence",  "t2_m1d": "how much language skincare and cosmetics reviews share",
        "t2_m2": "2019 baseline",           "t2_m2d": "almost no shared vocabulary",
        "t2_m3": "マスカラ decline",         "t2_m3d": "−76% in review language 2019→2025",

        "t2_wch": "Consumer vocabulary by year",
        "t2_wce": "What words appear most frequently in beauty reviews each year? Larger words = used more often. Brand names and generic sentiment words have been removed so only product-relevant vocabulary remains.",
        "t2_wc_early": "2019–2021: makeup application vocabulary dominates — マスカラ (mascara), アイライナー (eyeliner), まつ毛 (eyelashes), ブラシ (brush)",
        "t2_wc_2022":  "2022: transition year — makeup terms fading, skincare terms beginning to appear",
        "t2_wc_2023":  "2023: inflection point — both vocabularies visible, functional terms gaining ground",
        "t2_wc_late":  "2024–2025: skincare vocabulary dominant — 乾燥 (dryness), 保湿 (moisture), 香り (scent), クリーム (cream), 洗顔 (face wash)",

        "t2_cosh": "Vocabulary convergence — how similar are skincare and cosmetics reviews?",
        "t2_cose": "This heatmap measures vocabulary overlap between skincare and cosmetics reviews across different time periods. 0 = completely different language · 1 = identical language · the key number: the cross-category similarity rose from 0.38 to 0.81 in six years.",
        "t2_cosnote": "Neither category absorbed the other. Both moved toward a shared functional vocabulary: 乾燥 (dryness), 保湿 (moisture), しっとり (moist texture), 毛穴 (pores).",

        "t2_tfidfh": "Vocabulary shift — which words rose and fell?",
        "t2_tfidfe": "Comparing which words became more or less important in beauty reviews from pre-COVID (≤2020) to recent (≥2023). Longer bars = bigger change. Left = rising terms (skincare language). Right = declining terms (makeup language).",
        "t2_rise": "↑ Rising — skincare and functional vocabulary",
        "t2_decl": "↓ Declining — makeup and visual vocabulary",
        "t2_tfidfcap": "Note: 化粧水 (toner) appearing as \'declining\' is a small-sample artefact — the 2019 corpus over-indexed on toner reviews. Google Trends does not confirm this decline.",

        "f2_title": "Finding 2 — Consumer vocabulary converged dramatically across six years",
        "f2_body":  "In 2019, skincare and cosmetics reviews shared just 38% of their top vocabulary. By 2023–25, that figure is 81%. The direction is clear: mascara (マスカラ) −76%, eyelashes (まつ毛) −86%, eyeliner (アイライナー) −71% — replaced by moisture (保湿) +409%, cream (クリーム) +3,101%, dryness (乾燥) +312%. Cosmetics are now evaluated through a skincare lens.",

        # ── TAB 3: Discovery ──────────────────────────────────────────────
        "t3_intro": "Two discovery engines reveal what\'s coming next. Google Trends surfaces what consumers are searching for before it appears in reviews — a leading indicator of demand. The review map below shows the spatial shape of consumer vocabulary, revealing where skincare and cosmetics language has already merged.",

        "t3_m1": "Strongest recent signal",  "t3_m1d": "Korean brand · across 4 independent search terms",
        "t3_m2": "COVID-era leader",          "t3_m2d": "ingredient · 5 search terms · consumers learning",
        "t3_m3": "Review corpus shape",       "t3_m3d": "78% form a continuum, not clusters",

        "t3_bch": "Search discovery — what are consumers searching for next?",
        "t3_bce": "Starting from 20+ beauty search terms (e.g. スキンケア, ナイアシンアミド, 口紅), Google identifies the fastest-accelerating related searches. When the same brand or ingredient appears across multiple independent starting points, that\'s a strong signal. Size = signal strength · colour = signal type.",
        "t3_win_r": "Recent (2023–2025)", "t3_win_c": "COVID era (2020–2021)",
        "t3_sig_kr": "Korean brand", "t3_sig_in": "Ingredient", "t3_sig_ot": "Other",

        "f4r_title": "Finding 4 — Korean brands are harvesting Japanese demand",
        "f4r_body":  "During COVID, ingredient searches dominated — consumers were building knowledge (retinol appeared across 5 independent search terms, niacinamide across 4). In the recent window, Anua (アヌア, a Korean brand) is the single strongest signal, appearing across 4 independent search terms. The structural shift educated consumers. Korean brands captured them.",
        "f4c_title": "COVID era — consumers were learning ingredients, not searching for brands",
        "f4c_body":  "During 2020–2021, Japanese consumers weren\'t searching for brands — they were learning ingredients. Retinol (レチノール), niacinamide (ナイアシンアミド), and ceramide (セラミド) dominated the fastest-rising searches across multiple starting points. This ingredient literacy is the knowledge foundation that Korean brands later capitalised on.",

        "t3_ytch":  "YouTube content supply — top channels by category",
        "t3_ytche": "The top 15 YouTube beauty channels by total views, coloured by whether they focus on skincare or cosmetics. Notice the gap: Korean beauty (韓国コスメ) generates massive search demand (Finding 4), but has very little YouTube content covering it.",
        "t3_ytgap":  "Content supply gap — ",
        "t3_ytgapb": "Korean beauty (韓国コスメ) generates the strongest search signal (アヌア across 4 search terms) but has only 9 videos and 2.9M views in our dataset. Meanwhile, かずのすけ (a science-focused beauty creator) dominates ingredient content with 25 videos and 15.6M views — confirming that ingredient education drives engagement. Korean brands have captured search and reviews; YouTube is still wide open.",

        "t3_yttfh": "YouTube comments — what are viewers actually saying?",
        "t3_yttfe": "The same text analysis applied to YouTube comments reveals a surprise: YouTube and @cosme are different conversations. Only 14 out of 30 top skincare terms overlap between the two platforms.",
        "t3_ytreg":  "Platform difference — ",
        "t3_ytregb": "動画 (video) · 参考 (reference) · 思う (think) dominate YouTube — viewers are commenting <em>on the video</em>, not reviewing a product. @cosme = product evaluation language (しっとり/moist texture · 毛穴/pores · 香り/scent). YouTube = social reaction language. These are two genuinely different conversations about the same products. <b>かずのすけ</b> appears as a top-3 skincare term on YouTube — more prominent than 化粧水 (toner).",
        "t3_ytdivtitle": "← Cosmetics YouTube language  ·  Skincare YouTube language →",
        "t3_ytdivax":    "How much more a term appears in skincare vs cosmetics comments",

        "t3_umaph": "Review map — the shape of consumer vocabulary",
        "t3_umape": "Every dot is one @cosme review, positioned by vocabulary similarity — reviews using similar words appear close together. This turns 14,727 reviews into a landscape you can explore. Colours: blue = skincare, rose = cosmetics.",
        "t3_umap_yr": "Filter by year",
        "t3_umap_sk": "Skincare", "t3_umap_co": "Cosmetics",
        "t3_umap_note": "Labels show the key vocabulary of each region.\n\nCompare 2019 vs 2025 — where rose (cosmetics) dots mix into blue (skincare) territory, consumer vocabulary has converged.",

        "f3_title": "Finding 3 — The review map reveals three hidden structures",
        "f3_body":  "The northeast cluster (★ 収束点) is where skincare and cosmetics vocabulary has already merged — foundation reviews written in skincare language, cleansing reviews evaluating moisture and texture. The 0.38→0.81 convergence, made spatial.<br><br>The isolated top island reveals something equally important: influencer and giveaway reviews separated automatically from organic consumer reviews — without being told to. Brands measuring sentiment without filtering these out are mixing two different signals. The tone-up SPF satellite (right) confirms SPF is not one category — functional sunscreen and cosmetic base makeup are different conversations.",
    },
    "jp": {
        "tagline":        "日本の美容市場インテリジェンス",
        "subtitle":       "@cosme · 楽天市場 · Google Trends JP · YouTube · 2019–2026 · 22,451件レビュー · 31,202 SKU",
        "tab1": "📈  市場変化", "tab2": "🔤  消費者の言語", "tab3": "🔍  発見",

        "t1_intro":  "5つの独立したデータソースがすべて同じ方向を指している。コロナ禍以降、日本の消費者はメイクアップではなくスキンケアを美容の最優先事項に据えた。これはパンデミック中の一時的な現象ではない。構造的かつ恒久的な変化である。",

        "t1_m1":     "スキンケアレビュー比率",
        "t1_m2":     "COVID後の急増",           "t1_m2d": "スキンケアレビューが1年で+152%",
        "t1_m3":     "楽天SKU比率",
        "t1_m4":     "Googleトレンド逆転",       "t1_m4d": "スキンケアが化粧品を逆転した年",

        "t1_c1h":    "検索需要 — スキンケア vs 化粧品",
        "t1_c1e":    "日本の消費者は「スキンケア」と「化粧品」をどれくらい検索しているか？\u3000 2019年から2026年までの週次Google検索関心度を追跡。スキンケアが化粧品を恒久的に上回った逆転点が、構造的変化の可視化である。",
        "t1_c2h":    "成分検索の急増",
        "t1_c2e":    "消費者は「スキンケア」だけでなく、成分名を指名検索している。各線は1つの成分の検索人気を経時的に追跡。コロナ後の急増は、消費者が自分の使う製品の中身について学び始めたことを示す。",
        "t1_c2cap":  "点線 = COVID前から認知されていた成分  ·  実線 = 2020年以降に急浮上した成分",
        "t1_ingr_sel": "成分を選択",
        "t1_c3h":    "楽天カタログ — 市場が実際に売っているもの",
        "t1_c3e":    "各長方形は楽天市場（日本最大のECプラットフォーム）のサブカテゴリ。サイズ = 商品掲載数 · 色 = 選択レンズ。商業的供給の実態であり、スキンケアが棚を支配している。",
        "t1_lens":   "色分け基準",
        "t1_lens_opts": {"競合状況": "sku_count", "エンゲージメント": "avg_reviews", "価格帯": "avg_price", "品質": "avg_rating"},
        "t1_c4h":    "年別レビュー比率 — @cosmeコーパス",
        "t1_c4e":    "スキンケアとコスメのレビュー比率は年ごとにどう変化したか？\u3000 これが中核的エビデンスである。2019年はサンプル数が少ない（n=168）ため、白抜きマーカーで示している。2022年のコスメ回復（マスク解禁効果）は実在したが一時的だった。",
        "t1_c5h":    "YouTube美容言論 — 年別コメント数",
        "t1_c5e":    "5つ目の独立した確認源：日本の美容動画に対するYouTubeコメント量をスキンケア対コスメで分割。完全に別のプラットフォームのデータが同じストーリーを語っている。",
        "t1_c5cap":  "559件（2019）→ 17,645件（2024）スキンケア＋コスメ · 2022年はコスメが一時逆転（マスク解禁効果が3つ目のプラットフォームでも可視化）· 2024年にはスキンケアがコスメの3倍超に加速",

        "f1_title":  "発見1 — 構造的変化は5つの独立したソースで確認された",
        "f1_body":   "レビューコーパス · 検索需要 · 商業的供給 · 成分検索 · YouTube言論。2022年のコスメ一時回復（+20pp）は一過性だった。2025年にはコスメがデータセット最低値の12.7%まで後退。5つのソース、同じ方向性。",

        "t2_intro":  "変化は数値だけでなく、消費者が実際に使う「言葉」にも現れている。6年間の@cosmeレビューを分析すると、スキンケアとコスメの語彙が融合しつつあることがわかる。メイクアップ製品が「見た目」ではなく「肌への感触」で評価されるようになった。",

        "t2_m1":     "語彙収束度",  "t2_m1d": "スキンケアとコスメのレビューがどれだけ同じ言葉を使っているか",
        "t2_m2":     "2019年ベースライン", "t2_m2d": "ほぼ共通語彙なし",
        "t2_m3":     "マスカラ低下", "t2_m3d": "レビュー語彙で−76%（2019→2025）",

        "t2_wch":    "年別消費者語彙",
        "t2_wce":    "美容レビューで各年に最も頻出する語彙は何か？\u3000 大きい語 = より頻繁に使用。ブランド名と汎用感情語は除外し、製品に関連する語彙のみを表示。",
        "t2_wc_early":  "2019–2021：メイクアップ語彙が支配的 — マスカラ、アイライナー、まつ毛、ブラシ",
        "t2_wc_2022":   "2022：過渡期 — メイク語彙の衰退とスキンケア語彙の台頭",
        "t2_wc_2023":   "2023：変曲点 — 両方の語彙が共存、機能的語彙が優勢に",
        "t2_wc_late":   "2024–2025：スキンケア語彙が支配的 — 乾燥、保湿、香り、クリーム、洗顔",

        "t2_cosh":   "語彙収束 — スキンケアとコスメのレビューはどれくらい似ているか？",
        "t2_cose":   "異なる時期のスキンケアとコスメのレビューの語彙重複度を測定。0 = まったく異なる言葉 · 1 = 同一の言葉 · 注目すべき数値：カテゴリ間類似度が6年間で0.38から0.81に上昇。",
        "t2_cosnote":"どちらかがもう一方を吸収したのではない。両者が共有の機能的語彙（乾燥、保湿、しっとり、毛穴）へと移行した。",

        "t2_tfidfh": "語彙シフト — どの言葉が増え、どの言葉が減ったか？",
        "t2_tfidfe": "美容レビューにおける各語の重要度がCOVID前（≤2020）から直近（≥2023）にかけてどう変化したかを比較。長いバー = 大きな変化。左 = 上昇語（スキンケア語彙）。右 = 下降語（メイク語彙）。",
        "t2_rise":   "↑ 上昇 — スキンケア・機能的語彙",
        "t2_decl":   "↓ 下降 — メイク・ビジュアル語彙",
        "t2_tfidfcap": "注：化粧水の「下降」は少数サンプルによる統計的偏り — 2019年コーパスがトナーレビューに偏重していた。Googleトレンドではこの下降は確認されていない。",

        "f2_title":  "発見2 — 消費者語彙は6年間で劇的に収束した",
        "f2_body":   "2019年、スキンケアとコスメのレビューは上位語彙の38%を共有していた。2023–25年には81%に上昇。方向性は明確：マスカラ −76%、まつ毛 −86%、アイライナー −71% — 代わりに保湿 +409%、クリーム +3,101%、乾燥 +312%が台頭。コスメはスキンケアの文脈で評価されるようになった。",

        "t3_intro":  "2つの発見エンジンが「次に来るもの」を明らかにする。Googleトレンドはレビューに現れる前に消費者が検索しているものを特定する先行指標。下のレビューマップは消費者語彙の空間的形状を示し、スキンケアとコスメの言葉がすでに融合している領域を可視化する。",

        "t3_m1":     "直近の最強シグナル", "t3_m1d": "韓国ブランド · 4つの独立した検索語で出現",
        "t3_m2":     "COVID期リーダー",    "t3_m2d": "成分 · 5つの検索語 · 消費者が学習していた時期",
        "t3_m3":     "レビューコーパスの形状",  "t3_m3d": "78%はクラスタではなく連続体を形成",

        "t3_bch":    "検索発見 — 消費者は次に何を検索しているか？",
        "t3_bce":    "20以上の美容検索語（スキンケア、ナイアシンアミド、口紅など）を起点に、Googleが最も急上昇する関連検索を抽出。同じブランドや成分が複数の異なる起点から浮上する場合、それは強いシグナルである。サイズ = シグナル強度 · 色 = シグナル種別。",
        "t3_win_r":  "直近（2023–2025）", "t3_win_c": "COVID期（2020–2021）",
        "t3_sig_kr": "韓国ブランド", "t3_sig_in": "成分", "t3_sig_ot": "その他",

        "f4r_title": "発見4 — 韓国ブランドが日本の需要を取り込んでいる",
        "f4r_body":  "COVID期は成分検索が支配的だった — 消費者が知識を蓄積していた（レチノールが5つの独立検索語で出現、ナイアシンアミドが4つ）。直近では、アヌア（韓国ブランド）が4つの独立した検索語に登場する最強シグナルとなっている。構造的変化が消費者を教育した。韓国ブランドがその恩恵を受けている。",
        "f4c_title": "COVID期 — 消費者はブランドではなく成分を学んでいた",
        "f4c_body":  "2020–2021年、日本の消費者はブランドを検索していたのではなく、成分を学んでいた。レチノール、ナイアシンアミド、セラミドが複数の起点から急上昇検索を独占した。この成分リテラシーこそ、後に韓国ブランドが活用する知識基盤となった。",

        "t3_ytch":   "YouTubeコンテンツ供給 — カテゴリ別トップチャンネル",
        "t3_ytche":  "総視聴数上位15チャンネルをスキンケア/コスメ別に表示。注目すべきギャップ：韓国コスメは検索需要が巨大（発見4）にもかかわらず、YouTubeコンテンツがほとんどない。",
        "t3_ytgap":  "コンテンツ供給ギャップ — ",
        "t3_ytgapb": "韓国コスメは最強の検索シグナル（アヌアが4つの検索語で出現）を生成しているが、YouTube動画はわずか9本・視聴数290万。一方、かずのすけ（科学系美容クリエイター）は25本・1,560万回視聴で成分コンテンツを支配しており、成分教育がエンゲージメントを駆動することを裏付ける。韓国ブランドは検索と@cosmeを掌握した。YouTubeはまだ開かれている。",

        "t3_yttfh":  "YouTubeコメント — 視聴者は実際に何を言っているのか？",
        "t3_yttfe":  "同じテキスト分析をYouTubeコメントに適用すると意外な発見がある。YouTubeと@cosmeは異なる会話空間である。スキンケア上位30語のうち、両プラットフォームで共通するのはわずか14語。",
        "t3_ytreg":  "プラットフォーム間の違い — ",
        "t3_ytregb": "動画・参考・思うがYouTubeの両リストを支配 — 視聴者は商品をレビューするのではなく、<em>動画に対して</em>コメントしている。@cosme = 商品評価言語（しっとり・毛穴・香り）。YouTube = 社会的反応言語。これらは同じ製品について語る2つの異なる会話空間。<b>かずのすけ</b>がスキンケア上位3語として登場 — 化粧水よりも上位。",
        "t3_ytdivtitle": "← コスメYouTube言語  ·  スキンケアYouTube言語 →",
        "t3_ytdivax":    "スキンケアのコメントでどれだけ多く登場するか（コスメとの差分）",

        "t3_umaph":  "レビューマップ — 消費者語彙の地形",
        "t3_umape":  "各点が@cosmeレビュー1件。似た語彙を使うレビューほど近くに配置される。14,727件のレビューを探索可能な地形図に変換。色：青 = スキンケア、ローズ = コスメ。",
        "t3_umap_yr":   "年でフィルタ",
        "t3_umap_sk":   "スキンケア", "t3_umap_co": "コスメ",
        "t3_umap_note": "ラベルは各領域の主要語彙を示す。\n\n2019年と2025年を比較 — コスメ（ローズ）の点がスキンケア（ブルー）領域に混在している箇所が、消費者語彙の収束点。",

        "f3_title":  "発見3 — レビューマップが3つの隠れた構造を明らかにする",
        "f3_body":   "北東クラスター（★ 収束点）はスキンケアとコスメの語彙がすでに融合した領域 — スキンケア言語で書かれたファンデーションレビュー、テクスチャーと保湿で評価するクレンジングレビュー。コサイン収束0.38→0.81の空間的表現。<br><br>上部の孤立アイランドは同等に重要な発見を示す：インフルエンサーやモニターレビューが、意図的に探索しなくてもオーガニック消費者レビューから自動的に分離された。この2つを分けずにセンチメント測定を行うブランドは、2種類のシグナルを混在させている。右側のトーンアップSPF衛星が第3の発見を確認：SPFは単一カテゴリではなく、機能的日焼け止めとコスメベースは異なる会話空間である。",
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

@st.cache_resource
def get_db():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

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
def load_cosine_sim():
    df = pd.read_csv(ASSETS / "nb07_cosine_sim.csv", index_col=0)
    return df

@st.cache_data
def load_yt_volume():
    return pd.read_csv(ASSETS / "nb07_yt_volume.csv")

@st.cache_data
def load_yt_channels():
    return pd.read_csv(ASSETS / "nb07_yt_channels.csv")

@st.cache_data
def load_yt_tfidf():
    return pd.read_csv(ASSETS / "nb07_yt_tfidf.csv")

st.markdown(f"""
<style>
.stApp {{ background-color:{C["bg"]}; }}
[data-testid="stToolbar"]    {{ display:none !important; }}
[data-testid="stDecoration"] {{ display:none !important; }}
[data-testid="stMetric"] {{
    background:{C["card"]}; border:1px solid {C["border"]};
    border-radius:10px; padding:14px 18px;
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

_hdr_left, _hdr_right = st.columns([12, 1])
with _hdr_right:
    _lang = st.radio("lang", ["EN", "JP"], horizontal=True,
                     label_visibility="collapsed", key="lang_toggle")
lang = "jp" if _lang == "JP" else "en"
S = STRINGS[lang]

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

tab1, tab2, tab3 = st.tabs([S["tab1"], S["tab2"], S["tab3"]])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1
# ═══════════════════════════════════════════════════════════════════════════
with tab1:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t1_intro"]}</p>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(S["t1_m1"], f"{HEADLINE['skin_share_2025']}%",
                  f"+{HEADLINE['skin_share_2025']-HEADLINE['skin_share_2019']:.1f}pp vs 2019" if lang=="en" else f"+{HEADLINE['skin_share_2025']-HEADLINE['skin_share_2019']:.1f}pp（2019年比）")
    with m2:
        st.metric(S["t1_m2"], f"+{HEADLINE['covid_jump']}%",
                  S["t1_m2d"])
    with m3:
        st.metric(S["t1_m3"], f"{HEADLINE['sku_ratio']}x",
                  f"{HEADLINE['skin_skus']:,} vs {HEADLINE['cosm_skus']:,} SKUs" if lang=="en" else f"{HEADLINE['skin_skus']:,} vs {HEADLINE['cosm_skus']:,} SKU")
    with m4:
        st.metric(S["t1_m4"], str(HEADLINE["crossover_year"]),
                  S["t1_m4d"])

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
    fig1.add_annotation(x="2020-06-01", y=72, text=f"Crossover: {HEADLINE['crossover_year']}",
                        showarrow=True, arrowhead=2, arrowcolor=C["gold"],
                        font=dict(size=11, color=C["gold"]), bgcolor=C["card"],
                        bordercolor=C["gold"], borderwidth=1, borderpad=4)
    fig1.update_layout(**_base(height=360))
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                       legend=dict(orientation="h", yanchor="top", y=-0.12,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(range=[date_range[0], date_range[1]]),
                       yaxis=_yax(title="Search interest (0–100)"))
    st.plotly_chart(fig1, use_container_width=True)

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
                        "avg_price": "Oranges", "avg_rating": "Greens"}
        HOVER_LABELS = {"sku_count": "SKUs", "avg_reviews": "Avg reviews/SKU",
                        "avg_price": "Avg price (¥)", "avg_rating": "Avg rating"}

        lens_label = st.radio(S["t1_lens"], options=list(LENS_OPTIONS.keys()),
                               horizontal=True, key="treemap_lens")
        color_col = LENS_OPTIONS[lens_label]
        hover_lbl = HOVER_LABELS[color_col]

        # Build customdata array: [avg_reviews, avg_price, avg_rating, color_val]
        # color_val at index 3 is used in texttemplate for cell display
        df_sku["_cval"] = df_sku[color_col]
        CELL_LABELS = {
            "sku_count": "SKUs", "avg_reviews": "rev/SKU avg",
            "avg_price": "avg price", "avg_rating": "avg rating",
        }
        CELL_FMT = {
            "sku_count": lambda v: f"{v:,.0f}",
            "avg_reviews": lambda v: f"{v:.1f}",
            "avg_price": lambda v: f"¥{v:,.0f}",
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
            custom_data=["avg_reviews", "avg_price", "avg_rating", "tier_group"],
        )
        fig3.update_traces(
            texttemplate="<b>%{label}</b><br>%{value:,} SKUs",
            textfont=dict(size=10),
            marker_line=dict(width=2, color=C["bg"]),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "SKUs: %{value:,}<br>"
                "Avg reviews/SKU: %{customdata[0]:.1f}<br>"
                "Avg price: ¥%{customdata[1]:,.0f}<br>"
                "Avg rating: %{customdata[2]:.2f} / 5.0"
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
                                <p style="margin:0;font-size:10px;color:{C['muted']};">Avg price</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">¥{int(row['avg_price']):,}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};">Avg rating</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{row['avg_rating']:.2f} ★</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with btn_col:
                        if st.button("✕", key="rak_clear"):
                            st.rerun()
        else:
            detail_placeholder.caption("Click any tile to see category detail")

        st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:3px solid {C["korean"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:8px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">Korean cosmetics</span><span style="font-size:12px;color:{C["muted"]};">  — 2,718 SKUs · 16 avg reviews · ¥2,989 avg price. Large shelf presence, thin consumer engagement.</span></div>', unsafe_allow_html=True)


    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # Chart 4 — Review slope
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c4h"]}</h3><p class="expl">{S["t1_c4e"]}</p>', unsafe_allow_html=True)
    df_slope = load_review_slope()
    df_skin  = df_slope[df_slope["tier_group"] == "skincare"]
    df_cosm  = df_slope[df_slope["tier_group"] == "cosmetics"]
    fig4 = go.Figure()
    fig4.add_vrect(x0=2019.8, x1=2021.2, fillcolor=C["grid"], opacity=0.6,
                   layer="below", line_width=0, annotation_text="COVID",
                   annotation_position="top left",
                   annotation_font=dict(size=10, color=C["muted"]))
    # Marker arrays — hollow for 2019 (thin sample), filled for rest
    skin_symbols = ['circle-open' if y == 2019 else 'circle' for y in df_skin["review_year"]]
    cosm_symbols = ['circle-open' if y == 2019 else 'circle' for y in df_cosm["review_year"]]
    skin_opacity = [0.4 if y == 2019 else 1.0 for y in df_skin["review_year"]]
    cosm_opacity = [0.4 if y == 2019 else 1.0 for y in df_cosm["review_year"]]

    fig4.add_trace(go.Scatter(x=df_skin["review_year"], y=df_skin["share_pct"],
                               name="Skincare", mode="lines+markers",
                               line=dict(color=C["skin"], width=3),
                               marker=dict(size=10, symbol=skin_symbols,
                                           opacity=skin_opacity,
                                           line=dict(width=2, color=C["skin"])),
                               hovertemplate="Skincare: %{y:.1f}%<extra></extra>"))
    fig4.add_trace(go.Scatter(x=df_cosm["review_year"], y=df_cosm["share_pct"],
                               name="Cosmetics", mode="lines+markers",
                               line=dict(color=C["cosm"], width=3),
                               marker=dict(size=10, symbol=cosm_symbols,
                                           opacity=cosm_opacity,
                                           line=dict(width=2, color=C["cosm"])),
                               hovertemplate="Cosmetics: %{y:.1f}%<extra></extra>"))
    fig4.add_annotation(x=2019,
                        y=float(df_skin[df_skin.review_year==2019]["share_pct"].values[0]),
                        text="2019: thin sample<br>(n=168)", showarrow=True,
                        arrowhead=2, ax=50, ay=-40,
                        font=dict(size=10, color=C["muted"]), bgcolor=C["card"], borderpad=3)
    fig4.add_annotation(x=2022,
                        y=float(df_cosm[df_cosm.review_year==2022]["share_pct"].values[0]),
                        text="Mask-off rebound", showarrow=True,
                        arrowhead=2, ax=60, ay=30,
                        font=dict(size=10, color=C["cosm"]), bgcolor=C["card"], borderpad=3)
    fig4.update_layout(**_base(height=320))
    fig4.update_layout(margin=dict(l=20, r=20, t=20, b=60),
                       legend=dict(orientation="h", yanchor="top", y=-0.18,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(dtick=1, tickformat="d"),
                       yaxis=_yax(title="Review share (%)", suffix="%", range=[0, 100]))
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Chart 5 — YouTube comment volume
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
        st.metric(S["t2_m1"], f"{HEADLINE['cosine_2025']}",
                  S["t2_m1d"])
    with t2:
        st.metric(S["t2_m2"], f"{HEADLINE['cosine_2019']}",
                  S["t2_m2d"])
    with t3:
        st.metric(S["t2_m3"], "−76%",
                  S["t2_m3d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Row 1: Word clouds + Cosine similarity heatmap ────────────────────
    col_wc, col_cos = st.columns([1, 1])

    with col_wc:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_wch"]}</h3><p class="expl">{S["t2_wce"]}</p>', unsafe_allow_html=True)

        year = st.pills(
            "Year",
            options=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
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
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_cosh"]}</h3><p class="expl">{S["t2_cose"]}</p>', unsafe_allow_html=True)

        df_sim = load_cosine_sim()

        # Reorder for better visual — skincare rows first, cosmetics rows second
        ordered = [c for c in df_sim.index if 'Skincare' in c] + \
                  [c for c in df_sim.index if 'Cosmetics' in c]
        df_plot = df_sim.loc[ordered, ordered]

        # Short labels for axis
        SHORT = {
            'Skincare 2019':     'SK 2019',
            'Skincare 2020':     'SK 2020',
            'Skincare 2021–22':  'SK 21–22',
            'Skincare 2023–25':  'SK 23–25',
            'Cosmetics 2019':    'CM 2019',
            'Cosmetics 2020':    'CM 2020',
            'Cosmetics 2021–22': 'CM 21–22',
            'Cosmetics 2023–25': 'CM 23–25',
        }
        short_labels = [SHORT.get(l, l) for l in ordered]

        z    = df_plot.values
        text = [[f"{v:.2f}" for v in row] for row in z]

        fig_cos = go.Figure(go.Heatmap(
            z=z,
            x=short_labels,
            y=short_labels,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11, color="white"),
            colorscale=[
                [0.0, "#F5DDE3"],
                [0.4, "#C4627A"],
                [0.6, "#4A90B8"],
                [1.0, "#1A3A5C"],
            ],
            zmin=0.2, zmax=1.0,
            showscale=True,
            colorbar=dict(
                thickness=10, len=0.8,
                title=dict(text="similarity", font=dict(size=9), side="right"),
                tickfont=dict(size=9),
            ),
            hovertemplate=(
                "<b>%{y}</b> ↔ <b>%{x}</b><br>"
                "Cosine similarity: %{text}"
                "<extra></extra>"
            ),
        ))

        # Divider line between skincare and cosmetics blocks
        fig_cos.add_shape(
            type="line",
            x0=-0.5, x1=3.5, y0=3.5, y1=3.5,
            line=dict(color="white", width=3),
        )
        fig_cos.add_shape(
            type="line",
            x0=3.5, x1=3.5, y0=-0.5, y1=7.5,
            line=dict(color="white", width=3),
        )

        fig_cos.update_layout(**_base(height=380))
        fig_cos.update_layout(
            margin=dict(l=70, r=40, t=20, b=70),
            xaxis=dict(
                side="bottom",
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_cos, use_container_width=True)

        st.markdown(f'<div style="background:{C["skin_lt"]};border-left:3px solid {C["skin"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">0.38 → 0.81</span><span style="font-size:12px;color:{C["muted"]};">  — {S["t2_cosnote"]}</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Row 2: TF-IDF emerging / declining — live Plotly ─────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_tfidfh"]}</h3><p class="expl">{S["t2_tfidfe"]}</p>', unsafe_allow_html=True)

    df_tfidf = load_tfidf_delta()

    # Filter to clean content terms — exclude filler bigrams and politeness verbs
    TFIDF_EXCLUDE = {
            'プレゼント', 'タイプ', 'すぐ', '今まで', 'すごい', '使う みる',
        }
    df_tfidf = df_tfidf[~df_tfidf['term'].isin(TFIDF_EXCLUDE)]

    rising_df   = df_tfidf.sort_values('delta', ascending=False).head(15)
    declining_df = df_tfidf.sort_values('delta', ascending=True).head(15)

    col_r, col_d = st.columns(2)

    with col_r:
        st.markdown(f'<p style="font-size:13px;font-weight:600;color:{C["skin"]};margin-bottom:4px;">{S["t2_rise"]}</p>', unsafe_allow_html=True)

        fig_rise = go.Figure()
        fig_rise.add_trace(go.Bar(
            x=rising_df['delta'],
            y=rising_df['term'],
            orientation='h',
            marker=dict(
                color=rising_df['delta'],
                colorscale=[[0, C["skin_lt"]], [1, C["skin"]]],
                showscale=False,
                line=dict(width=0),
            ),
            customdata=np.stack([
                rising_df['pre_mean'].round(4),
                rising_df['post_mean'].round(4),
                rising_df['pct_change'].round(1),
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Delta: +%{x:.4f}<br>"
                "Pre-COVID: %{customdata[0]:.4f}<br>"
                "Recent: %{customdata[1]:.4f}<br>"
                "Change: +%{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        ))
        fig_rise.update_layout(**_base(height=380))
        fig_rise.update_layout(
            margin=dict(l=10, r=20, t=10, b=40),
            xaxis=dict(
                title=dict(text="TF-IDF weight delta", font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"],
                zerolinecolor=C["border"],
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=11),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_rise, use_container_width=True)

    with col_d:
        st.markdown(f'<p style="font-size:13px;font-weight:600;color:{C["cosm"]};margin-bottom:4px;">{S["t2_decl"]}</p>', unsafe_allow_html=True)

        fig_decl = go.Figure()
        fig_decl.add_trace(go.Bar(
            x=declining_df['delta'],
            y=declining_df['term'],
            orientation='h',
            marker=dict(
                color=declining_df['delta'],
                colorscale=[[0, C["cosm"]], [1, C["cosm_lt"]]],
                showscale=False,
                line=dict(width=0),
            ),
            customdata=np.stack([
                declining_df['pre_mean'].round(4),
                declining_df['post_mean'].round(4),
                declining_df['pct_change'].round(1),
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Delta: %{x:.4f}<br>"
                "Pre-COVID: %{customdata[0]:.4f}<br>"
                "Recent: %{customdata[1]:.4f}<br>"
                "Change: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        ))
        fig_decl.update_layout(**_base(height=380))
        fig_decl.update_layout(
            margin=dict(l=10, r=20, t=10, b=40),
            xaxis=dict(
                title=dict(text="TF-IDF weight delta", font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"],
                zerolinecolor=C["border"],
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=11),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_decl, use_container_width=True)

    st.caption(S["t2_tfidfcap"])

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
        st.metric(S["t3_m1"], "アヌア",
                  S["t3_m1d"])
    with d2:
        st.metric(S["t3_m2"], "レチノール",
                  S["t3_m2d"])
    with d3:
        st.metric(S["t3_m3"], "14,727 reviews",
                  S["t3_m3d"])

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
            options=["全" if lang=="jp" else "All", 2025, 2024, 2023, 2022, 2021, 2020, 2019],
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
            fig_umap.add_trace(go.Scatter(
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