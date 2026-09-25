"""Beauty Pulse copy: the EN/JA string table and the figures rebuilt into it.

build_strings() returns the table for one language with every figure-bearing
entry filled from the headline and launch dicts. Imports no UI framework.
"""

from .data import (LAUNCH_GATE, load_ingredient_surge, load_makeup_rebound,
                   load_trends_crossover)

STRINGS = {
    "en": {
        "tagline":       "Japanese beauty market analytics",
        "subtitle":      "@cosme · Rakuten Ichiba · Google Trends JP · YouTube · 2019–2026 · 45,510 reviews · 39,436 SKUs",
        "tab1": "📈  The shift", "tab2": "🔤  The language", "tab3": "🔍  Discovery",

        # ── TAB 1: The Shift ──────────────────────────────────────────────
        "t1_intro":  "",

        "t1_m1": "Cosmetics search",  "t1_m1d": "化粧品 search interest, full years 2019→2025 (anchored Google Trends)",
        "t1_m2": "Niacinamide search",   "t1_m2d": "",
        "t1_m3": "Rakuten SKU ratio",
        "t1_m4": "Makeup shipped value",  "t1_m4d": "",

        "t1_c1h": "Cosmetics search fell by about a third and stayed above skincare search in every year",
        "t1_c1e": "Monthly Google search interest, {tr_years} ({tr_part}). Both terms come from one anchored query and share one scale. 化粧品 search fell steadily; スキンケア search held roughly flat. 化粧品 is the Japanese umbrella term and includes skincare.",
        "t1_c2h": "",
        "t1_c2e": "Search interest for individual skincare ingredients. Each line is indexed to its own peak.",
        "t1_c2cap": "Dotted = ingredients with steady search before 2020  ·  solid = ingredients whose search rose after 2020  ·  {tr_part}",
        "t1_ingr_sel": "Select ingredients",
        # Rebuilt live from HEADLINE below. A figure left here is dead code if
        # the rebuild covers it and a silent contradiction if it does not;
        # empty means a missing rebuild shows up as a blank heading.
        "t1_c3h": "",
        "t1_c3e": "Each rectangle is a Rakuten Ichiba subcategory. Size = products listed · colour = the measure selected below. Ratings average rated SKUs only; price is the median.",
        "t1_lens": "Colour by",
        "t1_lens_opts": {"Reviews per SKU": "avg_reviews", "SKU count": "sku_count", "Median price": "med_price", "Average rating": "avg_rating"},

        "t1_c4h": "In 2025, two years after mask guidance was relaxed, lipstick search was 36% of its 2019 level",
        "t1_c4e": "Monthly search interest for three makeup terms, each indexed to its own peak. Japan relaxed mask guidance on 13 March 2023. Lipstick and foundation search rose in 2023 and fell in 2024–2025; lipstick search in 2025 was below its 2021 low. Eyeshadow search rose while masks were worn and fell below its 2019 level after the guidance changed.",
        "t1_c4cap": "Monthly search interest, each term indexed to its own peak · grey band = COVID state of emergency · dashed line = mask guidance relaxed (13 March 2023) · {tr_part}",
        "f1b_title": "Lipstick, foundation and eyeshadow search all stayed below 2019 after March 2023",
        "f1b_body":  "Annual average, each term's 2019 = 100: lipstick 100 → 42 (2021) → 53 (2023) → 36 (2025). Foundation 100 → 77 → 86 → 69. Eyeshadow 100 → 128 (2022) → 80 (2025). None of the three returned to 100 after mask guidance was relaxed.",

        "t1_c5h": "YouTube comments on skincare videos outnumbered cosmetics comments in every year except 2022",
        "t1_c5e": "Comments per year on Japanese beauty videos, by video category.",
        "t1_c5cap": "2022: cosmetics {c22:,} comments, skincare {s22:,}  ·  2024: skincare {s24:,}, cosmetics {c24:,}",

        # ── TAB 1 · market layer (METI 生産動態統計 + 財務省 貿易統計) ──────
        "t1_p1": "Attention: search, listings, reviews and comments",
        "t1_p1d": "Google Trends, Rakuten listings, @cosme reviews and YouTube comments, collected for this project.",
        "t1_p2": "Market: shipped value in yen",
        "t1_p2d": "",
        "t1_p3": "Search and shipped value, category by category",
        "t1_p3d": "Six categories measured both ways, each change measured on one side of the January 2022 break.",

        "t1_mkh": "Shipped value by group, with the January 2022 break marked",
        "t1_mke": "",
        "t1_mkcap": "",
        "t1_brkh": "化粧水, 美容液 and 乳液 yen per kg fell 21–35% from 2021 to 2022",
        "t1_brkb": "",
        "t1_brkfnh": "About the January 2022 break",
        "t1_brkfn": "",
        "t1_dvh": "Search interest and shipped value, measured within each period",
        "t1_dve": "",
        "t1_dv_pre": "Before the break",
        "t1_dv_post": "After the break",
        "t1_dv_att": "Search interest",
        "t1_dv_val": "Shipped value",

        "f1_title": "",
        "f1_body": "",

        # ── TAB 2: The Language ───────────────────────────────────────────
        "t2_intro": "",

        "t2_m1": "Vocabulary convergence",  "t2_m1d": "change in size-matched cosine similarity · 95% CI excludes 0",
        "t2_m2": "Size-matched cosine",     "t2_m2d": "",
        "t2_m3": "Sample-size effect",       "t2_m3d": "same reviews: cosine rises as N grows from 150 to 6,000",

        "t2_wch": "Most frequent review words by year",
        "t2_wce": "Word size = frequency in that year's @cosme reviews. Brand names and generic sentiment words are removed.",
        "t2_wc_early": "2019–2021: マスカラ (mascara), アイライナー (eyeliner), まつ毛 (eyelashes) and ブラシ (brush) are among the largest words",
        "t2_wc_2022":  "2022: makeup and skincare words both appear among the largest",
        "t2_wc_2023":  "2023: skincare words take more of the largest positions",
        "t2_wc_late":  "2024–2026: 乾燥 (dryness), 保湿 (moisture), 香り (scent), クリーム (cream) and 洗顔 (face wash) are among the largest words · 2026: reviews to mid-year",

        "t2_curveh": "Cosine similarity rises with sample size alone",
        # t2_m2d / t2_curvee / t2_curvenote / f2_body carry live figures and are
        # rebuilt from HEADLINE in the _h block below. Empty here on purpose: a
        # missing rebuild then fails visibly instead of shipping a stale number.
        "t2_curvee": "",
        "t2_curvenote": "",

        "f2_title": "Finding 2 — Review vocabulary converged slightly",
        "f2_body": "",

        # ── TAB 3: Discovery ──────────────────────────────────────────────
        "t3_intro": "Product-launch releases on PR TIMES, rising Google searches in two periods, the largest YouTube beauty channels and their comments, and a map of @cosme reviews placed by vocabulary.",
        # Launch panel. Figure-bearing strings are empty here and rebuilt from LAUNCH.
        "t3_lp": "Product launches", "t3_lpd": "",
        "t3_l1h": "", "t3_l1e": "", "t3_l1ax": "Launch releases, 12-month total",
        "t3_l2h": "", "t3_l2e": "",
        "t3_l3h": "", "t3_l3e": "",
        "t3_l4h": "", "t3_l4e": "",
        "t3_l5h": "Launch share and search interest, by ingredient", "t3_l5e": "",
        "t3_l5ax1": "Share of launch releases", "t3_l5ax2": "Search interest (0–100)",
        "t3_l5y1": "Launch share", "t3_l5y2": "Search (0–100)",
        "t3_lcap": "",
        "t3_lempty": "Launch export not found: dashboard/assets/prtimes_launches.csv.",
        "t3_lg_skincare": "Skincare", "t3_lg_makeup": "Makeup",
        "t3_lg_other": "Hair, body and fragrance", "t3_lg_none": "No category word",
        "t3_lpan_core": "Core issuers", "t3_lpan_pf": "Issuers with history from after Sep 2021",
        "t3_lwin_l12": "12 months to ", "t3_lwin_p12": "12 months before",
        "t3_p2": "Search, video and reviews",
        "t3_p2d": "Google Trends rising related searches, YouTube beauty channels and their comments, and @cosme reviews.",

        "t3_m1": "Top rising search, 2023–2025",  "t3_m1d": "Korean brand · surfaced from 6 seed terms",
        "t3_m2": "Top rising search, 2020–2021",  "t3_m2d": "ingredient · surfaced from 5 seed terms",
        "t3_m3": "Review map",                    "t3_m3d": "~69% of reviews fall in one central cluster",

        "t3_bch": "Fastest-rising related searches, 2020–2021 and 2023–2025",
        "t3_bce": "Rising related searches pulled from 20+ beauty seed terms (e.g. スキンケア, ナイアシンアミド, 口紅). Size = mean normalised rising score × number of seed terms a result surfaced from · colour = type. Brand origins are checked against official sources; unlabel, CERAMIAID and KITEN are Japanese brands.",
        "t3_win_r": "Recent (2023–2025)", "t3_win_c": "COVID era (2020–2021)",
        "t3_sig_kr": "Korean brand", "t3_sig_in": "Ingredient", "t3_sig_ot": "Other",

        "f4r_title": "Finding 4 — Anua, a Korean brand, surfaced from more seed terms than any other brand in 2023–2025",
        "f4r_body":  "2023–2025: Anua (アヌア) surfaced from 6 seed terms. 2020–2021: retinol surfaced from 5 and niacinamide from 4.",
        "f4c_title": "2020–2021: ingredient names led the fastest-rising searches",
        "f4c_body":  "Retinol (レチノール), niacinamide (ナイアシンアミド) and ceramide (セラミド) ranked highest among rising searches across seed terms in 2020–2021.",

        "t3_ytch":  "Top 15 YouTube beauty channels by total views",
        "t3_ytche": "Colour = skincare or cosmetics focus.",
        "t3_ytgap":  "Korean beauty on YouTube — ",
        "t3_ytgapb": "韓国コスメ: 16 videos and 4.4M views in this dataset. かずのすけ, a chemistry-focused creator: 71 videos and 43.4M views of ingredient content.",

        "t3_yttfh": "YouTube commenters write about the video; @cosme reviewers write about the product",
        "t3_yttfe": "15 of the top 30 skincare terms appear on both platforms.",
        "t3_ytreg":  "Top terms by platform — ",
        "t3_ytregb": "YouTube: 動画 (video), 参考 (reference), 思う (think). @cosme: しっとり (moist), 毛穴 (pores), 香り (scent). The creator name <b>かずのすけ</b> ranks among the top skincare comment terms.",
        "t3_ytdivtitle": "← More frequent in cosmetics comments  ·  More frequent in skincare comments →",
        "t3_ytdivax":    "Term frequency, skincare comments minus cosmetics comments",

        "t3_umaph": "Review map: @cosme reviews placed by vocabulary similarity",
        "t3_umape": "Each dot is one review; reviews with similar words are placed closer together. Blue = skincare, rose = cosmetics.",
        "t3_umap_yr": "Filter by year",
        "t3_umap_sk": "Skincare", "t3_umap_co": "Cosmetics",
        "t3_umap_note": "Labels show each region's most frequent words.\n\nSelect 2019 and 2025 to compare where rose (cosmetics) dots overlap blue (skincare) regions.",

        "f3_title": "Finding 3 — Giveaway reviews form a separate cluster on the review map",
        "f3_body":  "Northeast region: foundation reviews using skincare words, and cleansing reviews rated on moisture and texture.<br><br>Top cluster: influencer and giveaway reviews written with 「プレゼント」/「当選」 template phrases, placed apart from all other reviews. Sentiment measured on unfiltered @cosme data includes both groups.",

    },
    "jp": {
        "tagline":        "日本の美容市場分析",
        "subtitle":       "@cosme · 楽天市場 · Google Trends JP · YouTube · 2019–2026 · 45,510件レビュー · 39,436 SKU",
        "tab1": "📈  市場変化", "tab2": "🔤  消費者の言語", "tab3": "🔍  発見",

        "t1_intro":  "",

        "t1_m1":     "化粧品の検索",  "t1_m1d": "化粧品の検索関心度、暦年ベース2019→2025年（アンカー付きトレンド）",
        "t1_m2":     "ナイアシンアミドの検索",  "t1_m2d": "",
        "t1_m3":     "楽天SKU比率",
        "t1_m4":     "メイク出荷金額",  "t1_m4d": "",

        "t1_c1h":    "化粧品の検索は約3分の1低下し、全ての年でスキンケアの検索を上回った",
        "t1_c1e":    "{tr_years}年の月次Google検索関心度（{tr_part}）。両語は同一のアンカー付きクエリから取得しており、共通のスケールを持つ。化粧品の検索は着実に低下し、スキンケアはほぼ横ばい。「化粧品」はスキンケアを含む上位語である。",
        "t1_c2h": "",
        "t1_c2e":    "スキンケア成分ごとの検索関心度。各線は自身のピークを基準に指数化している。",
        "t1_c2cap":  "点線 = 2020年以前から検索が安定していた成分  ·  実線 = 2020年以降に検索が上昇した成分  ·  {tr_part}",
        "t1_ingr_sel": "成分を選択",
        "t1_c3h":    "",   # rebuilt live from HEADLINE below
        "t1_c3e":    "各長方形は楽天市場のサブカテゴリ。サイズ = 掲載商品数 · 色 = 下で選択した指標。評価は評価のあるSKUのみの平均、価格は中央値。",
        "t1_lens":   "色分け基準",
        "t1_lens_opts": {"SKUあたりレビュー数": "avg_reviews", "SKU数": "sku_count", "価格中央値": "med_price", "平均評価": "avg_rating"},

        "t1_c4h":    "マスク着用ルール緩和から2年後の2025年、口紅の検索は2019年の36%",
        "t1_c4e":    "メイク3語の月次検索関心度。各語は自身のピークを基準に指数化。日本は2023年3月13日にマスク着用ルールを緩和した。口紅とファンデーションの検索は2023年に上昇し、2024〜2025年に低下した。2025年の口紅検索は2021年の底を下回る。アイシャドウの検索はマスク着用期に上昇し、緩和後は2019年水準を下回った。",
        "t1_c4cap":  "月次検索関心度、各語は自身のピークを基準に指数化 · グレー帯 = 緊急事態宣言期 · 破線 = マスク着用ルール緩和（2023年3月13日） · {tr_part}",
        "f1b_title": "口紅・ファンデーション・アイシャドウの検索は、2023年3月以降いずれも2019年を下回る",
        "f1b_body":  "各語の2019年を100とした年平均：口紅 100 → 42（2021年）→ 53（2023年）→ 36（2025年）。ファンデーション 100 → 77 → 86 → 69。アイシャドウ 100 → 128（2022年）→ 80（2025年）。マスク着用ルール緩和後、3語とも100に戻っていない。",

        "t1_c5h":    "YouTubeのスキンケア動画へのコメント数は、2022年を除く全ての年でコスメ動画を上回った",
        "t1_c5e":    "日本の美容動画への年別コメント数、動画カテゴリ別。",
        "t1_c5cap":  "2022年：コスメ{c22:,}件、スキンケア{s22:,}件  ·  2024年：スキンケア{s24:,}件、コスメ{c24:,}件",

        # ── TAB 1 · 市場レイヤー（経産省 生産動態統計 + 財務省 貿易統計）──
        "t1_p1":  "関心：検索・掲載・レビュー・コメント",
        "t1_p1d": "Googleトレンド、楽天の掲載、@cosmeレビュー、YouTubeコメント。本プロジェクトで収集したデータ。",
        "t1_p2":  "市場：出荷金額",
        "t1_p2d": "",
        "t1_p3":  "品目別の検索と出荷金額",
        "t1_p3d": "6カテゴリを二つの尺度で測り、各変化は2022年1月の断層の片側で測っている。",

        "t1_mkh":   "区分別の出荷金額と2022年1月の断層",
        "t1_mke":   "",
        "t1_mkcap": "",
        "t1_brkh":  "化粧水・美容液・乳液のkg単価は2021年から2022年に21〜35%下落",
        "t1_brkb":  "",
        "t1_brkfnh": "2022年1月の断層について",
        "t1_brkfn": "",
        "t1_dvh":   "検索関心度と出荷金額、各区間の内側で測定",
        "t1_dve":   "",
        "t1_dv_pre":  "断層前",
        "t1_dv_post": "断層後",
        "t1_dv_att":  "検索関心度",
        "t1_dv_val":  "出荷金額",

        "f1_title":  "",
        "f1_body": "",

        "t2_intro":  "",

        "t2_m1":     "語彙収束",  "t2_m1d": "サイズを揃えたコサイン類似度の変化 · 95%CIはゼロを含まない",
        "t2_m2":     "サイズを揃えたコサイン", "t2_m2d": "",
        "t2_m3":     "サンプルサイズ効果", "t2_m3d": "同一データ：Nが150→6,000と増えるとコサインが上昇",

        "t2_wch":    "年別のレビュー頻出語",
        "t2_wce":    "語の大きさ = その年の@cosmeレビューでの出現頻度。ブランド名と汎用的な感情語は除外。",
        "t2_wc_early":  "2019–2021：マスカラ、アイライナー、まつ毛、ブラシが上位に入る",
        "t2_wc_2022":   "2022：メイクとスキンケアの語が共に上位に入る",
        "t2_wc_2023":   "2023：上位に占めるスキンケアの語が増える",
        "t2_wc_late":   "2024–2026：乾燥、保湿、香り、クリーム、洗顔が上位に入る · 2026年は年央までのレビュー",

        "t2_curveh": "コサイン類似度はサンプル数だけで上昇する",
        # t2_m2d / t2_curvee / t2_curvenote / f2_body carry live figures and are
        # rebuilt from HEADLINE in the _h block below. Empty here on purpose: a
        # missing rebuild then fails visibly instead of shipping a stale number.
        "t2_curvee": "",
        "t2_curvenote": "",

        "f2_title":  "発見2 — レビュー語彙はわずかに収束した",
        "f2_body": "",

        "t3_intro":  "PR TIMESの新商品リリース、2期間の急上昇Google検索、美容YouTubeの上位チャンネルとそのコメント、語彙で配置した@cosmeレビューのマップ。",
        "t3_lp": "新商品リリース", "t3_lpd": "",
        "t3_l1h": "", "t3_l1e": "", "t3_l1ax": "新商品リリース件数、12カ月合計",
        "t3_l2h": "", "t3_l2e": "",
        "t3_l3h": "", "t3_l3e": "",
        "t3_l4h": "", "t3_l4e": "",
        "t3_l5h": "成分別の新商品リリース比率と検索関心", "t3_l5e": "",
        "t3_l5ax1": "新商品リリースに占める比率", "t3_l5ax2": "検索関心（0–100）",
        "t3_l5y1": "リリース比率", "t3_l5y2": "検索（0–100）",
        "t3_lcap": "",
        "t3_lempty": "新商品リリースのデータが見つからない：dashboard/assets/prtimes_launches.csv",
        "t3_lg_skincare": "スキンケア", "t3_lg_makeup": "メイク",
        "t3_lg_other": "ヘア・ボディ・フレグランス", "t3_lg_none": "カテゴリ語なし",
        "t3_lpan_core": "コア発行元", "t3_lpan_pf": "履歴が2021年9月より後に始まる発行元",
        "t3_lwin_l12": "直近12カ月 〜", "t3_lwin_p12": "前年同期12カ月",
        "t3_p2": "検索・動画・レビュー",
        "t3_p2d": "Googleトレンドの急上昇関連検索、美容YouTubeのチャンネルとコメント、@cosmeレビュー。",

        "t3_m1":     "急上昇検索1位（2023–2025）", "t3_m1d": "韓国ブランド · 6つの起点語から出現",
        "t3_m2":     "急上昇検索1位（2020–2021）", "t3_m2d": "成分 · 5つの起点語から出現",
        "t3_m3":     "レビューマップ",  "t3_m3d": "レビューの約69%が中央の一つのクラスタに入る",

        "t3_bch":    "急上昇した関連検索、2020–2021年と2023–2025年",
        "t3_bce":    "20以上の美容起点語（スキンケア、ナイアシンアミド、口紅など）から急上昇関連検索を取得。サイズ = 正規化した急上昇スコアの平均 × その結果が出現した起点語の数 · 色 = 種別。ブランドの原産国は公式情報で確認しており、アンレーベル・セラミエイド・キテンは日本ブランド。",
        "t3_win_r":  "直近（2023–2025）", "t3_win_c": "コロナ期（2020–2021）",
        "t3_sig_kr": "韓国ブランド", "t3_sig_in": "成分", "t3_sig_ot": "その他",

        "f4r_title": "発見4 — 2023〜2025年、韓国ブランドのアヌアはブランド別で最多の起点語から出現した",
        "f4r_body":  "2023〜2025年：アヌアは6つの起点語から出現。2020〜2021年：レチノールは5つ、ナイアシンアミドは4つ。",
        "f4c_title": "2020〜2021年：急上昇検索の上位は成分名",
        "f4c_body":  "2020〜2021年、レチノール、ナイアシンアミド、セラミドが複数の起点語で急上昇検索の上位に入った。",

        "t3_ytch":   "総視聴数上位15の美容YouTubeチャンネル",
        "t3_ytche":  "色 = スキンケア／コスメのどちらを主に扱うか。",
        "t3_ytgap":  "YouTube上の韓国コスメ — ",
        "t3_ytgapb": "韓国コスメ：本データセットで16本・440万回視聴。化学系クリエイターのかずのすけ：成分コンテンツ71本・4,340万回視聴。",

        "t3_yttfh":  "YouTubeのコメントは動画について、@cosmeのレビューは商品について書かれている",
        "t3_yttfe":  "スキンケア上位30語のうち、両プラットフォームに共通するのは15語。",
        "t3_ytreg":  "プラットフォーム別の上位語 — ",
        "t3_ytregb": "YouTube：動画・参考・思う。@cosme：しっとり・毛穴・香り。クリエイター名<b>かずのすけ</b>がスキンケアコメントの上位語に入る。",
        "t3_ytdivtitle": "← コスメのコメントで多い  ·  スキンケアのコメントで多い →",
        "t3_ytdivax":    "語の出現頻度、スキンケアのコメント − コスメのコメント",

        "t3_umaph":  "レビューマップ：語彙の類似度で配置した@cosmeレビュー",
        "t3_umape":  "各点がレビュー1件。似た語を使うレビューほど近くに配置される。青 = スキンケア、ローズ = コスメ。",
        "t3_umap_yr":   "年でフィルタ",
        "t3_umap_sk":   "スキンケア", "t3_umap_co": "コスメ",
        "t3_umap_note": "ラベルは各領域の頻出語。\n\n2019年と2025年を選び、コスメ（ローズ）の点がスキンケア（青）の領域と重なる位置を比較できる。",

        "f3_title":  "発見3 — モニター・プレゼント当選レビューはレビューマップ上で別のクラスタを形成する",
        "f3_body":   "北東の領域：スキンケアの語で書かれたファンデーションのレビューと、保湿と質感で評価されたクレンジングのレビュー。<br><br>上部のクラスタ：「プレゼント」「当選」の定型句で書かれたインフルエンサー・モニターレビューで、他の全てのレビューから離れて配置される。未フィルタの@cosmeデータで測ったセンチメントは両方の集団を含む。",

    },
}


