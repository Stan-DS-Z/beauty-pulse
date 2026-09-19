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
- **SKU比率の見出しからの格下げ / SKU ratio demoted from the headline.** ジャンル564517「韓国コスメ」は原産国別ジャンルでありながら`cosmetics`として集計されていた。無作為150件の手作業分類（スキンケア49%・メイク36%・対象外15%）で再分類すると3.7倍は6.6倍（95%CI 6.1〜7.2）となり、メイク側のもう一方（204233）も24%が対象外であり、両ジャンルを再分類すると7.6倍（95%CI 6.9〜8.6）、処理方法により3.7〜10.7倍の幅を持つ。単一の倍率としては頑健でないため、見出しから外し注意点5に測定値と感度として記載した。 / Genre 564517 「韓国コスメ」 was counted wholly as `cosmetics` despite being a country-of-origin genre. Hand-labelling 150 random products (49% skincare, 36% makeup, 15% neither) moves 3.7× to 6.6×; hand-labelling the other makeup genre too (24% of it is out of scope) gives 7.6× (95% CI 6.9–8.6), and the figure spans 3.7–10.7× depending on treatment. Not robust as a single multiplier, so it was removed from the headline and recorded in caveat 5 as a measured figure with its sensitivity.
- **マスク検証の追加 / Mask test added.** 対立仮説「メイク検索の低下はマスクによる循環的なもの」を、既収集の口紅・ファンデーション・アイシャドウのトレンドデータで直接検証（発見1参照）。 / The rival hypothesis — "the makeup decline is a cyclical mask effect" — was tested directly using already-collected lipstick/foundation/eyeshadow trends data (see Finding 1).
- **ダッシュボードに「ブランドへの示唆」タブを追加 / "For brands" tab added.** 4つの発見を処方的な示唆に翻訳し、注目データ≠売上データの免責を明記。 / The four findings translated into prescriptive implications, with an explicit attention-≠-sales disclaimer.

**改訂5 — 公的統計との突き合わせ、および結論の変更 / Revision 5 — official statistics, and a changed conclusion**  
経産省 生産動態統計と財務省 貿易統計（HS 3304）をe-Stat API経由で取得し、注目データの発見を金額と突き合わせた。結論は変わった。  
METI 生産動態統計 and 財務省 貿易統計 (HS 3304) were pulled via the e-Stat API and the attention findings were set against money. The conclusion changed.
- **メイクは金額で裏づけられた / Makeup corroborated in yen.** ファンデーションと口紅の出荷金額は2019→2024年にいずれも42%減少し、落ち込みは2019→2021年に集中する（-47%、-74%）。マスク検証の所見と一致する。 / Foundation and lipstick shipped value both fell 42% over 2019→2024, concentrated in 2019→2021 (-47% and -74%). Consistent with the mask test.
- **「スキンケアへの再優先」を需要の主張として撤回 / "Skincare reprioritised" withdrawn as a demand claim.** 皮膚用の出荷金額は仕上用より大きく減っており、注目データから読める向きとは逆である。ただしこの比較自体が下記の断層をまたぐため、いずれの向きも需要の主張としては公表しない。関心の移動は関心の移動としてのみ述べる。 / Skincare shipped value fell *more* than makeup, the opposite direction to the attention reading — but that comparison itself spans the break below, so neither direction is published as a demand claim. The attention shift is now stated only as an attention shift.
- **2022年1月の断層 / A break at January 2022.** 化粧水・美容液・乳液のkg単価は2021年から2022年に21〜35%下落した。2015〜2021年の7年間はそれぞれ一定の範囲にあり、化粧水と美容液は2024年までその範囲を下回り、乳液は2024年に範囲内へ戻る。2022年の美容液は数量が2%増え金額が34%減り、化粧水は数量が12%、金額が36%減った。仕上用の品目に同様の段差はない。33品目のうち22品目はこの年に増加し、下落幅の上位3品目は化粧水・美容液・乳液である。日本化粧品工業会が注記する誤報告の修正（2020年に遡及）とは別物で、修正後の系列でも段差は残る。原因は公表統計に記載がない。したがって皮膚用の金額はこの点をまたいで測定しない。またいで測ると美容液の出荷金額は-39%・個数単価-25%、内側で測ると+20%・+40%となり、符号が反転する。 / Yen per kg for 化粧水, 美容液 and 乳液 fell 21–35% from 2021 to 2022, after seven years inside a range (2015–2021); 化粧水 and 美容液 stay below that range through 2024, and 乳液 is back inside it by 2024. In 2022 美容液 kilograms rose 2% while value fell 34%; 化粧水 kilograms fell 12% and value 36%. No makeup line shows the same step. 22 of the 33 component lines rose that year, and the three largest falls were 化粧水, 美容液 and 乳液. It is not the misreporting correction JCIA footnotes (retroactive to 2020) — the step survives on the restated series. The cause is undocumented. Skincare money is therefore never measured across it: across the break serum reads -39% value and -25% per unit; inside it, +20% and +40%.
- **区分の再構築 / Grouping rebuilt.** 「皮膚用化粧品計」等の小計行は2020年で終わるため、集計は33の品目行から組み直した。この区分は小計の存在する2年（2019・2020）を厳密に再現し、日本化粧品工業会が公表する2024年の構成比（皮膚用44.5%・仕上用20.9%）とも一致する。リップクリームは仕上用、ひげそり用・浴用化粧品は特殊用途であり、いずれもスキンケアではない。 / The 計 subtotal rows stop after 2020, so aggregates are summed from the 33 component lines. The partition reproduces both subtotal years exactly and matches JCIA's published 2024 shares (44.5% skincare, 20.9% makeup). リップクリーム is makeup and ひげそり用・浴用化粧品 is special-use; neither is skincare.
- **輸入代替仮説の棄却 / Import-substitution hypothesis rejected.** 輸入（HS 3304）は2024年に市場の12.2%で、2019年1,667億円、2023年のピーク2,242億円、2024年1,671億円と推移した。国内出荷の減少を吸収できる規模ではない。 / Imports were 12.2% of the market in 2024, running 1,667 億円 in 2019, 2,242 億円 at the 2023 peak and 1,671 億円 in 2024 — too small to absorb the domestic decline.
- **年次の導出を修正 / Year derivation corrected.** `trends_weekly.week_year` は2021・2022・2023年の1月を前年として扱っており、2020年が13か月になっていた。日付から導出するよう修正した。 / `trends_weekly.week_year` labels January of 2021, 2022 and 2023 as the previous year, leaving 2020 with thirteen months. The year is now derived from the date.


