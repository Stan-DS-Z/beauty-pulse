"""
Beauty Pulse — Japanese Beauty Market Analytics Dashboard
streamlit_app.py  ·  Streamlit Community Cloud  ·  numbers, copy and theme in bp/
"""

import html as _html
import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path

from bp import data, strings
from bp.theme import C, _base, _xax, _yax

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
LAUNCH_GROUPS = data.LAUNCH_GROUPS
LAUNCH_CAT = strings.LAUNCH_CAT
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
_li = strings._li(lang)


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
    min_date = df_cross["week_start"].min().to_pydatetime()
    max_date = df_cross["week_start"].max().to_pydatetime()
    date_range = st.slider("dr", min_value=min_date, max_value=max_date,
                           value=(min_date, max_date), format="YYYY-MM",
                           label_visibility="collapsed", key="crossover_slider")

    # Always plot full dataset — slider controls xaxis.range (zoom not filter)
    fig1 = go.Figure()
    fig1.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                   opacity=0.6, layer="below", line_width=0,
                   annotation_text="COVID", annotation_position="top left",
                   annotation_font=dict(size=10, color=C["muted"]))
    for term, color, label in [("スキンケア", C["skin"], "スキンケア (skincare)"),
                                 ("化粧品", C["cosm"], "化粧品 (cosmetics)")]:
        d = df_cross[df_cross["term"] == term]
        fig1.add_trace(go.Scatter(x=d["week_start"], y=d["interest"],
                                   name=label, mode="lines",
                                   line=dict(color=color, width=2.5),
                                   hovertemplate="%{y:.0f}<extra></extra>"))
    fig1.add_annotation(x="2024-01-01", y=70,
                        text="no crossover" if lang == "en" else "逆転なし",
                        showarrow=False,
                        font=dict(size=10, color=C["muted"]), bgcolor=C["card"],
                        bordercolor=C["border"], borderwidth=1, borderpad=4)
    fig1.update_layout(**_base(height=360))
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                       legend=dict(orientation="h", yanchor="top", y=-0.12,
                                   xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                       xaxis=_xax(range=[date_range[0], date_range[1]]),
                       yaxis=_yax(title="Search interest (0–100)"))
    st.plotly_chart(fig1, width="stretch")

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Chart 1b — The mask test: makeup-term rebound vs own 2019 baseline
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c4h"]}</h3><p class="expl">{S["t1_c4e"]}</p>', unsafe_allow_html=True)

    df_mk = load_makeup_rebound()
    # Index each term to its own 2019 mean = 100 — per-term own-baseline reads
    # are the only valid use of unanchored block_A data (no cross-term levels).
    base_2019 = df_mk[df_mk["year"] == 2019].groupby("term")["interest"].mean()
    df_mk = df_mk[df_mk["term"].isin(base_2019.index)].copy()
    df_mk["indexed"] = 100 * df_mk["interest"] / df_mk["term"].map(base_2019)
    # 3-month centred rolling mean per term for readability (monthly is noisy)
    df_mk["smooth"] = (df_mk.sort_values("week_start")
                       .groupby("term")["indexed"]
                       .transform(lambda s: s.rolling(3, center=True, min_periods=1).mean()))

    MAKEUP_META = {
        "口紅":           (C["cosm"],  "口紅 (lipstick)"),
        "ファンデーション": (C["gold"],  "ファンデーション (foundation)"),
        "アイシャドウ":     ("#7B5EA7", "アイシャドウ (eyeshadow)"),
    }
    fig1b = go.Figure()
    fig1b.add_vrect(x0="2020-01-01", x1="2021-06-01", fillcolor=C["grid"],
                    opacity=0.6, layer="below", line_width=0,
                    annotation_text="COVID", annotation_position="top left",
                    annotation_font=dict(size=10, color=C["muted"]))
    fig1b.add_vline(x="2023-03-13", line_dash="dash", line_color=C["muted"],
                    line_width=1.5)
    fig1b.add_annotation(x="2023-03-13", y=0.96, yref="paper",
                         text="マスク緩和<br>masks relaxed" if lang == "en" else "マスク着用ルール緩和",
                         showarrow=False, xanchor="left", xshift=4,
                         font=dict(size=9, color=C["muted"]))
    fig1b.add_hline(y=100, line_dash="dot", line_color=C["border"], line_width=1.5,
                    annotation_text="2019 baseline = 100",
                    annotation_position="bottom right",
                    annotation_font=dict(size=9, color=C["muted"]))
    for term, (color, label) in MAKEUP_META.items():
        d = df_mk[df_mk["term"] == term].sort_values("week_start")
        fig1b.add_trace(go.Scatter(
            x=d["week_start"], y=d["smooth"], name=label, mode="lines",
            line=dict(color=color, width=2.5),
            hovertemplate="%{y:.0f}<extra>" + label + "</extra>"))
    fig1b.update_layout(**_base(height=380))
    fig1b.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.12,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(),
                        yaxis=_yax(title="Search interest, own 2019 = 100"))
    st.plotly_chart(fig1b, width="stretch")
    st.caption(S["t1_c4cap"])
    st.markdown(f'<div style="background:{C["cosm_lt"]};border-left:4px solid {C["cosm"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f1b_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f1b_body"]}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    # Chart 2 — Ingredient surge
    with col_left:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c2h"]}</h3><p class="expl">{S["t1_c2e"]}</p>', unsafe_allow_html=True)
        df_ing = load_ingredient_surge()
        df_ing_yr = (df_ing[df_ing["year"] <= 2026]
                     .groupby(["year", "term"])["interest"].mean().reset_index())
        ESTABLISHED = ["ヒアルロン酸", "セラミド"]  # レチナール excluded: +11.4% post-COVID, not pre-established
        INGR_COLORS = {
            "ナイアシンアミド": "#2E7D32", "レチノール": "#1565C0",
            "グルタチオン": "#6A1B9A", "ビタミンC 美容": "#E65100",
            "トラネキサム酸": "#00695C", "アゼライン酸": "#AD1457",
            "エクソソーム": "#4E342E", "ヒアルロン酸": C["skin"],
            "セラミド": C["muted"], "レチナール": "#78909C",
        }
        all_terms = sorted(df_ing_yr["term"].unique().tolist())
        selected = st.multiselect(S["t1_ingr_sel"], options=all_terms,
                                   default=["ナイアシンアミド", "レチノール", "ヒアルロン酸", "アゼライン酸"],
                                   key="ingr_select")
        fig2 = go.Figure()
        fig2.add_vrect(x0=2019.8, x1=2021.2, fillcolor=C["grid"],
                       opacity=0.6, layer="below", line_width=0)
        for term in selected:
            d = df_ing_yr[df_ing_yr["term"] == term]
            fig2.add_trace(go.Scatter(
                x=d["year"], y=d["interest"].round(1), name=term,
                mode="lines+markers",
                line=dict(color=INGR_COLORS.get(term, C["muted"]), width=2,
                          dash="dot" if term in ESTABLISHED else "solid"),
                marker=dict(size=6),
                hovertemplate="%{y:.1f}<extra></extra>"))
        fig2.update_layout(**_base(height=380))
        fig2.update_layout(margin=dict(l=20, r=20, t=20, b=90),
                           legend=dict(orientation="h", yanchor="top", y=-0.2,
                                       xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                       font=dict(size=10)),
                           xaxis=_xax(dtick=1, range=[2018.8, 2026.2]),
                           yaxis=_yax(title="Avg search interest (0–100)"))
        st.plotly_chart(fig2, width="stretch")
        st.caption(S["t1_c2cap"])

    # Chart 3 — Rakuten treemap
    with col_right:
        st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_c3h"]}</h3><p class="expl">{S["t1_c3e"]}</p>', unsafe_allow_html=True)
        df_sku = load_sku_treemap()
        CAT_LABELS = {
            "korean_cosmetics": "Korean cosmetics", "cosmetics": "Cosmetics",
            "sun_protection": "Sun protection", "face_cream": "Face cream",
            "all_in_one": "All-in-one", "face_wash": "Face wash",
            "emulsion": "Emulsion", "serum_essence": "Serum / essence",
            "toner_lotion": "Toner / lotion", "skincare": "Skincare (general)",
        }
        df_sku["cat_display"] = df_sku["category"].map(lambda x: CAT_LABELS.get(x, x))
        df_sku["tier_display"] = df_sku["tier_group"].str.capitalize()

        LENS_OPTIONS = S["t1_lens_opts"]
        COLOR_SCALES = {"sku_count": "RdPu", "avg_reviews": "Blues",
                        "med_price": "Oranges", "avg_rating": "Greens"}
        HOVER_LABELS = {"sku_count": "SKUs", "avg_reviews": "Avg reviews/SKU",
                        "med_price": "Median price (¥)", "avg_rating": "Avg rating (rated SKUs)"}

        lens_label = st.radio(S["t1_lens"], options=list(LENS_OPTIONS.keys()),
                               horizontal=True, key="treemap_lens")
        color_col = LENS_OPTIONS[lens_label]
        hover_lbl = HOVER_LABELS[color_col]

        # Build customdata array: [avg_reviews, med_price, avg_rating, tier, rated_share]
        df_sku["_cval"] = df_sku[color_col]
        CELL_LABELS = {
            "sku_count": "SKUs", "avg_reviews": "rev/SKU avg",
            "med_price": "median price", "avg_rating": "avg rating",
        }
        CELL_FMT = {
            "sku_count": lambda v: f"{v:,.0f}",
            "avg_reviews": lambda v: f"{v:.1f}",
            "med_price": lambda v: f"¥{v:,.0f}",
            "avg_rating": lambda v: f"{v:.2f} ★",
        }

        # px.treemap single level — flat, butter zoom preserved
        df_sku["_color"] = df_sku[color_col]
        treemap_path = ["cat_display"]
        fig3 = px.treemap(
            df_sku,
            path=treemap_path,
            values="sku_count",
            color=color_col,
            color_continuous_scale=COLOR_SCALES[color_col],
            custom_data=["avg_reviews", "med_price", "avg_rating", "tier_group", "rated_share"],
        )
        fig3.update_traces(
            texttemplate="<b>%{label}</b><br>%{value:,} SKUs",
            textfont=dict(size=10),
            marker_line=dict(width=2, color=C["bg"]),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "SKUs: %{value:,}<br>"
                "Avg reviews/SKU: %{customdata[0]:.1f}<br>"
                "Median price: ¥%{customdata[1]:,.0f}<br>"
                "Avg rating: %{customdata[2]:.2f} / 5.0 "
                "(across the %{customdata[4]:.0%} of SKUs with ratings)"
                "<extra>%{customdata[3]}</extra>"
            ),
        )
        fig3.update_layout(**_base(height=420))
        fig3.update_layout(
            margin=dict(l=0, r=55, t=10, b=0),
            coloraxis_colorbar=dict(
                thickness=10, len=0.5,
                title=dict(text=hover_lbl, font=dict(size=9), side="right"),
                tickfont=dict(size=9),
            ),
        )
        rak_sel = st.plotly_chart(
            fig3, width="stretch",
            on_select="rerun", key="rak_treemap",
        )

        # Detail panel on click
        detail_placeholder = st.empty()
        if rak_sel and rak_sel.selection and rak_sel.selection.get("points"):
            pt  = rak_sel.selection["points"][0]
            lbl = pt.get("label", "")
            match = df_sku[df_sku["cat_display"] == lbl]
            if not match.empty:
                row = match.iloc[0]
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
        _kr = df_sku[df_sku["category"] == "korean_cosmetics"]
        if not _kr.empty:
            _kr = _kr.iloc[0]
            _all_rps = (df_sku["sku_count"] * df_sku["avg_reviews"]).sum() / df_sku["sku_count"].sum()
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
        df_yt_sk  = df_yt_vol[df_yt_vol["tier_group"] == "skincare"]
        df_yt_co  = df_yt_vol[df_yt_vol["tier_group"] == "cosmetics"]

        fig5 = go.Figure()
        fig5.add_vrect(x0=2019.6, x1=2021.4, fillcolor=C["grid"],
                       opacity=0.6, layer="below", line_width=0,
                       annotation_text="COVID", annotation_position="top left",
                       annotation_font=dict(size=10, color=C["muted"]))
        fig5.add_trace(go.Bar(
            x=df_yt_sk["comment_year"], y=df_yt_sk["n_comments"],
            name="Skincare", marker_color=C["skin"],
            hovertemplate="Skincare: %{y:,} comments<extra></extra>",
        ))
        fig5.add_trace(go.Bar(
            x=df_yt_co["comment_year"], y=df_yt_co["n_comments"],
            name="Cosmetics", marker_color=C["cosm"],
            hovertemplate="Cosmetics: %{y:,} comments<extra></extra>",
        ))
        fig5.update_layout(**_base(height=280))
        fig5.update_layout(
            barmode="group",
            margin=dict(l=20, r=20, t=20, b=60),
            legend=dict(orientation="h", yanchor="top", y=-0.24,
                        xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
            xaxis=_xax(dtick=1, tickformat="d"),
            yaxis=_yax(title="Comment count"),
        )
        st.plotly_chart(fig5, width="stretch")
        _yc = lambda d, y: int(d.loc[d["comment_year"] == y, "n_comments"].sum())
        st.caption(S["t1_c5cap"].format(c22=_yc(df_yt_co, 2022), s22=_yc(df_yt_sk, 2022),
                                        s24=_yc(df_yt_sk, 2024), c24=_yc(df_yt_co, 2024)))
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
    _brk = HEADLINE["mkt_break"]
    # The rule sits between December and January so each month's point falls
    # on its own side of it.
    _brk_x = pd.Timestamp(_brk, 1, 1) - pd.Timedelta(days=15)
    _mon_hover = "%{x|%b %Y}: %{y:,.0f} 億円<extra></extra>" if lang == "en" else "%{x|%Y年%-m月}：%{y:,.0f}億円<extra></extra>"
    figM1 = go.Figure()
    figM1.add_vrect(x0=_brk_x, x1=df_grp.index.max() + pd.Timedelta(days=15),
                    fillcolor=C["grid"], opacity=0.55, layer="below", line_width=0)
    figM1.add_shape(type="line", x0=_brk_x, x1=_brk_x, y0=0, y1=1, yref="paper",
                    line=dict(dash="dash", color=C["muted"], width=1.5))
    figM1.add_annotation(x=_brk_x, y=0.97, yref="paper", xanchor="left", xshift=5,
                         text=("series break<br>Jan 2022" if lang == "en" else "断層<br>2022年1月"),
                         showarrow=False, font=dict(size=9, color=C["muted"]))
    for col, color, lab_en, lab_ja in [
            ("skincare", C["skin"], "皮膚用 (skincare)", "皮膚用化粧品"),
            ("makeup",   C["cosm"], "仕上用 (makeup)",   "仕上用化粧品")]:
        figM1.add_trace(go.Scatter(
            x=df_grp.index, y=df_grp[col], mode="lines",
            name=lab_en if lang == "en" else lab_ja,
            line=dict(color=color, width=2),
            hovertemplate=_mon_hover))
    figM1.update_layout(**_base(height=340))
    figM1.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.14,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(dtick="M12", tickformat="%Y"),
                        yaxis=_yax(title="Shipped value per month (億円)" if lang == "en" else "月間出荷金額（億円）"))
    st.plotly_chart(figM1, width="stretch")
    st.caption(S["t1_mkcap"])

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    # Chart M2 — the break itself: yen per kg, broken lines against controls
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t1_brkh"]}</h3>', unsafe_allow_html=True)

    px_kg = px_kg_m
    BROKEN = [("化粧水", C["skin"], "toner"), ("美容液", "#2E6E8E", "serum"),
              ("乳液", "#7FB2CE", "emulsion")]
    CONTROL = [("モイスチャークリーム", C["muted"], "moisture cream"),
               ("ファンデーション", C["gold"], "foundation")]
    figM2 = go.Figure()
    for item, color, gloss in BROKEN + CONTROL:
        if item not in px_kg.columns:
            continue
        row = px_kg[item].dropna()
        dashed = item not in [b[0] for b in BROKEN]
        figM2.add_trace(go.Scatter(
            x=row.index, y=row.values, mode="lines",
            name=f"{item} ({gloss})" if lang == "en" else item,
            line=dict(color=color, width=2 if dashed else 2.5,
                      dash="dot" if dashed else "solid"),
            hovertemplate=("%{x|%b %Y}: ¥%{y:,.0f}/kg<extra></extra>" if lang == "en"
                           else "%{x|%Y年%-m月}：¥%{y:,.0f}/kg<extra></extra>")))
    figM2.add_shape(type="line", x0=_brk_x, x1=_brk_x, y0=0, y1=1, yref="paper",
                    line=dict(dash="dash", color=C["cosm"], width=1.5))
    figM2.add_annotation(x=_brk_x, y=0.97, yref="paper", xanchor="left", xshift=5,
                         text=("Jan 2022" if lang == "en" else "2022年1月"),
                         showarrow=False, font=dict(size=9, color=C["cosm"]))
    figM2.update_layout(**_base(height=360))
    figM2.update_layout(margin=dict(l=20, r=20, t=20, b=40),
                        legend=dict(orientation="h", yanchor="top", y=-0.14,
                                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                        xaxis=_xax(dtick="M12", tickformat="%Y"),
                        yaxis=_yax(title="¥ / kg", type="log"))
    st.plotly_chart(figM2, width="stretch")
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
    # Trends term -> METI product line. アイシャドウ maps to アイメークアップ, which
    # is broader than eyeshadow alone — it is the only eye-makeup line the
    # statistics carry, and the mismatch is stated rather than hidden.
    PAIRS = [("美容液", "美容液", "serum"), ("化粧水", "化粧水", "toner"),
             ("乳液", "乳液", "emulsion"), ("ファンデーション", "ファンデーション", "foundation"),
             ("口紅", "口紅", "lipstick"), ("アイシャドウ", "アイメークアップ", "eye makeup")]
    REGIMES = [(S["t1_dv_pre"], HEADLINE["mkt_y0"], HEADLINE["mkt_pre1"]),
               (S["t1_dv_post"], HEADLINE["mkt_break"], HEADLINE["mkt_y1"])]

    dv_cols = st.columns(2)
    for (title, ry0, ry1), col in zip(REGIMES, dv_cols):
        cats, d_att, d_val = [], [], []
        for term, item, gloss in PAIRS:
            if term not in att.columns or item not in val_all.index:
                continue
            cats.append(f"{term}<br>{gloss}" if lang == "en" else term)
            d_att.append(100 * (att[term][ry1] - att[term][ry0]) / att[term][ry0])
            d_val.append(100 * (val_all.loc[item, ry1] - val_all.loc[item, ry0])
                         / val_all.loc[item, ry0])
        figD = go.Figure()
        figD.add_trace(go.Bar(x=cats, y=d_att, name=S["t1_dv_att"],
                              marker_color=C["ingr"],
                              hovertemplate="%{y:+.0f}%<extra></extra>"))
        figD.add_trace(go.Bar(x=cats, y=d_val, name=S["t1_dv_val"],
                              marker_color=C["gold"],
                              hovertemplate="%{y:+.0f}%<extra></extra>"))
        figD.add_hline(y=0, line_color=C["text"], line_width=1)
        figD.update_layout(**_base(height=330))
        figD.update_layout(barmode="group", hovermode="x",
                           title=dict(text=f"{title} · {ry0}→{ry1}",
                                      font=dict(size=13, color=C["text"]), x=0, xanchor="left"),
                           margin=dict(l=20, r=10, t=44, b=40),
                           legend=dict(orientation="h", yanchor="top", y=-0.16,
                                       xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                           xaxis=_xax(tickfont=dict(size=10)),
                           yaxis=_yax(title="% change", range=[-80, 80]))
        with col:
            st.plotly_chart(figD, width="stretch")

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

        fig_cv = go.Figure()
        fig_cv.add_trace(go.Scatter(
            x=df_curve["sample_size"], y=df_curve["cross_tier_cosine"],
            mode="lines+markers",
            line=dict(color=C["cosm"], width=2.5),
            marker=dict(size=8, color=C["cosm"]),
            hovertemplate="N=%{x:,} reviews<br>cosine = %{y:.2f}<extra></extra>",
        ))
        fig_cv.add_hline(
            y=HEADLINE["conv_lo"], line_dash="dot", line_color=C["skin"],
            annotation_text=f"size-matched ≈ {HEADLINE['conv_lo']:.2f}",
            annotation_position="bottom left",
            annotation_font=dict(size=9, color=C["skin"]),
        )
        fig_cv.update_layout(**_base(height=380))
        fig_cv.update_layout(
            margin=dict(l=20, r=20, t=20, b=50),
            showlegend=False,
            xaxis=_xax(title=dict(text="Reviews per slice (subsample size)",
                                  font=dict(size=11))),
            yaxis=_yax(title="Skincare ↔ cosmetics cosine",
                       range=[0, 0.8]),
        )
        st.plotly_chart(fig_cv, width="stretch")

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
    # Launch data sits first: brands announce before consumers search. Colours
    # passed the dataviz validator as a set (blue, rose, ochre); the no-category
    # line is gray and dashed, and every line is labelled at its end.
    LG_COLOR = {"skincare": "#3F86B5", "makeup": "#C4627A", "other": "#A8861A",
                "none": C["muted"]}
    _h3 = (f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">'
           '{h}</h3><p class="expl">{e}</p>')
    panel_header(S["t3_lp"], S["t3_lpd"])
    if LAUNCH is None:
        st.markdown(f'<p class="expl">{S["t3_lempty"]}</p>', unsafe_allow_html=True)
    else:
        _gname = {g: S[f"t3_lg_{g}"] for g in LAUNCH_GROUPS}
        st.markdown(_h3.format(h=S["t3_l1h"], e=S["t3_l1e"]), unsafe_allow_html=True)
        lc1, lc2 = st.columns([3, 2])

        # Figure 1 — 12-month rolling totals by category group, core panel
        with lc1:
            _roll = LAUNCH["roll"]
            _x = pd.to_datetime(_roll.index + "-01")
            fig_l1 = go.Figure()
            for g in LAUNCH_GROUPS:
                fig_l1.add_trace(go.Scatter(
                    x=_x, y=_roll[g], name=_gname[g], mode="lines",
                    line=dict(color=LG_COLOR[g], width=2, dash="dash" if g == "none" else "solid"),
                    hovertemplate="%{y:.0f}<extra>" + _gname[g] + "</extra>"))
                fig_l1.add_annotation(x=_x[-1], y=_roll[g].iloc[-1], text=_gname[g],
                                      showarrow=False, xanchor="left", xshift=6,
                                      font=dict(size=10, color=C["text"]))
            fig_l1.update_layout(**_base(height=360))
            fig_l1.update_layout(margin=dict(l=20, r=150, t=10, b=40), showlegend=True,
                                 legend=dict(orientation="h", yanchor="top", y=-0.12,
                                             xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                                 xaxis=_xax(range=[_x[0], _x[-1] + pd.Timedelta(days=20)]),
                                 yaxis=_yax(title=S["t3_l1ax"], rangemode="tozero", automargin=True))
            st.plotly_chart(fig_l1, width="stretch")

        # Per category: latest 12 months against the 12 months before
        with lc2:
            st.markdown(_h3.format(h=S["t3_l2h"], e=S["t3_l2e"]), unsafe_allow_html=True)
            _c = LAUNCH["cats"].head(12).iloc[::-1]
            _cl = [LAUNCH_CAT[k][_li] for k in _c.index]
            _cc = [LG_COLOR.get(g, C["muted"]) for g in _c["group"]]
            fig_l2 = go.Figure()
            fig_l2.add_trace(go.Bar(y=_cl, x=_c["n_p12"], orientation="h", name=S["t3_lwin_p12"],
                                    marker=dict(color=_cc, opacity=0.35),
                                    hovertemplate="%{x}<extra>" + S["t3_lwin_p12"] + "</extra>"))
            fig_l2.add_trace(go.Bar(y=_cl, x=_c["n_l12"], orientation="h", name=S["t3_lwin_l12"],
                                    marker=dict(color=_cc),
                                    hovertemplate="%{x}<extra>" + S["t3_lwin_l12"] + "</extra>"))
            fig_l2.update_layout(**_base(height=420))
            # Bars take their category group's colour, so a legend swatch would show one
            # group's hue for every bar; the expl line names dark and light instead.
            fig_l2.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08,
                                 hovermode="y unified", showlegend=False,
                                 margin=dict(l=10, r=10, t=10, b=30),
                                 xaxis=_xax(), yaxis=_yax(automargin=True))
            st.plotly_chart(fig_l2, width="stretch")

        # Full roster, latest 12 months — present-forward feeds stacked on the core
        st.markdown(_h3.format(h=S["t3_l3h"], e=S["t3_l3e"]), unsafe_allow_html=True)
        _f = LAUNCH["full_grp"].iloc[::-1]
        fig_l3 = go.Figure()
        for pan, col, lab in [("core", "#5A6B7B", S["t3_lpan_core"]),
                              ("present_forward", "#B9C2CC", S["t3_lpan_pf"])]:
            fig_l3.add_trace(go.Bar(y=[_gname[g] for g in _f.index], x=_f[pan], name=lab,
                                    orientation="h", marker=dict(color=col, line=dict(color=C["bg"], width=2)),
                                    texttemplate="%{x}", textposition="inside",
                                    insidetextfont=dict(size=10),
                                    hovertemplate="%{x}<extra>" + lab + "</extra>"))
        fig_l3.update_layout(**_base(height=230))
        fig_l3.update_layout(barmode="stack", hovermode="y unified",
                             margin=dict(l=10, r=10, t=10, b=30),
                             legend=dict(orientation="h", yanchor="top", y=-0.15,
                                         xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                                         traceorder="normal"),
                             xaxis=_xax(), yaxis=_yax(automargin=True))
        st.plotly_chart(fig_l3, width="stretch")

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        lc3, lc4 = st.columns(2)

        # Figure 2 — ingredient share, latest 12 months against the 12 before
        with lc3:
            st.markdown(_h3.format(h=S["t3_l4h"], e=S["t3_l4e"]), unsafe_allow_html=True)
            _i = LAUNCH["ing"].iloc[::-1]
            _il = [_ing_label(k) for k in _i.index]
            fig_l4 = go.Figure()
            for yv, a, b in zip(_il, _i["s_p12"], _i["s_l12"]):
                fig_l4.add_shape(type="line", x0=a, x1=b, y0=yv, y1=yv,
                                 line=dict(color=C["border"], width=2), layer="below")
            fig_l4.add_trace(go.Scatter(
                x=_i["s_p12"], y=_il, mode="markers", name=S["t3_lwin_p12"],
                marker=dict(size=9, color=C["card"], line=dict(color=C["ingr"], width=2)),
                customdata=_i["n_p12"],
                hovertemplate="%{x:.1f}% (%{customdata})<extra>" + S["t3_lwin_p12"] + "</extra>"))
            fig_l4.add_trace(go.Scatter(
                x=_i["s_l12"], y=_il, mode="markers", name=S["t3_lwin_l12"],
                marker=dict(size=10, color=C["ingr"]),
                customdata=_i["n_l12"],
                hovertemplate="%{x:.1f}% (%{customdata})<extra>" + S["t3_lwin_l12"] + "</extra>"))
            fig_l4.update_layout(**_base(height=460))
            fig_l4.update_layout(hovermode="y unified", margin=dict(l=10, r=10, t=10, b=40),
                                 legend=dict(orientation="h", yanchor="top", y=-0.08,
                                             xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
                                 xaxis=_xax(ticksuffix="%", rangemode="tozero"),
                                 yaxis=_yax(automargin=True))
            st.plotly_chart(fig_l4, width="stretch")

        # One ingredient: launch share over search interest, one axis each
        with lc4:
            st.markdown(_h3.format(h=S["t3_l5h"], e=S["t3_l5e"]), unsafe_allow_html=True)
            _paired = LAUNCH["ing"][LAUNCH["ing"]["trends_term"] != ""]
            _opts = [_ing_label(k) for k in _paired.index]
            _pick = st.selectbox(S["t3_l5ax1"], _opts, index=0, key="launch_ing",
                                 label_visibility="collapsed")
            _canon = _paired.index[_opts.index(_pick)]
            _sr = LAUNCH["ing_roll"].get(_canon)
            _tr = load_ingredient_surge()
            _tr = (_tr[_tr["term"] == _paired.loc[_canon, "trends_term"]]
                   .set_index("week_start")["interest"].sort_index().rolling(12).mean().dropna())
            _x0 = pd.Timestamp(LAUNCH["roll"].index[0] + "-01")
            _tr = _tr[_tr.index >= _x0]
            fig_l5 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
            fig_l5.add_trace(go.Scatter(
                x=pd.to_datetime(_sr.index + "-01"), y=_sr, mode="lines", name=S["t3_l5ax1"],
                line=dict(color=C["ingr"], width=2),
                hovertemplate="%{y:.1f}%<extra>" + S["t3_l5ax1"] + "</extra>"), row=1, col=1)
            fig_l5.add_trace(go.Scatter(
                x=_tr.index, y=_tr, mode="lines", name=S["t3_l5ax2"],
                line=dict(color=C["text"], width=2),
                hovertemplate="%{y:.0f}<extra>" + S["t3_l5ax2"] + "</extra>"), row=2, col=1)
            fig_l5.update_layout(**_base(height=420))
            fig_l5.update_layout(showlegend=False, margin=dict(l=20, r=10, t=10, b=30))
            fig_l5.update_xaxes(**_xax())
            fig_l5.update_yaxes(**_yax(title=S["t3_l5y1"], suffix="%", rangemode="tozero",
                                       automargin=True), row=1, col=1)
            fig_l5.update_yaxes(**_yax(title=S["t3_l5y2"], rangemode="tozero", automargin=True),
                                row=2, col=1)
            st.plotly_chart(fig_l5, width="stretch")

        st.caption(S["t3_lcap"])

    panel_header(S["t3_p2"], S["t3_p2d"])

    # ── Block C treemap ───────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_bch"]}</h3><p class="expl">{S["t3_bce"]}</p>', unsafe_allow_html=True)

    df_bc = load_blockc()

    window_choice = st.pills(
        "Window",
        options=[S["t3_win_r"], S["t3_win_c"]],
        default=S["t3_win_r"],
        key="blockc_window",
    )
    if window_choice is None:
        window_choice = "Recent (2023–2025)"

    window_key = "recent" if window_choice == S["t3_win_r"] else "covid"
    df_window = df_bc[df_bc["window"] == window_key].copy()
    df_window = df_window[df_window["metric"] > 0].sort_values(
        "metric", ascending=False
    ).head(20).reset_index(drop=True)

    # Grammar + signal display setup
    df_window["seed_label"] = df_window["seed_count"].apply(
        lambda n: f"{n} seed" if n == 1 else f"{n} seeds"
    )
    SIG_DISPLAY = {
        "korean_brand": S["t3_sig_kr"],
        "ingredient":   S["t3_sig_in"],
        "other":        S["t3_sig_ot"],
    }
    SIG_COLORS = {
        "korean_brand": C["korean"],
        "ingredient":   C["skin"],
        "other":        C["ingr"],
    }
    df_window["sig_display"] = df_window["signal_type"].map(SIG_DISPLAY).fillna("Other")
    df_window["color"] = df_window["signal_type"].map(SIG_COLORS).fillna(C["ingr"])

    # px.treemap single level — flat, butter zoom, colour by signal type
    df_window["_color_val"] = df_window["signal_type"].map({
        "korean_brand": 0,
        "ingredient":   1,
        "other":        2,
    }).fillna(2)

    fig_bc = px.treemap(
        df_window,
        path=["root"],
        values="metric",
        color="signal_type",
        color_discrete_map={
            "korean_brand": C["korean"],
            "ingredient":   C["skin"],
            "other":        C["ingr"],
        },
        custom_data=["metric", "seed_count", "sig_display", "seeds", "seed_label"],
    )
    fig_bc.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[4]}",
        textfont=dict(size=11),
        marker_line=dict(width=2, color=C["bg"]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Signal strength: %{customdata[0]:.3f}<br>"
            "Found via %{customdata[4]}<br>"
            "Type: %{customdata[2]}<br>"
            "Search entry points: %{customdata[3]}"
            "<extra></extra>"
        ),
    )
    fig_bc.update_layout(**_base(height=400))
    fig_bc.update_layout(margin=dict(l=0, r=0, t=10, b=0))

    bc_selection = st.plotly_chart(
        fig_bc,
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
        match = df_window[df_window["root"] == clicked_label]

        if not match.empty:
            row = match.iloc[0]
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

    TIER_COLOURS = {
        "skincare":  C["skin"],
        "cosmetics": C["cosm"],
        "korean":    C["korean"],
        "other":     C["muted"],
    }

    try:
        df_ch = load_yt_channels()

        # Aggregate by channel — primary tier = category with highest total_views
        df_agg = (df_ch.groupby("channel_name")
                  .agg(total_views=("total_views", "sum"),
                       video_count=("video_count", "sum"),
                       total_comments=("total_comments", "sum"))
                  .reset_index())
        primary = (df_ch.sort_values("total_views", ascending=False)
                   .groupby("channel_name").first()[["tier_group", "search_category"]]
                   .reset_index())
        df_agg = df_agg.merge(primary, on="channel_name")
        df_agg = df_agg.sort_values("total_views", ascending=True).tail(15).copy()
        df_agg["colour"]  = df_agg["tier_group"].map(TIER_COLOURS).fillna(C["muted"])
        df_agg["views_M"] = (df_agg["total_views"] / 1_000_000).round(1)

        fig_yt_ch = go.Figure()
        fig_yt_ch.add_trace(go.Bar(
            x=df_agg["total_views"],
            y=df_agg["channel_name"],
            orientation="h",
            marker_color=df_agg["colour"].tolist(),
            marker_line=dict(width=0),
            customdata=np.stack([
                df_agg["views_M"],
                df_agg["video_count"],
                df_agg["total_comments"],
                df_agg["search_category"],
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{customdata[0]:.1f}M views · "
                "%{customdata[1]:.0f} videos · "
                "%{customdata[2]:,.0f} comments<br>"
                "Category: %{customdata[3]}"
                "<extra></extra>"
            ),
        ))
        fig_yt_ch.update_layout(**_base(height=380))
        fig_yt_ch.update_layout(
            margin=dict(l=10, r=20, t=10, b=50),
            xaxis=dict(
                title=dict(text="Total views", font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"],
                zerolinecolor=C["border"], tickformat=".2s",
            ),
            yaxis=dict(
                autorange=True,
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0)",
                linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_yt_ch, width="stretch")

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

        # ── Diverging view: terms that distinguish registers ───────────────
        # Raw top-15 per tier is dominated by shared generic verbs (使う, 動画).
        # The insight is what differs between skincare and cosmetics YouTube.
        # Compute TF-IDF delta: skincare score minus cosmetics score per term.
        # Positive = skews skincare · Negative = skews cosmetics.
        sk_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "skincare"].set_index("term")["tfidf"]
        co_tf = df_yt_tfidf[df_yt_tfidf["tier"] == "cosmetics"].set_index("term")["tfidf"]
        all_terms_yt = sk_tf.index.union(co_tf.index)
        df_div = pd.DataFrame({
            "skin": sk_tf.reindex(all_terms_yt, fill_value=0),
            "cosm": co_tf.reindex(all_terms_yt, fill_value=0),
        })
        df_div["delta"] = df_div["skin"] - df_div["cosm"]
        # Exclude generic Japanese verbs that appear in all YouTube comments
        # regardless of topic — these are not register-specific signals
        YT_EXCL = {'使う', '思う', 'する', 'なる', 'いる', 'ある', 'くれる', 'もらう'}
        df_div = df_div[~df_div.index.isin(YT_EXCL)]
        # Take top 12 each direction, exclude near-zero shared terms
        skin_terms = df_div[df_div["delta"] > 0].nlargest(12, "delta")
        cosm_terms = df_div[df_div["delta"] < 0].nsmallest(12, "delta")
        df_diverge = pd.concat([
            skin_terms.assign(label="skincare"),
            cosm_terms.assign(label="cosmetics"),
        ]).sort_values("delta")

        colors = [C["skin"] if r.label == "skincare" else C["cosm"]
                  for _, r in df_diverge.iterrows()]

        fig_yt_div = go.Figure()
        fig_yt_div.add_trace(go.Bar(
            x=df_diverge["delta"],
            y=df_diverge.index,
            orientation="h",
            marker_color=colors,
            marker_line=dict(width=0),
            customdata=np.stack([
                df_diverge["skin"].round(4),
                df_diverge["cosm"].round(4),
            ], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Skincare TF-IDF: %{customdata[0]:.4f}<br>"
                "Cosmetics TF-IDF: %{customdata[1]:.4f}<br>"
                "Delta: %{x:+.4f}"
                "<extra></extra>"
            ),
        ))
        fig_yt_div.add_vline(x=0, line_color=C["border"], line_width=1.5)
        fig_yt_div.update_layout(**_base(height=420))
        fig_yt_div.update_layout(
            margin=dict(l=10, r=20, t=30, b=40),
            title=dict(
                text=S["t3_ytdivtitle"],
                font=dict(size=11, color=C["muted"]), x=0.5, xanchor="center",
            ),
            xaxis=dict(
                title=dict(text=S["t3_ytdivax"], font=dict(size=10)),
                gridcolor=C["grid"], linecolor=C["border"], zerolinecolor=C["border"],
            ),
            yaxis=dict(
                tickfont=dict(size=11),
                gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_yt_div, width="stretch")

        st.markdown(f'<div style="background:{C["grid"]};border-left:3px solid {C["muted"]};border-radius:0 6px 6px 0;padding:10px 14px;margin-top:4px;"><span style="font-size:12px;color:{C["text"]};font-weight:600;">{S["t3_ytreg"]}</span><span style="font-size:12px;color:{C["muted"]};">{S["t3_ytregb"]}</span></div>', unsafe_allow_html=True)

    except FileNotFoundError:
        st.info("nb07_yt_tfidf.csv not found — run NB06 Section 6 to generate it.", icon="ℹ️")

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── UMAP scatter ──────────────────────────────────────────────────────
    st.markdown(f'<h3 style="font-size:16px;font-weight:600;color:{C["text"]};margin-bottom:2px;">{S["t3_umaph"]}</h3><p class="expl">{S["t3_umape"]}</p>', unsafe_allow_html=True)

    df_umap = load_umap()

    # Topic labels mapped from NB06 Cell 13
    TOPIC_LABELS = {
        "Skin T1": "Cleansing & face wash",
        "Skin T2": "Moisturising routine",
        "Skin T3": "Makeup (miscategorised)",
        "Skin T4": "Eye makeup & liner",
        "Skin T5": "Sun protection & base",
        "Cosm T1": "Foot care (off-topic)",
        "Cosm T2": "Foundation, skincare words ★",
        "Cosm T3": "Eyebrow pencil",
        "Cosm T4": "Powder & colour",
    }
    df_umap["topic_label"] = df_umap["dominant_topic"].map(TOPIC_LABELS).fillna("Unknown")

    umap_col1, umap_col2 = st.columns([3, 1])

    with umap_col2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Year filter — reverse chronological
        year_filter = st.pills(
            S["t3_umap_yr"],
            options=["全" if lang=="jp" else "All", 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019],
            default="全" if lang=="jp" else "All",
            key="umap_year",
        )
        if year_filter is None:
            year_filter = "全" if lang == "jp" else "All"

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

        n_shown = len(df_umap) if year_filter in ("All", "全") else \
                  len(df_umap[df_umap.review_year == int(year_filter)])
        st.caption(f"{n_shown:,} reviews")

    with umap_col1:
        # Vocabulary centroid keywords — always visible regardless of year
        TOPIC_KEYWORDS = {
            "Cleansing & face wash":     "洗顔 · 洗い上がり · 毛穴",
            "Moisturising routine":      "香り · 乾燥 · 保湿 · 化粧水",
            "Makeup (miscategorised)":   "メイク · 描く · 発色",
            "Eye makeup & liner":        "アイライナー · ライン · コットン",
            "Sun protection & base":     "日焼け止め · トーンアップ · 下地",
            "Foot care (off-topic)":         "⚠ 靴下 · 暖かい",
            "Foundation, skincare words ★": "乾燥 · しっとり · 毛穴 · ツヤ ★",
            "Eyebrow pencil":            "細い · 眉毛 · コスパ",
            "Powder & colour":           "パウダー · 香り · 発色",
        }
        TOPIC_ANNOT_COLORS = {
            "Cleansing & face wash":     "#4A90B8",
            "Moisturising routine":      "#5B8C6E",
            "Makeup (miscategorised)":   "#78909C",
            "Eye makeup & liner":        "#C4627A",
            "Sun protection & base":     "#B8965A",
            "Foot care (off-topic)":         "#B0BEC5",
            "Foundation, skincare words ★": "#D4785C",
            "Eyebrow pencil":            "#9C4E8A",
            "Powder & colour":           "#C4627A",
        }

        # Filter by year only
        df_u = df_umap.copy()
        if year_filter not in ("All", "全"):
            df_u = df_u[df_u["review_year"] == int(year_filter)]

        fig_umap = go.Figure()

        # Plot Tier — skincare and cosmetics always coloured the same
        for tier, color, name in [
            ("skincare",  C["skin"], S["t3_umap_sk"]),
            ("cosmetics", C["cosm"], S["t3_umap_co"]),
        ]:
            d = df_u[df_u["tier_group"] == tier]
            if len(d) == 0:
                continue
            # Scattergl: 21k points render via WebGL — SVG Scatter is sluggish here
            fig_umap.add_trace(go.Scattergl(
                x=d["umap_x"], y=d["umap_y"],
                mode="markers", name=S["t3_umap_sk"] if tier=="skincare" else S["t3_umap_co"],
                marker=dict(color=color, size=3, opacity=0.5,
                            line=dict(width=0)),
                customdata=np.stack([
                    d["review_year"].astype(int),
                    d["topic_label"],
                ], axis=-1),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Year: %{customdata[0]}<br>"
                    "Topic: %{customdata[1]}"
                    "<extra></extra>"
                ),
            ))

        # Centroid annotations — fixed coordinates from NB06 corpus analysis
        # Positions computed from full corpus so labels stay stable across year filters
        # Standard topic centroids from corpus median positions
        for topic, kw in TOPIC_KEYWORDS.items():
            color = TOPIC_ANNOT_COLORS.get(topic, C["muted"])
            d_full = df_umap[df_umap["topic_label"] == topic]
            if len(d_full) < 10:
                continue
            cx = d_full["umap_x"].median()
            cy = d_full["umap_y"].median()
            fig_umap.add_annotation(
                x=cx, y=cy,
                text=f"<b>{kw}</b>",
                showarrow=False,
                font=dict(size=9.5, color=color, family="sans-serif"),
                bgcolor="rgba(255,255,255,0.82)",
                borderpad=3,
                bordercolor=color,
                borderwidth=1,
            )

        # ── Manual island annotations ─────────────────────────────────────
        # Top island: influencer/monitor reviews — template vocabulary
        fig_umap.add_annotation(
            x=-1.72, y=9.47,
            text="<b>⚠ インフルエンサー · モニター</b><br>giveaway reviews",
            showarrow=True, arrowhead=2, arrowcolor=C["gold"],
            ax=60, ay=30,
            font=dict(size=9, color=C["gold"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["gold"],
            borderwidth=1.5,
        )

        # Right satellite: tone-up SPF — cosmetic SPF sub-category
        fig_umap.add_annotation(
            x=8.60, y=2.38,
            text="<b>トーンアップ · ファンデ · 伸び</b><br>Tone-up SPF as base makeup",
            showarrow=True, arrowhead=2, arrowcolor=C["ingr"],
            ax=-70, ay=-30,
            font=dict(size=9, color=C["ingr"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["ingr"],
            borderwidth=1.5,
        )

        # Northeast convergence zone
        fig_umap.add_annotation(
            x=3.41, y=7.22,
            text="<b>保湿 · 洗顔 · 乾燥</b><br>★ skincare and makeup words overlap",
            showarrow=True, arrowhead=2, arrowcolor=C["skin"],
            ax=-80, ay=20,
            font=dict(size=9, color=C["skin"], family="sans-serif"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4,
            bordercolor=C["skin"],
            borderwidth=1.5,
        )

        suffix = f" — {year_filter}" if year_filter not in ("All", "全") else " — all years"
        fig_umap.update_layout(**_base(height=520))
        fig_umap.update_layout(
            margin=dict(l=10, r=10, t=30, b=20),
            title=dict(
                text=f"UMAP embedding{suffix} · {n_shown:,} reviews",
                font=dict(size=12, color=C["muted"]),
                x=0,
            ),
            legend=dict(
                orientation="v", yanchor="top", y=1,
                xanchor="left", x=1.01,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=10),
            ),
            xaxis=dict(showgrid=False, showticklabels=False,
                       linecolor="rgba(0,0,0,0)", zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False,
                       linecolor="rgba(0,0,0,0)", zeroline=False),
        )
        st.plotly_chart(fig_umap, width="stretch")

    # Finding callout
    st.markdown(f'<div style="background:{C["skin_lt"]};border-left:4px solid {C["skin"]};border-radius:0 8px 8px 0;padding:14px 18px;margin-top:8px;"><p style="margin:0;font-size:13px;color:{C["text"]};font-weight:600;">{S["f3_title"]}</p><p style="margin:6px 0 0 0;font-size:12px;color:{C["muted"]};line-height:1.6;">{S["f3_body"]}</p></div>', unsafe_allow_html=True)