_MON_EN = [None, "January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"]


# ── Launch copy is rebuilt from LAUNCH ────────────────────────────────────
# Canonical category keys (config/launch_terms.xlsx) → display names.
LAUNCH_CAT = {
    "cleansing": ("Cleansing", "クレンジング"), "face_wash": ("Face wash", "洗顔料"),
    "toner_lotion": ("Toner", "化粧水"), "booster": ("Booster", "導入美容液"),
    "serum": ("Serum", "美容液"), "emulsion": ("Emulsion", "乳液"),
    "eye_cream": ("Eye cream", "アイクリーム"), "cream": ("Cream", "クリーム"),
    "mask": ("Mask", "パック"), "all_in_one": ("All-in-one", "オールインワン"),
    "sunscreen": ("Sunscreen", "日焼け止め"), "base_makeup": ("Base makeup", "化粧下地"),
    "foundation": ("Foundation", "ファンデーション"), "concealer": ("Concealer", "コンシーラー"),
    "powder": ("Powder", "パウダー"), "lipstick": ("Lipstick", "口紅"),
    "lip_balm": ("Lip balm", "リップクリーム"), "blush": ("Blush", "チーク"),
    "eye_makeup": ("Eye makeup", "アイメイク"), "lash_brow": ("Lash and brow", "まつ毛・眉"),
    "nail": ("Nail", "ネイル"), "hair": ("Hair", "ヘア"),
    "fragrance": ("Fragrance", "フレグランス"), "body": ("Body", "ボディ"),
}


