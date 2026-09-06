# 方法論と改訂履歴 / Methodology & Revision History

> [Beauty Pulse](README.md) の方法論的注意点と、データ修正・方法論監査による改訂の記録。  
> Methodological caveats for [Beauty Pulse](README.md), and the record of revisions from data
> correction and methodology audit.
>
> 本文中の「発見1〜4」は[ダッシュボード](https://ss-beauty-pulse.streamlit.app/)で提示している4つの発見を指す。  
> References to Findings 1–4 below are the four findings presented on the
> [dashboard](https://ss-beauty-pulse.streamlit.app/).

---

## 分析の改訂履歴 / Analysis Revision History

> 以下は、データ修正と方法論監査による改訂の記録である。  
> Below is the record of revisions from data correction and methodology audit.

**改訂1 — @cosmeカテゴリ分類の修正 / Revision 1 — @cosme category correction**  
@cosmeはランキングのカテゴリ体系を移行しており、旧IDは無言のまま無関係なカテゴリを返していた（HTTP 200のためエラーは表面化せず）。商品名とカテゴリラベルの不一致から検出し、検証済みの現行IDで@cosme全体を再取得した。  
@cosme had migrated its ranking taxonomy; stale category IDs silently resolved to unrelated categories while returning HTTP 200. Detected via product-name/category mismatches, then re-scraped in full against verified current IDs.

**改訂2 — サンプリング由来の指標を撤回 / Revision 2 — retiring sampling-artifact metrics**  
クリーンな再構築により、初期分析の2指標がアーティファクトと判明し撤回した：(a) **@cosmeレビュー量シェア** —— 取得カテゴリ数（スキンケア7：コスメ3）に支配されていた；(b) **期間横断のTF-IDF語彙デルタ** —— コーパスの年次構成比に交絡していた。  
A clean rebuild exposed two v1 metrics as artifacts, both retired: (a) **@cosme review-volume share** — driven by the count of categories scraped per tier (7 skincare : 3 cosmetics); (b) **pooled cross-period TF-IDF deltas** — confounded by the corpus's year-over-year tier composition.

**改訂3 — 方法論の見直し / Revision 3 — methodology review**  
分析手法を見直し、以下を検証・修正した：
The analysis methodology was reviewed; the following were verified and corrected:
- **語彙収束の再定義 / Convergence rescoped.** プールされたコーパス間のTF-IDFコサイン類似度はサンプル数とともに機械的に上昇する。初版の0.39→0.70はその大部分がサンプルサイズのアーティファクトだった。サンプル数を揃えた厳密な比較で再計算し、より小さく頑健な値（Δ +0.065）に再定義し、主力の発見からは外した。 / TF-IDF cosine between pooled corpora rises with sample size; v1's 0.39→0.70 was largely a size artifact. Recomputed under a size-matched comparison and rescoped to a smaller, robust value (Δ +0.065); no longer treated as a headline finding.
- **Googleトレンド比較の修正 / Trends comparison corrected.** 初版は非アンカーのblock_A（各語が独立に正規化され、語間比較が不可能）で「2020年の逆転」を主張していた。アンカー付きのblock_Bで再分析 —— 逆転はなく、化粧品の検索が約35%低下し差が半減した、という所見に修正。 / v1 claimed a "2020 crossover" using unanchored block_A (each term normalised to its own peak — not cross-comparable). Re-analysed on the anchored block_B: no crossover; reframed as cosmetics search falling ~35% with the gap halving.
- **カテゴリ結合経路の統一 / Canonical join path.** `products.category_id`と`reviews.category_id`の不整合を解消し、レビュー単位の正規経路に統一（NB02で取り込み時に調整）。 / Reconciled a `products.category_id` vs `reviews.category_id` inconsistency onto a single canonical review-level path (handled in NB02 at ingestion).
- **プレビュー打ち切りの開示 / Preview-truncation disclosed.** @cosmeレビュー本文が一覧ページのプレビューである点を方法論注記に明示。 / Disclosed that @cosme review bodies are listing-page previews (see Methodological Caveats).

**改訂4 — 事実検証・アーティファクト修正・マスク検証の追加 / Revision 4 — fact verification, artifact fixes, and the mask test**  
2度目の見直しにより、以下を検証・修正した：  
A second review verified and fixed the following:
- **ブランド分類の修正 / Brand classification corrected.** 「韓国ブランド」と分類していたアンレーベル（JPS LABO）・セラミエイド（コーセーコスメポート）・キテンは日本ブランドであり、公式情報で検証のうえ再分類した。ガラクトミセスはブランドではなく成分として再分類。発見4は検証済みの韓国シグナル（アヌア等5ブランド）で維持される。 / unlabel (JPS LABO), CERAMIAID (KOSÉ Cosmeport) and KITEN — previously tagged Korean — are Japanese brands, verified against official sources and reclassified. ガラクトミセス reclassified as an ingredient. Finding 4 stands on five verified Korean signals (Anua et al.).
- **評価レンズのアーティファクト修正 / Rating-lens artifact fixed.** 楽天treemapの平均評価が未評価SKU（評価0）を平均に含めていた —— オールインワンは3,030/5,534件が未評価で、表示値2.05に対し実際の評価済み平均は4.54。評価済みSKUのみの平均に修正し、評価カバー率を併記。価格も平均から中央値に変更（¥1のジャンク出品・¥30万超の外れ値のため）。 / The Rakuten treemap averaged unrated SKUs in as zeros — all-in-one showed 2.05 vs a true rated-only 4.54 (3,030 of 5,534 SKUs unrated). Now averages rated SKUs only, displays rated share, and uses median price (¥1 junk listings, ¥300k+ outliers).
- **部分年エンドポイントの修正 / Partial-year endpoint fixed.** 「2019→2026年（約35%低下）」は2026年の1〜3月のみを終点としており、季節性バイアスを含んでいた。暦年ベース2019→2025年（約32%低下、検索比0.31→0.53）に修正。粒度の誤記（週次→月次）も修正。 / The "2019→2026 (−35%)" comparison used a Jan–Mar-only 2026 endpoint, exposed to seasonality. Recomputed on full calendar years 2019→2025 (−32%; search ratio 0.31→0.53). A weekly-vs-monthly granularity mislabel was also fixed.
- **注意点7の事実誤認を修正 / Caveat 7 factual error corrected.** @cosme（アイスタイル）は「Rakutenグループ」ではなく、2022年からAmazon・三井物産と資本業務提携（Amazonが筆頭株主）。ソース独立性の記述を書き換えた。 / @cosme (istyle) is not "Rakuten Group"; it entered a capital alliance with Amazon and Mitsui in 2022 (Amazon is the largest shareholder). The source-independence caveat was rewritten.
- **マスク検証の追加 / Mask test added.** 対立仮説「メイク検索の低下はマスクによる循環的なもの」を、既収集の口紅・ファンデーション・アイシャドウのトレンドデータで直接検証（発見1参照）。 / The rival hypothesis — "the makeup decline is a cyclical mask effect" — was tested directly using already-collected lipstick/foundation/eyeshadow trends data (see Finding 1).
- **ダッシュボードに「ブランドへの示唆」タブを追加 / "For brands" tab added.** 4つの発見を処方的な示唆に翻訳し、注目データ≠売上データの免責を明記。 / The four findings translated into prescriptive implications, with an explicit attention-≠-sales disclaimer.

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
   @cosmeコーパスのカテゴリ構成比は年により変動する。両カテゴリを合算した期間横断比較（量シェア・語彙頻度デルタ）は交絡するため用いない。期間「内」のカテゴリ間比較（サンプル数を揃えた語彙収束）はこの交絡を受けない。  
   The @cosme corpus's category mix varies by year. Pooled cross-period comparisons (volume share, term-frequency deltas) are confounded and are not used. Within-period, size-matched tier-vs-tier comparison (vocabulary convergence) is not affected.

5. **SKU数 ≠ 売上高・需要 / SKU count ≠ sales or demand**  
   楽天カタログのSKU比率（3.7×）は棚占有率であり、GMVとは一致しない。さらに、SKU数はカタログ取得設計（どのジャンルをどの深さで取得したか）にも依存し、純粋な消費者選択の指標ではない。  
   The Rakuten SKU ratio (3.7×) measures shelf share, not GMV. It also reflects catalog-acquisition design (which genres were scraped, at what depth) and is not a pure consumer-choice signal.

6. **検索発見シグナルの正規化 / Search discovery signal normalisation**  
   検索起点ごとのボリュームは比較不可。メトリクスは起点内で独立に正規化済み。ツリーマップは相対的シグナル強度を示す。  
   Search volumes are not comparable across starting terms. Metrics are normalised within each starting term; treemaps show relative signal strength.

7. **ソースの非独立性 / Source non-independence**  
   @cosmeの運営会社アイスタイル（istyle）は2022年にAmazonおよび三井物産と資本業務提携しており（Amazonが筆頭株主）、本プロジェクトの@cosmeレビューとAmazon JPデータは厳密には独立でない。楽天カタログ・Googleトレンド・YouTubeは@cosmeから独立している。  
   @cosme is operated by istyle, which entered a capital/business alliance with Amazon and Mitsui in 2022 (Amazon is its largest shareholder) — so this project's @cosme reviews and Amazon JP data are not strictly independent of each other. The Rakuten catalog, Google Trends and YouTube are independent of @cosme.

8. **SudachiPy Mode Cの複合語分割 / Compound word splitting**  
   ナイアシンアミド → ナイアシン + アミドに分割される。成分検出はTF-IDF経由ではなく生テキスト検索で実施。  
   Niacinamide splits into niacin + amide under Mode C. Ingredient detection uses raw text search, not TF-IDF.

9. **レビュアー選択バイアス / Reviewer selection bias**  
   @cosmeレビューは自発的に書き込む消費者のみを反映する。トピックモデルはモニターレビューのバイアスを自律的に検出した（NB06）。  
   @cosme reviews reflect only consumers who choose to write. Topic modelling autonomously identified the giveaway-template bias (NB06).

10. **中国除外 / China exclusion**  
    楽天クロスボーダーおよびインバウンド需要は未定量化。  
    Rakuten cross-border and inbound demand from China is not quantified.

11. **一般語の検索ドリフト / Generic-term search drift**  
    「化粧品」のような一般語の検索低下は、需要低下だけでなく、消費者がより具体的な語（ブランド名・成分名）を検索するようになった効果も含みうる —— 本プロジェクトの発見4自体がその学習を示している。マスク検証（自身の2019年基準でのカテゴリ語追跡）はこの交絡の影響を受けにくいが、アンカー付き比較の約32%という規模は上限値として読むべきである。Googleトレンドの「トピック」エンティティでの再取得が今後の頑健性チェックとして残る。  
    The decline of a generic term like 化粧品 can partly reflect consumers migrating to more specific queries (brands, ingredients) rather than reduced demand — Finding 4 itself documents that learning. The mask test (category terms vs their own 2019 baselines) is less exposed to this confound, but the ~32% anchored-comparison figure should be read as an upper bound. Re-pulling with Google Trends *topic* entities remains a future robustness check.

12. **検索シグナル ≠ 支出 / Search signal ≠ spending**  
    本プロジェクトの全シグナルは注目（検索・コメント）と供給（SKU）であり、円ベースの需要ではない。総務省・家計調査の品目別支出（化粧水・乳液・ファンデーション・口紅）および経産省・生産動態統計による検証が、次の自然な拡張である。  
    Every signal here measures attention (search, comments) or supply (SKUs), not yen. Validating against 家計調査 household spending per item (toner, emulsion, foundation, lipstick) and METI shipment statistics is the natural next extension.
