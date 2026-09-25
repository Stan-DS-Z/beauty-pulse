"""
Beauty Pulse — Japanese Beauty Market Analytics Dashboard
streamlit_app.py  ·  Streamlit Community Cloud  ·  numbers, copy and theme in bp/
"""

import html as _html
import streamlit as st
import streamlit.components.v1 as _components
from pathlib import Path

from bp import data, figures, strings
from bp.theme import C

st.set_page_config(
    page_title="Beauty Pulse · Japanese Beauty Market",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ASSETS = Path(__file__).parent / "assets"
# Note: assets/ also ships signal_pulse_public.db (the stripped, queryable
# dataset) for anyone exploring the repo — the dashboard itself reads only
# the pre-computed CSV assets below.


# Numbers, copy and theme live in bp/, which imports no UI framework so the
# Dash app can share it. Caching stays here: st.cache_data hands each call a
# copy, so tab code that adds columns to a loaded frame never touches the cache.
HEADLINE = st.cache_data(data.compute_headline)(ASSETS)
LAUNCH = st.cache_data(data.compute_launch_headline)(ASSETS)
_MON_EN = strings._MON_EN


def _from_assets(load):
    """A cached loader bound to this app's assets, called as before: load()."""
    cached = st.cache_data(load)
    return lambda: cached(ASSETS)


load_trends_crossover = _from_assets(data.load_trends_crossover)
load_ingredient_surge = _from_assets(data.load_ingredient_surge)
load_sku_treemap = _from_assets(data.load_sku_treemap)
load_makeup_rebound = _from_assets(data.load_makeup_rebound)
load_blockc = _from_assets(data.load_blockc)
load_umap = _from_assets(data.load_umap)
load_cosine_sizecurve = _from_assets(data.load_cosine_sizecurve)
load_yt_volume = _from_assets(data.load_yt_volume)
load_yt_channels = _from_assets(data.load_yt_channels)
load_meti_annual = _from_assets(data.load_meti_annual)
load_meti_monthly = _from_assets(data.load_meti_monthly)
load_attention_annual = _from_assets(data.load_attention_annual)
load_yt_tfidf = _from_assets(data.load_yt_tfidf)


def panel_header(title, note):
    """Section rule inside a tab — marks which measurement the panel below is."""
    st.markdown(
        f'<div style="border-top:2px solid {C["border"]};margin:34px 0 18px 0;padding-top:14px;">'
        f'<p style="margin:0;font-size:15px;font-weight:700;color:{C["text"]};letter-spacing:.01em;">{title}</p>'
        f'<p style="margin:4px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{note}</p></div>',
        unsafe_allow_html=True)


def kpi_card(label, value, subtitle, arrow="up"):
    """KPI metric card with a CSS tooltip on the truncated subtitle."""
    if arrow == "up":
        sub_color, prefix = "#21a550", "↑ "
    elif arrow == "down":
        sub_color, prefix = "#e05252", "↓ "
    else:
        sub_color, prefix = C["muted"], ""
    tip = _html.escape(subtitle)
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub" style="color:{sub_color}" data-tooltip="{tip}">'
        f'{prefix}{tip}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.markdown(f"""
<style>
.stApp {{ background-color:{C["bg"]}; }}
[data-testid="stToolbar"]    {{ display:none !important; }}
[data-testid="stDecoration"] {{ display:none !important; }}
.kpi-card {{
    background:{C["card"]}; border:1px solid {C["border"]};
    border-radius:10px; padding:14px 18px;
}}
.kpi-label {{ font-size:12px; color:{C["muted"]}; font-weight:500; margin-bottom:6px; }}
.kpi-value {{ font-size:28px; font-weight:700; color:{C["text"]}; line-height:1.1; margin-bottom:6px; }}
.kpi-sub {{
    font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    cursor:help; display:block;
}}
.stTabs [data-baseweb="tab-list"] {{ gap:8px; border-bottom:2px solid {C["border"]}; }}
.stTabs [data-baseweb="tab"] {{
    background:transparent; border-radius:6px 6px 0 0;
    color:{C["muted"]}; font-weight:500; padding:8px 20px;
}}
.stTabs [aria-selected="true"] {{
    background:{C["card"]}; color:{C["text"]};
    border-bottom:2px solid {C["skin"]};
}}
.expl {{ font-size:12px; color:{C["muted"]}; margin-top:2px; margin-bottom:10px; }}
</style>
""", unsafe_allow_html=True)

# st.markdown cannot execute <script> tags (React strips them).
# components.html runs inside an iframe where scripts execute; we reach
# the parent document via window.parent to attach the floating tooltip.
#
# Deprecated in favour of st.iframe, but not migrated: st.iframe rejects
# height=0 (positive int, 'stretch' or 'content' only) and this element is
# a zero-height script host with nothing to show. Streamlit renders that
# error into the page rather than failing the server, so it is caught by
# tests/test_dashboard_runs.py, not by a boot check. Revisit when the
# streamlit pin moves.
_components.html("""
<script>
var doc = window.parent.document;
if (!doc.getElementById('_kpi_tip')) {
    var tip = doc.createElement('div');
    tip.id = '_kpi_tip';
    tip.style.cssText = 'position:fixed;background:#1e1e1e;color:#fff;padding:7px 11px;'
        + 'border-radius:7px;font-size:12px;max-width:280px;line-height:1.5;z-index:99999;'
        + 'box-shadow:0 2px 10px rgba(0,0,0,.2);pointer-events:none;display:none;white-space:normal;';
    doc.body.appendChild(tip);
    doc.addEventListener('mouseover', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (el) { tip.textContent = el.getAttribute('data-tooltip'); tip.style.display = 'block'; }
    });
    doc.addEventListener('mouseout', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (el) tip.style.display = 'none';
    });
    doc.addEventListener('mousemove', function(e) {
        if (tip.style.display === 'block') {
            tip.style.left = Math.min(e.clientX + 14, window.parent.innerWidth - 300) + 'px';
            tip.style.top  = (e.clientY - 42) + 'px';
        }
    });
}
</script>
""", height=0)

_hdr_left, _hdr_right = st.columns([12, 1])
with _hdr_right:
    _lang = st.radio("lang", ["EN", "JA"], horizontal=True,
                     label_visibility="collapsed", key="lang_toggle")
lang = "jp" if _lang == "JA" else "en"
S = strings.build_strings(lang, HEADLINE, LAUNCH, ASSETS)


def _ing_label(canon):
    return strings._ing_label(canon, lang, LAUNCH)


with _hdr_left:
    st.markdown(f"""