**改訂6 — 経産省データを2026年7月まで延長 / Revision 6 — METI data extended to July 2026**  
2025年の時系列表（2026年6月30日公表）と、2026年1〜7月の月次確報を追加した。確報はe-Statのデータベースではなく `getDataCatalog` の月次ワークブックから取得する。  
Added the 2025 時系列表 (opened 30 June 2026) and January–July 2026 from the monthly 確報 workbook, found through `getDataCatalog` rather than the e-Stat database.
- **年次の窓を2019→2025年へ / Annual window moved to 2019→2025.** ファンデーション-40%、口紅-44%（改訂5ではいずれも-42%、2019→2024年）。皮膚用対仕上用の比は2025年に2.24。年の途中の月は年次値に含めず、前年同月と比べる。 / Foundation -40%, lipstick -44% (both -42% over 2019→2024 in Revision 5). The skincare-to-makeup ratio is 2.24 in 2025. Part-year months never enter the annual figures; they are compared with the same months a year earlier.
- **2026年1〜7月 / January–July 2026.** 前年同期比で皮膚用+7.7%、仕上用-0.3%、全体+4.0%。確報と年報の差は2025年で合計0.2%未満、品目別で最大4%（口紅）。 / Against the same months of 2025: skincare +7.7%, makeup -0.3%, total +4.0%. On 2025, 確報 and the yearly table differed by under 0.2% in total and up to 4% by line (口紅).
- **メイクの回復は2025年に止まった / The makeup recovery stopped in 2025.** 仕上用の出荷金額は2,872億円から2,811億円に減少した。 / Makeup shipped value fell from 2,872 to 2,811 億円.
- **断層はメイクのkg単価にも現れる / The break also shows in makeup yen per kg.** 口紅は-40%、アイメークアップは-23%（2021→2022年）。重量がそれぞれ149%、44%増え、出荷金額は49%、11%増えており、金額の段差はない。経産省は化粧品のリンク係数を公表していない。 / 口紅 -40% and アイメークアップ -23% from 2021 to 2022. Their kilograms rose 149% and 44% while shipped value rose 49% and 11%, so there is no step in value. METI publishes no link coefficients for cosmetics.
- **乳液のkg単価 / 乳液 yen per kg.** 2024年に2015〜2021年の範囲内（9,523円）、2025年は範囲を下回る（9,049円）。化粧水は2026年1〜7月に6,686円で、範囲（6,787〜7,824円）に近づいている。 / Inside its 2015–2021 range in 2024 (9,523), below it in 2025 (9,049). 化粧水 reached 6,686 in January–July 2026, against a 6,787–7,824 range.
- **輸入の記述を修正 / Imports corrected.** 改訂5は「ほぼ横ばい」としていたが、2023年に2,242億円のピークがある。 / Revision 5 called imports flat; they peaked at 2,242 億円 in 2023.
- **ダッシュボードの出荷チャートを月次に / Shipment charts made monthly.**

