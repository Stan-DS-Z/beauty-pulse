# Beauty Pulse — 日本美容市場アナリティクス

**コロナ禍はどのように日本の美容消費を再構成したのか？**  
How did COVID permanently restructure Japanese beauty consumption?

5つの独立したデータソース（レビュー・検索行動・商品カタログ・成分検索・YouTube）が同じ構造的変化を指している。  
Five independent sources — consumer reviews, search behaviour, product catalog, ingredient searches, and YouTube discourse — converge on the same structural shift.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red)
![SQLite](https://img.shields.io/badge/Data-SQLite-lightgrey)
![NLP](https://img.shields.io/badge/NLP-SudachiPy%20%7C%20TF--IDF%20%7C%20UMAP-violet)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)
![Markets](https://img.shields.io/badge/Market-Japan-white)

<p align="center">
  <a href="https://ss-beauty-pulse.streamlit.app/">
    <img src="https://img.shields.io/badge/%E2%9C%A8_ダッシュボード-ss--beauty--pulse.streamlit.app-4A90B8?style=for-the-badge" alt="Dashboard">
  </a>
</p>

---

## 仮説 / Hypothesis

> コロナ禍以降、日本の消費者はスキンケアを美容の最優先事項として位置づけるようになった。  
> 「正直なスキンケア」が「演出するコスメ」を、構造的に、かつ永続的に凌駕している。

> Post-COVID Japanese consumers have structurally reprioritised skincare over cosmetics.  
> "Honest skincare" has permanently displaced "performance cosmetics" as the dominant consumer concern.

---

## 検証結果：確認 ✓ / Verdict: Confirmed ✓

**5つのソース、同じ方向性。** 2022年のコスメ一時回復（マスク解禁効果）は本物だったが、一過性だった。  
2025年にはコスメのレビュー比率がデータセット最低値の12.7%まで後退。

**Five sources, same direction.** The 2022 cosmetics rebound (mask-off effect) was real but transient.  
By 2025, cosmetics retreated to 12.7% review share — the lowest point in the dataset.

*Nuance:* スキンケアの語彙はコスメを「吸収」したわけではない。  
両者が共有の機能的語彙へと収束した（語彙重複度 0.38 → 0.81）。  
*Nuance:* Skincare did not absorb cosmetics. Both categories converged toward a shared functional vocabulary — vocabulary overlap rose from 0.38 to 0.81 over six years.

---

## 主要な発見 / Key Findings

| シグナル / Signal | 2019 | 2025 | 変化 / Change |
|---|---|---|---|
| スキンケアレビュー比率 / Skincare review share | 85.7% | 87.3% | +1.6pp |
| COVID後の急増（2020） / COVID surge (2020) | — | — | **+152.1%** |
| 楽天SKU比率 / Rakuten SKU ratio (skin:cosm) | — | — | **4.0×** |
| Googleトレンド逆転 / Google Trends crossover | — | — | **2020** |
| 語彙収束 / Vocabulary convergence | 0.38 | 0.81 | **+0.43** |
| ナイアシンアミド検索 / Niacinamide search interest | 5.2 | 62.8 | **+57.6pp** |

---

## 発見の詳細 / What the Data Found

### 発見1 — 構造的変化は5つのソースで確認された

5つの独立したソースが同じ方向性を示した。  
@cosmeレビューコーパス、Google検索トレンド（スキンケアが化粧品を2020年に逆転）、楽天市場の商品カタログ（スキンケアの商品数がコスメの4.0倍）、成分名の検索急増（ナイアシンアミド12倍）、YouTubeコメント量の加速。

**Finding 1 — The Structural Shift**  
Five independent sources, same direction: @cosme review corpus, Google search trends (skincare overtakes cosmetics in 2020), Rakuten Ichiba product catalog (4.0× skincare-to-cosmetics product ratio), ingredient search surge (niacinamide ×12), and YouTube comment volume acceleration.

---

### 発見2 — 消費者の言葉が変わった

2019年：スキンケアとコスメのレビューは語彙の38%しか共有していなかった。2023–25年：81%に上昇。  
消費者がレビューで使う言葉を分析すると、方向性は明確：  
マスカラ −76%、まつ毛 −86%、アイライナー −71%（メイク語彙の衰退）。  
代わりに台頭：保湿 +409%、クリーム +3,101%、乾燥 +312%（スキンケア語彙の台頭）。  
コスメはスキンケアの基準で評価されるようになった。

**Finding 2 — Consumer Language Changed**  
2019: skincare and cosmetics reviews shared just 38% of their top vocabulary. By 2023–25: 81%.  
Text analysis of review language confirms the direction:  
Mascara (マスカラ) −76%, eyelashes (まつ毛) −86%, eyeliner (アイライナー) −71% — declining.  
Moisture (保湿) +409%, cream (クリーム) +3,101%, dryness (乾燥) +312% — rising.  
Cosmetics are now evaluated through a skincare lens.

---

### 発見3 — 14,727件のレビューを「地図」にすると、隠れた構造が見える

レビューの語彙を空間的に可視化すると、3つの構造が浮かび上がった。  
インフルエンサー・モニターレビューは、指示なしに自動的にオーガニックレビューと分離された — この2つを区別せずにセンチメント分析を行うと、異なるシグナルが混在する。  
「ファンデーション as スキンケア」クラスターは、コスメレビューがスキンケア語彙（乾燥・しっとり・毛穴）で書かれている収束点を示す。  
SPFは単一カテゴリではない：機能的日焼け止めとベースメイク型SPFは、消費者がまったく異なる言葉で語っている。

**Finding 3 — Mapping 14,727 Reviews Reveals Hidden Structures**  
Visualising review vocabulary as a spatial map reveals three structures.  
Influencer/giveaway reviews separated automatically from organic consumer reviews — without being told to. Brands measuring sentiment without filtering these populations are mixing two different signals.  
A "Foundation as skincare" cluster marks where cosmetics reviews are already written in skincare language (dryness, moist texture, pores).  
SPF is not one category: functional sun protection and cosmetic base makeup consumers speak entirely different vocabularies.

---

### 発見4 — 韓国ブランドが日本の需要を取り込んでいる

COVID期：消費者は成分名を検索していた（レチノールが5つの異なる検索起点で浮上、ナイアシンアミドが4つ）。ブランドではなく知識を求めていた。  
直近：アヌア（韓国ブランド）が4つの独立した検索語で最強シグナルを記録。  
構造的変化が消費者を教育した。韓国ブランドがその恩恵を受けている。YouTubeはまだ開かれている。

**Finding 4 — Korean Brands Are Harvesting Japanese Demand**  
COVID era: consumers were searching for ingredient names (retinol appeared across 5 independent search starting points, niacinamide across 4). They were building knowledge, not searching for brands.  
Recent window: Anua (アヌア, a Korean brand) is the single strongest signal, appearing across 4 independent search terms.  
The structural shift educated consumers. Korean brands captured them. YouTube is still wide open.

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced and self-collected. No Kaggle datasets.
```

| ソース / Source | 内容 / Contents | 規模 / Scale |
|---|---|---|
| @cosme | Consumer reviews (skincare + cosmetics) | 22,451 reviews |
| Rakuten Ichiba API | Product catalog, prices, review counts | 31,202 SKUs |
| Google Trends JP | Weekly search interest (2019–2026) | 4,635 rows |
| YouTube Data API v3 | Beauty video comments | 248 videos · 60,676 comments |

**@cosmeデータについて / Note on @cosme data:**  
カテゴリレベルのスクレイピング（ブランド属性なし）。これは設計上の選択であり、データギャップではない。  
Category-level scraping without brand attribution. This is a design choice, not a data gap — brand neutrality was maintained to preserve the integrity of market-level analysis.

---

## 技術スタック / Technical Stack

```python
# Analysis pipeline
Python       3.12      # Core language
SQLite       3.x       # Single shared database via get_connection()
SudachiPy    0.5.x     # Japanese text analysis (morphological analysis, Mode C)
scikit-learn 1.x       # Text importance scoring (TF-IDF), topic modelling (LDA)
umap-learn   0.5.x     # Dimensionality reduction for review mapping
hdbscan      0.8.x     # Automatic cluster detection

# Dashboard
Streamlit    1.x       # Interactive web UI
Plotly       5.24.1    # Charts (version pinned for API stability)
```

**設計原則 / Design Principles:**
- **Single source of truth for product tiers:** `COALESCE(p.tier_predicted, p.tier_override, c.tier)` used consistently across all notebooks
- **No hardcoded paths:** `get_connection()` from `src.schema` manages all database access
- **Explainable NLP progression:** term importance scoring → topic modelling → dimensionality reduction — each step has a clear analytical purpose
- **Privacy-aware deployment:** public dashboard uses `signal_pulse_public.db` with product names and raw JSON stripped

---

## ノートブック構成 / Notebook Pipeline

| Notebook | Purpose |
|---|---|
| NB01a–e | Data collection (Rakuten API, @cosme, Amazon JP, Google Trends, YouTube) |
| NB02 | Database schema design and data quality audit |
| NB02b | Product tier classification (XGBoost classifier for unlabelled products) |
| NB02c | Weekly Rakuten snapshot ingestion (time-series tracking) |
| NB03 | SQL analytical foundation — BI layer demonstrating CTEs, window functions, self-joins |
| NB04 | Consumer voice — vocabulary analysis, ingredient detection, review quality |
| NB05 | The Shift — confirmatory analysis across 3 independent sources |
| NB06 | Discovery layer — vocabulary convergence, topic modelling, review mapping, search discovery |
| NB07 | Executive synthesis + dashboard asset generation |

**Execution order:** NB02 → NB02b → NB02c → NB03 → NB04 → NB05 → NB06 → NB07 → `streamlit_app.py`

---

## ライブダッシュボード / Live Dashboard

**[Beauty Pulse](https://ss-beauty-pulse.streamlit.app/)** is deployed on Streamlit Community Cloud with an EN/JP language toggle.

| Tab | What it shows |
|---|---|
| 📈 The Shift / 市場変化 | Five-source confirmation, ingredient search surge, Rakuten treemap, YouTube trends |
| 🔤 The Language / 消費者の言語 | Word clouds by year, vocabulary convergence heatmap, rising and declining terms |
| 🔍 Discovery / 発見 | Google Trends rising searches, YouTube channel analysis, interactive review map |

---

## 方法論的注意点 / Methodological Caveats

1. **COVID前コーパスの非対称性 / Pre-COVID corpus asymmetry**  
   2019–2020年レビュー数は565件 vs 直近12,517件。時系列比較はサンプルサイズの非対称性を伴う。  
   Bootstrap CI（NB06）により、この非対称性が語彙収束の所見を説明しないことを確認済み（Δ 95% CI 全体がゼロ以上）。  
   Googleトレンド（週次、2019年から）が方向性を補完する。  
   Pre-COVID reviews total 565 vs 12,517 recent. All temporal comparisons carry this asymmetry.  
   Bootstrap CI (NB06) confirms the vocabulary convergence finding is robust — the Δ 95% CI is entirely above zero.  
   Google Trends (weekly, from 2019) provides full temporal coverage as a complementary source.

2. **SudachiPy Mode Cの複合語分割 / Compound word splitting**  
   ナイアシンアミド → ナイアシン + アミドに分割される。成分検出はTF-IDF経由ではなく生テキスト検索で実施。  
   Niacinamide splits into niacin + amide under Mode C. Ingredient detection uses raw text search, not TF-IDF.

3. **@cosmeの交差検証非独立性 / Cross-validation non-independence**  
   レビューコーパスと楽天カタログは共にRakutenグループのデータ。厳密な独立性はGoogleトレンドとYouTubeのみ。  
   The review corpus (@cosme) and Rakuten catalog are both Rakuten Group data. Strictly independent sources are Google Trends and YouTube only.

4. **検索発見シグナルの正規化 / Search discovery signal normalisation**  
   検索起点ごとの検索ボリュームは比較不可。メトリクスは起点内で独立に正規化済み。ツリーマップは相対的シグナル強度を示す（絶対ボリュームではない）。  
   Search volumes are not comparable across starting terms. Metrics are normalised within each starting term independently. Treemaps show relative signal strength, not absolute volume.

5. **中国除外 / China exclusion**  
   楽天クロスボーダーおよびインバウンド需要は未定量化。  
   Rakuten cross-border and inbound demand from China is not quantified.

6. **レビュアー選択バイアス / Reviewer selection bias**  
   @cosmeレビューは自発的に書き込む消費者のみを反映する。購入者全体の意見分布とは異なる可能性がある。  
   特に、レビューを書く動機（不満の表出・高評価推奨・モニター当選報告）がコーパスの語彙構成に影響している。  
   @cosme reviews reflect only consumers who choose to write — not the purchasing population.  
   Motivation to review (dissatisfaction, recommendation, or monitor/giveaway participation) shapes the corpus vocabulary. Topic modelling autonomously identified the giveaway template bias (NB06 Skincare Topic 4).

7. **SKU数 ≠ 売上高 / SKU count ≠ sales volume**  
   楽天カタログのSKU比率（スキンケア4.0×コスメ）は棚占有率を示すが、GMV（流通総額）とは一致しない。  
   少数SKUで高売上のコスメカテゴリが過小評価されている可能性がある。  
   The Rakuten SKU ratio (skincare 4.0× cosmetics) measures shelf share, not GMV.  
   A cosmetics category with fewer SKUs but higher per-SKU sales could be underrepresented by this metric.

8. **Googleトレンドの絶対ボリューム不明 / Google Trends absolute volume unknown**  
   Googleトレンドは0–100の相対指標を返す。実際の検索ボリュームは不明。  
   「スキンケア」が「化粧品」を超えたという所見は相対的シェアの逆転を意味するが、両方の絶対ボリュームが同時に成長していた可能性もある。  
   Google Trends returns a 0–100 relative index, not absolute search volume.  
   The finding that スキンケア overtook 化粧品 reflects a relative share crossover — both terms could have grown in absolute volume simultaneously.

---

## セットアップ / Setup

```bash
git clone https://github.com/Stan-DS-Z/beauty-pulse.git
cd beauty-pulse
conda activate beauty-pulse
pip install -r requirements.txt
python -m sudachipy download
streamlit run dashboard/streamlit_app.py
```

**Note:** `signal_pulse.db` (primary database) is gitignored for data privacy.  
The dashboard uses `signal_pulse_public.db` (stripped version in `dashboard/assets/`).

---

## プロジェクトの背景 / Context

このプロジェクトは、日本の美容・FMCGアナリティクスへのキャリアピボットを目的としたデータポートフォリオ作品。  
自己収集データの構築（Kaggle不使用）、日本語NLPパイプライン、SQLite設計、Streamlitダッシュボード展開を含む。

This project forms one half of a data analytics portfolio targeting Japanese beauty and FMCG analytics roles.  
It demonstrates self-sourced data construction, Japanese NLP, SQL architecture, and deployed dashboard work —  
built as a complement to [The Masstige Moment](https://github.com/Stan-DS-Z/the-masstige-moment), which analyses the same market from a top-down revenue perspective.

**Built with free, public APIs only — imagine what's possible with proprietary data.**

JLPT N1 · DALF C1 — 分析資産として日英仏3言語での納品が可能。  
JLPT N1 · DALF C1 — trilingual analytical delivery across EN / JP / FR.

---

![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)
![Data](https://img.shields.io/badge/Data-Self--sourced-blue)
![NLP](https://img.shields.io/badge/NLP-Japanese-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

*Analysis by Stanley Shi · [LinkedIn](https://www.linkedin.com/in/stanley-shi-7b604b104/) · 2026*
