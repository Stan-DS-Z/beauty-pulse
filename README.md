# Beauty Pulse — 日本美容市場アナリティクス

**コロナ禍はどのように日本の美容消費を再構成したのか？**  
How did COVID permanently restructure Japanese beauty consumption?

5つの独立したデータソース（レビューコーパス・検索行動・商業カタログ・成分インテリジェンス・YouTube言論）が同じ構造的変化を指している。  
Five independent sources — review corpus, search behaviour, commercial catalog, ingredient intelligence, and YouTube discourse — converge on the same structural shift.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red)
![SQLite](https://img.shields.io/badge/Data-SQLite-lightgrey)
![NLP](https://img.shields.io/badge/NLP-SudachiPy%20%7C%20TF--IDF%20%7C%20UMAP-violet)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)
![Markets](https://img.shields.io/badge/Market-Japan-white)

**[→ Live Dashboard](https://beauty-pulse.streamlit.app/)**

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
両者が共有の機能的語彙へと収束した（コサイン類似度 0.38 → 0.81）。  
*Nuance:* Skincare did not absorb cosmetics. Both categories converged toward a shared functional vocabulary — cosine similarity rose from 0.38 to 0.81 over six years.

---

## 主要な発見 / Key Findings

| シグナル / Signal | 2019 | 2025 | 変化 / Change |
|---|---|---|---|
| スキンケアレビュー比率 | 85.7% | 87.3% | +1.6pp |
| COVID後YoY急増（2020） | — | — | **+152.1%** |
| 楽天SKU比率（スキン対コスメ） | — | — | **4.0×** |
| Googleトレンド逆転年 | — | — | **2020年** |
| 語彙収束（コサイン類似度） | 0.38 | 0.81 | **+0.43** |
| ナイアシンアミド検索関心度 | 5.2 | 62.8 | **+57.6pp** |

---

## 発見の詳細 / What the Data Found

### 発見1 — 構造的変化
5つの独立したソースが同じ方向性を示した。@cosmeレビューコーパス、Googleトレンド（スキンケア検索逆転2020年）、楽天市場SKUカタログ（4.0倍の棚占有率）、成分検索急増（ナイアシンアミド12倍）、YouTubeコメント量加速。

**Finding 1 — The Structural Shift**  
Five independent sources, same direction. @cosme + Amazon JP review corpus, Google Trends (スキンケア overtakes 化粧品 in 2020), Rakuten Ichiba commercial catalog (4.0× skincare SKU ratio), ingredient search surge (niacinamide ×12), and YouTube comment volume acceleration.

---

### 発見2 — 消費者語彙の収束
2019年：スキンケアとコスメのレビューは語彙の38%を共有していた。2023–25年：81%に上昇。  
TF-IDF分析が方向性を裏付ける：マスカラ −76%、まつ毛 −86%、アイライナー −71%。  
代わりに台頭：保湿 +409%、クリーム +3,101%、乾燥 +312%。  
コスメはスキンケアの文脈で評価されるようになった。

**Finding 2 — Vocabulary Convergence**  
2019: skincare and cosmetics reviews shared 38% of top vocabulary. By 2023–25: 81%.  
TF-IDF confirms the direction: マスカラ −76%, まつ毛 −86%, アイライナー −71%.  
Rising: 保湿 +409%, クリーム +3,101%, 乾燥 +312%.  
Cosmetics are now evaluated through a skincare lens.

---

### 発見3 — コーパスは連続体であり、各アイランドが異なる物語を語る
UMAPによる14,727件のレビュー埋め込みにより、語彙空間の構造が可視化された。  
インフルエンサー・モニターレビューは、指示なしに自動的にオーガニックレビューと分離された。  
「Foundation as skincare」クラスターは、コスメレビューがスキンケア語彙（乾燥・しっとり・毛穴）で書かれている収束点を示す。  
SPFは単一カテゴリではない：機能的日焼け止めとベースメイク型SPFは語彙が完全に異なる。

**Finding 3 — The Corpus Is a Continuum**  
UMAP embedding of 14,727 reviews reveals the spatial structure of vocabulary space.  
Influencer/monitor reviews separated automatically from organic consumer reviews — without being told to look.  
A "Foundation as skincare" cluster marks where cosmetics reviews are already written in skincare language.  
SPF is not one category: functional sun protection and cosmetic base makeup consumers speak entirely different vocabularies.

---

### 発見4 — 韓国ブランドが日本の需要を取り込んでいる
COVID期：成分検索が支配的だった（レチノール×5シード、ナイアシンアミド×4シード）。消費者がリテラシーを形成していた。  
直近ウィンドウ：アヌアが4つの独立したシードキーワードで最強シグナルを記録。  
構造的変化が消費者を教育した。韓国ブランドがその恩恵を受けている。YouTubeはまだ開かれている。

**Finding 4 — Korean Brands Are Harvesting Japanese Demand**  
COVID window: ingredient searches dominated — consumers building literacy (レチノール ×5 seeds, ナイアシンアミド ×4 seeds).  
Recent window: アヌア is the single strongest Block C signal, appearing across 4 independent seed keywords.  
The structural shift educated consumers. Korean brands captured them. YouTube is still wide open.

---

## データソース / Data Sources

```
自己収集・完全ボトムアップ構成 — Kaggleデータセット不使用
All data self-sourced. No Kaggle datasets.
```

| ソース | 内容 | 規模 |
|---|---|---|
| @cosme | スキンケア・コスメレビュー | 22,451件 |
| 楽天市場 API | 商品カタログ・価格・レビュー数 | 31,202 SKU |
| Google Trends JP | 週次検索関心度（2019–2026） | 4,635行 |
| YouTube Data API v3 | 美容動画コメント | 248動画・60,676件 |

**@cosmeデータについて：**  
カテゴリレベルのスクレイピング（ブランド属性なし）。これは設計上の選択であり、データギャップではない。  
NB05市場ベースラインの整合性を保つためにブランド中立性を維持した。

---

## 技術スタック / Technical Stack

```python
# 分析パイプライン
Python       3.12  # コア言語
SQLite       3.x   # get_connection() — パス依存なし
SudachiPy    0.5.x # 日本語形態素解析 Mode C
scikit-learn 1.x   # TF-IDF, LDA
umap-learn   0.5.x # 次元削減
hdbscan      0.8.x # クラスタリング

# ダッシュボード
Streamlit    1.x   # UI
Plotly       5.24.1 # ピン留め — 5.xのAPIで構築
```

**設計原則 / Design Principles:**  
- `COALESCE(p.tier_predicted, p.tier_override, c.tier)` — カノニカルティア（全ノートブック共通）  
- `get_connection()` from `src.schema` — ハードコードパス禁止  
- NLP技術選択の順序：TF-IDF → 埋め込み → ニューラル（各ステップに説明責任）  
- 公開ダッシュボードは`signal_pulse_public.db`（`product_name`・`raw_json`除去済み）

---

## ノートブック構成 / Notebook Pipeline

```
NB01e  YouTube Data API 収集
NB02   スキーマ設計・品質監査
NB02b  XGBoost ティア分類器（NB02修正適用済み）
NB02c  週次スナップショット
NB03   SQL基盤クエリ
NB04   消費者ボイス — 語彙・成分・品質分析
NB05   市場変化の確認 — 3独立ソース
NB06   発見レイヤー — TF-IDF・LDA・UMAP・Block C
NB07   エグゼクティブ統合 + ダッシュボードアセット生成
```

実行順序：NB02 → NB02b → NB02c → NB03 → NB04 → NB05 → NB06 → NB07 → `streamlit_app.py`

---

## ライブダッシュボード / Live Dashboard

**Beauty Pulse** はStreamlit Community Cloudにデプロイ済み。

3タブ構成・EN/JP切り替えトグル付き：

| タブ | 内容 |
|---|---|
| 📈 市場変化 / The Shift | 5ソース確認・成分急増・SKUトリーマップ・YouTube推移 |
| 🔤 消費者の言語 / The Language | ワードクラウド（年別）・コサイン類似度ヒートマップ・TF-IDF差分 |
| 🔍 発見 / Discovery | Block C検索発見・YouTubeチャンネル分析・UMAPコーパス可視化 |

---

## 方法論的注意点 / Methodological Caveats

1. **COVID前コーパスの非対称性**  
   2019–2020年レビュー数は565件 vs 直近12,517件。時系列比較はサンプルサイズの非対称性を伴う。Googleトレンド（週次、2019年から）がこれを補完する。

2. **SudachiPy Mode Cの複合語分割**  
   ナイアシンアミド → ナイアシン + アミドに分割される。成分検出はTF-IDF経由ではなく生テキスト検索で実施。

3. **@cosmeの交差検証非独立性**  
   レビューコーパスと楽天カタログは共にRakutenグループのデータ。厳密な独立性はGoogleトレンドとYouTubeのみ。

4. **Block Cシグナル正規化**  
   シード間の検索ボリュームは比較不可。メトリクスはシード内で独立に正規化済み。ツリーマップは相対的シグナル強度を示す（絶対ボリュームではない）。

5. **中国除外**  
   楽天クロスボーダーおよびインバウンド需要は未定量化。

---

## セットアップ / Setup

```bash
# リポジトリのクローン
git clone https://github.com/Stan-DS-Z/beauty-pulse.git
cd beauty-pulse

# 環境のアクティベート（conda推奨）
conda activate beauty-pulse

# 依存関係のインストール
pip install -r requirements.txt

# SudachiPy辞書のセットアップ
python -m sudachipy download

# ダッシュボードの起動
streamlit run dashboard/streamlit_app.py
```

**Note:** `signal_pulse.db`（プライマリDB）はデータプライバシー上gitignored。  
ダッシュボードは`signal_pulse_public.db`（stripped版・`dashboard/assets/`内）を使用。

---

## プロジェクトの背景 / Context

このプロジェクトは、日本の美容・FMCGアナリティクスへのキャリアピボットを目的としたデータポートフォリオ作品。  
自己収集データの構築（Kaggle不使用）、日本語NLPパイプライン、SQLite設計、Streamlitダッシュボード展開を含む。

This project forms one half of a data analytics portfolio targeting Japanese beauty and FMCG analytics roles.  
It demonstrates self-sourced data construction, Japanese NLP, SQL architecture, and deployed dashboard work —  
built as a complement to [The Masstige Moment](https://github.com/Stan-DS-Z/masstige-moment), which analyses the same market from a top-down revenue perspective.

JLPT N1 · DALF C1 — 分析資産として日英仏3言語での納品が可能。  
JLPT N1 · DALF C1 — trilingual analytical delivery across EN / JP / FR.

---

![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)
![Data](https://img.shields.io/badge/Data-Self--sourced-blue)
![NLP](https://img.shields.io/badge/NLP-Japanese-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

*Analysis by Stanley S · [LinkedIn](https://www.linkedin.com/in/stanley-shi-7b604b104/) · 2026*