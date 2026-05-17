# Beauty Pulse — 日本美容市場アナリティクス

**コロナ禍はどのように日本の美容消費を再構成したのか？**  
How did COVID restructure Japanese beauty consumption?

検索行動・商品カタログ・成分検索・YouTube・消費者レビュー — 複数の独立した signal を、懐疑的に突き合わせる。  
Search behaviour, product catalog, ingredient searches, YouTube discourse, and consumer reviews — multiple independent signals, cross-checked skeptically.

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
> 「正直なスキンケア」が「演出するコスメ」を、構造的に凌駕している。

> Post-COVID Japanese consumers have structurally reprioritised skincare over cosmetics.  
> "Honest skincare" has displaced "performance cosmetics" as the dominant consumer concern.

---

## 検証結果：部分的に確認（限定的） / Verdict: Partially Confirmed

**方向性は支持されるが、初版の強い主張は監査により下方修正された。**
独立した方法論監査（懐疑的なピアレビュー）の結果、構造的変化の*方向*は維持されたが、その*規模*は当初の主張より小さい。コロナ後、化粧品の検索需要は約35%低下した一方、スキンケアの検索はほぼ横ばい —— 両者の差は半減したが、化粧品が依然として上回る（「逆転」ではない）。楽天市場のカタログはスキンケアSKUがコスメの4.1倍。成分名検索（ナイアシンアミド・レチノール）はコロナ後に約6〜7倍に急増。

**The direction is supported, but v1's strong claims were revised down by audit.**
An independent methodology audit (skeptical peer review) preserved the *direction* of the structural shift but cut its *magnitude*. Post-COVID, cosmetics search demand fell ~35% while skincare search held roughly flat — the gap halved, but cosmetics still leads (this is **not** a "crossover"). Rakuten Ichiba's catalog carries 4.1× more skincare SKUs than cosmetics. Ingredient-name searches (niacinamide, retinol) surged ~6–7× post-COVID.

*Nuance:* スキンケアとコスメのレビュー言語は緩やかに収束しているが、当初報告した収束の規模（0.39→0.70）の大部分はサンプルサイズのアーティファクトだった。サンプル数を揃えた厳密な比較では、収束は実在するがはるかに小さい（Δ +0.06）。  
*Nuance:* skincare and cosmetics review language is converging slowly, but most of the originally reported magnitude (0.39→0.70) was a sample-size artifact. Under a size-matched comparison the convergence is real but much smaller (Δ +0.06).

