"""Beauty Pulse copy: the EN/JA string table and the figures rebuilt into it.

build_strings() returns the table for one language with every figure-bearing
entry filled from the headline and launch dicts. Imports no UI framework.
"""

import pandas as pd

from .brief import TRENDS_PULL_SPREAD
from .demand import MASK_YEARS
from .seasonal import FULL_YEARS
from .supply import HELD_PCT, KEY_CATEGORY
from .data import LAUNCH_GATE, LAUNCH_WINDOW_START
from .sources import EDITION

STRINGS = {
    "en": {
        "tagline":       "Japanese beauty market analytics",
        "subtitle":      "",   # rebuilt from the edition (sources.EDITION)
        "nav_report": "Report", "nav_brief": "Brief", "nav_market": "Market",
        "nav_demand": "Demand", "nav_supply": "Supply", "nav_consumer": "Consumer",
        "nav_timing": "Timing",
        "launch_empty": "Launch export not found: dashboard/assets/prtimes_launches.csv.",
    },
    "jp": {
        "tagline":        "日本の美容市場分析",
        "subtitle":       "",  # rebuilt from the edition (sources.EDITION)
        "nav_report": "レポート", "nav_brief": "要旨", "nav_market": "市場", "nav_demand": "需要", "nav_supply": "供給",
        "nav_consumer": "消費者", "nav_timing": "季節性",
        "launch_empty": "新商品リリースのデータが見つからない：dashboard/assets/prtimes_launches.csv",
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


def build_strings(lang, HEADLINE, LAUNCH, ASSETS, BRIEF=None, REGISTRY=None, MARKET=None,
                  DEMAND=None, SUPPLY=None, CONSUMER=None, TIMING=None):
    """STRINGS[lang] with the live figures written in, and each report page's
    copy when its figures (brief.compute_brief, market.compute_market) and the
    source registry are given."""
    S = dict(STRINGS[lang])
    _ed = pd.Timestamp(EDITION + "-01")
    S["subtitle"] = (f"Report: {_MON_EN[_ed.month]} {_ed.year} edition" if lang == "en"
                     else f"レポート：{_ed.year}年{_ed.month}月版")
    if BRIEF is not None and REGISTRY is not None:
        S.update(brief_strings(lang, BRIEF, BRIEF["H"], REGISTRY))
    if MARKET is not None and REGISTRY is not None:
        S.update(market_strings(lang, MARKET, REGISTRY))
    if DEMAND is not None and REGISTRY is not None:
        S.update(demand_strings(lang, DEMAND, REGISTRY))
    if SUPPLY is not None and REGISTRY is not None:
        S.update(supply_strings(lang, SUPPLY, REGISTRY))
    if CONSUMER is not None and REGISTRY is not None:
        S.update(consumer_strings(lang, CONSUMER, REGISTRY))
    if TIMING is not None and REGISTRY is not None:
        S.update(timing_strings(lang, TIMING, REGISTRY))
    return S


# ── The Brief ───────────────────────────────────────────────────────────────
# Every figure comes from brief.compute_brief. The sentences carry directions
# (rose, fell, below) that the data decides; tests/test_brief.py holds the data
# to each direction the copy states, so a refresh that turns one fails there
# and the sentence is rewritten for the new edition.

_NUM_EN = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
           8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
           14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
           19: "nineteen", 20: "twenty"}
_MON_ABBR = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
             "Nov", "Dec"]
# Where each key finding's page lives until the report pages are built: the
# page that carries that layer today, or None.
BRIEF_LINKS = {"market": ("/market", "nav_market"), "demand": ("/demand", "nav_demand"),
               "supply": ("/supply", "nav_supply"), "consumer": ("/consumer", "nav_consumer"),
               "timing": ("/timing", "nav_timing")}


def _and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _cat(key, cap=False):
    name = LAUNCH_CAT[key][0]
    return name if cap else name[0].lower() + name[1:]


def _pct(x):
    return f"{x:+.0f}%"


def _ym_en(ym):
    return f"{_MON_EN[int(ym[5:7])]} {ym[:4]}"


def _and_ja(items):
    items = list(items)
    return items[0] if len(items) == 1 else (
        f"{items[0]}と{items[1]}" if len(items) == 2 else "、".join(items))


def _ym_ja(ym):
    return f"{ym[:4]}年{int(ym[5:7])}月"


def _half_ja(h):
    """"2026 H1" -> "2026年1〜6月". Not 上期: in Japanese business writing 上期
    is often the fiscal half, April to September."""
    return f"{h[:4]}年{'1〜6' if h.endswith('1') else '7〜12'}月"


def _same(d):
    return len(set(d.values())) == 1


def _timing_en(T):
    """Sunscreen's shipment and search peak runs in each full year, with the
    offset, and how many lines ship most in the same month every year."""
    ys, sh, se, off = list(T["ship"]), T["ship"], T["search"], T["offset"]
    rng = lambda r: f"{_MON_EN[r[0]]}–{_MON_EN[r[1]]}"  # noqa: E731
    if _same(sh) and _same(se):
        a, b, o = sh[ys[0]], se[ys[0]], off[ys[0]]
        first = (f"Sunscreen shipments peak <b>{rng(a)}</b> and search peaks {rng(b)}, "
                 f"{_NUM_EN[o]} months later, in every year from {ys[0]} to {ys[-1]}.")
    else:
        first = ("Sunscreen shipments and search peak " + "; ".join(
            f"{rng(sh[y])} and {rng(se[y])} in {y}" for y in ys) + ".")
    return (f"{first} {_NUM_EN[T['n_stable']].capitalize()} of the {T['n_lines']} product lines "
            "ship most in the same month, give or take one, every year.")


def _timing_ja(T):
    ys, sh, se, off = list(T["ship"]), T["ship"], T["search"], T["offset"]
    rng = lambda r: f"{r[0]}〜{r[1]}月"  # noqa: E731
    if _same(sh) and _same(se):
        a, b, o = sh[ys[0]], se[ys[0]], off[ys[0]]
        first = (f"日焼け止めの出荷金額は<b>{rng(a)}</b>、検索は{rng(b)}にピークとなり、"
                 f"{ys[0]}〜{ys[-1]}年の各年で{o}カ月の差がある。")
    else:
        first = ("日焼け止めの出荷金額と検索のピークは、" + "、".join(
            f"{y}年が{rng(sh[y])}と{rng(se[y])}" for y in ys) + "である。")
    return (f"{first}{T['n_lines']}品目のうち{T['n_stable']}品目は、毎年同じ月（前後1カ月以内）に"
            "出荷金額が最も多い。")


def brief_strings(lang, B, H, REG):
    """The Brief page's copy in one language. Besides text it carries two
    lookups for the page and its figures: which LAUNCH_CAT name to use
    (b_catix) and which column of the actives holds their names (b_namecol)."""
    out = _brief_en(B, H, REG) if lang == "en" else _brief_ja(B, H, REG)
    out["b_catix"] = 0 if lang == "en" else 1
    out["b_namecol"] = "en" if lang == "en" else "ja"
    return out