**改訂7 — 新商品リリース層の追加（2026年9月19日）/ Revision 7 — launch layer added (19 September 2026)**  
PR TIMES上の企業別RSSから新商品リリースを数える層を「発見」タブに追加した。市場層と関心層は変更していない。  
A layer counting product-launch releases from PR TIMES company feeds was added to the Discovery tab. The market and attention layers are unchanged.
- **判定 / Gate.** タイトルと抜粋に対する語彙ルール（`src/prtimes.gate`、語彙は`config/launch_terms.xlsx`）。語彙は手作業ラベル150件で設計し、設計に用いていない別の100件で測定した。 / A vocabulary rule over title and excerpt (`src/prtimes.gate`, vocabulary in `config/launch_terms.xlsx`), designed on 150 hand-labelled releases and measured on a separate 100 not used in its design.
- **パネル / Panel.** 2021年9月まで履歴が遡る41フィード（30社）をコアとし、推移はコアのみで測る。それより後に履歴が始まる14フィードは直近12カ月の全体集計にのみ含める。 / The core is the 41 feeds (30 issuers) whose history reaches September 2021, and every trend is measured on the core only. The 14 feeds whose history starts later enter only the latest-12-month full-roster figure.
- **ラベル / Labels.** `config/prtimes_launch_validation_labels.csv`（150件）と`config/prtimes_launch_holdout_labels.csv`（100件）。リリース本文を含まない。 / Both label files hold ids and labels only, no release text.
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