> **正直さについての注記 / A note on honesty.** この結論の根拠は、初版から二度にわたり改訂されている。@cosmeレビューの「量」に基づく指標、期間横断のTF-IDF語彙デルタ、そして「Googleトレンドの逆転」は、いずれも後のデータ修正・方法論監査で問題が判明し、撤回または再定義された。詳細は[分析の改訂履歴](#分析の改訂履歴--analysis-revision-history)を参照。**過去の弱い分析を公開の場で上書きすることは、本プロジェクトの設計思想である。**  
> The evidence behind this verdict has been revised twice. Metrics based on @cosme review *volume*, pooled TF-IDF term deltas, and a "Google Trends crossover" were each found flawed by later data correction and methodology audit, and retired or rescoped — see [Analysis Revision History](#分析の改訂履歴--analysis-revision-history). **Overwriting prior, weaker analysis in public is a design principle of this project.**

---

## 主要な発見 / Key Findings

監査を経て維持された signal のみを記載する（撤回・再定義された指標は改訂履歴を参照）。  
Only signals that survived the audit are listed (retired/rescoped metrics are in the revision history).

| シグナル / Signal | 値 / Value | ソース / Source |
|---|---|---|
| 化粧品の検索需要の低下 / Cosmetics search-demand decline | 85.6 → **56.0** (−35%) | Google Trends (anchored) |
| スキンケア:化粧品 検索比の上昇 / Skincare-to-cosmetics search ratio | 0.31 → **0.58** | Google Trends (anchored) |
| 楽天SKU比率（スキンケア:コスメ）/ Rakuten SKU ratio | **4.1×** | Rakuten Ichiba |
| ナイアシンアミド検索 / Niacinamide search interest | 11 → **74** | Google Trends |
| レチノール検索 / Retinol search interest | 11 → **69** | Google Trends |
| 語彙収束（サンプル数を揃えた厳密値）/ Vocabulary convergence (size-matched) | **Δ +0.06** [95%CI +0.05, +0.08] | @cosme reviews |

---

## 発見の詳細 / What the Data Found

### 発見1 — 構造的変化は複数の独立シグナルで支持される（規模は控えめ）

@cosmeのレビュー「量」は構造的変化の指標として用いていない（理由は[改訂履歴](#分析の改訂履歴--analysis-revision-history)）。代わりに、消費者行動を直接反映する独立シグナルに依拠する。
**Googleトレンド（アンカー付き＝期間横断比較が可能なデータ）では、化粧品の検索需要が2019→2026年に約35%低下した一方、スキンケアの検索はほぼ横ばい。** 両者の差は半減したが、化粧品の検索量は依然としてスキンケアを上回る —— 初版が主張した「2020年の逆転」は、比較不可能なデータ（非アンカーのblock_A）に基づく誤りであった。楽天市場のカタログはスキンケア商品数がコスメの4.1倍（棚シェア）。成分名検索の急増（ナイアシンアミド・レチノールとも約6〜7倍）は、消費者がブランドではなく知識を求め始めたことを示す。

**Finding 1 — The Structural Shift Is Supported by Independent Signals (Modest in Size)**  
@cosme review *volume* is not used as a shift metric (see [revision history](#分析の改訂履歴--analysis-revision-history)). The finding rests on signals that directly reflect consumer behaviour. **In anchored Google Trends data (the only block where the two terms are cross-comparable), cosmetics search demand fell ~35% from 2019 to 2026 while skincare search held roughly flat.** The gap halved — but cosmetics still out-searches skincare in every year; v1's "2020 crossover" was an error built on non-comparable, unanchored data (block_A). Rakuten Ichiba's catalog carries 4.1× more skincare SKUs than cosmetics (shelf share). An ingredient-search surge (niacinamide and retinol both ~6–7×) shows consumers seeking knowledge, not brands.

---

### 発見2 — スキンケアとコスメの語彙はわずかに収束した（初版の主張を大幅に下方修正）

@cosmeの貢献は「量」ではなく「言語」にある。初版では、各期間内でスキンケアレビューとコスメレビューの語彙コサイン類似度が0.39（2021–22）から0.70（2023–25）へ上昇したと報告した。
**独立した方法論監査により、この上昇の大部分がサンプルサイズのアーティファクトであることが判明した。** プールされたコーパス間のTF-IDFコサイン類似度は、サンプル数とともに機械的に上昇する —— 同一の2023–25年データを用いても、コサイン類似度はN=150件で0.31、N=6,000件で0.66まで上昇する（語彙の被覆率がサンプル数で変わるため）。初版のブートストラップCIは固定サンプルサイズ内での分散しか測っておらず、この期間間のサンプル数の非対称性を検出できなかった。
**全スライスを同一サンプルサイズ（各249件）に揃えた厳密な比較**では、収束は依然として存在するが、はるかに小さい：**0.25 → 0.32、Δ +0.06**（ブートストラップ95%CI [+0.05, +0.08]、ゼロを除外）。
結論：語彙の収束は実在し統計的にも頑健だが、その規模は初版が主張した値（Δ +0.31）の約5分の1。@cosmeは語彙が「緩やかに近づいている」ことを示すが、「劇的な融合」ではない。

**Finding 2 — Skincare and Cosmetics Language Converged Slightly (v1 Claim Cut Sharply)**  
@cosme's contribution is *language*, not volume. v1 reported the within-period cosine similarity of skincare-review vs cosmetics-review vocabulary rising from 0.39 (2021–22) to 0.70 (2023–25).  
**An independent methodology audit found most of that rise was a sample-size artifact.** TF-IDF cosine similarity between *pooled* corpora rises mechanically with sample size — on the *identical* 2023–25 data, the cosine climbs from 0.31 at N=150 reviews to 0.66 at N=6,000 (vocabulary coverage scales with N). v1's bootstrap CI measured only variance within fixed sample sizes; it could not detect the across-period size asymmetry.  
Under a **size-matched comparison** (all slices equalised to 249 reviews), a convergence still exists but is far smaller: **0.25 → 0.32, Δ +0.06** (bootstrap 95% CI [+0.05, +0.08], excludes zero).  
Conclusion: the convergence is real and statistically robust, but roughly one-fifth the magnitude v1 claimed (Δ +0.31). @cosme shows vocabulary drifting slowly closer — not a dramatic merger.

---

### 発見3 — 21,058件のレビューを「地図」にすると、構造が見える

レビューの語彙を空間的に可視化（UMAP + HDBSCAN）すると、コーパスは離散的なセグメントではなく連続体であることが分かる（約28%がどのクラスタにも属さない「ノイズ」）。  
注目すべきは、インフルエンサー・モニターレビュー（「プレゼント」「当選」テンプレート）が、指示なしに自動的にオーガニックレビューと分離されたこと。この2集団を区別せずにセンチメント分析を行うブランドは、異なるシグナルを混在させている。これは規模の主張ではなく定性的構造の観察であり、サンプルサイズの影響を受けない。

**Finding 3 — Mapping 21,058 Reviews Reveals Structure**  
Visualising review vocabulary spatially (UMAP + HDBSCAN) shows the corpus is a continuum, not discrete segments — ~28% of reviews resist any cluster.  
Notably, influencer/giveaway reviews (「プレゼント」/「当選」 template language) separated automatically from organic consumer reviews — without being told to. Brands measuring sentiment without filtering these populations are mixing two different signals. This is a qualitative-structure observation, not a magnitude claim, and is unaffected by sample size.

---

### 発見4 — 韓国ブランドが日本の需要を取り込んでいる

コロナ期：消費者は成分名を検索していた（レチノール・ナイアシンアミドが複数の独立した検索起点で浮上）。ブランドではなく知識を求めていた。  
直近：アヌア（韓国ブランド）が4つの独立した検索語で最強シグナルを記録。構造的変化が消費者を教育し、韓国ブランドがその恩恵を受けている。

**Finding 4 — Korean Brands Are Harvesting Japanese Demand**  
COVID era: consumers searched for ingredient names (retinol, niacinamide appeared across multiple independent search starting points) — building knowledge, not searching for brands.  
Recent window: Anua (アヌア, a Korean brand) is the single strongest signal, appearing across 4 independent search terms. The structural shift educated consumers; Korean brands captured them.

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced and self-collected. No Kaggle datasets.
```

| ソース / Source | 内容 / Contents | 規模 / Scale |
|---|---|---|
| @cosme | Consumer reviews — used for *language* analysis | 45,510 reviews |
| Rakuten Ichiba API | Product catalog, prices, review counts | 36,386 SKUs |
| Amazon | Name, price, aggregate rating, review count | 111 ASINs · 1,079 reviews |
| Google Trends JP | Weekly search interest (2019–2026) | 4,635 rows |
| YouTube Data API v3 | Beauty video comments | 248 videos · 60,676 comments |

**@cosmeデータの役割と限界 / The role and limits of @cosme data:**  
@cosmeはカテゴリ単位で取得している。レビュー「量」は取得設計（カテゴリ数）に依存するため市場シグナルとして用いず、レビュー「テキスト」のみを語彙分析に使用する。なお、レビュー本文は一覧ページのプレビュー（約76字、約67%が末尾省略）であり、全文ではない —— 個別ページの全文取得には数万件規模の追加スクレイピングが必要となるため、計算資源が限られた個人プロジェクトとして、また@cosmeのサーバ負荷を抑える判断から、プレビュー本文を用いている。この打ち切りはスキンケア・コスメ両方に等しく作用するため、カテゴリ間の比較は妨げないが、分析の語彙的な深さは制限される。  
@cosme is scraped category-by-category. Review *volume* depends on scraping design, so only review *text* is used, for vocabulary analysis. Note that review bodies are listing-page **previews** (~76 chars, ~67% end mid-sentence), not full text — fetching full bodies would require tens of thousands of extra per-review page requests; as a personal/portfolio project with limited compute, and to avoid putting heavy load on @cosme's servers, the analysis uses preview text. The truncation applies equally to skincare and cosmetics, so it does not bias the cross-category comparisons, but it does limit the lexical depth of the analysis.

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
- **One canonical join path:** `reviews.category_id` is authoritative for review-level tier; `products.category_id` is reconciled to it during ingestion (see revision history)
- **Explainable NLP progression:** term importance scoring → topic modelling → dimensionality reduction — each step has a clear analytical purpose
- **Privacy-aware deployment:** public dashboard uses `signal_pulse_public.db` with product names and raw JSON stripped
- **Reproducible from raw data:** the database rebuilds cleanly from raw files via `NB02 → … → NB07`

---

## ノートブック構成 / Notebook Pipeline

| Notebook | Purpose |
|---|---|
| NB01a–e | Data collection (Rakuten API, @cosme, Amazon JP, Google Trends, YouTube) |
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

## ライブダッシュボード / Live Dashboard

**[Beauty Pulse](https://ss-beauty-pulse.streamlit.app/)** is deployed on Streamlit Community Cloud with an EN/JP language toggle.

| Tab | What it shows |
|---|---|
| 📈 The Shift / 市場変化 | Independent-signal evidence, ingredient search surge, Rakuten treemap, YouTube trends |
| 🔤 The Language / 消費者の言語 | Word clouds by year, size-matched vocabulary convergence |
| 🔍 Discovery / 発見 | Google Trends rising searches, YouTube channel analysis, interactive review map |

---

## 分析の改訂履歴 / Analysis Revision History

> このプロジェクトは継続的なデータ精緻化と方法論監査を経ている。過去の不十分な分析を上書きし改善することは、本プロジェクトの設計思想である —— 隠すべき欠陥ではない。  
> This project undergoes continuous data refinement and methodology audit. Overwriting and improving prior, weaker analysis is a design principle here — not a flaw to hide.

**改訂1 — @cosmeカテゴリ分類の修正 / Revision 1 — @cosme category correction**  
@cosmeはランキングのカテゴリ体系を移行しており、旧IDは無言のまま無関係なカテゴリを返していた（HTTP 200のためエラーは表面化せず）。商品名とカテゴリラベルの不一致から検出し、検証済みの現行IDで@cosme全体を再取得した。  
@cosme had migrated its ranking taxonomy; stale category IDs silently resolved to unrelated categories while returning HTTP 200. Detected via product-name/category mismatches, then re-scraped in full against verified current IDs.

**改訂2 — サンプリング由来の指標を撤回 / Revision 2 — retiring sampling-artifact metrics**  
クリーンな再構築により、初期分析の2指標がアーティファクトと判明し撤回した：(a) **@cosmeレビュー量シェア** —— 取得カテゴリ数（スキンケア7：コスメ3）に支配されていた；(b) **期間横断のTF-IDF語彙デルタ** —— コーパスの年次構成比に交絡していた。  
A clean rebuild exposed two v1 metrics as artifacts, both retired: (a) **@cosme review-volume share** — driven by the count of categories scraped per tier (7 skincare : 3 cosmetics); (b) **pooled cross-period TF-IDF deltas** — confounded by the corpus's year-over-year tier composition.

**改訂3 — 独立した方法論監査 / Revision 3 — independent methodology audit**  
新しいインスタンスによる懐疑的なピアレビューを実施し、その指摘を検証のうえ反映した：
A skeptical peer review by a fresh, context-free reviewer was commissioned; its findings were verified and acted on:
- **語彙収束の再定義 / Convergence rescoped.** プールされたコーパス間のTF-IDFコサイン類似度はサンプル数とともに機械的に上昇する。初版の0.39→0.70はその大部分がサンプルサイズのアーティファクトだった。サンプル数を揃えた厳密な比較で再計算し、より小さく頑健な値（Δ +0.06）に再定義 —— 「主力の発見」から格下げした。 / TF-IDF cosine between pooled corpora rises with sample size; v1's 0.39→0.70 was largely a size artifact. Recomputed under a size-matched comparison and rescoped to a smaller, robust value (Δ +0.06) — downgraded from "headline finding."
- **Googleトレンド比較の修正 / Trends comparison corrected.** 初版は非アンカーのblock_A（各語が独立に正規化され、語間比較が不可能）で「2020年の逆転」を主張していた。アンカー付きのblock_Bで再分析 —— 逆転はなく、化粧品の検索が約35%低下し差が半減した、という所見に修正。 / v1 claimed a "2020 crossover" using unanchored block_A (each term normalised to its own peak — not cross-comparable). Re-analysed on the anchored block_B: no crossover; reframed as cosmetics search falling ~35% with the gap halving.
- **カテゴリ結合経路の統一 / Canonical join path.** `products.category_id`と`reviews.category_id`の不整合を解消し、レビュー単位の正規経路に統一（NB02で取り込み時に調整）。 / Reconciled a `products.category_id` vs `reviews.category_id` inconsistency onto a single canonical review-level path (handled in NB02 at ingestion).
- **プレビュー打ち切りの開示 / Preview-truncation disclosed.** @cosmeレビュー本文が一覧ページのプレビューである点を方法論注記に明示。 / Disclosed that @cosme review bodies are listing-page previews (see Methodological Caveats).

---

## 方法論的注意点 / Methodological Caveats

1. **TF-IDFコサイン類似度のサンプルサイズ依存 / Sample-size dependence of TF-IDF cosine**  
   プールされたコーパス間のコサイン類似度は、語彙被覆率がサンプル数とともに増えるため機械的に上昇する。期間横断の収束比較は、必ずサンプル数を揃えて行う必要がある（発見2参照）。  
   Cosine similarity between pooled corpora rises mechanically with sample size as vocabulary coverage grows. Any cross-period convergence comparison must be size-matched (see Finding 2).

2. **Googleトレンドのアンカー / Google Trends anchoring**  
   非アンカーのクエリ（block_A）は各語を独自のピークに正規化するため、語間比較に使えない。スキンケア対化粧品の比較はアンカー付きのblock_Bのみを用いる。  
   Unanchored queries (block_A) normalise each term to its own peak and cannot be compared across terms. The skincare-vs-cosmetics comparison uses only the anchored block_B.

3. **@cosmeレビュー本文の打ち切り / @cosme review-text truncation**  
   レビュー本文は一覧ページのプレビュー（約76字、約67%が末尾省略）。全文取得は計算資源・サーバ負荷の観点から見送った。打ち切りは両カテゴリに等しく作用するため比較は妨げないが、語彙的な深さは制限される。  
   Review bodies are listing-page previews (~76 chars, ~67% truncated). Full-text scraping was deferred for compute and server-load reasons. Truncation applies equally to both tiers, so it does not bias comparisons, but limits lexical depth.

4. **コーパス構成の交絡 / Corpus-composition confound**  
   @cosmeコーパスのカテゴリ構成比は年により変動する。両カテゴリを合算した期間横断比較（量シェア・語彙頻度デルタ）は交絡するため撤回済み。期間「内」のカテゴリ間比較（サンプル数を揃えた語彙収束）はこの交絡を受けない。  
   The @cosme corpus's category mix varies by year. Pooled cross-period comparisons (volume share, term-frequency deltas) are confounded and were retired. Within-period, size-matched tier-vs-tier comparison (vocabulary convergence) is not affected.

5. **SKU数 ≠ 売上高・需要 / SKU count ≠ sales or demand**  
   楽天カタログのSKU比率（4.1×）は棚占有率であり、GMVとは一致しない。さらに、SKU数はカタログ取得設計（どのジャンルをどの深さで取得したか）にも依存し、純粋な消費者選択の指標ではない。  
   The Rakuten SKU ratio (4.1×) measures shelf share, not GMV. It also reflects catalog-acquisition design (which genres were scraped, at what depth) and is not a pure consumer-choice signal.

6. **検索発見シグナルの正規化 / Search discovery signal normalisation**  
   検索起点ごとのボリュームは比較不可。メトリクスは起点内で独立に正規化済み。ツリーマップは相対的シグナル強度を示す。  
   Search volumes are not comparable across starting terms. Metrics are normalised within each starting term; treemaps show relative signal strength.

7. **ソースの非独立性 / Source non-independence**  
   @cosmeレビューと楽天カタログは共にRakutenグループのデータ。厳密に独立なソースはGoogleトレンドとYouTube。  
   The @cosme review corpus and Rakuten catalog are both Rakuten Group data. Strictly independent sources are Google Trends and YouTube.

8. **SudachiPy Mode Cの複合語分割 / Compound word splitting**  
   ナイアシンアミド → ナイアシン + アミドに分割される。成分検出はTF-IDF経由ではなく生テキスト検索で実施。  
   Niacinamide splits into niacin + amide under Mode C. Ingredient detection uses raw text search, not TF-IDF.

9. **レビュアー選択バイアス / Reviewer selection bias**  
   @cosmeレビューは自発的に書き込む消費者のみを反映する。トピックモデルはモニターレビューのバイアスを自律的に検出した（NB06）。  
   @cosme reviews reflect only consumers who choose to write. Topic modelling autonomously identified the giveaway-template bias (NB06).

10. **中国除外 / China exclusion**  
    楽天クロスボーダーおよびインバウンド需要は未定量化。  
    Rakuten cross-border and inbound demand from China is not quantified.

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
自己収集データの構築（Kaggle不使用）、日本語NLPパイプライン、SQLite設計、Streamlitダッシュボード展開、そして継続的なデータ精緻化と方法論監査を含む。

This project forms one half of a data analytics portfolio targeting Japanese beauty and FMCG analytics roles.  
It demonstrates self-sourced data construction, Japanese NLP, SQL architecture, deployed dashboard work, and continuous data refinement under audit —  
built as a complement to [The Masstige Moment](https://github.com/Stan-DS-Z/the-masstige-moment), which analyses the same market from a top-down revenue perspective.

**Built with free, public APIs.**

---

![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)
![Data](https://img.shields.io/badge/Data-Self--sourced-blue)
![NLP](https://img.shields.io/badge/NLP-Japanese-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

*Analysis by Stanley Shi · [LinkedIn](https://www.linkedin.com/in/stanley-shi-7b604b104/) · 2026*