def _li(lang):
    return 0 if lang == "en" else 1


def _ym(ym, lang):
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{_MON_EN[m]} {y}" if lang == "en" else f"{y}年{m}月"


def _ing_label(canon, lang, _L):
    t = _L["terms"].set_index("canonical")
    return t.loc[canon, "label_short_en" if lang == "en" else "label_ja"]


def _trends_span(df, lang):
    """A Trends asset's span of years, and the months its last year covers."""
    y0, last = df["week_start"].min().year, df["week_start"].max()
    y1, m = last.year, last.month
    if lang == "en":
        return f"{y0}–{y1}", f"{y1}: January" + ("" if m == 1 else f"–{_MON_EN[m]}")
    return f"{y0}〜{y1}", f"{y1}年は1" + ("" if m == 1 else f"〜{m}") + "月"


def build_strings(lang, HEADLINE, LAUNCH, ASSETS):
    """STRINGS[lang] with the live figures written in."""
    S = dict(STRINGS[lang])
    # The Trends pull runs into the current year; each caption names the months
    # its own chart's asset covers.
    _cr_years, _cr_part = _trends_span(load_trends_crossover(ASSETS), lang)
    S["t1_c1e"] = S["t1_c1e"].format(tr_years=_cr_years, tr_part=_cr_part)
    S["t1_c2cap"] = S["t1_c2cap"].format(tr_part=_trends_span(load_ingredient_surge(ASSETS), lang)[1])
    S["t1_c4cap"] = S["t1_c4cap"].format(tr_part=_trends_span(load_makeup_rebound(ASSETS), lang)[1])
    # ── Convergence copy is rebuilt from live figures ─────────────────────────
    # These numbers recompute whenever NB06 re-runs (corpus growth, re-scrape),
    # so the prose is generated from HEADLINE rather than hardcoded — it can never
    # drift out of sync with the KPI cards or the size-curve chart.
    _h = HEADLINE
    if lang == "en":
        S["t2_intro"] = (
            f"Measured at equal sample sizes, skincare and cosmetics reviews shared more vocabulary "
            f"in {_h['conv_p1']} than in {_h['conv_p0']}.")
        S["t2_m2d"] = f"each period set to {_h['matched_n']} reviews · {_h['conv_ci']}"
        S["t1_m2d"] = f"Trends index, annual mean, {_h['ing_y0']} vs {_h['ing_y1']}"
        S["t1_m3"] = "Rakuten SKU ratio (relabelled)"
        S["t1_c3h"] = (
            f"Rakuten lists {_h['sku_measured']}× more skincare SKUs than makeup SKUs "
            f"after relabelling the Korean-cosmetics genre")
        S["t1_c3e"] = (
            f"Both makeup-side genres were sampled at 150 products each and labelled by hand. "
            f"The Korean-cosmetics genre, tagged as makeup, is 49% skincare, 36% makeup and "
            f"15% other, and is 62% of the makeup total. The base-makeup genre is 75% makeup "
            f"and 24% other, mostly lash-extension and double-eyelid products. Relabelling "
            f"both gives {_h['sku_measured']}× (95% CI {_h['sku_lo']}–{_h['sku_hi']}); the "
            f"original tags give {_h['sku_span_lo']}×; genres whose names fix the product type "
            f"give {_h['sku_span_hi']}×. " + S["t1_c3e"])
        S["t1_c2h"] = (
            f"Niacinamide search rose from {_h['nia_pre']} to {_h['nia_post']} on the Trends "
            f"index, {_h['ing_y0']}→{_h['ing_y1']}")
        S["f1_title"] = "Finding 1 — Makeup fell in search and in shipped value; skincare shipped value steps down in 2022"
        S["t1_intro"] = (
            "After 2020, Japanese beauty search, Rakuten listings, @cosme reviews and YouTube comments "
            "moved toward skincare. METI shipment statistics record the makeup side in yen: foundation "
            f"shipped value fell {abs(_h['found_d'])}% and lipstick {abs(_h['lip_d'])}% from "
            f"{_h['mkt_y0']} to {_h['mkt_y1']}. METI's skincare lines step down in January "
            f"{_h['mkt_break']}, and serum shipped value falls when measured across that step and rises "
            f"when measured after it. January–{_MON_EN[_h['ytd_m']]} {_h['ytd_y']} against the same "
            f"months of {_h['ytd_y'] - 1}: skincare {_h['ytd_skin']:+}%, makeup {_h['ytd_make']:+}%.")
        S["t1_mkcap"] = (
            f"Monthly, January 2019 – {_MON_EN[_h['ytd_m']]} {_h['ytd_y']} · shaded from January "
            f"{_h['mkt_break']} = after the break · skincare peaks in December in 2021–2024 and October "
            "in 2025; makeup peaks in November in six of seven years")
        S["t1_brkfn"] = (
            "METI's 生産動態統計 collects monthly shipments from cosmetics manufacturers: yen value, "
            "units and kilograms for each product line. Yen divided by kilograms gives an average price "
            "per kg. For 化粧水, 美容液 and 乳液 that price drops at January 2022. 化粧水 and 美容液 stay "
            f"below their 2015–2021 range through {_MON_EN[_h['ytd_m']]} {_h['ytd_y']}; 乳液 was inside "
            "its range in 2024 and below it in 2025. Comparing January 2022 with January 2021, shipped "
            "value fell 38% for 化粧水 (116 → 72 億円), 34% for 美容液 (102 → 67 億円) and 40% for 乳液 "
            "(53 → 32 億円), while モイスチャークリーム rose 6% and ファンデーション 18%. 口紅 and "
            "アイメークアップ yen per kg also fall in 2022, with a different pattern: their kilograms rose "
            "149% and 44% while shipped value rose 49% and 11%. A change in which companies or products "
            "are counted would produce the skincare pattern; METI has published no such change and no "
            "link coefficients for cosmetics. A skincare yen comparison between a year before 2022 and a "
            f"year after includes the drop, so skincare yen changes on this tab are measured within "
            f"2019–2021 or within 2022–{_h['mkt_y1']}. {_h['ytd_y']} figures come from METI's monthly "
            "確報 release.")
        S["f1_body"] = (
            f"Google Trends: 化粧品 search fell ~{abs(_h['cosm_decline'])}% over full years "
            f"{_h['ing_y0']}→{_h['ing_y1']}, and スキンケア search held roughly flat. Rakuten lists "
            f"{_h['sku_measured']}× more skincare SKUs than makeup SKUs. Niacinamide search rose from "
            f"{_h['nia_pre']} to {_h['nia_post']}. Lipstick, foundation and eyeshadow search stayed "
            "below 2019 after mask guidance was relaxed."
            f"<br><br>METI shipments: foundation shipped value fell {abs(_h['found_d'])}% and lipstick "
            f"{abs(_h['lip_d'])}% from {_h['mkt_y0']} to {_h['mkt_y1']}. Most of the fall came in "
            f"{_h['mkt_y0']}→{_h['mkt_pre1']} ({_h['found_d_pre']}% and {_h['lip_d_pre']}%), in lines "
            f"without the {_h['mkt_break']} step; from {_h['mkt_break']} to {_h['mkt_y1']} they rose "
            f"+{_h['found_d_post']}% and +{_h['lip_d_post']}%. Toner, serum and emulsion yen per kg "
            f"step down in January {_h['mkt_break']}, and METI publishes no reason. Serum shipped "
            f"value changes {_h['serum_val_span']}% across the step and +{_h['serum_val_post']}% after it."
            f"<br><br>January–{_MON_EN[_h['ytd_m']]} {_h['ytd_y']} against the same months of "
            f"{_h['ytd_y'] - 1}: skincare shipped value {_h['ytd_skin']:+}%, makeup {_h['ytd_make']:+}%, "
            f"all cosmetics {_h['ytd_total']:+}%.")
        S["t1_m4d"] = (
            f"foundation {_h['found_d']}%, lipstick {_h['lip_d']}%, {_h['mkt_y0']}→{_h['mkt_y1']} · "
            "METI shipments")
        S["t1_dve"] = (
            "Change in search interest and in shipped value for six categories named in both "
            f"datasets, each measured within one period. {_h['mkt_y0']}→{_h['mkt_pre1']}: foundation "
            f"and lipstick fell on both measures. {_h['mkt_break']}→{_h['mkt_y1']}: foundation and "
            "lipstick search fell while their shipped value rose. Serum search rose in both periods "
            f"(+{_h['serum_att_span']}% over {_h['mkt_y0']}→{_h['mkt_y1']}); serum shipped value fell "
            "before the break and rose after it. Eye makeup is METI's アイメークアップ line, paired "
            "with アイシャドウ search.")
        S["t1_c1e"] += (f" Skincare-to-cosmetics search ratio, full years {_h['ing_y0']}→{_h['ing_y1']}: "
                        f"{_h['ratio_0']} → {_h['ratio_1']}.")
        S["t1_p2d"] = (
            f"経済産業省生産動態統計, shipped value in 億円, {_h['mkt_y0']}–{_h['mkt_y1']}. Of the "
            f"{_h['mkt_total_y1']:,} 億円 shipped in {_h['mkt_y1']}, skincare was {_h['skin_share_y1']}% "
            f"and makeup {_h['make_share_y1']}%. Imports (財務省 貿易統計, HS 3304) were "
            f"{_h['imp_share_y1']}% of the market in {_h['mkt_y1']}: {_h['imp_y0']:,} 億円 in "
            f"{_h['mkt_y0']}, {_h['imp_peak']:,} 億円 at the {_h['imp_peak_y']} peak, {_h['imp_y1']:,} 億円 "
            f"in {_h['mkt_y1']}. January–{_MON_EN[_h['ytd_m']]} {_h['ytd_y']} against the same months of "
            f"{_h['ytd_y'] - 1}: skincare {_h['ytd_skin']:+}%, makeup {_h['ytd_make']:+}%, total "
            f"{_h['ytd_total']:+}% (monthly 確報).")
        S["t1_mke"] = (
            "Shipped value for skincare (皮膚用) and makeup (仕上用), summed from METI's 33 component "
            "product lines. The grouping reproduces METI's 計 subtotals for 2019 and 2020 and JCIA's "
            f"published 2024 shares. The vertical line marks January {_h['mkt_break']}.")
        S["t1_brkb"] = (
            "化粧水 yen per kg ranged 6,787–7,824 in every year from 2015 to 2021, fell to 5,256 in "
            "2022, and was 5,967 in 2025 and 6,686 in January–July 2026. 美容液 ranged 32,563–42,781, "
            "fell to 23,874, and was 28,933 in 2025. 乳液 ranged 9,347–12,233, fell to 7,426, was "
            "9,523 in 2024 and 9,049 in 2025. 口紅 and アイメークアップ yen per kg fell 40% and 23% in "
            "2022 as their kilograms rose 149% and 44%. In "
            "2022 美容液 shipped 2% more kilograms while its shipped value fell 34%; 化粧水 kilograms "
            "fell 12% and its value 36%. 22 of METI's 33 component lines rose that year, and the "
            "three largest falls were 化粧水 (−36%), 美容液 (−34%) and 乳液 (−27%). JCIA's "
            "misreporting correction restates other lines, and the step remains in the restated "
            "series. METI publishes no reason for it."
            f"<br><br>Serum shipped value: {_h['serum_val_span']}% over {_h['mkt_y0']}→{_h['mkt_y1']}, "
            f"+{_h['serum_val_post']}% over {_h['mkt_break']}→{_h['mkt_y1']}. Serum price per unit: "
            f"{_h['serum_ppu_span']}% and +{_h['serum_ppu_post']}% over the same two spans."
            f"<br><br>Skincare-to-makeup shipped value ratio: {_h['mkt_ratio_pre0']} in {_h['mkt_y0']}, "
            f"{_h['mkt_ratio_pre1']} in {_h['mkt_pre1']}, {_h['mkt_ratio_post0']} in {_h['mkt_break']}, "
            f"{_h['mkt_ratio_post1']} in {_h['mkt_y1']}.")
        S["t2_curvee"] = (
            f"The same {_h['conv_p1']} reviews, subsampled to different sizes: cosine similarity "
            f"between pooled skincare and cosmetics reviews rises from ~{_h['size_lo_cos']} to "
            f"~{_h['size_hi_cos']}. Convergence on this tab is measured at equal sample sizes.")
        S["t2_curvenote"] = (
            f"At {_h['matched_n']} reviews per period: {_h['conv_lo']} → {_h['conv_hi']}, "
            f"Δ +{_h['conv_delta']} (bootstrap {_h['conv_ci']}).")
        S["f2_body"] = (
            f"With each period set to {_h['matched_n']} reviews, cosine similarity between skincare "
            f"and cosmetics review language rose from {_h['conv_lo']} ({_h['conv_p0']}) to "
            f"{_h['conv_hi']} ({_h['conv_p1']}), Δ +{_h['conv_delta']} ({_h['conv_ci']}).")
    else:
        S["t2_intro"] = (
            f"サンプル数を揃えて測ると、スキンケアとコスメのレビューが共有する語彙は、"
            f"{_h['conv_p0']}年より{_h['conv_p1']}年のほうが多い。")
        S["t2_m2d"] = f"各期間を{_h['matched_n']}件に均一化 · {_h['conv_ci_jp']}"
        S["t1_m2d"] = f"トレンド指数の年平均、{_h['ing_y0']}年と{_h['ing_y1']}年"
        S["t1_m3"] = "楽天SKU比率（再分類後）"
        S["t1_c3h"] = (
            f"韓国コスメジャンルの再分類後、楽天のスキンケアSKUはメイクの{_h['sku_measured']}倍")
        S["t1_c3e"] = (
            f"メイク側の2ジャンルからそれぞれ150件を抽出し、手作業で分類した。"
            f"メイクとして分類されている韓国コスメジャンルは、スキンケア49%・メイク36%・その他15%で、"
            f"メイク総数の62%を占める。ベースメイクジャンルはメイク75%・その他24%で、その他の大半は"
            f"まつげエクステ用品と二重まぶた用品。両ジャンルを再分類すると{_h['sku_measured']}倍"
            f"（95%CI {_h['sku_lo']}〜{_h['sku_hi']}）、元の分類のままでは{_h['sku_span_lo']}倍、"
            f"商品種別が名称で定まるジャンルのみでは{_h['sku_span_hi']}倍。" + S["t1_c3e"])
        S["t1_c2h"] = (
            f"ナイアシンアミドの検索は{_h['ing_y0']}年{_h['nia_pre']}→{_h['ing_y1']}年"
            f"{_h['nia_post']}に上昇（トレンド指数）")
        S["f1_title"] = "発見1 —— メイクは検索・出荷金額ともに減少、スキンケアの出荷金額は2022年に段差"
        S["t1_intro"] = (
            "2020年以降、美容の検索、楽天の掲載、@cosmeレビュー、YouTubeコメントはスキンケアの比重を高めた。"
            f"経産省の出荷統計はメイク側を金額で記録しており、{_h['mkt_y0']}年から{_h['mkt_y1']}年にかけて"
            f"ファンデーションの出荷金額は{abs(_h['found_d'])}%、口紅は{abs(_h['lip_d'])}%減少した。"
            f"スキンケアの品目は{_h['mkt_break']}年1月に段差があり、美容液の出荷金額は段差をまたいで測ると減少、"
            f"段差の後で測ると増加となる。{_h['ytd_y']}年1〜{_h['ytd_m']}月は前年同期比で"
            f"皮膚用{_h['ytd_skin']:+}%、仕上用{_h['ytd_make']:+}%。")
        S["t1_mkcap"] = (
            f"月次、2019年1月〜{_h['ytd_y']}年{_h['ytd_m']}月 · {_h['mkt_break']}年1月以降の網掛け = 断層後 · "
            "皮膚用は2021〜2024年に12月、2025年に10月がピーク、仕上用は7年中6年で11月がピーク")
        S["t1_brkfn"] = (
            "経産省の生産動態統計は、化粧品メーカーから品目ごとの出荷金額・個数・重量（kg）を毎月集計している。"
            "金額を重量で割るとkgあたりの平均単価になる。化粧水・美容液・乳液では、この単価が2022年1月に下落する。"
            f"化粧水と美容液は{_h['ytd_y']}年{_h['ytd_m']}月まで2015〜2021年の範囲を下回り、乳液は2024年に範囲内、"
            "2025年に範囲を下回った。2021年1月と2022年1月を比べると、出荷金額は化粧水が38%（116→72億円）、"
            "美容液が34%（102→67億円）、乳液が40%（53→32億円）減少し、モイスチャークリームは6%、"
            "ファンデーションは18%増加した。口紅とアイメークアップのkg単価も2022年に下落するが形が異なり、"
            "重量が149%、44%増えた一方で出荷金額の増加は49%、11%だった。集計対象の企業や製品が変わった場合に"
            "スキンケアのこの形になるが、経産省はそのような変更も化粧品のリンク係数も公表していない。"
            "2022年より前の年と後の年を比べるスキンケアの金額にはこの下落が含まれるため、このタブのスキンケアの"
            f"金額変化は2019〜2021年または2022〜{_h['mkt_y1']}年の内側で測っている。{_h['ytd_y']}年の数値は"
            "経産省の月次確報による。")
        S["f1_body"] = (
            f"Googleトレンド：化粧品の検索は暦年ベース{_h['ing_y0']}→{_h['ing_y1']}年で約"
            f"{abs(_h['cosm_decline'])}%低下し、スキンケアはほぼ横ばい。楽天のスキンケアSKUはメイクの"
            f"{_h['sku_measured']}倍。ナイアシンアミドの検索は{_h['nia_pre']}→{_h['nia_post']}に上昇。"
            "口紅・ファンデーション・アイシャドウの検索は、マスク着用ルール緩和後も2019年を下回る。"
            f"<br><br>経産省出荷統計：{_h['mkt_y0']}年から{_h['mkt_y1']}年に、ファンデーションの出荷金額は"
            f"{abs(_h['found_d'])}%、口紅は{abs(_h['lip_d'])}%減少した。減少の大半は{_h['mkt_y0']}→{_h['mkt_pre1']}年"
            f"（{_h['found_d_pre']}%、{_h['lip_d_pre']}%）で、{_h['mkt_break']}年の段差がない品目である。"
            f"{_h['mkt_break']}年から{_h['mkt_y1']}年にはそれぞれ+{_h['found_d_post']}%、+{_h['lip_d_post']}%"
            f"増加した。化粧水・美容液・乳液のkg単価は{_h['mkt_break']}年1月に下方へ段差があり、経産省は理由を"
            f"公表していない。美容液の出荷金額は段差をまたぐと{_h['serum_val_span']}%、段差の後では"
            f"+{_h['serum_val_post']}%。"
            f"<br><br>{_h['ytd_y']}年1〜{_h['ytd_m']}月の前年同期比：皮膚用{_h['ytd_skin']:+}%、"
            f"仕上用{_h['ytd_make']:+}%、化粧品全体{_h['ytd_total']:+}%。")
        S["t1_m4d"] = (
            f"ファンデーション{_h['found_d']}%、口紅{_h['lip_d']}%（{_h['mkt_y0']}→{_h['mkt_y1']}年）· "
            "経産省出荷統計")
        S["t1_dve"] = (
            "統計の品目名と検索語の双方にある6カテゴリについて、検索関心度と出荷金額の変化を各区間の内側で測った。"
            f"{_h['mkt_y0']}→{_h['mkt_pre1']}年：ファンデーションと口紅は両尺度で減少。"
            f"{_h['mkt_break']}→{_h['mkt_y1']}年：ファンデーションと口紅は検索が減少し、出荷金額は増加。"
            f"美容液の検索は両区間で上昇し（{_h['mkt_y0']}→{_h['mkt_y1']}年で+{_h['serum_att_span']}%）、"
            "出荷金額は断層前に減少、断層後に増加。アイシャドウの検索は経産省の「アイメークアップ」品目と対応させている。")
        S["t1_c1e"] += (f"暦年ベース{_h['ing_y0']}→{_h['ing_y1']}年のスキンケア対化粧品の検索比："
                        f"{_h['ratio_0']}→{_h['ratio_1']}。")
        S["t1_p2d"] = (
            f"経済産業省生産動態統計、出荷金額（億円）、{_h['mkt_y0']}〜{_h['mkt_y1']}年。{_h['mkt_y1']}年の出荷"
            f"{_h['mkt_total_y1']:,}億円のうち、皮膚用が{_h['skin_share_y1']}%、仕上用が{_h['make_share_y1']}%。"
            f"輸入（財務省貿易統計 HS 3304）は{_h['mkt_y1']}年に市場の{_h['imp_share_y1']}%で、"
            f"{_h['mkt_y0']}年{_h['imp_y0']:,}億円、{_h['imp_peak_y']}年のピーク{_h['imp_peak']:,}億円、"
            f"{_h['mkt_y1']}年{_h['imp_y1']:,}億円。{_h['ytd_y']}年1〜{_h['ytd_m']}月の前年同期比は"
            f"皮膚用{_h['ytd_skin']:+}%、仕上用{_h['ytd_make']:+}%、全体{_h['ytd_total']:+}%（月次確報）。")
        S["t1_mke"] = (
            "経産省の33品目を合算した、皮膚用と仕上用の出荷金額。この区分は2019年と2020年の「計」小計を再現し、"
            f"日本化粧品工業会が公表する2024年の構成比と一致する。縦線は{_h['mkt_break']}年1月。")
        S["t1_brkb"] = (
            "化粧水のkg単価は2015年から2021年まで毎年6,787〜7,824円の範囲にあり、2022年に5,256円へ下落し、"
            "2025年は5,967円、2026年1〜7月は6,686円。美容液は32,563〜42,781円から23,874円へ下落し、2025年は"
            "28,933円。乳液は9,347〜12,233円から7,426円へ下落し、2024年は9,523円、2025年は9,049円。"
            "口紅とアイメークアップのkg単価は2022年に40%、23%下落し、重量は149%、44%増えた。"
            "2022年の美容液は数量が2%増え、"
            "出荷金額は34%減った。化粧水は数量が12%、出荷金額が36%減った。経産省の33品目のうち22品目がこの年に"
            "増加し、下落幅の上位3品目は化粧水（−36%）、美容液（−34%）、乳液（−27%）。"
            "日本化粧品工業会が注記する誤報告の修正は他の品目を対象としており、段差は修正後の"
            "系列にも残る。経産省は段差の理由を公表していない。"
            f"<br><br>美容液の出荷金額：{_h['mkt_y0']}→{_h['mkt_y1']}年で{_h['serum_val_span']}%、"
            f"{_h['mkt_break']}→{_h['mkt_y1']}年で+{_h['serum_val_post']}%。美容液の個数単価：同じ二区間で"
            f"{_h['serum_ppu_span']}%、+{_h['serum_ppu_post']}%。"
            f"<br><br>皮膚用対仕上用の出荷金額比：{_h['mkt_y0']}年{_h['mkt_ratio_pre0']}、"
            f"{_h['mkt_pre1']}年{_h['mkt_ratio_pre1']}、{_h['mkt_break']}年{_h['mkt_ratio_post0']}、"
            f"{_h['mkt_y1']}年{_h['mkt_ratio_post1']}。")
        S["t2_curvee"] = (
            f"同一の{_h['conv_p1']}年レビューを異なるサイズにサブサンプルすると、プールしたスキンケアとコスメの"
            f"レビュー間のコサイン類似度は約{_h['size_lo_cos']}から約{_h['size_hi_cos']}へ上昇する。"
            "このタブの収束はサンプル数を揃えて測っている。")
        S["t2_curvenote"] = (
            f"各期間{_h['matched_n']}件：{_h['conv_lo']} → {_h['conv_hi']}、"
            f"Δ +{_h['conv_delta']}（ブートストラップ{_h['conv_ci_jp']}）。")
        S["f2_body"] = (
            f"各期間を{_h['matched_n']}件に揃えると、スキンケアとコスメのレビュー言語のコサイン類似度は"
            f"{_h['conv_lo']}（{_h['conv_p0']}年）から{_h['conv_hi']}（{_h['conv_p1']}年）へ上昇した。"
            f"Δ +{_h['conv_delta']}（{_h['conv_ci_jp']}）。")

    _L = LAUNCH

    if _L:
        _last = _ym(_L["last"], lang)
        _pct = lambda a, b: round(100 * (a - b) / b)
        _gl, _gp = _L["grp_l12"], _L["grp_p12"]
        _cats = _L["cats"]
        _top_cat = _cats.index[0]
        _fall = (_cats["n_l12"] - _cats["n_p12"]).idxmin()
        _fell = (_cats.loc[_fall, "n_l12"] - _cats.loc[_fall, "n_p12"]) < 0
        _pf_share = round(100 * _L["full_pf"] / _L["full_tot"])
        _top_ing = _ing_label(_L["top_ing"], lang, _L)
        _trends_last = _ym(str(load_ingredient_surge(ASSETS)["week_start"].max())[:7], lang)
        _G = LAUNCH_GATE
        if lang == "en":
            def _move(a, b):
                p = _pct(a, b)
                return f"held at {a}" if abs(p) < 3 else f"{'rose' if p > 0 else 'fell'} {abs(p)}% to {a}"
            S["t3_lpd"] = (
                f"Product-launch releases on PR TIMES from {_L['n_core']} issuers since September 2021 "
                f"and {_L['n_all']} issuers over the latest 12 months, by month of release. "
                "One release is one count.")
            S["t3_l1h"] = (
                f"Skincare launch releases {_move(_gl['skincare'], _gp['skincare'])} in the 12 months "
                f"to {_last}; makeup {_move(_gl['makeup'], _gp['makeup'])}")
            S["t3_l1e"] = (
                f"{_L['n_core']} issuers whose PR TIMES history reaches back to September 2021. "
                "12-month totals by the product category named in the title or excerpt; releases "
                "that name no category word form their own line.")
            S["t3_l2h"] = (
                f"{LAUNCH_CAT[_top_cat][0]} had the most launch releases, {_cats.loc[_top_cat, 'n_l12']}, "
                f"against {_cats.loc[_top_cat, 'n_p12']} a year earlier"
                + (f"; {LAUNCH_CAT[_fall][0].lower()} fell to {_cats.loc[_fall, 'n_l12']} "
                   f"from {_cats.loc[_fall, 'n_p12']}" if _fell else ""))
            S["t3_l2e"] = (
                "Core issuers. The first category named in the title, otherwise in the excerpt. "
                f"Dark bars: the 12 months to {_last}; light bars: the 12 months before.")
            S["t3_l3h"] = (
                f"All {_L['n_all']} issuers, 12 months to {_last}: {_L['full_tot']:,} launch releases, "
                f"{_L['full_pf']} of them ({_pf_share}%) from the {_L['n_pf_feeds']} feeds whose history "
                "starts after September 2021")
            S["t3_l3e"] = (
                f"{_L['n_all_feeds']} feeds whose PR TIMES history covers all 12 months. Feeds whose "
                "history starts after September 2021 appear here and are left out of the series above.")
            S["t3_l4h"] = (
                f"{_top_ing} appeared in {_L['top_s_l12']}% of launch releases in the 12 months to "
                f"{_last} ({_L['top_n_l12']} of {_L['den_l12']}), from {_L['top_s_p12']}% a year earlier")
            S["t3_l4e"] = (
                "Core issuers. Share of launch releases whose title or excerpt names the ingredient: "
                f"{_L['den_l12']} releases in the 12 months to {_last}, {_L['den_p12']} in the 12 months "
                f"before. {_L['any_ing_share']}% name at least one of the {len(_L['terms'])} tracked "
                "ingredients. Releases whose title names a re-release, refill or limited packaging "
                "are excluded.")
            S["t3_l5e"] = (
                "Upper: share of core launch releases naming the ingredient, 12-month rolling, to "
                f"{_last}. Lower: Google Trends interest, 12-month rolling mean, to {_trends_last}.")
            S["t3_lcap"] = (
                f"Measured {_G['asof']}. Launch gate: precision {_G['precision']} (95% CI "
                f"{_G['p_lo']}–{_G['p_hi']}) and recall {_G['recall']} ({_G['r_lo']}–{_G['r_hi']}) "
                f"on {_G['n_holdout']} hand-labelled releases held out from the gate's design, "
                f"weighted to {_G['n_store']:,} stored releases. PR TIMES coverage: "
                f"{_G['prestige_unseen']} of {_G['prestige_n']} prestige (デパコス) brands in the brand "
                f"list appear in no stored release, against {_G['other_unseen']} of {_G['other_n']} "
                f"brands in other tiers. The edition filter finds {_G['edition_found']} of "
                f"{_G['edition_n']} hand-labelled editions.")
            S["t3_lwin_l12"] += _last
        else:
            def _move(a, b):
                p = _pct(a, b)
                return "で横ばい" if abs(p) < 3 else f"、前年同期比{abs(p)}%{'増' if p > 0 else '減'}"
            S["t3_lpd"] = (
                f"PR TIMES上の新商品リリース。2021年9月以降は{_L['n_core']}社、直近12カ月は"
                f"{_L['n_all']}社。配信月別、1リリースを1件と数える。")
            S["t3_l1h"] = (
                f"直近12カ月（{_last}まで）のスキンケア新商品リリースは{_gl['skincare']}件"
                f"{_move(_gl['skincare'], _gp['skincare'])}。メイクは{_gl['makeup']}件"
                f"{_move(_gl['makeup'], _gp['makeup'])}")
            S["t3_l1e"] = (
                f"PR TIMES上の履歴が2021年9月まで遡る{_L['n_core']}社。タイトルまたは抜粋に記載された"
                "商品カテゴリ別の12カ月合計。カテゴリ語を含まないリリースは別系列とした。")
            S["t3_l2h"] = (
                f"直近12カ月の新商品リリースは{LAUNCH_CAT[_top_cat][1]}が{_cats.loc[_top_cat, 'n_l12']}件で"
                f"最多（前年同期{_cats.loc[_top_cat, 'n_p12']}件）"
                + (f"。{LAUNCH_CAT[_fall][1]}は{_cats.loc[_fall, 'n_l12']}件"
                   f"（同{_cats.loc[_fall, 'n_p12']}件）" if _fell else ""))
            S["t3_l2e"] = (
                "コア発行元。タイトル、なければ抜粋で最初に記載されたカテゴリ。"
                f"濃い棒：{_last}までの12カ月、淡い棒：その前の12カ月。")
            S["t3_l3h"] = (
                f"直近12カ月（{_last}まで）の全{_L['n_all']}社の新商品リリースは{_L['full_tot']:,}件。"
                f"うち{_L['full_pf']}件（{_pf_share}%）は履歴が2021年9月より後に始まる"
                f"{_L['n_pf_feeds']}フィードから")
            S["t3_l3e"] = (
                f"PR TIMES上の履歴が12カ月すべてを含む{_L['n_all_feeds']}フィード。履歴が2021年9月より後に"
                "始まるフィードはここにのみ含め、上の系列には加えない。")
            S["t3_l4h"] = (
                f"{_top_ing}を含む新商品リリースは直近12カ月で{_L['top_s_l12']}%"
                f"（{_L['den_l12']}件中{_L['top_n_l12']}件）、前年同期は{_L['top_s_p12']}%")
            S["t3_l4e"] = (
                "コア発行元。タイトルまたは抜粋に成分名を含む新商品リリースの比率。"
                f"{_last}までの12カ月は{_L['den_l12']}件、その前の12カ月は{_L['den_p12']}件。"
                f"追跡する{len(_L['terms'])}成分のいずれかを含むのは{_L['any_ing_share']}%。"
                "タイトルに再発売・詰め替え・限定パッケージを含むリリースは除いた。")
            S["t3_l5e"] = (
                f"上：成分名を含むコア新商品リリースの比率、12カ月移動、{_last}まで。"
                f"下：Googleトレンドの検索関心、12カ月移動平均、{_trends_last}まで。")
            S["t3_lcap"] = (
                f"{_G['asof']}測定。新商品判定の精度：適合率{_G['precision']}（95%信頼区間"
                f"{_G['p_lo']}〜{_G['p_hi']}）、再現率{_G['recall']}（同{_G['r_lo']}〜{_G['r_hi']}）。"
                f"判定語彙の設計に用いていない手作業ラベル{_G['n_holdout']}件で測り、保存済み"
                f"{_G['n_store']:,}件に加重した。PR TIMESの収録：ブランドリストのデパコス"
                f"{_G['prestige_n']}ブランドのうち{_G['prestige_unseen']}ブランドは保存済みリリースに一度も"
                f"現れない。その他の価格帯は{_G['other_n']}ブランド中{_G['other_unseen']}。"
                f"限定・再発売の除外判定は手作業ラベルの{_G['edition_n']}件中{_G['edition_found']}件を検出する。")
            S["t3_lwin_l12"] += _last
    return S