def _brief_ja(B, H, REG):
    """The Brief in Japanese: 産業調査体, である調 in the body, titles without a
    closing 。, the site's existing terms (出荷金額, 皮膚用・仕上用, 検索関心度,
    コア発行元, 新商品リリース)."""
    from .sources import source_line
    y0, y1 = B["window"]
    M, Dm, Sp, P, T = B["market"], B["demand"], B["supply"], B["portfolio"], B["timing"]
    A = B["actives"]
    top3 = sorted(A.loc[Dm["top3"], "ja"])                     # never ranked
    cj = lambda k: LAUNCH_CAT[k][1]                            # noqa: E731
    ed = pd.Timestamp(EDITION + "-01")
    out = {}

    out["b_kicker"] = f"レポート · {ed.year}年{ed.month}月版 · 日本の美容市場"
    out["b_governing"] = (
        f"{y0}年以降、新商品リリースの構成比（以下、リリース構成比）、検索、出荷金額は、それぞれ"
        f"異なるカテゴリで伸びた。リリース構成比が最も伸びたのは{_and_ja(cj(k) for k in P['gainers'])}で、その出荷金額の変化は"
        f"{_pct(P['gain_ship_lo'])}〜{_pct(P['gain_ship_hi'])}である。検索が最も伸びたのは、"
        f"新商品リリースでの言及が少ない成分名である。出荷金額が最も伸びたのは"
        f"{_and_ja(cj(k) for k in P['risers'])}である。")

    out["b_kf_market"] = (
        f"{y0}→{y1}年に出荷金額は皮膚用が<b>{_pct(M['skin_d'])}</b>、仕上用が"
        f"<b>{_pct(M['make_d'])}</b>となった。仕上用は{M['base']}年をなお{abs(M['make_vs_base']):.0f}%"
        f"下回る。美容液の{_pct(M['serum_d'])}は、個数が{abs(M['serum_units']):.0f}%減るなかで"
        f"1個あたり金額が{_pct(M['serum_vpu'])}となったことによる。")
    _within = _and_ja(sorted(A.loc[Dm["within"], "ja"]))
    _up = "、".join(f"{cj(k)}は{v:.0f}ポイント上昇" for k, v in Dm["words_up"].items()) + "し"
    _wwords = _and_ja(cj(k) for k in Dm["words_within"])
    out["b_kf_demand"] = (
        f"追跡する{Dm['n_actives']}成分のうち{Dm['n_rose']}成分で、{y0}→{y1}年に検索が"
        f"<b>{Dm['rose_lo']:.0f}〜{Dm['rose_hi']:.0f}ポイント</b>上昇した。最も伸びたのは"
        f"{_and_ja(top3)}の3成分である。{_within}の変化は、同じ月を再取得したときのばらつき"
        f"（{TRENDS_PULL_SPREAD}ポイント）の範囲内にある。カテゴリ語{Dm['n_words']}語のうち"
        f"{Dm['words_down']}語は低下した。{_up}、{_wwords}はばらつきの範囲内だった。")
    _g = (f"それぞれ<b>{Sp['gain_lo']:.0f}ポイント</b>" if round(Sp["gain_lo"]) == round(Sp["gain_hi"])
          else f"<b>{Sp['gain_lo']:.0f}〜{Sp['gain_hi']:.0f}ポイント</b>")
    (k0, n0), (k1, n1) = Sp["kr_first"], Sp["kr_last"]
    out["b_kf_supply"] = (
        f"{y0}→{y1}年に、リリース構成比は{_and_ja(cj(k) for k in Sp['gainers'])}が"
        f"{_g}上昇し、{cj(Sp['loser'])}は{abs(Sp['loss']):.0f}ポイント低下した。コア発行元の新商品"
        f"リリースのうち韓国系発行元によるものは、{_half_ja(Sp['h_last'])}に<b>{100 * k1 / n1:.0f}%</b>"
        f"（{n1}件中{k1}件）で、{_half_ja(Sp['h_first'])}の{100 * k0 / n0:.0f}%"
        f"（{n0}件中{k0}件）から上昇した。")
    out["b_kf_consumer"] = (
        f"@cosmeレビューのスキンケア上位{H['vocab_top']}語のうち<b>{H['vocab_shared']}語</b>が、"
        f"YouTubeのスキンケア動画へのコメントの上位{H['vocab_top']}語にも入る。")
    out["b_kf_timing"] = _timing_ja(T)
    out["b_kf_labels"] = {"market": "市場", "demand": "需要", "supply": "供給",
                          "consumer": "消費者", "timing": "季節性"}

    # Exhibit 1: launch share against shipped value
    out["b_p_h"] = (
        f"リリース構成比が最も伸びた{_and_ja(cj(k) for k in P['gainers'])}の出荷金額は"
        f"{_pct(P['gain_ship_lo'])}〜{_pct(P['gain_ship_hi'])}、構成比が下がった"
        f"{_and_ja(cj(k) for k in P['fell'])}の出荷金額は"
        f"{P['fell_ship_lo']:.0f}〜{P['fell_ship_hi']:.0f}%増")
    n_y0, n_y1 = P["den"]
    out["b_p_e"] = (
        f"各バブルは製品カテゴリ。横軸：経産省の出荷金額、{y1}年の{y0}年比。縦軸：カテゴリを"
        f"判定できたコア発行元の新商品リリースに占める比率の差、{y1}年（{n_y1}件）−{y0}年"
        f"（{n_y0}件）。"
        f"バブルの面積：{y1}年の出荷金額。カーソルを合わせると件数を表示する。")
    out["b_p_x"] = f"出荷金額、{y1}年の{y0}年比（%）"
    out["b_p_y"] = f"リリース構成比、{y1}年−{y0}年（ポイント）"
    out["b_p_q"] = ["出荷金額・構成比とも増加", "出荷金額増・構成比減",
                    "構成比増・出荷金額減", "ともに減少"]
    out["b_p_groups"] = {"skincare": "スキンケア", "sunscreen": "日焼け止め", "makeup": "メイク"}
    out["b_p_src"] = source_line(["meti", "prtimes"], REG, "ja")

    # Exhibit 2: the actives, search against launch share
    out["b_a_h"] = (
        f"{_and_ja(top3)}の検索は{Dm['top3_lo']:.0f}〜{Dm['top3_hi']:.0f}ポイント上昇、"
        f"この3成分を含む新商品リリースは{Dm['launch_den']:,}件中{Dm['top3_n']}件")
    out["b_a_e"] = (
        f"GoogleトレンドとPR TIMESの双方で追跡する{Dm['n_actives']}成分。横軸：検索関心度、"
        f"{y1}年の年平均−{y0}年（各語は自身のピーク = 100）。縦軸：成分名を含む、コア発行元の"
        f"新商品リリースの比率、{_ym_ja(Dm['launch_from'])}〜{_ym_ja(Dm['launch_to'])}、再発売・"
        "詰め替え・限定パッケージを除く。括弧内は件数。点線は中央値。")
    out["b_a_x"] = f"検索関心度、{y1}年−{y0}年（ポイント、自身のピーク = 100）"
    out["b_a_y"] = "新商品リリースに占める比率（%）"
    out["b_a_q"] = "検索の上昇は中央値超、リリースに占める比率は中央値未満"
    out["b_a_src"] = source_line(["trends", "prtimes"], REG, "ja")

    # Exhibit 3: the category table
    out["b_t_h"] = f"{B['n_rows']}カテゴリを同じ尺度で比較"
    out["b_t_e"] = (
        "PR TIMESの新商品リリースと経産省の品目の双方にあるカテゴリ。検索はカテゴリ語を追跡して"
        f"いる場合のみ表示する。韓国系発行元：カテゴリの{y1}年のコア発行元の新商品リリースに占める"
        f"比率、括弧内は件数。出荷ピーク：出荷金額を中心化12カ月移動平均で割った比率が最も高い月で、"
        f"{FULL_YEARS[0]}〜{FULL_YEARS[-1]}年の各年のピークがその前後1カ月以内にある品目のみ示す。")
    out["b_t_cols"] = [("カテゴリ", ""), ("経産省の品目", ""), (f"{y1}年の金額", "億円"),
                       ("金額", f"{y0}→{y1}年"), ("個数", f"{y0}→{y1}年"),
                       ("1個あたり金額", f"{y0}→{y1}年"),
                       ("検索", f"{y0}→{y1}年、ポイント"), ("リリース構成比", f"{y0}→{y1}年"),
                       ("韓国系発行元", f"{y1}年リリースに占める比率"), ("出荷ピーク", "月")]
    out["b_t_partial"] = "一部"
    out["b_t_nopeak"] = "ピーク月は年により異なる"
    out["b_t_months"] = [None] + [f"{m}月" for m in range(1, 13)]
    out["b_t_src"] = source_line(["meti", "trends", "prtimes"], REG, "ja")
    _G = LAUNCH_GATE
    out["b_fn_t"] = "各指標の範囲"
    out["b_fn_b"] = (
        "出荷金額は、国内の化粧品メーカーが経産省に報告する出荷の金額で、輸入を含まない。リリース構成比"
        f"は、PR TIMES上の履歴が{_ym_ja(LAUNCH_WINDOW_START)}まで遡る{B['n_core']}社のプレス"
        f"リリースで測る。ブランドリストのデパコス{_G['prestige_n']}ブランドのうち"
        f"{_G['prestige_unseen']}ブランドは、保存済みリリースに一度も現れない"
        f"（{_G['asof'][:4]}年{int(_G['asof'][5:7])}月{int(_G['asof'][8:])}日測定）。検索は語ごと"
        "の指数で、各語は自身のピークを基準とするため、変化は語ごとに測る。")
    return out


def _brief_en(B, H, REG):
    """The Brief in English."""
    from .sources import source_line
    y0, y1 = B["window"]
    M, Dm, Sp, P, T = B["market"], B["demand"], B["supply"], B["portfolio"], B["timing"]
    A = B["actives"]
    top3 = sorted(A.loc[Dm["top3"], "en"])                     # never ranked
    ed = pd.Timestamp(EDITION + "-01")
    out = {}

    out["b_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year} · Japanese beauty market"
    out["b_governing"] = (
        f"After {y0}, launch share, search and shipped value rose in different categories: "
        f"launch share rose most in {_and(_cat(k) for k in P['gainers'])}, whose shipped value "
        f"moved {_pct(P['gain_ship_lo'])} to {_pct(P['gain_ship_hi'])}; search rose most for "
        f"named actives that few launches carry; and shipped value rose most in "
        f"{_and(_cat(k) for k in P['risers'])}.")

    out["b_kf_market"] = (
        f"Shipped value rose <b>{_pct(M['skin_d'])}</b> in skincare and <b>{_pct(M['make_d'])}</b> "
        f"in makeup, {y0}→{y1}; makeup is still {abs(M['make_vs_base']):.0f}% below {M['base']}. "
        f"Serum's {_pct(M['serum_d'])} came from value per unit ({_pct(M['serum_vpu'])}) on "
        f"{abs(M['serum_units']):.0f}% fewer units.")
    _within = _and(sorted(A.loc[Dm["within"], "en"].str.lower()))
    _up = "; ".join(f"{_cat(k)} rose {v:.0f} points" for k, v in Dm["words_up"].items())
    _wwords = _and(_cat(k) for k in Dm["words_within"])
    out["b_kf_demand"] = (
        f"Search rose <b>{Dm['rose_lo']:.0f}–{Dm['rose_hi']:.0f} points</b> for "
        f"{_NUM_EN[Dm['n_rose']]} of {_NUM_EN[Dm['n_actives']]} tracked actives, {y0}→{y1}, most "
        f"for {_and(t[0].lower() + t[1:] for t in top3)}; {_within} stayed within the "
        f"{TRENDS_PULL_SPREAD}-point spread between repeat pulls. Of "
        f"{_NUM_EN[Dm['n_words']]} category words, {_NUM_EN[Dm['words_down']]} fell, {_up}, and "
        f"{_wwords} stayed within the spread.")
    _g = (f"<b>{Sp['gain_lo']:.0f} points</b> of launch share each"
          if round(Sp["gain_lo"]) == round(Sp["gain_hi"])
          else f"<b>{Sp['gain_lo']:.0f}–{Sp['gain_hi']:.0f} points</b> of launch share")
    (k0, n0), (k1, n1) = Sp["kr_first"], Sp["kr_last"]
    out["b_kf_supply"] = (
        f"{_and(_cat(k, True) if i == 0 else _cat(k) for i, k in enumerate(Sp['gainers']))} "
        f"gained {_g}, {y0}→{y1}; {_cat(Sp['loser'])} lost {abs(Sp['loss']):.0f}. Korean issuers "
        f"made <b>{100 * k1 / n1:.0f}%</b> ({k1} of {n1}) of core launch releases in "
        f"{Sp['h_last']}, from {100 * k0 / n0:.0f}% ({k0} of {n0}) in {Sp['h_first']}.")
    out["b_kf_consumer"] = (
        f"<b>{H['vocab_shared']} of the top {H['vocab_top']}</b> skincare terms in @cosme "
        f"reviews are also in the top {H['vocab_top']} of comments on YouTube skincare videos.")
    out["b_kf_timing"] = _timing_en(T)
    out["b_kf_labels"] = {"market": "Market", "demand": "Demand", "supply": "Supply",
                          "consumer": "Consumer", "timing": "Timing"}

    # Exhibit 1: launch share against shipped value
    out["b_p_h"] = (
        f"Launch share rose most in {_and(_cat(k) for k in P['gainers'])}, whose shipped value "
        f"moved {_pct(P['gain_ship_lo'])} to {_pct(P['gain_ship_hi'])}; it fell in "
        f"{_and(_cat(k) for k in P['fell'])}, where value rose "
        f"{P['fell_ship_lo']:.0f}–{P['fell_ship_hi']:.0f}%")
    n_y0, n_y1 = P["den"]
    out["b_p_e"] = (
        f"Each bubble is a product category. Horizontal: METI shipped value, {y1} against {y0}. "
        f"Vertical: the category's share of categorised core-panel launch releases, {y1} "
        f"({n_y1} releases) minus {y0} ({n_y0}). Bubble area: {y1} shipped value. "
        "Hover for counts.")
    out["b_p_x"] = f"Shipped value, {y1} vs {y0} (%)"
    out["b_p_y"] = f"Launch share, {y1} minus {y0} (points)"
    out["b_p_q"] = ["Value and launch share rose", "Value rose, launch share fell",
                    "Launch share rose, value fell", "Both fell"]
    out["b_p_groups"] = {"skincare": "Skincare", "sunscreen": "Sunscreen", "makeup": "Makeup"}
    out["b_p_src"] = source_line(["meti", "prtimes"], REG)

    # Exhibit 2: the actives, search against launch share
    out["b_a_h"] = (
        f"Search for {_and(t[0].lower() + t[1:] for t in top3)} rose "
        f"{Dm['top3_lo']:.0f}–{Dm['top3_hi']:.0f} points; together they appear in "
        f"{Dm['top3_n']} of {Dm['launch_den']:,} launch releases")
    out["b_a_e"] = (
        f"{_NUM_EN[Dm['n_actives']].capitalize()} actives tracked in both Google Trends and PR TIMES. "
        f"Horizontal: search interest, {y1} annual mean minus {y0}, each term scaled to its own "
        f"peak. Vertical: share of core-panel launch releases naming the ingredient, "
        f"{_ym_en(Dm['launch_from'])} – {_ym_en(Dm['launch_to'])}, editions left out; count in "
        "brackets. Dotted lines: medians.")
    out["b_a_x"] = f"Search interest, {y1} minus {y0} (points, own peak = 100)"
    out["b_a_y"] = "Share of launch releases (%)"
    out["b_a_q"] = "Search above median rise · launch share below median"
    out["b_a_src"] = source_line(["trends", "prtimes"], REG)

    # Exhibit 3: the category table
    out["b_t_h"] = f"{_NUM_EN[B['n_rows']].capitalize()} categories measured the same way"
    out["b_t_e"] = (
        "Categories that PR TIMES launch releases and METI product lines both name. Search is "
        "shown where the category word is tracked. Korean share: Korean-origin issuers' share of "
        f"the category's {y1} core launch releases, count in brackets. Shipment peak: the month "
        "with the highest ratio of shipped value to its centred 12-month average, shown where "
        f"each of {FULL_YEARS[0]}–{FULL_YEARS[-1]} peaks within a month of it.")
    out["b_t_cols"] = [("Category", ""), ("METI line", ""), (f"Value {y1}", "¥億"),
                       ("Value", f"{y0}→{y1}"), ("Units", f"{y0}→{y1}"),
                       ("Value / unit", f"{y0}→{y1}"),
                       ("Search", f"{y0}→{y1}, pts"), ("Launch share", f"{y0} → {y1}"),
                       ("Korean issuers", f"share of {y1} launches"), ("Shipment peak", "month")]
    out["b_t_partial"] = "partial"
    out["b_t_nopeak"] = "Peak month differs by year"
    out["b_t_months"] = _MON_ABBR
    out["b_t_src"] = source_line(["meti", "trends", "prtimes"], REG)
    _G = LAUNCH_GATE
    out["b_fn_t"] = "How each measure is bounded"
    out["b_fn_b"] = (
        "Shipped value is what manufacturers in Japan report to METI; it leaves out imports. "
        f"Launch share is measured on press releases from {B['n_core']} issuers whose PR TIMES "
        f"history reaches {_ym_en(LAUNCH_WINDOW_START)}; {_G['prestige_unseen']} of the "
        f"{_G['prestige_n']} prestige brands in the brand list appear in no stored release "
        f"(measured {int(_G['asof'][8:])} {_MON_EN[int(_G['asof'][5:7])]} {_G['asof'][:4]}). "
        "Search is an index per term, each scaled to its own peak; changes are measured within "
        "a term.")
    return out


# ── Market ──────────────────────────────────────────────────────────────────
# Every figure comes from market.compute_market; tests/test_market.py holds the
# data to each direction the copy states.

# METI product line -> (English name, Japanese name on the page). The Japanese
# names are METI's own, shortened where a line's full name runs long.
METI_LINE = {
    "化粧水": ("Toner", "化粧水"), "美容液": ("Serum", "美容液"), "乳液": ("Emulsion", "乳液"),
    "モイスチャークリーム": ("Moisture cream", "モイスチャークリーム"),
    "マッサージ・コールドクリーム": ("Massage cream", "マッサージ・コールドクリーム"),
    "クレンジングクリーム": ("Cleansing", "クレンジングクリーム"),
    "洗顔クリーム・フォーム": ("Face wash", "洗顔クリーム・フォーム"),
    "パック": ("Mask/pack", "パック"), "男性皮膚用化粧品": ("Men's skincare", "男性皮膚用"),
    "その他の皮膚用化粧品": ("Other skincare", "その他の皮膚用"),
    "ファンデーション": ("Foundation", "ファンデーション"), "おしろい": ("Powder", "おしろい"),
    "口紅": ("Lipstick", "口紅"), "ほほ紅": ("Blush", "ほほ紅"),
    "アイメークアップ": ("Eye makeup", "アイメークアップ"),
    "まゆ墨・まつ毛化粧料": ("Brow & lash", "まゆ墨・まつ毛"),
    "つめ化粧料(除光液を含む)": ("Nail", "つめ化粧料"), "リップクリーム": ("Lip balm", "リップクリーム"),
    "その他の仕上用化粧品": ("Other makeup", "その他の仕上用"),
    "日やけ止め及び日やけ用化粧品": ("Sunscreen", "日やけ止め"),
}

# 財務省's country names -> (English, Japanese on the page); an origin missing
# here shows under 財務省's name.
ORIGIN = {
    "大韓民国": ("Korea", "韓国"), "フランス": ("France", "フランス"),
    "アメリカ合衆国": ("United States", "米国"), "中華人民共和国": ("China", "中国"),
    "イタリア": ("Italy", "イタリア"), "英国": ("United Kingdom", "英国"),
    "タイ": ("Thailand", "タイ"), "台湾": ("Taiwan", "台湾"), "ドイツ": ("Germany", "ドイツ"),
}


def _line(li, lang, cap=True):
    if lang != "en":
        return METI_LINE[li][1]
    name = METI_LINE[li][0]
    return name if cap else name[0].lower() + name[1:]


def _origin(c, lang):
    return ORIGIN.get(c, (c, c))[0 if lang == "en" else 1]


def _year_runs(years):
    """[2019, 2021, 2022, 2023] -> [(2019, 2019), (2021, 2023)]."""
    runs = []
    for y in sorted(years):
        if runs and y == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], y)
        else:
            runs.append((y, y))
    return runs