5. **SKU比率はジャンル設計に依存する / The SKU ratio depends on genre design**  
   楽天のSKU比率は棚占有率であり、GMVとは一致しない。さらにこの比率は、楽天のジャンルが商品種別にどう対応するかに強く依存する。ジャンル564517「韓国コスメ」は`cosmetics`として分類されているが、実際は商品種別ではなく原産国別のジャンルであり、メイク側総数の62%を占める。無作為抽出150件を手作業で分類した結果は、スキンケア49%・メイク36%・対象外15%（ヘアケア、ボディケア、生理用品、二重まぶた用テープ、歯磨き粉、玩具）であった。メイク側のもう一方、204233「ベースメイク・メイクアップ」も同様に150件を手作業で分類した結果、メイク75%・対象外24%・スキンケア1%であり、対象外の大半はまつげエクステ用品と二重まぶた用品である。両ジャンルを再分類すると**7.6倍（ブートストラップ95%CI 6.9〜8.6）**、564517のみなら6.6倍、分類のままなら3.7倍、564517を両側から除くと9.7倍、商品種別が名称で定まるジャンルのみなら10.7倍となる。カタログはスキンケア8ジャンルに対しメイクは1ジャンルであるため、この比率は取得設計を大きく反映する。手作業のラベルは`config/rakuten_564517_validation_labels.csv`と`config/rakuten_204233_validation_labels.csv`、算出は`build_sku_ratio.py`。教師あり分類器は用いていない —— 564517はNB02bの分類器のcosmetics訓練クラスの66%を占めるため循環的である。商品種別ジャンルのみで再学習した分類器も、ドメイン内では0.981の精度である一方、564517に対しては0.740、メイクの再現率0.389にとどまり、手作業ラベルが58%とする箇所を84%スキンケアと予測した。学習器の問題ではない：同一特徴量でロジスティック回帰0.851、LinearSVC 0.838、XGBoost 0.788であり、いずれもドメイン内では0.98〜0.99である。同じモデルが204233では0.974を記録しており、補正が必要なジャンルでのみ失敗する。手作業ラベル241件を訓練に加えると0.905に上がる —— 効くのは学習器ではなくラベルである。  
   The Rakuten SKU ratio measures shelf share, not GMV, and it depends heavily on how Rakuten's genres map to product type. Genre 564517 「韓国コスメ」 is tagged `cosmetics` but is a country-of-origin genre rather than a product-type one, and it is 62% of the makeup total. 150 of its products drawn at random and labelled by hand are 49% skincare, 36% makeup and 15% neither (haircare, bodycare, sanitary products, eyelid tape, toothpaste, a toy). The other genre on that side, 204233 ベースメイク・メイクアップ, was hand-labelled the same way and is 75% makeup, 24% neither, 1% skincare — the out-of-scope share is mostly lash-extension supplies and double-eyelid products. Reclassifying both gives **7.6× (bootstrap 95% CI 6.9–8.6)**; 564517 alone gives 6.6×; leaving both as tagged gives 3.7×; dropping 564517 from both sides gives 9.7×; counting only genres whose name fixes the product type gives 10.7×. The catalogue holds eight skincare genres and one makeup genre, so the ratio substantially reflects acquisition design. Hand labels in `config/rakuten_564517_validation_labels.csv` and `config/rakuten_204233_validation_labels.csv`, computation in `build_sku_ratio.py`. No supervised classifier was used: 564517 is 66% of NB02b's cosmetics training class, so that model cannot audit it without circularity, and a clean classifier retrained on product-type genres only scored 0.981 in-domain but 0.740 on 564517, with 0.389 recall on makeup — it predicts 84% skincare there where the hand labels say 58%. The learner is not the constraint: on identical features, logistic regression reached 0.851 across both label sets, calibrated LinearSVC 0.838 and XGBoost 0.788, while all three scored 0.98–0.99 in-domain. The same model handles 204233 at 0.974, so it fails precisely on the genre the correction is for. Adding the 241 in-scope hand labels to training lifts it to 0.905, which is the actual lever — labels, not model class.

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
    関心層の全シグナルは注目（検索・コメント）と供給（SKU）であり、円ベースの需要ではない。経産省・生産動態統計と財務省・貿易統計による検証は改訂5で実施済みであり、メイクについては金額で裏づけられ、スキンケアについては2022年1月の断層により測定できないという結論に至った。残るのは総務省・家計調査であるが、**美容液と日焼け止めの品目を持たない** —— 最も動いたカテゴリはこの系列では検証できず、化粧水・乳液・化粧クリーム・ファンデーション・口紅に限られる。  
    Attention-layer signals measure attention (search, comments) or supply (SKUs), not yen. Validation against METI shipments and 財務省 trade statistics was carried out in Revision 5: makeup is corroborated in money, skincare is unmeasurable across the January 2022 break. What remains unpulled is 家計調査 household spending, which carries **no 美容液 line and no sunscreen line** — it cannot test the categories that moved most, only 化粧水, 乳液, 化粧クリーム, ファンデーション and 口紅.

13. **新商品リリース層の測定精度と収録範囲 / Launch layer: gate accuracy and PR TIMES coverage**  
    2026年9月19日測定。判定の適合率は0.89（95%信頼区間0.76〜0.98）、再現率は0.81（同0.68〜0.92）。判定語彙の設計に用いていない手作業ラベル100件で測り、保存済みリリース6,554件に加重した。デパコスの発行元に限った再現率は、別の100件で7件中6件、設計用の150件で12件中11件であり、他の価格帯と区別できる差はない。PR TIMESの収録は価格帯で異なる：ブランドリストのデパコス26ブランドのうち11ブランドは保存済みリリースに一度も現れず、その他の価格帯では92ブランド中28ブランドである。成分比率の図は、タイトルに再発売・詰め替え・限定パッケージを含むリリースを除く。この除外は手作業ラベルの限定・再発売13件中7件を検出する。成分比率の分子は件数が少ないため、ダッシュボードでは比率に件数を併記する。  
    Measured 19 September 2026. Gate precision 0.89 (95% CI 0.76–0.98) and recall 0.81 (0.68–0.92), on 100 hand-labelled releases held out from the gate's design, weighted to 6,554 stored releases. Recall on prestige (デパコス) issuers alone was 6 of 7 on the holdout and 11 of 12 on the design sample, not separable from the other tiers. PR TIMES coverage differs by tier: 11 of the 26 prestige brands in the brand list appear in no stored release, against 28 of 92 brands in other tiers. The ingredient-share chart excludes releases whose title names a re-release, refill or limited packaging; that filter finds 7 of 13 hand-labelled editions. Ingredient counts are small, so the dashboard shows each share with its count.
