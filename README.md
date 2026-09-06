# Beauty Pulse — 日本美容市場アナリティクス

**コロナ禍はどのように日本の美容消費を再構成したのか？**  
How did COVID restructure Japanese beauty consumption?

検索行動・商品カタログ・成分検索・YouTube・消費者レビュー — 複数の独立した signal を突き合わせる。  
Search behaviour, product catalog, ingredient searches, YouTube discourse, and consumer reviews — multiple independent signals, cross-checked across sources.

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

> Post-COVID Japanese consumers have structurally reprioritised skincare over cosmetics.

---

## 検証結果：メイクでは確認、スキンケアでは測定不能 / Verdict: Confirmed for makeup, unmeasurable for skincare

**関心は動いた。金額の裏づけは半分しか取れない。**
コロナ後、化粧品の検索需要は暦年ベース2019→2025年で約32%低下し、スキンケアの検索はほぼ横ばいで推移した。公的な出荷統計（経産省 生産動態統計）を突き合わせると、この発見は二つに分かれる。**メイクは金額でも裏づけられた** —— ファンデーションと口紅の出荷金額は2019→2024年にいずれも42%減少し、落ち込みは2019→2021年に集中する。**スキンケアは裏づけられない** —— 金額系列は2022年1月に断層を持ち、そこをまたいで測った数値は断層の内側で測り直すと符号が反転する（美容液の出荷金額はまたげば-39%、内側なら+20%）。断層の原因は公表統計に記載がない。成分名検索は同じ期間に上昇したが（ナイアシンアミド 5→81、Googleトレンド指数）、こちらには行動側の対応物がそもそも存在しない —— 成分単位の需要を追う公的系列はない。

**Attention moved. Only half of it can be checked against money.**
Cosmetics search demand fell ~32% across full calendar years 2019→2025 while skincare search held roughly flat. Set against official shipment statistics (METI 生産動態統計), that finding splits in two. **Makeup is corroborated in yen** — foundation and lipstick shipped value both fell 42% over 2019→2024, with the collapse concentrated in 2019→2021, before the break and in lines it does not touch. **Skincare is not** — its money series steps in January 2022, and figures measured across that step reverse sign when measured inside it (serum shipped value reads -39% across the break and +20% after it). The cause is undocumented in the published statistics, so no skincare demand reading is offered. Ingredient-name search rose over the same years (niacinamide 5→81 on the Trends index) and has no behavioural counterpart at all — no official series tracks ingredient-level demand. A mask test rules out the cyclical explanation for the makeup decline: search did not recover after Japan relaxed mask guidance in March 2023.

*何が測れるか / What is measured where:* この分析は二つの層を別々の測定として扱う。**関心層** —— Googleトレンド、楽天の掲載数、@cosmeレビュー、YouTube —— は検索と言葉を測る。**市場層** —— 経産省 生産動態統計と財務省 貿易統計 —— は金額と数量を測る。両者が一致する箇所だけが行動の裏づけを持つ。

*The two layers:* the **attention layer** (Google Trends, Rakuten listings, @cosme reviews, YouTube — all self-built) measures what people search for and say. The **market layer** (METI shipments, 財務省 trade statistics HS 3304) measures what they buy, in yen and kilograms. They are different measurements and are never averaged together; only where they agree is a behavioural claim made. Full argument and the per-finding status: [METHODOLOGY.md](METHODOLOGY.md).

*Nuance:* スキンケアとコスメのレビュー言語は緩やかに収束しているが、その規模は小さく、サンプルサイズに敏感である。サンプル数を揃えた厳密な比較では Δ +0.065（0.252→0.317、ブートストラップ95%CI [+0.047, +0.083]）。  
*Nuance:* skincare and cosmetics review language is converging slowly, but the effect is small and sample-size sensitive — Δ +0.065 (0.252→0.317, bootstrap 95% CI [+0.047, +0.083]) under a size-matched comparison.

---

## ライブダッシュボード / Live Dashboard

