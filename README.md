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

## 検証結果：部分的に確認（限定的） / Verdict: Partially Confirmed

**方向性は支持されるが、規模は限定的である。**
コロナ後、化粧品の検索需要は暦年ベース2019→2025年で約32%低下した一方、スキンケアの検索はほぼ横ばい —— 両者の差は半減したが、化粧品が依然として上回る（「逆転」ではない）。楽天市場のカタログはスキンケアSKUがコスメの3.7倍。成分名検索（ナイアシンアミド・レチノール）はコロナ後に約6〜7倍へ増加。マスク検証は循環的な「マスク効果」説を退ける：2023年3月のマスク緩和後もメイク検索は回復せず、2025年の口紅検索は2019年比36% —— コロナ期の底を下回る。

**The direction holds, but the magnitude is limited.**
Cosmetics search demand fell ~32% across full calendar years 2019→2025 while skincare search held roughly flat — the gap halved, but cosmetics still leads (not a "crossover"). Rakuten Ichiba's catalog carries 3.7× more skincare SKUs than cosmetics. Ingredient-name searches (niacinamide, retinol) rose ~6–7× post-COVID. A mask test rules out the cyclical "mask effect" explanation: makeup search did not recover after Japan relaxed mask guidance in March 2023 — by 2025 lipstick search sat at 36% of its 2019 baseline, below its COVID-era trough.

*Nuance:* スキンケアとコスメのレビュー言語は緩やかに収束しているが、その規模は小さく、サンプルサイズに敏感である。サンプル数を揃えた厳密な比較では Δ +0.065（0.252→0.317、ブートストラップ95%CI [+0.047, +0.083]）。  
*Nuance:* skincare and cosmetics review language is converging slowly, but the effect is small and sample-size sensitive — Δ +0.065 (0.252→0.317, bootstrap 95% CI [+0.047, +0.083]) under a size-matched comparison.

---

## ライブダッシュボード / Live Dashboard

**[Beauty Pulse](https://ss-beauty-pulse.streamlit.app/)** is deployed on Streamlit Community Cloud with an EN/JP language toggle.

| Tab | What it shows |
|---|---|
| 📈 The Shift / 市場変化 | Independent-signal evidence, the mask-rebound test, ingredient search surge, Rakuten treemap, YouTube trends |
| 🔤 The Language / 消費者の言語 | Word clouds by year, size-matched vocabulary convergence |
| 🔍 Discovery / 発見 | Google Trends rising searches, YouTube channel analysis, interactive review map |
| 💡 For brands / ブランドへの示唆 | The four findings translated into prescriptive plays — with an explicit attention-data-≠-sales-data disclaimer |

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced and self-collected. No Kaggle datasets.
```

| ソース / Source | 内容 / Contents | 規模 / Scale |
|---|---|---|
| @cosme | Consumer reviews — used for *language* analysis | 45,510 reviews |
| Rakuten Ichiba API | Product catalog, prices, review counts | 46,193 SKUs · 580,139 weekly rows |
| Amazon | Name, price, aggregate rating, review count | 161 ASINs · 1,124 reviews |
| Google Trends JP | Monthly search interest (2019–2026) | 4,842 rows |
| YouTube Data API v3 | Beauty video comments | 296 videos · 74,679 comments |

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

これは[方法論](METHODOLOGY.md)の注意点12の延長線上にある —— 公開統計（家計調査・経産省生産動態統計）での
検証が次の段階であり、1stパーティデータはその先にある。  
This extends caveat 12 in [Methodology](METHODOLOGY.md): validating against public statistics
(家計調査 household spending, METI shipment data) is the next step; first-party data is the one after.

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

**分析を検証・再実行する / Interrogate or re-run the analysis (NB02 → NB07):**

```bash
pip install -r requirements-analysis.txt
```

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