def _years_en(years):
    return ", ".join(str(a) if a == b else f"{a}–{b}" for a, b in _year_runs(years))


def _years_ja(years):
    return "、".join(f"{a}年" if a == b else f"{a}〜{b}年" for a, b in _year_runs(years))


def market_strings(lang, M, REG):
    """The Market page's copy in one language. Besides text it carries the
    lookups its figures use: the language (mk_en), line and origin names
    (mk_line, mk_origin) and the label formats (mk_l_vs, mk_b_names)."""
    out = _market_en(M, REG) if lang == "en" else _market_ja(M, REG)
    out["mk_en"] = lang == "en"
    out["mk_line"] = {li: _line(li, lang) for li in METI_LINE}
    out["mk_origin"] = {c: _origin(c, lang) for c in M["imports"]["frame"].index}
    return out


def _market_en(M, REG):
    from .sources import source_line
    y0, y1 = M["window"]
    base, K, Y, I, B = M["base"], M["keys"], M["ytd"], M["imports"], M["brk"]
    ed = pd.Timestamp(EDITION + "-01")
    ly, lm = M["last_month"]
    out = {}

    out["mk_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year}"
    out["mk_intro"] = (
        "経済産業省 生産動態統計: manufacturers' monthly shipments by product line, in yen, units "
        f"and kilograms. Changes are measured {y0}→{y1}, after the January {y0} break in the "
        f"skincare lines; makeup, whose shipped value has no step at the break, is also set "
        f"against {base}.")
    figs = [
        (f"Shipped value, {y1}", f"¥{K['total_y1']:,.0f}億",
         f"all {K['n_items']} product lines · skincare {K['skin_share']:.1f}%, "
         f"makeup {K['make_share']:.1f}%"),
        (f"Skincare, {y0}→{y1}", _pct(K["skin_d"]),
         f"¥{K['skin_y0']:,.0f}億 → ¥{K['skin_y1']:,.0f}億"),
        (f"Makeup, {y0}→{y1}", _pct(K["make_d"]),
         f"¥{K['make_y1']:,.0f}億 in {y1} · {_pct(K['make_vs_base'])} against {base}"),
    ]
    if Y:
        figs.append((f"Skincare, Jan–{_MON_ABBR[Y['month']]} {Y['year']} vs {Y['year'] - 1}",
                     f"{Y['skin']:+.1f}%",
                     f"makeup {Y['make']:+.1f}% · all product lines {Y['total']:+.1f}%"))
    out["mk_figs"] = figs

    rows = M["rows"]
    a, b = M["lead"]
    out["mk_l_h"] = (f"{_line(a, 'en')} and {_line(b, 'en', False)} lead shipped value, "
                     f"¥{rows.loc[a, 'value_y1']:,.0f}億 and ¥{rows.loc[b, 'value_y1']:,.0f}億 "
                     f"in {y1}")
    out["mk_l_e"] = (f"{_NUM_EN[len(rows)].capitalize()} METI product lines in skincare, makeup "
                     f"and sunscreen, {y1}. Label: change against {y0}.")
    out["mk_l_x"] = f"Shipped value {y1} (億円)"
    out["mk_l_vs"] = "{d:+.0f}% vs {y}"
    out["mk_l_hover"] = f"¥%{{x:,.0f}}億 in {y1}"

    fu = [_line(li, "en", i == 0) for i, li in enumerate(M["fewer_units"])]
    bu = [_line(li, "en", False) for li in M["by_units"]]
    out["mk_b_h"] = (f"{_and(fu)} grew through value per unit on fewer units; {_and(bu)} grew "
                     "mostly through units")
    out["mk_b_e"] = (f"Change {y1} against {y0}. Circle: units (販売個数). Diamond: value per "
                     "unit (販売金額 ÷ 販売個数). Vertical mark: shipped value. Value per unit moves "
                     "with price and with product mix.")
    out["mk_b_names"] = ["Units", "Value per unit", "Shipped value"]
    out["mk_b_x"] = f"Change {y1} vs {y0} (%)"

    first = M["monthly"].index.min()
    pk = {g: (f"{name} {_MON_EN[p['month']]} ({_years_en(p['years'])})" if p["month"]
              else f"{name}'s differs by year")
          for g, name in (("makeup", "makeup"), ("skincare", "skincare"))
          for p in [M["peaks"][g]]}
    out["mk_g_h"] = f"Shipped value by group, with the January {y0} break marked"
    out["mk_g_e"] = (
        "Shipped value for skincare (皮膚用) and makeup (仕上用), summed from METI's "
        f"{K['n_items']} component product lines. The grouping reproduces METI's 計 subtotals "
        "for 2019 and 2020 and JCIA's published 2024 shares. The vertical line marks January "
        f"{y0}.")
    out["mk_g_cap"] = (
        f"Monthly, {_MON_EN[first.month]} {first.year} – {_MON_EN[lm]} {ly} · shaded from January "
        f"{y0} = after the break · highest month against its centred 12-month average: "
        f"{pk['makeup']}; {pk['skincare']}")

    lead, run = _origin(I["leader"], "en"), _origin(I["runner"], "en")
    since = (f"since {I['since']}" if I["since"] < I["y1"] else f"in {I['y1']}")
    out["mk_i_h"] = (f"{lead} has been the largest origin of HS 3304 imports {since}: "
                     f"¥{I['lead_y1']:,.0f}億 in {I['y1']} against {run}'s ¥{I['runner_y1']:,.0f}億"
                     if I["since"] < I["y1"] else
                     f"{lead} was the largest origin of HS 3304 imports in {I['y1']}: "
                     f"¥{I['lead_y1']:,.0f}億 against {run}'s ¥{I['runner_y1']:,.0f}億")
    out["mk_i_e"] = (
        "財務省 貿易統計, HS 3304 (beauty, make-up and skin-care preparations), imports by "
        f"country of origin, {I['y0']}–{I['y1']}. All HS 3304 sub-codes, including 3304.99-010.")
    out["mk_i_y"] = "億円"

    out["mk_fn_t"] = f"About the January {y0} break"
    out["mk_fn_b"] = _break_note_en(M)

    out["mk_src_meti"] = source_line(["meti"], REG)
    out["mk_src_trade"] = source_line(["trade"], REG)
    return out


def _market_ja(M, REG):
    """The Market page in Japanese: 産業調査体, である調, titles without a
    closing 。, the site's terms (出荷金額, 皮膚用・仕上用, 1個あたり金額)."""
    from .sources import source_line
    y0, y1 = M["window"]
    base, K, Y, I, B = M["base"], M["keys"], M["ytd"], M["imports"], M["brk"]
    ed = pd.Timestamp(EDITION + "-01")
    ly, lm = M["last_month"]
    out = {}

    out["mk_kicker"] = f"レポート · {ed.year}年{ed.month}月版"
    out["mk_intro"] = (
        "経済産業省 生産動態統計：国内の化粧品メーカーによる品目別の月次出荷（金額・個数・重量）。"
        f"皮膚用の品目に{y0}年1月の断層があるため、変化は{y0}→{y1}年で測る。仕上用は出荷金額に"
        f"断層の段差がないため、{base}年とも比べる。")
    figs = [
        (f"{y1}年の出荷金額", f"{K['total_y1']:,.0f}億円",
         f"全{K['n_items']}品目 · 皮膚用{K['skin_share']:.1f}%、仕上用{K['make_share']:.1f}%"),
        (f"皮膚用 {y0}→{y1}年", _pct(K["skin_d"]),
         f"{K['skin_y0']:,.0f}億円 → {K['skin_y1']:,.0f}億円"),
        (f"仕上用 {y0}→{y1}年", _pct(K["make_d"]),
         f"{y1}年 {K['make_y1']:,.0f}億円 · {base}年比{_pct(K['make_vs_base'])}"),
    ]
    if Y:
        figs.append((f"皮膚用 {Y['year']}年1〜{Y['month']}月（{Y['year'] - 1}年同期比）",
                     f"{Y['skin']:+.1f}%",
                     f"仕上用{Y['make']:+.1f}% · 全品目{Y['total']:+.1f}%"))
    out["mk_figs"] = figs

    rows = M["rows"]
    a, b = M["lead"]
    out["mk_l_h"] = (f"出荷金額の上位は{_line(a, 'jp')}と{_line(b, 'jp')}で、{y1}年はそれぞれ"
                     f"{rows.loc[a, 'value_y1']:,.0f}億円、{rows.loc[b, 'value_y1']:,.0f}億円")
    out["mk_l_e"] = (f"経産省の{len(rows)}品目（皮膚用・仕上用・日やけ止め）、{y1}年。"
                     f"ラベルは{y0}年比の変化。")
    out["mk_l_x"] = f"{y1}年の出荷金額（億円）"
    out["mk_l_vs"] = "{y}年比{d:+.0f}%"
    out["mk_l_hover"] = f"{y1}年 %{{x:,.0f}}億円"

    fu = [_line(li, "jp") for li in M["fewer_units"]]
    bu = [_line(li, "jp") for li in M["by_units"]]
    out["mk_b_h"] = (f"{_and_ja(fu)}は個数が減るなか1個あたり金額で伸び、"
                     f"{_and_ja(bu)}は主に個数で伸びた")
    out["mk_b_e"] = (f"{y0}年比の{y1}年の変化。丸：個数（販売個数）、ひし形：1個あたり金額"
                     "（販売金額÷販売個数）、縦線：出荷金額。1個あたり金額は価格と製品構成の両方で動く。")
    out["mk_b_names"] = ["個数", "1個あたり金額", "出荷金額"]
    out["mk_b_x"] = f"{y0}→{y1}年の変化（%）"

    first = M["monthly"].index.min()
    pk = {g: (f"{name}は{p['month']}月（{_years_ja(p['years'])}）" if p["month"]
              else f"{name}は年により異なる")
          for g, name in (("makeup", "仕上用"), ("skincare", "皮膚用"))
          for p in [M["peaks"][g]]}
    out["mk_g_h"] = f"区分別の出荷金額と{y0}年1月の断層"
    out["mk_g_e"] = (
        f"経産省の{K['n_items']}品目を合算した、皮膚用と仕上用の出荷金額。この区分は2019年と2020年の"
        "「計」小計を再現し、日本化粧品工業会が公表する2024年の構成比と一致する。"
        f"縦線は{y0}年1月。")
    out["mk_g_cap"] = (
        f"月次、{first.year}年{first.month}月〜{ly}年{lm}月 · {y0}年1月以降の網掛け＝断層後 · "
        f"中心化12カ月移動平均に対して最も高い月：{pk['makeup']}、{pk['skincare']}")

    lead, run = _origin(I["leader"], "jp"), _origin(I["runner"], "jp")
    out["mk_i_h"] = (f"HS 3304の輸入元は{I['since']}年以降{lead}が最大で、{I['y1']}年は"
                     f"{I['lead_y1']:,.0f}億円（{run}は{I['runner_y1']:,.0f}億円）"
                     if I["since"] < I["y1"] else
                     f"{I['y1']}年のHS 3304の輸入元は{lead}が最大で、{I['lead_y1']:,.0f}億円"
                     f"（{run}は{I['runner_y1']:,.0f}億円）")
    out["mk_i_e"] = (
        "財務省 貿易統計、HS 3304（美容用、メーキャップ用又は皮膚の手入れ用の調製品）、"
        f"原産国別の輸入、{I['y0']}〜{I['y1']}年。HS 3304の全細分（3304.99-010を含む）。")
    out["mk_i_y"] = "億円"

    out["mk_fn_t"] = f"{y0}年1月の断層について"
    out["mk_fn_b"] = _break_note_ja(M)

    out["mk_src_meti"] = source_line(["meti"], REG, "ja")
    out["mk_src_trade"] = source_line(["trade"], REG, "ja")
    return out


def _break_note_en(M):
    """The note on METI's January 2022 break, in English, worded
    from market.compute_market: the Market page carries it."""
    y0, y1 = M["window"]
    base, Y, B = M["base"], M["ytd"], M["brk"]
    ly, lm = M["last_month"]
    J, R = B["jan"], B["range"]
    below = [li for li, r in R.items() if not r["inside"] and not r["above"]]
    other = [li for li in R if li not in below]
    rng = []
    if below:
        rng.append(f"{_and(below)} stay below {'their' if len(below) > 1 else 'its'} "
                   f"{B['pre'][0]}–{B['pre'][1]} range through {_MON_EN[lm]} {ly}")
    for li in other:
        r = R[li]
        part = []
        if r["inside"]:
            part.append(f"inside its range in {_years_en(r['inside'])}")
        if r["above"]:
            part.append(f"above it in {_years_en(r['above'])}")
        rng.append(f"{li} was {' and '.join(part)} and below it in the other years")
    jan = lambda li: f"{abs(J[li][2]):.0f}% for {li} ({J[li][0]:.0f} → {J[li][1]:.0f} 億円)"  # noqa: E731
    ctl = [li for li in J if li not in B["drop"]]
    (k1, k2), kg = list(B["kg"]), B["kg"]
    return (
        "METI's 生産動態統計 collects monthly shipments from cosmetics manufacturers: yen value, "
        "units and kilograms for each product line. Yen divided by kilograms gives an average "
        f"price per kg. For {_and(B['drop'])} that price drops at January {y0}. "
        f"{'; '.join(rng)}. Comparing January {y0} with January {y0 - 1}, shipped value fell "
        f"{_and(jan(li) for li in B['drop'])}, while "
        f"{_and(f'{li} rose {J[li][2]:.0f}%' if i == 0 else f'{li} {J[li][2]:.0f}%' for i, li in enumerate(ctl))}. "
        f"{k1} and {k2} yen per kg also fall in {y0}, with a different pattern: their kilograms "
        f"rose {kg[k1][0]:.0f}% and {kg[k2][0]:.0f}% while shipped value rose {kg[k1][1]:.0f}% "
        f"and {kg[k2][1]:.0f}%. A change in which companies or products are counted would "
        "produce the skincare pattern; METI has published no such change and no link "
        "coefficients for cosmetics. A skincare yen comparison between a year before "
        f"{y0} and a year after includes the drop, so skincare yen changes are measured within "
        f"{base}–{y0 - 1} or within {y0}–{y1}."
        + (f" {Y['year']} figures come from METI's monthly 確報 release." if Y else ""))


def _break_note_ja(M):
    """The note on METI's January 2022 break, in Japanese, worded
    from market.compute_market: the Market page carries it."""
    y0, y1 = M["window"]
    base, Y, B = M["base"], M["ytd"], M["brk"]
    ly, lm = M["last_month"]
    J, R = B["jan"], B["range"]
    below = [li for li, r in R.items() if not r["inside"] and not r["above"]]
    other = [li for li in R if li not in below]
    rng = []
    if below:
        rng.append(f"{_and_ja(below)}は{ly}年{lm}月まで{B['pre'][0]}〜{B['pre'][1]}年の範囲を下回り")
    for li in other:
        r = R[li]
        part = []
        if r["inside"]:
            part.append(f"{_years_ja(r['inside'])}に範囲内")
        if r["above"]:
            part.append(f"{_years_ja(r['above'])}に範囲を上回り")
        rng.append(f"{li}は{'、'.join(part)}、それ以外の年は範囲を下回った")
    ctl = [li for li in J if li not in B["drop"]]
    (k1, k2), kg = list(B["kg"]), B["kg"]
    return (
        "経産省の生産動態統計は、化粧品メーカーから品目ごとの出荷金額・個数・重量（kg）を毎月集計している。"
        "金額を重量で割るとkgあたりの平均単価になる。"
        f"{'・'.join(B['drop'])}では、この単価が{y0}年1月に下落する。{'、'.join(rng)}。"
        f"{y0 - 1}年1月と{y0}年1月を比べると、出荷金額は"
        + "、".join(f"{li}が{abs(J[li][2]):.0f}%（{J[li][0]:.0f}→{J[li][1]:.0f}億円）"
                   for li in B["drop"])
        + "減少し、"
        + "、".join(f"{li}は{J[li][2]:.0f}%" for li in ctl)
        + f"増加した。{k1}と{k2}のkg単価も{y0}年に下落するが形が異なり、重量が{kg[k1][0]:.0f}%、"
        f"{kg[k2][0]:.0f}%増えた一方で出荷金額の増加は{kg[k1][1]:.0f}%、{kg[k2][1]:.0f}%だった。"
        "集計対象の企業や製品が変わった場合に皮膚用のこの形になるが、経産省はそのような変更も"
        f"化粧品のリンク係数も公表していない。{y0}年より前の年と後の年を比べる皮膚用の金額には"
        f"この下落が含まれるため、皮膚用の金額変化は{base}〜{y0 - 1}年または{y0}〜{y1}年の内側で"
        "測る。"
        + (f"{Y['year']}年の数値は経産省の月次確報による。" if Y else ""))


# ── Demand ──────────────────────────────────────────────────────────────────
# Every figure comes from demand.compute_demand; tests/test_demand.py holds the
# data to each direction the copy states.

# block_A's category words and umbrella terms -> (English, Japanese). The
# actives take their names from prtimes_ingredient_terms.csv.
SEARCH_TERM = {
    "美容液": ("Serum", "美容液"), "化粧水": ("Toner", "化粧水"), "洗顔": ("Face wash", "洗顔"),
    "乳液": ("Emulsion", "乳液"), "日焼け止め": ("Sunscreen", "日焼け止め"),
    "ファンデーション": ("Foundation", "ファンデーション"), "口紅": ("Lipstick", "口紅"),
    "アイシャドウ": ("Eyeshadow", "アイシャドウ"),
    "スキンケア": ("Skincare (スキンケア)", "スキンケア"), "化粧品": ("Cosmetics (化粧品)", "化粧品"),
}
# Readings for the kanji terms, so Japanese lists follow 五十音 order.
_READING = {"美容液": "びようえき", "化粧水": "けしょうすい", "洗顔": "せんがん", "乳液": "にゅうえき",
            "日焼け止め": "ひやけどめ", "口紅": "くちべに", "化粧品": "けしょうひん",
            "DNA-Na": "ぴーでぃーあーるえぬ"}
DEMAND_GROUPS = ("active", "category", "umbrella")


def _kana_key(term, name):
    """五十音 sort key: the reading for a kanji term, katakana folded to hiragana."""
    s = _READING.get(term, name)
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def _term_name(term, M, lang, cap=True):
    t = M["terms"]
    if term in t.index:
        name = t.loc[term, "label_short_en" if lang == "en" else "label_ja"]
    else:
        name = SEARCH_TERM[term][0 if lang == "en" else 1]
    return name if (cap or lang != "en" or "(" in name) else name[0].lower() + name[1:]


def _sorted_terms(terms, M, lang):
    if lang == "en":
        return sorted(terms, key=lambda x: _term_name(x, M, "en").lower())
    return sorted(terms, key=lambda x: _kana_key(x, _term_name(x, M, "jp")))


def demand_strings(lang, M, REG):
    """The Demand page's copy in one language, and the lookups its figures use:
    the language (dm_en), each term's name (dm_term) and the change chart's
    order by group (dm_order)."""
    out = _demand_en(M, REG) if lang == "en" else _demand_ja(M, REG)
    out["dm_en"] = lang == "en"
    out["dm_term"] = {t: _term_name(t, M, lang) for t in M["change"].index}
    ch = M["change"]
    out["dm_order"] = [t for g in DEMAND_GROUPS
                       for t in _sorted_terms(list(ch.index[ch["kind"] == g]), M, lang)]
    return out


def _demand_en(M, REG):
    from .sources import source_line
    y0, y1 = M["window"]
    C, P, K, MK = M["changes"], M["pair"], M["keys"], M["makeup"]
    ed = pd.Timestamp(EDITION + "-01")
    last = M["cross"]["week_start"].max()
    nm = lambda t, cap=False: _term_name(t, M, "en", cap)  # noqa: E731
    out = {}

    out["dm_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year}"
    out["dm_intro"] = (
        "Google Trends, Japan. Each term is requested on its own and scaled to its own peak "
        "(= 100), so a change reads in points of that term's peak and levels are not compared "
        "across terms. スキンケア and 化粧品 are also requested together, on one scale.")
    (lt, la, lb, lv0, lv1), (wt, wa, wb, wv0, wv1) = K["long"], K["window"]
    out["dm_figs"] = [
        ("Cosmetics search", f"{P['cosm_d']:+.0f}%",
         f"化粧品, full years {P['y0']}→{P['y1']}, one request with スキンケア"),
        (f"{nm(lt, True)} search", f"{lv0:.0f} → {lv1:.0f}",
         f"annual mean, {la}→{lb}, own peak = 100"),
        (f"{nm(wt, True)} search", f"{wv0:.0f} → {wv1:.0f}",
         f"annual mean, {wa}→{wb}, own peak = 100"),
    ]

    within = _and(nm(t) for t in _sorted_terms(C["within"], M, "en"))
    up = "; ".join(f"{nm(t, True)} rose {M['change'].loc[t, 'd']:.0f} points" for t in C["words_up"])
    out["dm_c_h"] = (
        f"Search rose {C['rose_lo']:.0f}–{C['rose_hi']:.0f} points for {_NUM_EN[C['n_rose']]} of "
        f"{_NUM_EN[C['n_actives']]} tracked actives, {y0}→{y1}; {_NUM_EN[len(C['words_down'])]} "
        f"of {_NUM_EN[C['n_words']]} category words fell")
    out["dm_c_e"] = (
        f"Annual mean, {y1} minus {y0}, in points of each term's own peak. Ink: the "
        f"{_NUM_EN[C['n_rose']]} actives that rose. The shaded band is ±{TRENDS_PULL_SPREAD} "
        f"points, the spread between two downloads of the same series; {within} moved less than "
        f"that. {up}. Terms are alphabetical within each group.")
    out["dm_c_x"] = f"Change, {y1} minus {y0} (points)"
    out["dm_c_groups"] = {"active": "Actives", "category": "Category words",
                          "umbrella": "Umbrella terms"}
    out["dm_c_hover"] = "%{customdata[1]:.0f} → %{customdata[2]:.0f} (annual mean)"

    out["dm_p_h"] = (
        f"Cosmetics (化粧品) search fell {abs(P['cosm_d']):.0f}%, {P['y0']}→{P['y1']}, and stayed "
        "above skincare (スキンケア) search in every year")
    out["dm_p_e"] = (
        f"Monthly, January {P['years'][0]} – {_MON_EN[last.month]} {last.year}, both terms from "
        "one request on one scale. 化粧品 is the umbrella term and includes skincare. Full years "
        f"{P['y0']}→{P['y1']}: スキンケア search {'rose' if P['skin_d'] >= 0 else 'fell'} "
        f"{abs(P['skin_d']):.0f}%, and the gap between the two narrowed {abs(P['gap_d']):.0f}%, "
        f"{P['cosm_share']:.0f}% of it from the fall in 化粧品; the skincare-to-cosmetics ratio "
        f"went from {P['ratio_0']:.2f} to {P['ratio_1']:.2f}.")
    out["dm_p_names"] = {"化粧品": "Cosmetics", "スキンケア": "Skincare"}
    out["dm_p_y"] = "Search interest (one scale)"

    out["dm_i_h"] = (f"{nm(lt, True)} search rose from {lv0:.0f} to {lv1:.0f} on the Trends "
                     f"index, {la}→{lb}")
    out["dm_i_e"] = (f"Annual mean search interest, full years {la}–{lb}, each term scaled to "
                     "its own peak (= 100).")
    out["dm_i_y"] = "Annual mean (own peak = 100)"

    a = MK["annual"]
    gap = MK["last"] - MK["relaxed"].year
    out["dm_m_h"] = (f"In {MK['last']}, {_NUM_EN[gap]} years after mask guidance was relaxed, "
                     f"lipstick search was {a.loc[MK['last'], '口紅']:.0f}% of its 2019 level")
    my0, my1 = min(MASK_YEARS), max(MASK_YEARS)
    out["dm_m_e"] = (
        "Monthly search for three makeup terms, each term's 2019 mean = 100, three-month centred "
        f"average. The dashed line marks {MK['relaxed'].day} {_MON_EN[MK['relaxed'].month]} "
        f"{MK['relaxed'].year}, when Japan left mask wearing to individual judgment. Lipstick and "
        f"foundation search rose in {MK['relaxed'].year} and fell in {MK['last'] - 1} and "
        f"{MK['last']}; lipstick's {MK['last']} mean was below its {_MASK_LOW(a)} mean, the lowest "
        f"of the mask years {my0}–{my1}. Eyeshadow search was above its 2019 level in {my0}–{my1} "
        f"and below it in {MK['last'] - 1}–{MK['last']}.")
    out["dm_m_names"] = {"口紅": "Lipstick (口紅)", "ファンデーション": "Foundation (ファンデーション)",
                         "アイシャドウ": "Eyeshadow (アイシャドウ)"}
    out["dm_m_mask"] = "Mask guidance relaxed"
    out["dm_m_base"] = "2019 = 100"
    out["dm_m_y"] = "Search interest, own 2019 = 100"

    out["dm_src_trends"] = source_line(["trends"], REG)
    return out


def _demand_ja(M, REG):
    """The Demand page in Japanese: 産業調査体, である調, titles without a closing
    。, the site's terms (検索関心度, カテゴリ語)."""
    from .sources import source_line
    y0, y1 = M["window"]
    C, P, K, MK = M["changes"], M["pair"], M["keys"], M["makeup"]
    ed = pd.Timestamp(EDITION + "-01")
    last = M["cross"]["week_start"].max()
    nm = lambda t: _term_name(t, M, "jp")  # noqa: E731
    out = {}

    out["dm_kicker"] = f"レポート · {ed.year}年{ed.month}月版"
    out["dm_intro"] = (
        "Googleトレンド（日本）。各語は単独で取得し、その語のピークを100とする指数である。変化はその語"
        "自身のピークに対するポイントで読み、語どうしの水準は比べない。スキンケアと化粧品は2語を1回で"
        "取得した系列もあり、同じ尺度にある。")
    (lt, la, lb, lv0, lv1), (wt, wa, wb, wv0, wv1) = K["long"], K["window"]
    out["dm_figs"] = [
        ("化粧品の検索", f"{P['cosm_d']:+.0f}%",
         f"暦年{P['y0']}→{P['y1']}年、スキンケアと同一リクエスト"),
        (f"{nm(lt)}の検索", f"{lv0:.0f} → {lv1:.0f}", f"年平均、{la}→{lb}年、自身のピーク＝100"),
        (f"{nm(wt)}の検索", f"{wv0:.0f} → {wv1:.0f}", f"年平均、{wa}→{wb}年、自身のピーク＝100"),
    ]

    within = "、".join(nm(t) for t in _sorted_terms(C["within"], M, "jp"))
    up = "、".join(f"{nm(t)}は{M['change'].loc[t, 'd']:.0f}ポイント上昇した" for t in C["words_up"])
    out["dm_c_h"] = (
        f"{y0}→{y1}年に、追跡する成分{C['n_actives']}語のうち{C['n_rose']}語の検索が"
        f"{C['rose_lo']:.0f}〜{C['rose_hi']:.0f}ポイント上昇し、カテゴリ語は{C['n_words']}語中"
        f"{len(C['words_down'])}語が低下した")
    out["dm_c_e"] = (
        f"年平均の差（{y1}年−{y0}年）、各語のピーク＝100に対するポイント。濃色は上昇した"
        f"{C['n_rose']}成分。網掛けは±{TRENDS_PULL_SPREAD}ポイントで、同じ系列を2回取得したときの差の"
        f"幅である。{within}の変化はこの幅に収まる。{up}。各グループ内は五十音順。")
    out["dm_c_x"] = f"変化、{y1}年−{y0}年（ポイント）"
    out["dm_c_groups"] = {"active": "成分", "category": "カテゴリ語", "umbrella": "総称"}
    out["dm_c_hover"] = "%{customdata[1]:.0f} → %{customdata[2]:.0f}（年平均）"

    out["dm_p_h"] = (f"化粧品の検索は{P['y0']}→{P['y1']}年に{abs(P['cosm_d']):.0f}%低下し、"
                     "どの年もスキンケアの検索を上回った")
    out["dm_p_e"] = (
        f"月次、{P['years'][0]}年1月〜{last.year}年{last.month}月。2語を1回で取得し、同じ尺度にある。"
        f"化粧品は総称で、スキンケアを含む。暦年{P['y0']}→{P['y1']}年でスキンケアの検索は"
        f"{abs(P['skin_d']):.0f}%{'上昇' if P['skin_d'] >= 0 else '低下'}し、両語の差は"
        f"{abs(P['gap_d']):.0f}%縮小した。その{P['cosm_share']:.0f}%は化粧品の低下による。"
        f"スキンケア対化粧品の検索比は{P['ratio_0']:.2f}→{P['ratio_1']:.2f}。")
    out["dm_p_names"] = {"化粧品": "化粧品", "スキンケア": "スキンケア"}
    out["dm_p_y"] = "検索関心度（同一尺度）"

    out["dm_i_h"] = (f"{nm(lt)}の検索は{la}→{lb}年にGoogleトレンドの指数で{lv0:.0f}から"
                     f"{lv1:.0f}へ上昇")
    out["dm_i_e"] = f"年平均の検索関心度、暦年{la}〜{lb}年、各語のピーク＝100。"
    out["dm_i_y"] = "年平均（自身のピーク＝100）"

    a = MK["annual"]
    gap = MK["last"] - MK["relaxed"].year
    out["dm_m_h"] = (f"マスク着用ルール緩和から{gap}年後の{MK['last']}年、口紅の検索は2019年の"
                     f"{a.loc[MK['last'], '口紅']:.0f}%")
    my0, my1 = min(MASK_YEARS), max(MASK_YEARS)
    rl = MK["relaxed"]
    out["dm_m_e"] = (
        "メイク3語の月次検索、各語の2019年平均＝100、3カ月中心移動平均。破線は"
        f"{rl.year}年{rl.month}月{rl.day}日で、この日からマスクの着用は個人の判断となった。"
        f"口紅とファンデーションの検索は{rl.year}年に上昇し、{MK['last'] - 1}年と{MK['last']}年に"
        f"低下した。口紅の{MK['last']}年平均は、マスク着用期（{my0}〜{my1}年）で最も低い"
        f"{_MASK_LOW(a)}年を下回った。アイシャドウの検索は{my0}〜{my1}年に2019年を上回り、"
        f"{MK['last'] - 1}〜{MK['last']}年に下回った。")
    out["dm_m_names"] = {"口紅": "口紅", "ファンデーション": "ファンデーション",
                         "アイシャドウ": "アイシャドウ"}
    out["dm_m_mask"] = "マスク着用ルール緩和"
    out["dm_m_base"] = "2019年＝100"
    out["dm_m_y"] = "検索関心度（各語の2019年＝100）"

    out["dm_src_trends"] = source_line(["trends"], REG, "ja")
    return out


def _MASK_LOW(a):
    """The mask year in which lipstick search was lowest."""
    return int(a.loc[list(MASK_YEARS), "口紅"].idxmin())


# ── Supply ──────────────────────────────────────────────────────────────────
# Every figure comes from supply.compute_supply; tests/test_supply.py holds the
# data to each direction the copy states.

SUPPLY_ORIGIN = {"KR": ("Korea", "韓国"), "JP": ("Japan", "日本"),
                 "global": ("Global majors", "グローバル大手"), "CN": ("China", "中国")}
SUPPLY_GROUP = {"skincare": ("Skincare", "スキンケア"), "makeup": ("Makeup", "メイク"),
                "other": ("Hair, body and fragrance", "ヘア・ボディ・フレグランス"),
                "none": ("No category word", "カテゴリ語なし")}

def _supply_ing(M, lang):
    """Each ingredient named in either window -> its name, and their order:
    alphabetical in English, 五十音 in Japanese."""
    t = M["terms"].set_index("canonical")
    col = "label_short_en" if lang == "en" else "label_ja"
    names = {k: t.loc[k, col] for k in M["ingredients"]["frame"].index}
    if lang == "en":
        order = sorted(names, key=lambda k: names[k].lower())
    else:
        order = sorted(names, key=lambda k: _kana_key(k, names[k]))
    return names, order


def supply_strings(lang, M, REG):
    """The Supply page's copy in one language, and the lookups its figures
    use: the language (sp_en), the names of categories, origins, half-years,
    groups and ingredients, and the ingredients' order."""
    li = _li(lang)
    out = _supply_en(M, REG) if lang == "en" else _supply_ja(M, REG)
    out["sp_en"] = lang == "en"
    out["sp_cat"] = {k: LAUNCH_CAT[k][li] for k in M["share"]["rows"].index}
    out["sp_origin"] = {k: v[li] for k, v in SUPPLY_ORIGIN.items()}
    out["sp_half"] = {h: (h if lang == "en" else _half_ja(h)) for h in M["origin"]["shares"].index}
    out["sp_group"] = {k: v[li] for k, v in SUPPLY_GROUP.items()}
    out["sp_ing"], out["sp_ing_order"] = _supply_ing(M, lang)
    return out


def _held(a, b):
    """True when a 12-month total is within HELD_PCT percent of the one before."""
    return abs(100 * (a / b - 1)) < HELD_PCT


def _supply_en(M, REG):
    from .sources import source_line
    y0, y1 = M["window"]
    SH, O, G, I = M["share"], M["origin"], M["groups"], M["ingredients"]
    rows, (n0, n1) = SH["rows"], SH["den"]
    ed = pd.Timestamp(EDITION + "-01")
    last = _ym(M["last"], "en")
    last_short = f"{_MON_ABBR[int(M['last'][5:7])]} {M['last'][:4]}"
    (k0, t0), (k1, t1) = O["kr_first"], O["kr_last"]
    gl, gp = G["l12"], G["p12"]
    f = I["frame"]
    top = f.loc[I["top"]]
    ing_name = _supply_ing(M, "en")[0]
    key = rows.loc[KEY_CATEGORY]
    out = {}

    out["sp_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year}"
    out["sp_intro"] = (
        f"Product-launch releases from the {M['n_core']} issuers whose PR TIMES history reaches "
        "back to September 2021, by month of release; one release is one count.")
    out["sp_figs"] = [
        (f"Launch releases, 12 months to {last_short}", f"{M['tot_l12']:,}",
         f"core issuers · {M['tot_p12']:,} in the 12 months before"),
        (f"{_cat(KEY_CATEGORY, True)} share of launch releases, {y1}",
         f"{key['launch_s1']:.0f}%", f"{key['launch_n1']} of {n1} categorised releases"),
        (f"Korean issuers, {O['last']}", f"{100 * k1 / t1:.0f}%",
         f"{k1} of {t1} core launch releases · {100 * k0 / t0:.0f}% in {O['first']}"),
        ("Releases naming a tracked ingredient", f"{I['any_share']}%",
         f"{I['any_n']} of {I['den_l12']}, 12 months to {last_short}, editions left out"),
    ]

    g_lo, g_hi = SH["gain_lo"], SH["gain_hi"]
    a, b = SH["gainers"]
    each = (f"each gained {g_lo:.0f} points" if round(g_lo) == round(g_hi)
            else f"gained {SH['rows'].loc[a, 'launch_d']:.0f} and {SH['rows'].loc[b, 'launch_d']:.0f} points")
    out["sp_s_h"] = (
        f"{_cat(a, True)} and {_cat(b)} {each} of launch share, {y0}→{y1} "
        f"({rows.loc[a, 'launch_n1']} and {rows.loc[b, 'launch_n1']} of {n1} releases in {y1}); "
        f"{_cat(SH['loser'])} lost {abs(SH['loss']):.0f} ({rows.loc[SH['loser'], 'launch_n1']} of {n1})")
    out["sp_s_e"] = (
        f"Share of the categorised core launch releases that name each category: {y0} ({n0} "
        f"releases, hollow) and {y1} ({n1}, filled). A release naming two categories counts in "
        f"each. Ink: {_cat(a)}, {_cat(b)} and {_cat(SH['loser'])}.")
    out["sp_s_x"] = "Share of categorised core launch releases (%)"

    iss = O["issuers"]
    out["sp_o_h"] = (
        f"Korean issuers made {100 * k1 / t1:.0f}% ({k1} of {t1}) of core launch releases in "
        f"{O['last']}, from {100 * k0 / t0:.0f}% ({k0} of {t0}) in {O['first']}")
    out["sp_o_e"] = (
        f"The {M['n_core']} core issuers by brand origin: {iss['KR']} Korean, {iss['JP']} Japanese, "
        f"{iss['global']} global majors and {iss['CN']} Chinese. Each complete half-year from "
        f"{O['first']} to {O['last']}; releases per half-year on hover.")
    out["sp_o_y"] = "Share of core launch releases"

    def _move(g):
        if _held(gl[g], gp[g]):
            return f"held at {gl[g]}"
        d = G["change"][g]
        return f"{'rose' if d > 0 else 'fell'} {abs(d):.0f}% to {gl[g]}"
    out["sp_g_h"] = (f"Skincare launch releases {_move('skincare')} in the 12 months to {last}; "
                     f"makeup {_move('makeup')}")
    out["sp_g_e"] = (
        f"The {M['n_core']} core issuers. 12-month totals by the product category named in the "
        "title or excerpt; releases that name no category word form their own line. The 12 "
        f"months before: skincare {gp['skincare']}, makeup {gp['makeup']}.")
    out["sp_g_y"] = "Launch releases, 12-month total"

    out["sp_i_h"] = (
        f"{ing_name[I['top']]} appeared in {top['s_l12']:.1f}% of launch releases in the 12 months "
        f"to {last} ({top['n_l12']} of {I['den_l12']}), from {top['s_p12']:.1f}% a year earlier "
        f"({top['n_p12']} of {I['den_p12']})")
    out["sp_i_e"] = (
        f"The {M['n_core']} core issuers. Share of launch releases whose title or excerpt names the "
        f"ingredient; hollow: the 12 months before, filled: the 12 months to {last}. "
        f"{I['any_share']}% ({I['any_n']}) name at least one of the {I['n_terms']} tracked "
        f"ingredients; the {len(f)} named at least once are listed alphabetically. Releases whose "
        "title names a re-release, refill or limited packaging are left out.")
    out["sp_i_x"] = "Share of launch releases (%)"
    out["sp_win_l12"] = f"12 months to {last}"
    out["sp_win_p12"] = "12 months before"

    _G = LAUNCH_GATE
    out["sp_cap"] = (
        f"Measured {_G['asof']}. Launch gate: precision {_G['precision']} (95% CI "
        f"{_G['p_lo']}–{_G['p_hi']}) and recall {_G['recall']} ({_G['r_lo']}–{_G['r_hi']}) "
        f"on {_G['n_holdout']} hand-labelled releases held out from the gate's design, "
        f"weighted to {_G['n_store']:,} stored releases. PR TIMES coverage: "
        f"{_G['prestige_unseen']} of {_G['prestige_n']} prestige (デパコス) brands in the brand "
        f"list appear in no stored release, against {_G['other_unseen']} of {_G['other_n']} "
        f"brands in other tiers. The edition filter finds {_G['edition_found']} of "
        f"{_G['edition_n']} hand-labelled editions.")
    out["sp_src_prtimes"] = source_line(["prtimes"], REG)
    return out


def _supply_ja(M, REG):
    """The Supply page in Japanese: 産業調査体, である調, titles without a closing
    。, the site's terms (リリース構成比, コア発行元の新商品リリース, 韓国系発行元)."""
    from .sources import source_line
    y0, y1 = M["window"]
    SH, O, G, I = M["share"], M["origin"], M["groups"], M["ingredients"]
    rows, (n0, n1) = SH["rows"], SH["den"]
    ed = pd.Timestamp(EDITION + "-01")
    last = _ym(M["last"], "jp")
    (k0, t0), (k1, t1) = O["kr_first"], O["kr_last"]
    gl, gp = G["l12"], G["p12"]
    f = I["frame"]
    top = f.loc[I["top"]]
    ing_name = _supply_ing(M, "jp")[0]
    cj = lambda k: LAUNCH_CAT[k][1]  # noqa: E731
    key = rows.loc[KEY_CATEGORY]
    out = {}

    out["sp_kicker"] = f"レポート · {ed.year}年{ed.month}月版"
    out["sp_intro"] = (
        f"PR TIMES上の新商品リリース。同サイト上の履歴が2021年9月まで遡る{M['n_core']}社を配信月別に"
        "数え、1リリースを1件とする。")
    out["sp_figs"] = [
        (f"新商品リリース、{last}までの12カ月", f"{M['tot_l12']:,}件",
         f"コア発行元 · 前年同期{M['tot_p12']:,}件"),
        (f"{cj(KEY_CATEGORY)}のリリース構成比、{y1}年", f"{key['launch_s1']:.0f}%",
         f"カテゴリ付きリリース{n1}件中{key['launch_n1']}件"),
        (f"韓国系発行元、{_half_ja(O['last'])}", f"{100 * k1 / t1:.0f}%",
         f"コア発行元の新商品リリース{t1}件中{k1}件 · {_half_ja(O['first'])}は{100 * k0 / t0:.0f}%"),
        ("追跡成分を含むリリース", f"{I['any_share']}%",
         f"{I['den_l12']}件中{I['any_n']}件、{last}までの12カ月、限定・再発売を除く"),
    ]

    g_lo, g_hi = SH["gain_lo"], SH["gain_hi"]
    a, b = SH["gainers"]
    each = (f"それぞれ{g_lo:.0f}ポイント" if round(g_lo) == round(g_hi)
            else f"{rows.loc[a, 'launch_d']:.0f}ポイントと{rows.loc[b, 'launch_d']:.0f}ポイント")
    out["sp_s_h"] = (
        f"{y0}→{y1}年に、リリース構成比は{cj(a)}と{cj(b)}が{each}上昇し（{y1}年は{n1}件中"
        f"{rows.loc[a, 'launch_n1']}件と{rows.loc[b, 'launch_n1']}件）、{cj(SH['loser'])}は"
        f"{abs(SH['loss']):.0f}ポイント低下した（同{rows.loc[SH['loser'], 'launch_n1']}件）")
    out["sp_s_e"] = (
        f"カテゴリ付きのコア新商品リリースのうち、各カテゴリを記載したものの比率。{y0}年（{n0}件、"
        f"白抜き）と{y1}年（{n1}件、塗り）。2つのカテゴリを記載したリリースはそれぞれに数える。"
        f"濃色は{cj(a)}・{cj(b)}・{cj(SH['loser'])}。")
    out["sp_s_x"] = "カテゴリ付きコア新商品リリースに占める比率（%）"

    iss = O["issuers"]
    out["sp_o_h"] = (
        f"コア発行元の新商品リリースに占める韓国系発行元の比率は{_half_ja(O['last'])}に"
        f"{100 * k1 / t1:.0f}%（{t1}件中{k1}件）となり、{_half_ja(O['first'])}の"
        f"{100 * k0 / t0:.0f}%（{t0}件中{k0}件）から上昇")
    out["sp_o_e"] = (
        f"コア発行元{M['n_core']}社をブランドの出自で分けた（韓国系{iss['KR']}社、日系{iss['JP']}社、"
        f"グローバル大手{iss['global']}社、中国系{iss['CN']}社）。{_half_ja(O['first'])}から"
        f"{_half_ja(O['last'])}まで、6カ月そろった半期ごと。半期ごとの件数はカーソルを合わせると表示される。")
    out["sp_o_y"] = "コア新商品リリースに占める比率"

    def _move(g):
        if _held(gl[g], gp[g]):
            return f"{gl[g]}件で横ばい"
        d = G["change"][g]
        return f"{gl[g]}件で前年同期比{abs(d):.0f}%{'増' if d > 0 else '減'}"
    out["sp_g_h"] = (f"直近12カ月（{last}まで）のスキンケア新商品リリースは{_move('skincare')}、"
                     f"メイクは{_move('makeup')}")
    out["sp_g_e"] = (
        f"コア発行元{M['n_core']}社。タイトルまたは抜粋に記載された商品カテゴリ別の12カ月合計。"
        "カテゴリ語を含まないリリースは別系列とした。前年同期12カ月はスキンケア"
        f"{gp['skincare']}件、メイク{gp['makeup']}件。")
    out["sp_g_y"] = "新商品リリース件数、12カ月合計"

    out["sp_i_h"] = (
        f"{ing_name[I['top']]}を含む新商品リリースは直近12カ月（{last}まで）で{top['s_l12']:.1f}%"
        f"（{I['den_l12']}件中{top['n_l12']}件）、前年同期は{top['s_p12']:.1f}%"
        f"（{I['den_p12']}件中{top['n_p12']}件）")
    out["sp_i_e"] = (
        f"コア発行元{M['n_core']}社。タイトルまたは抜粋に成分名を含む新商品リリースの比率。白抜きは"
        f"前年同期12カ月、塗りは{last}までの12カ月。追跡する{I['n_terms']}成分のいずれかを含むのは"
        f"{I['any_share']}%（{I['any_n']}件）。1件以上に記載された{len(f)}成分を五十音順に示す。"
        "タイトルに再発売・詰め替え・限定パッケージを含むリリースは除いた。")
    out["sp_i_x"] = "新商品リリースに占める比率（%）"
    out["sp_win_l12"] = f"直近12カ月（{last}まで）"
    out["sp_win_p12"] = "前年同期12カ月"

    _G = LAUNCH_GATE
    out["sp_cap"] = (
        f"{_G['asof']}測定。新商品判定の精度：適合率{_G['precision']}（95%信頼区間"
        f"{_G['p_lo']}〜{_G['p_hi']}）、再現率{_G['recall']}（同{_G['r_lo']}〜{_G['r_hi']}）。"
        f"判定語彙の設計に用いていない手作業ラベル{_G['n_holdout']}件で測り、保存済み"
        f"{_G['n_store']:,}件に加重した。PR TIMESの収録：ブランドリストのデパコス"
        f"{_G['prestige_n']}ブランドのうち{_G['prestige_unseen']}ブランドは保存済みリリースに一度も"
        f"現れない。その他の価格帯は{_G['other_n']}ブランド中{_G['other_unseen']}。"
        f"限定・再発売の除外判定は手作業ラベルの{_G['edition_n']}件中{_G['edition_found']}件を検出する。")
    out["sp_src_prtimes"] = source_line(["prtimes"], REG, "ja")
    return out


# ── Consumer ────────────────────────────────────────────────────────────────
# Every figure comes from consumer.compute_consumer. @cosme and YouTube are
# read within one side (METHODOLOGY, Source roles): the copy compares no
# vocabulary, count, share or volume across sides or years.

# The @cosme categories in review_map.csv (categories.normalized_name) → names.
REVIEW_CAT = {
    "cleansing": ("Cleansing", "クレンジング"), "face_wash": ("Face wash", "洗顔料"),
    "toner_lotion": ("Toner", "化粧水"), "serum_essence": ("Serum", "美容液"),
    "emulsion": ("Emulsion", "乳液"), "face_cream": ("Face cream", "フェイスクリーム"),
    "sun_protection": ("Sunscreen", "日焼け止め"), "foundation": ("Foundation", "ファンデーション"),
    "lip_colour": ("Lipstick and gloss", "口紅・グロス"), "eye_shadow": ("Eyeshadow", "アイシャドウ"),
}


def consumer_strings(lang, M, REG):
    """The Consumer page's copy in one language, and the lookups its figures
    use: the language (cs_en), category names (cs_cat) and hover text."""
    out = _consumer_en(M, REG) if lang == "en" else _consumer_ja(M, REG)
    out["cs_en"] = lang == "en"
    out["cs_cat"] = {k: v[_li(lang)] for k, v in REVIEW_CAT.items()}
    return out


def _consumer_en(M, REG):
    from .sources import source_line
    vc, ph = M["vocab"], M["phrase"]
    ed = pd.Timestamp(EDITION + "-01")
    out = {}
    out["cs_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year}"
    out["cs_intro"] = ("Skincare vocabulary in @cosme reviews and YouTube comments, and a map of "
                       "@cosme reviews placed by vocabulary.")

    out["cs_v_h"] = (f"{vc['shared']} of the top {vc['top']} skincare terms appear in both "
                     "@cosme reviews and YouTube comments")
    out["cs_v_e"] = (
        "@cosme skincare reviews, and comments on YouTube videos from the skincare search "
        "categories. One tokeniser (nouns and adjectives) and one TF-IDF for both; terms ranked "
        "by mean weight across skincare documents. In ink: terms in both lists.")
    out["cs_vcols"] = ["", "@cosme reviews", "YouTube comments"]

    out["cs_m_h"] = (
        f"Reviews that contain プレゼント or 当選 sit together on the review map: on average "
        f"{ph['nn_phrase']:.1f} of their {ph['k']} nearest reviews contain one too, against "
        f"{ph['nn_other']:.1f} for other reviews")
    cats = (f"all {_NUM_EN[ph['n_cats']]}" if ph["cats"] == ph["n_cats"]
            else f"{_NUM_EN[ph['cats']]} of {_NUM_EN[ph['n_cats']]}")
    out["cs_m_e"] = (
        f"Each dot is one of {ph['total']:,} @cosme reviews, placed by vocabulary (UMAP): "
        f"reviews that use similar words sit closer together. In ink: the {ph['n']:,} reviews "
        f"that contain プレゼント (present) or 当選 (won a draw), from {cats} product categories.")
    out["cs_m_label"] = "プレゼント / 当選"
    out["cs_m_hover"] = {0: "%{customdata}", 1: "%{customdata} · プレゼント / 当選"}

    out["cs_src_cosme"] = source_line(["cosme"], REG)
    out["cs_src_both"] = source_line(["cosme", "youtube"], REG)
    return out


def _consumer_ja(M, REG):
    """The Consumer page in Japanese: 産業調査体, である調, titles without a
    closing 。, the site's terms (スキンケアとメイク)."""
    from .sources import source_line
    vc, ph = M["vocab"], M["phrase"]
    ed = pd.Timestamp(EDITION + "-01")
    out = {}
    out["cs_kicker"] = f"レポート · {ed.year}年{ed.month}月版"
    out["cs_intro"] = "@cosmeレビューとYouTubeコメントのスキンケア語彙、および語彙で配置した@cosmeレビューのマップ。"

    out["cs_v_h"] = (f"スキンケアの上位{vc['top']}語のうち{vc['shared']}語が、@cosmeレビューと"
                     "YouTubeコメントの両方に入る")
    out["cs_v_e"] = (
        "@cosmeのスキンケアレビューと、スキンケアの検索カテゴリで集めたYouTube動画へのコメント。両者に同じ"
        "トークナイザー（名詞と形容詞）とTF-IDFを用い、スキンケア文書での平均重みで順位を付けた。"
        "濃色は両方のリストにある語。")
    out["cs_vcols"] = ["", "@cosmeレビュー", "YouTubeコメント"]

    cats = (f"{ph['n_cats']}の商品カテゴリすべて" if ph["cats"] == ph["n_cats"]
            else f"{ph['n_cats']}の商品カテゴリのうち{ph['cats']}")
    out["cs_m_h"] = (
        f"「プレゼント」「当選」を含むレビューはレビューマップ上でまとまり、最も近い{ph['k']}件のうち"
        f"平均{ph['nn_phrase']:.1f}件が同じ語を含む（他のレビューは{ph['nn_other']:.1f}件）")
    out["cs_m_e"] = (
        f"各点は@cosmeレビュー{ph['total']:,}件のうちの1件で、語彙によって配置した（UMAP）。"
        f"似た語を使うレビューほど近くに置かれる。濃色は「プレゼント」または「当選」を含む"
        f"{ph['n']:,}件で、{cats}にわたる。")
    out["cs_m_label"] = "プレゼント／当選"
    out["cs_m_hover"] = {0: "%{customdata}", 1: "%{customdata} · プレゼント／当選"}

    out["cs_src_cosme"] = source_line(["cosme"], REG, "ja")
    out["cs_src_both"] = source_line(["cosme", "youtube"], REG, "ja")
    return out


# ── Timing ──────────────────────────────────────────────────────────────────
# Every figure comes from timing.compute_timing on the seasonal method
# (bp/seasonal.py). The copy names a peak only where the method finds it
# stable, and uses no causal wording.

# The umbrella search terms are not categories; they are named as terms.
_UMBRELLA_ROW = {"スキンケア": ("スキンケア", "スキンケア"), "化粧品": ("化粧品", "化粧品")}


def timing_strings(lang, M, REG):
    """The Timing page's copy in one language, and the lookups its figures
    use: row names by category (tm_rows_ship, tm_rows_search), month labels,
    panel names and hover text."""
    out = _timing_page_en(M, REG) if lang == "en" else _timing_page_ja(M, REG)
    li = _li(lang)
    out["tm_rows_ship"] = {k: LAUNCH_CAT[k][li] for k in M["ship"].index}
    out["tm_rows_search"] = {t: (_UMBRELLA_ROW.get(t) or SEARCH_TERM[t])[li]
                             for t in M["search"].index}
    return out


def _tm_facts(M):
    from .seasonal import RATIO_WINDOW, SEARCH_SWING
    ship, srch, t = M["ship"], M["search"], M["tests"]
    odd = t[~t["even"]]
    w0, w1 = (pd.Timestamp(x) for x in RATIO_WINDOW)
    per_side = t.groupby("side")["even"].agg(["sum", "size"])
    per_side = per_side.sort_values("sum", ascending=False)
    return dict(ship=ship, srch=srch, t=t, odd=odd, w0=w0, w1=w1, swing=SEARCH_SWING,
                per_side=per_side,
                n_pass=int(ship["passes"].sum()), n_ship=len(ship),
                s_pass=srch[srch["passes"]].sort_values("swing", ascending=False),
                n_even=int(t["even"].sum()), n_tests=len(t),
                sl=M["sun_launch"], sun=M["sun"], y0=FULL_YEARS[0], y1=FULL_YEARS[-1])


def _timing_page_en(M, REG):
    from .sources import source_line
    F = _tm_facts(M)
    ed = pd.Timestamp(EDITION + "-01")
    sun, off = F["sun"], F["sun"]["offset"]
    (sa, sb), (ha, hb) = sun["search"]["run"], sun["ship"]["run"]
    rng = lambda a, b: f"{_MON_EN[a]}–{_MON_EN[b]}"  # noqa: E731
    win = f"{_MON_EN[F['w0'].month]} {F['w0'].year} – {_MON_EN[F['w1'].month]} {F['w1'].year}"
    out = {}
    out["tm_kicker"] = f"Report · Edition {_MON_EN[ed.month]} {ed.year}"
    out["tm_intro"] = (
        "Seasonal ratio: each month's value divided by the centred 12-month average around it, "
        f"× 100, so 100 is a month on trend. Every series is averaged over {win}. A peak month is "
        f"named only where each of {F['y0']}–{F['y1']} has its highest month within one month of "
        "the centre of the average's three-month peak run.")
    same = len(set(off.values())) == 1
    out["tm_figs"] = [
        ("Sunscreen, search after shipments",
         f"{off[F['y0']]} months" if same else "varies",
         f"peak runs, each year {F['y0']}–{F['y1']}"),
        ("Stable shipment peaks", f"{F['n_pass']} of {F['n_ship']}", "METI product lines"),
        ("Search terms with a season", f"{len(F['s_pass'])} of {len(F['srch'])}",
         f"stable peak and a swing above {F['swing']} points"),
    ]
    out["tm_s_h"] = (f"Sunscreen search peaks {rng(sa, sb)} and shipments {rng(ha, hb)}, "
                     f"{_NUM_EN[off[F['y0']]]} months apart in every year from {F['y0']} to {F['y1']}"
                     if same else f"Sunscreen search peaks {rng(sa, sb)} and shipments {rng(ha, hb)}")
    out["tm_s_e"] = (
        f"Seasonal ratio by month. Line: the average over {win}. Grey band: the lowest and "
        "highest year for each month. Shaded: the three months with the highest average.")
    out["tm_s_search"] = "Search: 日焼け止め (Google Trends)"
    out["tm_s_ship"] = "Shipped value: 日やけ止め及び日やけ用化粧品 (METI)"
    out["tm_y"] = "Seasonal ratio (trend = 100)"
    out["tm_h_months"] = [m[0] for m in _MON_ABBR[1:]]
    out["tm_h_hover"] = "%{customdata}, month %{x}: %{z:.0f}"
    cap = "Shading is capped at 70 and 130; printed values are not."

    out["tm_h1_h"] = (f"{_NUM_EN[F['n_pass']].capitalize()} of the {F['n_ship']} METI product lines "
                      f"ship most in the same month, give or take one, every year {F['y0']}–{F['y1']}")
    out["tm_h1_e"] = (
        f"Seasonal ratio of shipped value, averaged over {win}; lines ordered by their highest "
        "month. Grey label: in at least one year the highest month is more than one month from "
        f"the centre of the average's peak run. {cap}")
    sp = F["s_pass"]
    names = _and(f"{SEARCH_TERM[t][0].lower()} ({r['swing']:.1f})" for t, r in sp.iterrows())
    out["tm_h2_h"] = (f"{_NUM_EN[len(sp)].capitalize()} of {_NUM_EN[len(F['srch'])]} search terms "
                      f"have a stable peak and swing more than {F['swing']} index points: {names}")
    out["tm_h2_e"] = (
        f"Google Trends, each term requested on its own; seasonal ratio averaged over {win}. Swing: "
        "the average's peak-to-trough range in index points. "
        f"{F['swing']} points is the top of the spread between repeat pulls of the same month. "
        "スキンケア and 化粧品 are the umbrella terms. Grey label: a term that fails either test. "
        f"{cap}")
    out["tm_h2_swing"] = "Swing"

    odd = F["odd"]
    exc = "; ".join(f"the exception is {r['side']} in {r['year']}, with {r['top_n']} of {r['n']} "
                    f"in {_MON_EN[r['top_month']]}" for _, r in odd.iterrows())
    sides = _and((f"all {_NUM_EN[n]} {side} years" if e == n
                  else f"{_NUM_EN[e]} of {_NUM_EN[n]} {side} years")
                 for side, (e, n) in F["per_side"].iterrows())
    out["tm_l_h"] = (f"Launch releases by month are consistent with an even spread in {sides}"
                     + (f"; {exc}" if len(odd) else ""))
    t = F["t"]
    out["tm_l_e"] = (
        f"Core-panel launch releases by month of release, {t['year'].min()}–{t['year'].max()}; "
        f"each year tested against an even spread across the months (chi-square, 11 degrees of "
        "freedom, 5%). Ink: the year that departs from an even spread.")
    out["tm_l_side"] = {"skincare": "Skincare", "makeup": "Makeup"}
    out["tm_l_hover"] = "{y}, month %{{x}}: %{{y}} releases"
    out["tm_l_end"] = "{y}: {n}"
    out["tm_l_y"] = "Launch releases per month"

    out["tm_src_sun"] = source_line(["trends", "meti"], REG)
    out["tm_src_meti"] = source_line(["meti"], REG)
    out["tm_src_trends"] = source_line(["trends"], REG)
    out["tm_src_prtimes"] = source_line(["prtimes"], REG)
    return out


def _timing_page_ja(M, REG):
    """The Timing page in Japanese: 産業調査体, である調, titles without a
    closing 。."""
    from .sources import source_line
    F = _tm_facts(M)
    ed = pd.Timestamp(EDITION + "-01")
    sun, off = F["sun"], F["sun"]["offset"]
    (sa, sb), (ha, hb) = sun["search"]["run"], sun["ship"]["run"]
    win = f"{F['w0'].year}年{F['w0'].month}月〜{F['w1'].year}年{F['w1'].month}月"
    same = len(set(off.values())) == 1
    out = {}
    out["tm_kicker"] = f"レポート · {ed.year}年{ed.month}月版"
    out["tm_intro"] = (
        "季節比率：各月の値を、その月を中心とする12カ月移動平均で割り100を掛けたもの。100はトレンド"
        f"どおりの月である。どの系列も{win}で平均する。ピーク月は、{F['y0']}〜{F['y1']}年の各年で最も"
        "高い月が、平均で最も高い3カ月の中央の月の前後1カ月以内にある場合のみ示す。")
    out["tm_figs"] = [
        ("日焼け止め、出荷から検索まで", f"{off[F['y0']]}カ月" if same else "年により異なる",
         f"ピークの3カ月、{F['y0']}〜{F['y1']}年の各年"),
        ("出荷ピークが安定した品目", f"{F['n_ship']}品目中{F['n_pass']}品目", "経産省の品目"),
        ("季節性のある検索語", f"{len(F['srch'])}語中{len(F['s_pass'])}語",
         f"ピークが安定し、振れ幅が{F['swing']}ポイント超"),
    ]
    out["tm_s_h"] = (f"日焼け止めの検索は{sa}〜{sb}月、出荷金額は{ha}〜{hb}月にピークとなり、"
                     f"{F['y0']}〜{F['y1']}年の各年で{off[F['y0']]}カ月の差がある"
                     if same else f"日焼け止めの検索は{sa}〜{sb}月、出荷金額は{ha}〜{hb}月にピークとなる")
    out["tm_s_e"] = (f"月別の季節比率。線：{win}の平均。灰色の帯：各月の最も低い年と最も高い年。"
                     "網掛け：平均が最も高い3カ月。")
    out["tm_s_search"] = "検索：日焼け止め（Googleトレンド）"
    out["tm_s_ship"] = "出荷金額：日やけ止め及び日やけ用化粧品（経産省）"
    out["tm_y"] = "季節比率（トレンド＝100）"
    out["tm_h_months"] = [str(m) for m in range(1, 13)]
    out["tm_h_hover"] = "%{customdata}、%{x}月：%{z:.0f}"
    cap = "濃淡は70と130で打ち切り、表示の数値は打ち切らない。"

    out["tm_h1_h"] = (f"経産省の{F['n_ship']}品目のうち{F['n_pass']}品目は、{F['y0']}〜{F['y1']}年の"
                      "毎年、同じ月（前後1カ月以内）に出荷金額が最も多い")
    out["tm_h1_e"] = (f"出荷金額の季節比率を{win}で平均し、最も高い月の順に並べた。灰色のラベル：少なくとも"
                      f"1年で、最も高い月が平均のピークの3カ月の中央から1カ月より離れている品目。{cap}")
    sp = F["s_pass"]
    names = "、".join(f"{SEARCH_TERM[t][1]}（{r['swing']:.1f}）" for t, r in sp.iterrows())
    out["tm_h2_h"] = (f"{len(F['srch'])}語のうち、ピークが安定し振れ幅が{F['swing']}ポイントを超える検索語は"
                      f"{len(sp)}語：{names}")
    out["tm_h2_e"] = (
        f"Googleトレンド、各語を単独で取得。季節比率は{win}の平均。振れ幅：平均のピークから谷までの"
        f"幅を指数のポイントで表したもの。{F['swing']}ポイントは同じ月を再取得したときの差の上限である。"
        f"スキンケアと化粧品は総称。灰色のラベル：いずれかの基準を満たさない語。{cap}")
    out["tm_h2_swing"] = "振れ幅"

    odd = F["odd"]
    side = {"skincare": "スキンケア", "makeup": "メイク"}
    exc = "、".join(f"例外は{r['year']}年の{side[r['side']]}で、{r['n']}件中{r['top_n']}件が"
                    f"{r['top_month']}月" for _, r in odd.iterrows())
    sides = "、".join((f"{side[sd]}は{n}年すべて" if e == n else f"{side[sd]}は{n}年中{e}年")
                     for sd, (e, n) in F["per_side"].iterrows())
    out["tm_l_h"] = (f"新商品リリースの月別件数は、{sides}で均等な分布と区別できない"
                     + (f"（{exc}）" if len(odd) else ""))
    t = F["t"]
    out["tm_l_e"] = (
        f"コアパネルの新商品リリースを公開月で数えた（{t['year'].min()}〜{t['year'].max()}年）。各年を"
        "月ごとに均等な分布と比べた（カイ二乗、自由度11、5%）。濃色：均等な分布から外れた年。")
    out["tm_l_side"] = {"skincare": "スキンケア", "makeup": "メイク"}
    out["tm_l_hover"] = "{y}年%{{x}}月：%{{y}}件"
    out["tm_l_end"] = "{y}年：{n}"
    out["tm_l_y"] = "月あたりの新商品リリース"

    out["tm_src_sun"] = source_line(["trends", "meti"], REG, "ja")
    out["tm_src_meti"] = source_line(["meti"], REG, "ja")
    out["tm_src_trends"] = source_line(["trends"], REG, "ja")
    out["tm_src_prtimes"] = source_line(["prtimes"], REG, "ja")
    return out
