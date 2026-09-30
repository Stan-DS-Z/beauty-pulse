# Beauty Pulse — 日本美容市場アナリティクス

**コロナ禍はどのように日本の美容消費を再構成したのか？**  
How did COVID restructure Japanese beauty consumption?

市場の測定：Google検索、経産省の出荷統計、財務省の貿易統計、PR TIMESの新商品リリース。  
Market measures: Google search, METI shipment statistics, 財務省 trade statistics, and PR TIMES product-launch releases.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Dash](https://img.shields.io/badge/Dashboard-Dash-blue)
![SQLite](https://img.shields.io/badge/Data-SQLite-lightgrey)
![NLP](https://img.shields.io/badge/NLP-SudachiPy%20%7C%20TF--IDF%20%7C%20UMAP-violet)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)
![Markets](https://img.shields.io/badge/Market-Japan-white)

<p align="center">
  <a href="https://beautypulse.web.app">
    <img src="https://img.shields.io/badge/%E2%9C%A8_ダッシュボード-beautypulse.web.app-4A90B8?style=for-the-badge" alt="Dashboard">
  </a>
</p>

---

## 仮説 / Hypothesis

> コロナ禍以降、日本の消費者はスキンケアを美容の最優先事項として位置づけるようになった。

> Post-COVID Japanese consumers have structurally reprioritised skincare over cosmetics.

---

## 検証結果：メイクでは確認、スキンケアでは測定不能 / Verdict: Confirmed for makeup, unmeasurable for skincare

**関心は動いた。金額の裏づけは半分しか取れない。**<br><!--f:lead_search_ja-->化粧品の検索は2019→2025年に33%低下し、どの年もスキンケアの検索を上回った<!--/f-->。化粧品は総称で、スキンケアを含む。公的な出荷統計（経産省 生産動態統計）と突き合わせると、検索の所見は二つに分かれる。**メイクは金額でも裏づけられた** —— <!--f:mkt_y0-->2019<!--/f-->→<!--f:mkt_y1-->2025<!--/f-->年にファンデーションの出荷金額は<!--f:found_d-->40<!--/f-->%、口紅は<!--f:lip_d-->44<!--/f-->%減少し、落ち込みは<!--f:mkt_y0-->2019<!--/f-->→<!--f:mkt_pre1-->2021<!--/f-->年に集中する。<!--f:lead_mask_ja-->マスク着用ルール緩和から2年後の2025年、口紅の検索は2019年の34%<!--/f-->。**スキンケアは裏づけられない** —— 金額系列は<!--f:mkt_break-->2022<!--/f-->年1月に断層を持ち、そこをまたいで測った数値は断層の内側で測り直すと符号が反転する（美容液の出荷金額はまたげば-<!--f:serum_val_span-->38<!--/f-->%、内側なら+<!--f:serum_val_post-->23<!--/f-->%）。断層の原因は公表統計に記載がない。<!--f:ytd_y-->2026<!--/f-->年1〜<!--f:ytd_m-->7<!--/f-->月の出荷金額は前年同期比で皮膚用+<!--f:ytd_skin-->7.7<!--/f-->%、仕上用-<!--f:ytd_make-->0.3<!--/f-->%（月次確報）。<!--f:lead_actives_ja-->追跡する10成分のうち8成分で、2022→2025年に検索が<b>15〜59ポイント</b>上昇した。最も伸びたのはアゼライン酸、グルタチオン、トラネキサム酸の3成分である。セラミドとレチナールの変化は、同じ月を再取得したときのばらつき（5ポイント）の範囲内にある。カテゴリ語8語のうち5語は低下した。美容液は18ポイント上昇し、日焼け止めと乳液はばらつきの範囲内だった。<!--/f-->成分単位の需要を追う公的系列はなく、成分名の検索には金額側の対応物がない。

**Attention moved. Only half of it can be checked against money.**<br><!--f:lead_search_en-->Cosmetics (化粧品) search fell 33%, 2019→2025, and stayed above skincare (スキンケア) search in every year<!--/f-->; 化粧品 is the umbrella term and includes skincare. Set against official shipment statistics (METI 生産動態統計), the search finding splits in two. **Makeup is corroborated in yen** — foundation shipped value fell <!--f:found_d-->40<!--/f-->% and lipstick <!--f:lip_d-->44<!--/f-->% over <!--f:mkt_y0-->2019<!--/f-->→<!--f:mkt_y1-->2025<!--/f-->, with the fall concentrated in <!--f:mkt_y0-->2019<!--/f-->→<!--f:mkt_pre1-->2021<!--/f-->, before the break and in lines it does not touch. <!--f:lead_mask_en-->In 2025, two years after mask guidance was relaxed, lipstick search was 34% of its 2019 level<!--/f-->. **Skincare is not** — its money series steps in January <!--f:mkt_break-->2022<!--/f-->, and figures measured across that step reverse sign when measured inside it (serum shipped value reads -<!--f:serum_val_span-->38<!--/f-->% across the break and +<!--f:serum_val_post-->23<!--/f-->% after it). The cause is undocumented in the published statistics, so no skincare demand reading is offered. January–<!--f:ytd_m_en-->July<!--/f--> <!--f:ytd_y-->2026<!--/f--> against the same months of <!--f:mkt_y1-->2025<!--/f-->: skincare shipped value +<!--f:ytd_skin-->7.7<!--/f-->%, makeup -<!--f:ytd_make-->0.3<!--/f-->% (METI monthly 確報). <!--f:lead_actives_en-->Search rose <b>15–59 points</b> for eight of ten tracked actives, 2022→2025, most for azelaic acid, glutathione and tranexamic acid; ceramides and retinal stayed within the 5-point spread between repeat pulls. Of eight category words, five fell, serum rose 18 points, and sunscreen and emulsion stayed within the spread.<!--/f--> No official series tracks ingredient-level demand, so ingredient search has no counterpart in money.

*何が測れるか / What is measured where:* **市場の測定** —— Googleトレンド、経産省 生産動態統計、財務省 貿易統計、PR TIMESのコアパネル —— は測定の枠が本プロジェクトの外で決まっており、スキンケアとメイクの比較や年をまたぐ比較に用いる。検索は関心を、出荷と貿易は金額と数量を測る。**側ごとの測定** —— @cosmeレビューとYouTubeコメント —— は本プロジェクトが各側を深く調べるために収集したもので、言葉を各側の内側で読み、件数や比率を側や年をまたいで比べない。

*What is measured where:* **Market measures** (Google Trends, METI shipments, 財務省 trade statistics HS 3304, the PR TIMES core panel) have a frame set outside this project, and are compared across skincare and makeup and across years: search measures attention, shipments and trade measure yen and kilograms. **Within-side instruments** (@cosme reviews, YouTube comments) were collected by this project for depth on each side; they are read for language within a side, and no count or share from them is compared across sides or years. Rules and reasons: [METHODOLOGY.md](METHODOLOGY.md), Source roles.

---

## ライブダッシュボード / Live Dashboard

**[Beauty Pulse](https://beautypulse.web.app)** はDashアプリで、Google Cloud Run上で動き、Firebase Hosting経由で英語・日本語で配信している。  
**[Beauty Pulse](https://beautypulse.web.app)** is a Dash app on Google Cloud Run, served through Firebase Hosting, in English and Japanese.

| ページ / Page | 内容 / What it shows |
|---|---|
| [Brief / 要旨](https://beautypulse.web.app/brief) | The edition's governing thought and one finding per layer, each linking to its page |
| [Market / 市場](https://beautypulse.web.app/market) | METI shipped value by product line and group, and the January 2022 break; 財務省 imports (HS 3304) by origin |
| [Demand / 需要](https://beautypulse.web.app/demand) | Google Trends: actives, category words, 化粧品 against スキンケア, the makeup terms around the mask years |
| [Supply / 供給](https://beautypulse.web.app/supply) | PR TIMES product-launch releases: category share, issuer origin, 12-month totals, ingredients |
| [Consumer / 消費者](https://beautypulse.web.app/consumer) | The top-30 skincare terms in @cosme reviews and YouTube comments; the review map |
| [Timing / 季節性](https://beautypulse.web.app/timing) | Seasonality by stage: sunscreen search and shipments, METI product lines, search terms, launch releases by month |
| [Method / 手法](https://beautypulse.web.app/method) | Sources, series breaks, the seasonal method, the launch classifier, coverage, and the review-vocabulary record |

---

## 最新版の要旨 / The current edition

**<!--f:edition_ja-->2026年9月版<!--/f-->**（<!--f:cutoff_ja-->2026年8月<!--/f-->までのデータ）の要旨と五つの所見。各所見はそのページにリンクする。
<!--f:brief_ja-->

> 2022年以降、新商品リリースの構成比（以下、リリース構成比）、検索、出荷金額は、それぞれ異なるカテゴリで伸びた。リリース構成比が最も伸びたのは化粧水とクリームで、その出荷金額の変化は-3%〜+2%である。検索が最も伸びたのは、新商品リリースでの言及が少ない成分名である。出荷金額が最も伸びたのはリップクリーム、パウダー、口紅、チーク、クレンジング、日焼け止めである。

- **[市場](https://beautypulse.web.app/market?lang=ja)** — 2022→2025年に出荷金額は皮膚用が<b>+11%</b>、仕上用が<b>+16%</b>となった。仕上用は2019年をなお25%下回る。美容液の+23%は、個数が12%減るなかで1個あたり金額が+39%となったことによる。
- **[需要](https://beautypulse.web.app/demand?lang=ja)** — 追跡する10成分のうち8成分で、2022→2025年に検索が<b>15〜59ポイント</b>上昇した。最も伸びたのはアゼライン酸、グルタチオン、トラネキサム酸の3成分である。セラミドとレチナールの変化は、同じ月を再取得したときのばらつき（5ポイント）の範囲内にある。カテゴリ語8語のうち5語は低下した。美容液は18ポイント上昇し、日焼け止めと乳液はばらつきの範囲内だった。
- **[供給](https://beautypulse.web.app/supply?lang=ja)** — 2022→2025年に、リリース構成比は化粧水とクリームがそれぞれ<b>6ポイント</b>上昇し、アイメイクは14ポイント低下した。コア発行元の新商品リリースのうち韓国系発行元によるものは、2026年1〜6月に<b>49%</b>（289件中141件）で、2022年1〜6月の30%（81件中24件）から上昇した。
- **[消費者](https://beautypulse.web.app/consumer?lang=ja)** — @cosmeレビューのスキンケア上位30語のうち<b>15語</b>が、YouTubeのスキンケア動画へのコメントの上位30語にも入る。
- **[季節性](https://beautypulse.web.app/timing?lang=ja)** — 日焼け止めの出荷金額は<b>2〜4月</b>、検索は5〜7月にピークとなり、2023〜2025年の各年で3カ月の差がある。16品目のうち6品目は、毎年同じ月（前後1カ月以内）に出荷金額が最も多い。

<!--/f-->
**<!--f:edition_en-->Edition September 2026<!--/f-->** (data to <!--f:cutoff_en-->August 2026<!--/f-->): the governing thought and five findings, each linking to its page.
<!--f:brief_en-->

> After 2022, launch share, search and shipped value rose in different categories: launch share rose most in toner and cream, whose shipped value moved -3% to +2%; search rose most for named actives that few launches carry; and shipped value rose most in lip balm, powder, lipstick, blush, cleansing and sunscreen.

- **[Market](https://beautypulse.web.app/market)** — Shipped value rose <b>+11%</b> in skincare and <b>+16%</b> in makeup, 2022→2025; makeup is still 25% below 2019. Serum's +23% came from value per unit (+39%) on 12% fewer units.
- **[Demand](https://beautypulse.web.app/demand)** — Search rose <b>15–59 points</b> for eight of ten tracked actives, 2022→2025, most for azelaic acid, glutathione and tranexamic acid; ceramides and retinal stayed within the 5-point spread between repeat pulls. Of eight category words, five fell, serum rose 18 points, and sunscreen and emulsion stayed within the spread.
- **[Supply](https://beautypulse.web.app/supply)** — Toner and cream gained <b>6 points</b> of launch share each, 2022→2025; eye makeup lost 14. Korean issuers made <b>49%</b> (141 of 289) of core launch releases in 2026 H1, from 30% (24 of 81) in 2022 H1.
- **[Consumer](https://beautypulse.web.app/consumer)** — <b>15 of the top 30</b> skincare terms in @cosme reviews are also in the top 30 of comments on YouTube skincare videos.
- **[Timing](https://beautypulse.web.app/timing)** — Sunscreen shipments peak <b>February–April</b> and search peaks May–July, three months later, in every year from 2023 to 2025. Six of the 16 product lines ship most in the same month, give or take one, every year.

<!--/f-->

### 版 / Editions

レポートの各版は、発行時にすべてのソースで揃っている最後の月でデータを締める。`issue_edition.py` がレポートの読むファイルを `dashboard/assets/editions/<版>/` に凍結し、各ファイルのハッシュをマニフェストに記録する。レポートの各ページはこのフォルダだけを読む。版を後から補う場合は、日付つきの追補としてマニフェストに記録し、締め月までのデータから導いたファイルを加えるだけとする。新しいソースデータは次の版まで入らない。`issue_edition.py --check` は、変更されたファイルやマニフェストにないファイルがあれば失敗する。  
Each report edition cuts its data at the last month complete in every source at issue. `issue_edition.py` freezes the files the report reads into `dashboard/assets/editions/<edition>/`, with each file's hash in a manifest, and the report pages read only that folder. A dated amendment, recorded in the manifest, only adds files derived from data inside the cut-off; new source data waits for the next edition. `issue_edition.py --check` fails if a frozen file has changed or an unlisted one has appeared.

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced and self-collected. No Kaggle datasets.
```

**市場の測定 / Market measures** —— 測定の枠が本プロジェクトの外で決まり、スキンケアとメイク、年をまたいで比べる。 Frame set outside this project; compared across sides and years.
<!--f:sources_market-->

| ソース / Source | 測るもの / Measures | 収録範囲 / Coverage | 掲載ページ / Report pages |
|---|---|---|---|
| METI 生産動態統計 | Manufacturers' monthly shipments for 33 product lines: value, units, kilograms | Monthly, Jan 2019 – Jul 2026 | Brief · Market · Timing |
| 財務省 貿易統計 HS 3304 | Imports by country of origin, all HS 3304 sub-codes | Annual, 2016–2025 | Market |
| Google Trends JP | Search interest per term; each request is scaled to its own peak of 100 | Monthly, Jan 2019 – Aug 2026 | Brief · Demand · Timing |
| PR TIMES | Product-launch releases from 30 core issuers (41 feeds) | Per release, Sep 2021 – 31 Aug 2026 | Brief · Supply · Timing |

<!--/f-->
**側ごとの測定 / Within-side instruments** —— 各側を深く調べるために本プロジェクトが収集し、側の内側で読む。 Collected by this project for depth on each side; read within a side.
<!--f:sources_within-->

| ソース / Source | 測るもの / Measures | 収録範囲 / Coverage | 掲載ページ / Report pages |
|---|---|---|---|
| @cosme | 39,978 reviews of more than 20 characters in 10 product categories | Reviews dated 2019 – 17 May 2026 | Consumer |
| YouTube | 296 videos from 145 channels, found by 15 search categories, and their comments | Comments to 12 Jun 2026 | Consumer |

<!--/f-->
**収集済み、どのレポートページにも用いない / Collected, used on no report page**
<!--f:sources_unused-->

| ソース / Source | 測るもの / Measures | 収録範囲 / Coverage | 掲載ページ / Report pages |
|---|---|---|---|
| Google Trends related searches | Related queries for seed terms | pull date not recorded | None: its pull records no date or window |
| Rakuten Ichiba | Product listings from weekly ranking pulls | 22 weekly pulls, 2 Apr 2026 – 20 Sep 2026 | None: its frozen snapshot is dated after the cut-off, and its genres mix a parent genre with its subgenres |
| Amazon JP | Product listings and reviews | 3 pulls, the last dated 13 Jun 2026 | None: its products carry no category |

<!--/f-->
件数は版が保持するものだけを示す。 Counts are shown only where the edition's files hold them.

再現は `build_estat_shipments.py` と `build_estat_imports.py`（要 `ESTAT_APP_ID`）。表IDは `getStatsList` で確認した日付とともに各スクリプトに記載している —— IDは安定しておらず、広く引用されているMETIのIDは2010年の単月表を指す。経産省の最新の年次表より後の月は月次確報から取る。貿易統計はデータベースを同じ表のCSVファイルと突き合わせ、データベースにない品目（2024年以降の3304.99-010）をファイルから補う。いずれのファイルも `getDataCatalog` で探す。  
Rebuild with `build_estat_shipments.py` and `build_estat_imports.py` (`ESTAT_APP_ID` required). Each script lists its table IDs with the date they were confirmed against `getStatsList`: the IDs are not stable, and the commonly cited METI one resolves to a single month of 2010. Months after the last yearly METI table come from the monthly 確報 workbook. The trade pull checks the database against the same table's CSV file and takes lines the database lacks (3304.99-010 from 2024) from the file. Both files are found through `getDataCatalog`.

レビュー「量」は取得設計に依存するため市場シグナルとして用いず、レビュー「テキスト」のみを語彙分析に使用する。本文は一覧ページに表示されるプレビューである —— 詳細は[方法論](METHODOLOGY.md)。  
Review *volume* depends on scraping design, so only review *text* is used, for vocabulary analysis. Bodies are the previews shown on the listing pages — see [Methodology](METHODOLOGY.md).

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
Dash         4.2.0     # Web app: pages, callbacks, EN/JA routing
Plotly       5.24.1    # Charts (version pinned for API stability)
gunicorn     26.0.0    # WSGI server in the Cloud Run image
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
| NB05 | Google Trends search: 化粧品 against スキンケア on one scale, and ingredient search |
| NB06 | Discovery layer — cosine similarity and sample size, topic modelling, review mapping, search discovery |
| NB07 | Executive synthesis + dashboard asset generation |

**Execution order:** NB02 → NB02b → NB02c → NB03 → NB04 → NB05 → NB06 → NB07 → the root `build_*.py` scripts → `issue_edition.py` → `dashboard/app.py`

---

## 方法論と改訂履歴 / Methodology & Revision History

情報源の役割、注意点、日付つきの改訂履歴は[**方法論と改訂履歴**](METHODOLOGY.md)にまとめている。コミットごとにテストスイートがCIで走り、次の検査を含む：版のマニフェスト（凍結したファイルが変わっていないこと）、撤回した指標の言い回しの検査（`tests/retired_phrases.py`：撤回した指標の表現がサイトや文書に現れると失敗する）、公表数値の検査（`build_docs_figures.py --check`：READMEとMETHODOLOGYの数値と文が、版から計算した値と一致すること）。  
Source roles, caveats and the dated revision log are in [**Methodology & Revision History**](METHODOLOGY.md). The test suite runs in CI on every commit, and includes the edition manifest check (no frozen file has changed), the retired-phrases test (`tests/retired_phrases.py`: wording of a withdrawn measure fails on the site and in the docs) and the published-figures check (`build_docs_figures.py --check`: every figure and sentence marked in the README and METHODOLOGY equals what the edition computes).

---

## 公開データで測れること・測れないこと / What This Data Can and Cannot Show

検索は関心を測り、経産省の出荷統計と財務省の貿易統計は市場の金額と数量を測る。転換率、再購買、ブランド別の売上を測るものはない。
左列は公開データで測れた範囲、右列は同じ問いを1stパーティデータに当てたときに解ける指標である。  
Search measures attention; METI shipments and 財務省 trade statistics measure market value and volume. Nothing here measures conversion, repeat purchase or brand sales.
The left column is what public data measured; the right is what the same questions resolve into against first-party data.

| 本プロジェクトで測れたもの / Measured here | 1stパーティデータで解ける問い / Resolvable with first-party data |
|---|---|
| Googleトレンドの検索需要 / Search demand (Google Trends) | 獲得単価・広告転換率 / Paid-search CPA and conversion |
| @cosmeのレビュー言語 / Review language (@cosme) | CRM・アプリ内行動・再購買率 / CRM, in-app behaviour, repeat rate |
| 経産省の品目別出荷金額 / METI shipped value by product line | SKU別のPOS実売・在庫回転・粗利 / POS sell-through by SKU, stock turns, margin |

残る限界は三つ: 経産省統計の年次値は<!--f:mkt_y1-->2025<!--/f-->年まで、<!--f:ytd_y-->2026<!--/f-->年は1〜<!--f:ytd_m-->7<!--/f-->月の月次確報で、年報の公表時に改定される。皮膚用の金額系列は<!--f:mkt_break-->2022<!--/f-->年1月に断層があり、またいだ測定はできない。家計調査は未取得で、かつ**美容液と日焼け止めの品目を持たない** —— 最も動いたカテゴリを検証できる系列ではない。1stパーティデータはその先にある。  
Three limits remain. METI annual figures run to <!--f:mkt_y1-->2025<!--/f-->; <!--f:ytd_y-->2026<!--/f--> is January–<!--f:ytd_m_en-->July<!--/f--> from the monthly 確報 release and is revised when the yearly table opens. The skincare money series breaks in January <!--f:mkt_break-->2022<!--/f-->, so it cannot be measured across that point. And 家計調査 (household spending) is not pulled — it would be immune to the tourist and export effects, but it carries **no 美容液 line and no sunscreen line**, so it cannot test the categories that moved most. First-party data is the step after.

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
python dashboard/app.py           # http://localhost:8050
```

**分析を検証・再実行する / Interrogate or re-run the analysis (NB03 → NB07):**

```bash
pip install -r requirements-analysis.txt
```

主データベースはgitignoreされているため、クローンには含まれない。`src.schema.get_connection()`
は同梱の公開DBに自動でフォールバックし（初回のみ`dashboard/assets/`から`data/`へ展開）、
読み取り専用で開く。クローンから動くのはNB03・NB04b・NB05 —— 市場層とSQL層である。NB04・NB06・NB07は
動かない。語彙分析が読むレビュー本文とYouTubeコメント本文は第三者の文章であり、公開DBには含めていない。
これらのノートブックの結果は`dashboard/assets/`のCSVとして同梱されており、計算過程はノートブックで読める。
NB02も動かない —— 未公開の生データを要する。

The primary database is gitignored, so a clone does not have it.
`src.schema.get_connection()` falls back to the bundled public DB — extracting it from
`dashboard/assets/` into `data/` once — and opens it read-only. From a clone this runs NB03,
NB04b and NB05: the SQL layer and the market layer. NB04, NB06 and NB07 do not run. The
vocabulary analysis reads review bodies and YouTube comment bodies, which are text other
people wrote, and the public DB does not carry it. Their outputs ship as the CSV assets in
`dashboard/assets/`, and the method stays readable in the notebooks. NB02 does not run
either: it ingests raw data that is not published.

**リポジトリの範囲 / Repository scope:**  
公開：分析ノートブック（NB02〜NB07）、ダッシュボード、CSVアセット、`signal_pulse_public.db.gz`（照会可能なデータセット。商品名・生JSON・レビュー本文・YouTubeコメント本文を削除。`gunzip`して利用）。  
ローカルのみ：収集ノートブック（NB01x）、生データ、主データベース。  
Public: analysis notebooks (NB02–NB07), the dashboard, CSV assets, and `signal_pulse_public.db.gz` — a queryable dataset with product names, raw JSON, review bodies and YouTube comment bodies stripped (`gunzip` it first). Local-only: the collection notebooks (NB01x), raw data, and the primary database. From the public repo you can run the dashboard, query the public DB, and audit every analysis step against it.

---

## プロジェクトの背景 / Context

このプロジェクトは、日本の美容・FMCGアナリティクスへのキャリアピボットを目的としたデータポートフォリオ作品。自己収集データの構築（Kaggle不使用）、日本語NLPパイプライン、SQLite設計、Dashダッシュボードの展開を含む。

This project forms one half of a data analytics portfolio targeting Japanese beauty and FMCG analytics roles. It demonstrates self-sourced data construction, Japanese NLP, SQL architecture, and deployed dashboard work — built as a complement to [The Masstige Moment](https://github.com/Stan-DS-Z/the-masstige-moment), which analyses the same market from a top-down revenue perspective.

**Built with free, public APIs.**

---

*Analysis by Stanley Shi · [LinkedIn](https://www.linkedin.com/in/stanley-shi-7b604b104/) · 2026*