<div style="padding:28px 0 8px 0; border-bottom:1px solid {C['border']}; margin-bottom:20px;">
    <div style="display:flex; align-items:baseline; gap:12px;">
        <h1 style="margin:0; font-size:30px; font-weight:800; color:{C['text']};
                   letter-spacing:-1px; font-family:Georgia,serif;">Beauty Pulse</h1>
        <span style="font-size:13px; color:{C['muted']}; font-style:italic;">
            {S["tagline"]}
        </span>
    </div>
    <p style="margin:6px 0 0 0; font-size:13px; color:{C['muted']};">
        {S["subtitle"]}
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([S["tab1"], S["tab2"], S["tab3"]])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1
# ═══════════════════════════════════════════════════════════════════════════
with tab1:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t1_intro"]}</p>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        kpi_card(S["t1_m1"], f"{HEADLINE['cosm_decline']}%", S["t1_m1d"], arrow=None)
    with m2:
        kpi_card(S["t1_m2"], f"{HEADLINE['nia_pre']} → {HEADLINE['nia_post']}", S["t1_m2d"])
    with m3:
        _sub3 = (f"95% CI {HEADLINE['sku_lo']}–{HEADLINE['sku_hi']} · "
                 f"{HEADLINE['sku_span_lo']}–{HEADLINE['sku_span_hi']} across genre treatments"
                 if lang == "en" else
                 f"95%CI {HEADLINE['sku_lo']}〜{HEADLINE['sku_hi']} · "
                 f"ジャンル処理により{HEADLINE['sku_span_lo']}〜{HEADLINE['sku_span_hi']}倍")
        kpi_card(S["t1_m3"], f"{HEADLINE['sku_measured']}x", _sub3)
    with m4:
        kpi_card(S["t1_m4"], f"{HEADLINE['found_d']}%", S["t1_m4d"], arrow=None)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    panel_header(S["t1_p1"], S["t1_p1d"])

    # Chart 1 — Trends crossover
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c1h"]}</h3><p class="expl">{S["t1_c1e"]}</p>', unsafe_allow_html=True)

    df_cross = load_trends_crossover()
    min_date, max_date = figures.crossover_bounds(df_cross)
    date_range = st.slider("dr", min_value=min_date, max_value=max_date,
                           value=(min_date, max_date), format="YYYY-MM",
                           label_visibility="collapsed", key="crossover_slider")
    st.plotly_chart(figures.fig_trends_crossover(df_cross, date_range, lang), width="stretch")

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Chart 1b — The mask test: makeup-term rebound vs own 2019 baseline
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c4h"]}</h3><p class="expl">{S["t1_c4e"]}</p>', unsafe_allow_html=True)

    st.plotly_chart(figures.fig_makeup_rebound(load_makeup_rebound(), lang), width="stretch")
    st.caption(S["t1_c4cap"])
    st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["cosm"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f1b_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f1b_body"]}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    # Chart 2 — Ingredient surge
    with col_left:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c2h"]}</h3><p class="expl">{S["t1_c2e"]}</p>', unsafe_allow_html=True)
        df_ing = load_ingredient_surge()
        selected = st.multiselect(S["t1_ingr_sel"], options=figures.ingredient_options(df_ing),
                                   default=figures.ingredient_default(),
                                   key="ingr_select")
        st.plotly_chart(figures.fig_ingredient_surge(df_ing, selected), width="stretch")
        st.caption(S["t1_c2cap"])

    # Chart 3 — Rakuten treemap
    with col_right:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c3h"]}</h3><p class="expl">{S["t1_c3e"]}</p>', unsafe_allow_html=True)
        df_sku = load_sku_treemap()
        _lens = figures.lens_options(S)
        color_col = st.radio(S["t1_lens"], options=list(_lens), format_func=_lens.get,
                             horizontal=True, key="treemap_lens")
        rak_sel = st.plotly_chart(
            figures.fig_sku_treemap(df_sku, color_col), width="stretch",
            on_select="rerun", key="rak_treemap",
        )

        # Detail panel on click
        detail_placeholder = st.empty()
        if rak_sel and rak_sel.selection and rak_sel.selection.get("points"):
            pt  = rak_sel.selection["points"][0]
            lbl = pt.get("label", "")
            row = figures.sku_detail(df_sku, lbl)
            if row is not None:
                tc  = C["skin"] if row["tier_group"] == "skincare" else C["cosm"]
                with detail_placeholder.container():
                    detail_col, btn_col = st.columns([10, 1])
                    with detail_col:
                        st.markdown(f"""
                        <div style="background:{C['card']};border:1px solid {C['border']};
                                    border-left:4px solid {tc};border-radius:0 8px 8px 0;
                                    padding:12px 20px;display:flex;gap:32px;align-items:center;">
                            <div style="min-width:110px;">
                                <p style="margin:0;font-size:12px;font-weight:700;
                                          color:{C['text']};white-space:nowrap;">{lbl}</p>
                                <p style="margin:2px 0 0;font-size:11px;
                                          color:{C['muted']};">{row['tier_group'].capitalize()}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};">SKUs</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{int(row['sku_count']):,}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};white-space:nowrap;">Avg reviews / SKU</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{row['avg_reviews']:.1f}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};">Median price</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">¥{int(row['med_price']):,}</p>
                            </div>
                            <div>
                                <p style="margin:0;font-size:10px;color:{C['muted']};white-space:nowrap;">Avg rating (rated SKUs)</p>
                                <p style="margin:0;font-size:13px;font-weight:600;
                                          color:{tc};white-space:nowrap;">{row['avg_rating']:.2f} ★ · {row['rated_share']:.0%} rated</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with btn_col:
                        if st.button("✕", key="rak_clear"):
                            st.rerun()
        else:
            detail_placeholder.caption("Click any tile to see category detail" if lang == "en" else "タイルをクリックするとカテゴリの詳細を表示")

        # Korean-cosmetics callout — computed from the same CSV as the treemap
        # (a previous hardcoded version drifted out of sync with the data)
        _kr = figures.korean_callout(df_sku)
        if _kr is not None:
            _all_rps = _kr["all_rps"]
            if lang == "en":
                _kr_txt = (f"  — {int(_kr['sku_count']):,} SKUs · "
                           f"{_kr['avg_reviews']:.1f} reviews per SKU, against {_all_rps:.1f} "
                           f"across all categories · ¥{int(_kr['med_price']):,} median price")
            else:
                _kr_txt = (f"  — {int(_kr['sku_count']):,} SKU · "
                           f"SKUあたりレビュー{_kr['avg_reviews']:.1f}件（全カテゴリ平均{_all_rps:.1f}件） · "
                           f"価格中央値 ¥{int(_kr['med_price']):,}")
            st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:3px solid {C["korean"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:8px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{"Korean cosmetics" if lang == "en" else "韓国コスメ"}</span><span style="font-size:12px;color:{C["muted"]};">{_kr_txt}</span></div>', unsafe_allow_html=True)


    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # Chart 4 — YouTube comment volume
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c5h"]}</h3><p class="expl">{S["t1_c5e"]}</p>', unsafe_allow_html=True)

    try:
        df_yt_vol = load_yt_volume()
        st.plotly_chart(figures.fig_yt_volume(df_yt_vol), width="stretch")
        st.caption(S["t1_c5cap"].format(**figures.yt_volume_counts(df_yt_vol)))
    except FileNotFoundError:
        st.info("nb07_yt_volume.csv not found — run the NB07 YouTube export cells to generate it.", icon="ℹ️")


    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1 · MARKET PANEL — METI shipments and 財務省 trade
    # Money, not attention. Kept behind its own rule and labelled as a
    # different measurement, because the reader comparing the two panels is
    # the whole point of the layout.
    # ═══════════════════════════════════════════════════════════════════════
    panel_header(S["t1_p2"], S["t1_p2d"])

    # Chart M1 — shipped value by group, with the break marked
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_mkh"]}</h3><p class="expl">{S["t1_mke"]}</p>', unsafe_allow_html=True)

    df_grp, px_kg_m = load_meti_monthly()
    st.plotly_chart(figures.fig_meti_groups(df_grp, HEADLINE, lang), width="stretch")
    st.caption(S["t1_mkcap"])

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    # Chart M2 — the break itself: yen per kg, broken lines against controls
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_brkh"]}</h3>', unsafe_allow_html=True)

    st.plotly_chart(figures.fig_meti_price_per_kg(px_kg_m, HEADLINE, lang), width="stretch")
    st.caption(f"Monthly, January 2019 – {_MON_EN[HEADLINE['ytd_m']]} {HEADLINE['ytd_y']} · solid = the three lines with the step · dotted = comparison lines · log scale: equal vertical distance = equal percentage change"
               if lang == "en" else
               f"月次、2019年1月〜{HEADLINE['ytd_y']}年{HEADLINE['ytd_m']}月 · 実線＝段差のある3品目 · 点線＝比較品目 · 対数軸：縦方向の同じ距離＝同じ変化率")

    st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["cosm"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:12px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["t1_brkh"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["t1_brkb"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="border-top:1px solid {C["border"]};margin-top:10px;padding-top:8px;"><p style="margin:0;font-size:11px;color:{C["muted"]};font-weight:600;">{S["t1_brkfnh"]}</p><p style="margin:4px 0 0 0;font-size:11px;color:{C["muted"]};line-height:1.6;">{S["t1_brkfn"]}</p></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1 · SYNTHESIS — the two measurements side by side
    # ═══════════════════════════════════════════════════════════════════════
    panel_header(S["t1_p3"], S["t1_p3d"])

    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_dvh"]}</h3><p class="expl">{S["t1_dve"]}</p>', unsafe_allow_html=True)

    val_all, _ = load_meti_annual()
    att = load_attention_annual()
    dv_cols = st.columns(2)
    for period, col in zip(("pre", "post"), dv_cols):
        with col:
            st.plotly_chart(figures.fig_search_vs_value(val_all, att, HEADLINE, period, lang, S),
                            width="stretch")

    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f1_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f1_body"]}</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — THE LANGUAGE
# ═══════════════════════════════════════════════════════════════════════════
with tab2:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t2_intro"]}</p>', unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────────────────────────────
    t1, t2, t3 = st.columns(3)
    with t1:
        kpi_card(S["t2_m1"], f"+{HEADLINE['conv_delta']}", S["t2_m1d"])
    with t2:
        kpi_card(S["t2_m2"], f"{HEADLINE['conv_lo']} → {HEADLINE['conv_hi']}", S["t2_m2d"])
    with t3:
        kpi_card(S["t2_m3"], f"{HEADLINE['size_lo_cos']} → {HEADLINE['size_hi_cos']}", S["t2_m3d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Row 1: Word clouds + Cosine similarity heatmap ────────────────────
    col_wc, col_cos = st.columns([1, 1])

    with col_wc:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_wch"]}</h3><p class="expl">{S["t2_wce"]}</p>', unsafe_allow_html=True)

        year = st.pills(
            "Year",
            options=[2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
            default=2025,
            key="wc_year_slider",
        )
        if year is None:
            year = 2025

        wc_path = ASSETS / f"wordcloud_{year}.png"
        if wc_path.exists():
            from PIL import Image as PILImage
            img = PILImage.open(wc_path)
            st.image(img, width="stretch")
        else:
            st.caption(f"wordcloud_{year}.png not found")

        if year <= 2021:
            note_text = S["t2_wc_early"]
            note_color = C["cosm_lt"]
            note_border = C["cosm"]
        elif year == 2022:
            note_text = S["t2_wc_2022"]
            note_color = C["grid"]
            note_border = C["muted"]
        elif year == 2023:
            note_text = S["t2_wc_2023"]
            note_color = C["grid"]
            note_border = C["gold"]
        else:
            note_text = S["t2_wc_late"]
            note_color = C["skin_lt"]
            note_border = C["skin"]

        st.markdown(f'<div style="background:{note_color};border-left:3px solid {note_border};border-radius:0 6px 6px 0;padding:8px 12px;margin-top:8px;"><span style="font-size:12px;color:{C["text"]};">{note_text}</span></div>', unsafe_allow_html=True)

    with col_cos:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t2_curveh"]}</h3><p class="expl">{S["t2_curvee"]}</p>', unsafe_allow_html=True)

        df_curve = load_cosine_sizecurve()
        st.plotly_chart(figures.fig_cosine_sizecurve(df_curve, HEADLINE), width="stretch")

        st.markdown(f'<div style="background:{C["skin_lt"]};border-left:3px solid {C["skin"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">+{HEADLINE["conv_delta"]}</span><span style="font-size:12px;color:{C["muted"]};">  — {S["t2_curvenote"]}</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Finding 2 callout ─────────────────────────────────────────────────
    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f2_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f2_body"]}</p></div>', unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════
with tab3:

    st.markdown(f'<p style="color:{C["muted"]};font-size:14px;margin-bottom:20px;">{S["t3_intro"]}</p>', unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────────────────────────────
    d1, d2, d3 = st.columns(3)
    with d1:
        kpi_card(S["t3_m1"], "アヌア", S["t3_m1d"])
    with d2:
        kpi_card(S["t3_m2"], "レチノール", S["t3_m2d"])
    with d3:
        kpi_card(S["t3_m3"], f"{len(load_umap()):,} reviews", S["t3_m3d"])

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Launch panel — PR TIMES ───────────────────────────────────────────
    # Launch data sits first: brands announce before consumers search.
    _h3 = (f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">'
           '{h}</h3><p class="expl">{e}</p>')
    panel_header(S["t3_lp"], S["t3_lpd"])
    if LAUNCH is None:
        st.markdown(f'<p class="expl">{S["t3_lempty"]}</p>', unsafe_allow_html=True)
    else:
        st.markdown(_h3.format(h=S["t3_l1h"], e=S["t3_l1e"]), unsafe_allow_html=True)
        lc1, lc2 = st.columns([3, 2])

        # Figure 1 — 12-month rolling totals by category group, core panel
        with lc1:
            st.plotly_chart(figures.fig_launch_groups(LAUNCH, S), width="stretch")

        # Per category: latest 12 months against the 12 months before
        with lc2:
            st.markdown(_h3.format(h=S["t3_l2h"], e=S["t3_l2e"]), unsafe_allow_html=True)
            st.plotly_chart(figures.fig_launch_categories(LAUNCH, lang, S), width="stretch")

        # Full roster, latest 12 months — present-forward feeds stacked on the core
        st.markdown(_h3.format(h=S["t3_l3h"], e=S["t3_l3e"]), unsafe_allow_html=True)
        st.plotly_chart(figures.fig_launch_roster(LAUNCH, S), width="stretch")

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        lc3, lc4 = st.columns(2)

        # Figure 2 — ingredient share, latest 12 months against the 12 before
        with lc3:
            st.markdown(_h3.format(h=S["t3_l4h"], e=S["t3_l4e"]), unsafe_allow_html=True)
            st.plotly_chart(figures.fig_launch_ingredients(LAUNCH, lang, S), width="stretch")

        # One ingredient: launch share over search interest, one axis each
        with lc4:
            st.markdown(_h3.format(h=S["t3_l5h"], e=S["t3_l5e"]), unsafe_allow_html=True)
            _canon = st.selectbox(S["t3_l5ax1"], figures.launch_ingredient_options(LAUNCH),
                                  index=0, key="launch_ing", label_visibility="collapsed",
                                  format_func=_ing_label)
            st.plotly_chart(
                figures.fig_launch_vs_search(LAUNCH, load_ingredient_surge(), _canon, S),
                width="stretch")

        st.caption(S["t3_lcap"])

    panel_header(S["t3_p2"], S["t3_p2d"])

    # ── Block C treemap ───────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_bch"]}</h3><p class="expl">{S["t3_bce"]}</p>', unsafe_allow_html=True)

    df_bc = load_blockc()

    _win = figures.blockc_window_options(S)
    window_key = st.pills(
        "Window",
        options=list(_win),
        default="recent",
        format_func=_win.get,
        key="blockc_window",
    )
    if window_key is None:
        window_key = "recent"

    SIG_DISPLAY = figures.blockc_signal_labels(S)
    SIG_COLORS = figures.SIG_COLORS

    bc_selection = st.plotly_chart(
        figures.fig_blockc(df_bc, window_key, S),
        width="stretch",
        on_select="rerun",
        key="bc_treemap",
    )

    # Detail panel — auto-populates on click
    if (bc_selection and
        hasattr(bc_selection, "selection") and
        bc_selection.selection and
        bc_selection.selection.get("points")):

        pt = bc_selection.selection["points"][0]
        clicked_label = pt.get("label", "")
        row = figures.blockc_detail(df_bc, window_key, clicked_label)

        if row is not None:
            border_color = SIG_COLORS.get(row["signal_type"], C["ingr"])
            sig_label = SIG_DISPLAY.get(row["signal_type"], "Other")
            seed_word = "seed" if row["seed_count"] == 1 else "seeds"
            seeds_str = row.get("seeds", "—")

            st.markdown(f"""
            <div style="background:{C["card"]};
                        border:1px solid {C["border"]};
                        border-left:4px solid {border_color};
                        border-radius:0 8px 8px 0;
                        padding:16px 20px;margin-top:12px;">
                <div style="display:flex;align-items:baseline;gap:12px;">
                    <span style="font-size:18px;font-weight:700;color:{C["text"]};">
                        {row["root"]}
                    </span>
                    <span style="font-size:12px;color:{border_color};font-weight:600;">
                        {sig_label}
                    </span>
                </div>
                <div style="margin-top:8px;display:flex;gap:24px;">
                    <div>
                        <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                    letter-spacing:1px;">Signal strength</div>
                        <div style="font-size:13px;font-weight:700;color:{C["text"]};">
                            {row["metric"]:.3f}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                    letter-spacing:1px;">Seed queries</div>
                        <div style="font-size:13px;font-weight:700;color:{C["text"]};">
                            {row["seed_count"]} {seed_word}
                        </div>
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <div style="font-size:10px;color:{C["muted"]};text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:4px;">Appears in searches for</div>
                    <div style="font-size:13px;color:{C["text"]};">
                        {seeds_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{C["grid"]};border-radius:8px;
                    padding:12px 20px;margin-top:12px;text-align:center;">
            <span style="font-size:12px;color:{C["muted"]};font-style:italic;">
                Click any tile to see detail
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Legend
    leg1, leg2, leg3, _ = st.columns([1, 1, 1, 3])
    with leg1:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["korean"]};"></div><span style="font-size:12px;color:{C["text"]};">Korean brands</span></div>', unsafe_allow_html=True)
    with leg2:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["skin"]};"></div><span style="font-size:12px;color:{C["text"]};">Ingredients</span></div>', unsafe_allow_html=True)
    with leg3:
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;border-radius:2px;background:{C["ingr"]};"></div><span style="font-size:12px;color:{C["text"]};">Other</span></div>', unsafe_allow_html=True)

    if window_key == "recent":
        st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["korean"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:12px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f4r_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f4r_body"]}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:12px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f4c_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f4c_body"]}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── YouTube content supply ─────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_ytch"]}</h3><p class="expl">{S["t3_ytche"]}</p>', unsafe_allow_html=True)

    try:
        df_ch = load_yt_channels()
        st.plotly_chart(figures.fig_yt_channels(df_ch), width="stretch")

        yt_leg1, yt_leg2, yt_leg3, _ = st.columns([1, 1, 1, 3])
        for col, (lbl, clr) in zip([yt_leg1, yt_leg2, yt_leg3],
                                    [(S["t3_umap_sk"], C["skin"]),
                                     (S["t3_umap_co"], C["cosm"]),
                                     ("Korean", C["korean"])]):
            with col:
                st.markdown(f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:2px;background:{clr};"></div><span style="font-size:12px;color:{C["text"]};">{lbl}</span></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:3px solid {C["korean"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:10px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{S["t3_ytgap"]}</span><span style="font-size:12px;color:{C["muted"]};">{S["t3_ytgapb"]}</span></div>', unsafe_allow_html=True)

    except FileNotFoundError:
        st.info("nb07_yt_channels.csv not found — run the NB07 YouTube export cells to generate it.", icon="ℹ️")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── YouTube TF-IDF — what are they actually saying? ───────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_yttfh"]}</h3><p class="expl">{S["t3_yttfe"]}</p>', unsafe_allow_html=True)

    try:
        df_yt_tfidf = load_yt_tfidf()
        st.plotly_chart(figures.fig_yt_tfidf(df_yt_tfidf, S), width="stretch")

        st.markdown(f'<div style="background:{C["grid"]};border-left:3px solid {C["muted"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{S["t3_ytreg"]}</span><span style="font-size:12px;color:{C["muted"]};">{S["t3_ytregb"]}</span></div>', unsafe_allow_html=True)

    except FileNotFoundError:
        st.info("nb07_yt_tfidf.csv not found — run NB06 Section 6 to generate it.", icon="ℹ️")

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── UMAP scatter ──────────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_umaph"]}</h3><p class="expl">{S["t3_umape"]}</p>', unsafe_allow_html=True)

    df_umap = load_umap()

    umap_col1, umap_col2 = st.columns([3, 1])

    with umap_col2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Year filter — reverse chronological
        year_filter = st.pills(
            S["t3_umap_yr"],
            options=figures.umap_year_options(),
            default="all",
            format_func=lambda v: figures.umap_year_label(v, lang),
            key="umap_year",
        )
        if year_filter is None:
            year_filter = "all"

        st.markdown(f"""
        <div style="margin-top:16px;">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                <div style="width:10px;height:10px;border-radius:50%;
                            background:{C['skin']};opacity:0.8;"></div>
                <span style="font-size:12px;color:{C['text']};">{S["t3_umap_sk"]}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:16px;">
                <div style="width:10px;height:10px;border-radius:50%;
                            background:{C['cosm']};opacity:0.8;"></div>
                <span style="font-size:12px;color:{C['text']};">{S["t3_umap_co"]}</span>
            </div>
            <p style="font-size:11px;color:{C['muted']};line-height:1.6;margin:0;">
                {S["t3_umap_note"].replace(chr(10), "<br><br>")}
            </p>
        </div>
        """, unsafe_allow_html=True)

        n_shown = figures.umap_count(df_umap, year_filter)
        st.caption(f"{n_shown:,} reviews")

    with umap_col1:
        st.plotly_chart(figures.fig_umap(df_umap, year_filter, S), width="stretch")

    # Finding callout
    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f3_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f3_body"]}</p></div>', unsafe_allow_html=True)