**[Beauty Pulse](https://ss-beauty-pulse.streamlit.app/)** is deployed on Streamlit Community Cloud with an EN/JP language toggle.

| Tab | What it shows |
|---|---|
| 📈 The Shift / 市場変化 | Three panels: the attention layer (search, mask-rebound test, ingredient surge, Rakuten treemap, YouTube), the market layer (METI shipped value, the 2022 break), then the two set side by side |
| 🔤 The Language / 消費者の言語 | Word clouds by year, size-matched vocabulary convergence |
| 🔍 Discovery / 発見 | Google Trends rising searches, YouTube channel analysis, interactive review map |
| 💡 For brands / ブランドへの示唆 | The four findings translated into prescriptive plays — with an explicit attention-data-≠-sales-data disclaimer |

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced and self-collected. No Kaggle datasets.
```

**関心層 / Attention layer** — 検索と言葉。自己収集。 What people search for and say; self-collected.

| ソース / Source | 内容 / Contents | 規模 / Scale |
|---|---|---|
| @cosme | Consumer reviews — used for *language* analysis | 45,510 reviews |
| Rakuten Ichiba API | Product catalog, prices, review counts | 46,193 SKUs · 580,139 weekly rows |
| Amazon | Name, price, aggregate rating, review count | 161 ASINs · 1,124 reviews |
| Google Trends JP | Monthly search interest (2019–2026) | 4,842 rows |
| YouTube Data API v3 | Beauty video comments | 296 videos · 74,679 comments |

**市場層 / Market layer** — 金額と数量。公的統計、e-Stat API 経由。 What people buy, in yen and kilograms; official statistics via the e-Stat API.

| ソース / Source | 内容 / Contents | 規模 / Scale |
|---|---|---|
| 経産省 生産動態統計「11.化粧品」 | Shipments by product line — value, volume, unit count | monthly 2019–2024, annual to 2015 |
| 財務省 貿易統計 HS 3304 | Imports and exports by country | annual 2016–2025 |

再現は `build_estat_shipments.py` と `build_estat_imports.py`（要 `ESTAT_APP_ID`）。両スクリプトは表IDを `getStatsList` から実行時に解決する —— IDは安定しておらず、広く引用されているMETIのIDは2010年の単月表を指す。  
Rebuild with `build_estat_shipments.py` and `build_estat_imports.py` (`ESTAT_APP_ID` required). Both resolve table IDs from `getStatsList` at run time: the IDs are not stable, and the commonly cited METI one resolves to a single month of 2010.

レビュー「量」は取得設計に依存するため市場シグナルとして用いず、レビュー「テキスト」のみを語彙分析に使用する。本文は一覧ページのプレビューであり全文ではない —— 詳細は[方法論](METHODOLOGY.md)。  
Review *volume* depends on scraping design, so only review *text* is used, for vocabulary analysis. Bodies are listing-page previews, not full text — see [Methodology](METHODOLOGY.md).

---

## 技術スタック / Technical Stack

```python
# Analysis pipeline
Python       3.12      # Core language
SQLite       3.x       # Single shared database via get_connection()
SudachiPy    0.6.x     # Japanese text analysis (morphological analysis, Mode C)
scikit-learn 1.x       # Text importance scoring (TF-IDF), topic modelling (LDA)
umap-learn   0.5.x     # Dimensionality reduction for review mapping
hdbscan      0.8.x     # Automatic cluster detection

# Dashboard
Streamlit    1.x       # Interactive web UI
Plotly       5.24.1    # Charts (version pinned for API stability)
```

**設計原則 / Design Principles:**
- **Tier resolution is one expression everywhere:** `COALESCE(p.tier_predicted, p.tier_override, c.tier)`
- **One canonical join path:** `reviews.category_id` is authoritative for review-level tier
- **Snapshot-dated raw layer:** every scraper stamps outputs `…_YYYY-MM-DD.json`; readers take the newest via `latest_snapshot()`
- **Privacy-aware publishing:** `signal_pulse_public.db` ships with product names and raw JSON stripped; the primary DB stays local
- **Rebuilds from raw:** `NB02 → … → NB07` reconstructs the database end to end

---

## ノートブック構成 / Notebook Pipeline

| Notebook | Purpose |
|---|---|
| NB01a–e | Data collection (Rakuten API, @cosme, Amazon JP, Google Trends, YouTube) — *kept local; scraping code is not published* |
| NB02 | Database schema design, data quality audit, category-path reconciliation |
| NB02b | Product tier classification (XGBoost classifier for unlabelled products) |
| NB02c | Weekly Rakuten snapshot ingestion (time-series tracking) |
| NB03 | SQL analytical foundation — BI layer demonstrating CTEs, window functions, self-joins |
| NB04 | Consumer voice — vocabulary analysis, ingredient detection, review quality |
| NB05 | The Shift — confirmatory analysis across independent sources |
| NB06 | Discovery layer — vocabulary convergence (size-matched), topic modelling, review mapping, search discovery |
| NB07 | Executive synthesis + dashboard asset generation |

**Execution order:** NB02 → NB02b → NB02c → NB03 → NB04 → NB05 → NB06 → NB07 → `streamlit_app.py`

---

## 方法論と改訂履歴 / Methodology & Revision History

撤回・再定義した指標、サンプルサイズ依存、ソースの非独立性など12項目の注意点と、
4回の改訂記録は[**方法論と改訂履歴**](METHODOLOGY.md)にまとめている。  
Retired and rescoped metrics, sample-size dependence, source non-independence and nine further
caveats — plus the four-revision audit log — are in [**Methodology & Revision History**](METHODOLOGY.md).

---

## 公開データで測れること・測れないこと / What This Data Can and Cannot Show

本プロジェクトのシグナルはすべて注目（検索・コメント）または供給（SKU）であり、金額・転換率・再購買ではない。
左列は公開データで測れた範囲、右列は同じ問いを1stパーティデータに当てたときに解ける指標である。  
Every signal here measures attention (search, comments) or supply (SKUs) — not yen, not conversion,
not repeat purchase. The left column is what public data measured; the right is what the same
questions resolve into against first-party data.

| 本プロジェクトで測れたもの / Measured here | 1stパーティデータで解ける問い / Resolvable with first-party data |
|---|---|
| Googleトレンドの検索需要 / Search demand (Google Trends) | 獲得単価・広告転換率 / Paid-search CPA and conversion |
| @cosmeのレビュー言語 / Review language (@cosme) | CRM・アプリ内行動・再購買率 / CRM, in-app behaviour, repeat rate |
| 楽天のSKU棚シェア / Shelf share by SKU (Rakuten) | POS実売・在庫回転・粗利 / POS sell-through, stock turns, margin |

注意点12（公開統計での検証）は実行済みであり、その結果が上の検証結果である。残る限界は三つ:
経産省統計は2024年までで、関心データは2026年まで —— 直近2年は関心のみ。皮膚用の金額系列は2022年1月に断層があり、
またいだ測定はできない。家計調査は未取得で、かつ**美容液と日焼け止めの品目を持たない** ——
最も動いたカテゴリを検証できる系列ではない。1stパーティデータはその先にある。  
Caveat 12 — validate against public statistics — has been done, and the verdict above is its result.
Three limits remain. METI runs to 2024 while the attention data runs to 2026, so the last two years
are attention-only. The skincare money series breaks in January 2022, so it cannot be measured across
that point. And 家計調査 (household spending) is not pulled — it would be immune to the tourist and
export effects, but it carries **no 美容液 line and no sunscreen line**, so it cannot test the categories
that moved most. First-party data is the step after.

---

## セットアップ / Setup

**ダッシュボードを動かす / Run the dashboard — works out of the box:**  
リポジトリにはダッシュボードが読む全アセット（事前計算済みCSVと公開DB）が同梱されており、クローン直後にそのまま起動できる。  
The repo ships every asset the dashboard reads (pre-computed CSVs + the public DB), so it runs immediately after cloning.

```bash
git clone https://github.com/Stan-DS-Z/beauty-pulse.git
cd beauty-pulse
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run dashboard/streamlit_app.py
```

**分析を検証・再実行する / Interrogate or re-run the analysis (NB03 → NB07):**

```bash
pip install -r requirements-analysis.txt
```

主データベースはgitignoreされているため、クローンには含まれない。`src.schema.get_connection()`
は同梱の公開DBに自動でフォールバックし（初回のみ`dashboard/assets/`から`data/`へ展開）、
読み取り専用で開く。NB03〜NB07はクローンから実行順どおりに動作する。NB02は未公開の生データを要するため動かない。

The primary database is gitignored, so a clone does not have it.
`src.schema.get_connection()` falls back to the bundled public DB — extracting it from
`dashboard/assets/` into `data/` once — and opens it read-only. NB03–NB07 therefore run from
a clone in the stated order. NB02 does not: it ingests raw data that is not published.

**リポジトリの範囲 / Repository scope:**  
公開：分析ノートブック（NB02〜NB07）、ダッシュボード、CSVアセット、`signal_pulse_public.db.gz`（商品名・生JSONを削除した照会可能なデータセット。`gunzip`して利用）。  
ローカルのみ：収集ノートブック（NB01x）、生データ、主データベース。  
Public: analysis notebooks (NB02–NB07), the dashboard, CSV assets, and `signal_pulse_public.db.gz` — a queryable dataset with product names and raw JSON stripped (`gunzip` it first). Local-only: the collection notebooks (NB01x), raw data, and the primary database. From the public repo you can run the dashboard, query the public DB, and audit every analysis step against it.

---

## プロジェクトの背景 / Context

このプロジェクトは、日本の美容・FMCGアナリティクスへのキャリアピボットを目的としたデータポートフォリオ作品。自己収集データの構築（Kaggle不使用）、日本語NLPパイプライン、SQLite設計、Streamlitダッシュボード展開を含む。

This project forms one half of a data analytics portfolio targeting Japanese beauty and FMCG analytics roles. It demonstrates self-sourced data construction, Japanese NLP, SQL architecture, and deployed dashboard work — built as a complement to [The Masstige Moment](https://github.com/Stan-DS-Z/the-masstige-moment), which analyses the same market from a top-down revenue perspective.

**Built with free, public APIs.**

---

*Analysis by Stanley Shi · [LinkedIn](https://www.linkedin.com/in/stanley-shi-7b604b104/) · 2026*
