"""Export the ingredient-search chart as a PNG, in English or Japanese.

    python export_ingredient_chart.py --lang en   ->  ingredient_surge_linkedin.png
    python export_ingredient_chart.py --lang jp   ->  ingredient_surge_jp.png

Window: full calendar years only, selected the same way compute_headline() in
dashboard/streamlit_app.py selects them (>= 12 points in the year). The source
CSV carries a partial current year; averaging it against full years would put a
figure on the chart that the dashboard does not report, and beauty search is
seasonal enough that a half-year mean is not comparable to a full one.
"""

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ASSETS = Path(__file__).resolve().parent / "dashboard" / "assets"

ESTABLISHED = ["ヒアルロン酸", "セラミド"]

# Label per language; the JP column differs from the term only where the search
# term carries a disambiguating suffix ("ビタミンC 美容").
LABELS = {
    "ナイアシンアミド": {"en": "Niacinamide",     "jp": "ナイアシンアミド"},
    "レチノール":       {"en": "Retinol",         "jp": "レチノール"},
    "グルタチオン":     {"en": "Glutathione",     "jp": "グルタチオン"},
    "ビタミンC 美容":   {"en": "Vitamin C",       "jp": "ビタミンC"},
    "トラネキサム酸":   {"en": "Tranexamic acid", "jp": "トラネキサム酸"},
    "アゼライン酸":     {"en": "Azelaic acid",    "jp": "アゼライン酸"},
    "エクソソーム":     {"en": "Exosomes",        "jp": "エクソソーム"},
    "ヒアルロン酸":     {"en": "Hyaluronic acid", "jp": "ヒアルロン酸"},
    "セラミド":         {"en": "Ceramide",        "jp": "セラミド"},
    "レチナール":       {"en": "Retinal",         "jp": "レチナール"},
}

COLORS = {
    "ナイアシンアミド": "#2E7D32", "レチノール": "#1565C0",
    "グルタチオン": "#6A1B9A", "ビタミンC 美容": "#E65100",
    "トラネキサム酸": "#00695C", "アゼライン酸": "#AD1457",
    "エクソソーム": "#4E342E", "ヒアルロン酸": "#4A90B8",
    "セラミド": "#90A4AE", "レチナール": "#78909C",
}

COPY = {
    "en": {
        "outfile": "ingredient_surge_linkedin.png",
        "covid":   "COVID",
        "title":   "Japanese Beauty: Ingredient Search Surge {y0}–{y1}"
                   "<br><sup>Google Trends Japan · avg annual search interest "
                   "(0–100) · Beauty Pulse</sup>",
        "yaxis":   "Avg search interest (0–100)",
        "footnote": "Dashed = established pre-COVID  ·  Solid = post-COVID breakouts",
    },
    "jp": {
        "outfile": "ingredient_surge_jp.png",
        "covid":   "COVID\n（2020-21）",
        "title":   "日本の美容成分検索トレンド {y0}–{y1}"
                   "<br><sup>Google Trends Japan · 年間平均検索関心度（0–100）"
                   "· Beauty Pulse</sup>",
        "yaxis":   "年間平均検索関心度（0–100）",
        "footnote": "点線 = COVID前からの定番成分  ·  実線 = COVID後に急伸した成分",
    },
}


def full_calendar_years(df: pd.DataFrame) -> pd.Index:
    """Years with a complete set of observations — the dashboard's rule."""
    per_year = df.groupby("year")["week_start"].nunique()
    return per_year[per_year >= 12].index


def build(lang: str) -> Path:
    copy = COPY[lang]

    df = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
    df["year"] = df["week_start"].dt.year
    df = df[df["year"].isin(full_calendar_years(df))]

    df_yr = df.groupby(["year", "term"])["interest"].mean().reset_index()
    y0, y1 = int(df_yr["year"].min()), int(df_yr["year"].max())

    # Legend order: highest interest in the final full year first.
    ordered = (df_yr[df_yr["year"] == y1]
               .groupby("term")["interest"].mean()
               .sort_values(ascending=False).index.tolist())
    ordered += [t for t in df_yr["term"].unique() if t not in ordered]

    fig = go.Figure()
    fig.add_vrect(x0=2019.8, x1=2021.2, fillcolor="#E0E0E0",
                  opacity=0.6, layer="below", line_width=0,
                  annotation_text=copy["covid"], annotation_position="top left",
                  annotation_font_size=11, annotation_font_color="#888888")

    for term in ordered:
        d = df_yr[df_yr["term"] == term]
        label = LABELS.get(term, {}).get(lang, term)
        fig.add_trace(go.Scatter(
            x=d["year"], y=d["interest"].round(1),
            name=label,
            mode="lines+markers",
            line=dict(color=COLORS.get(term, "#90A4AE"), width=2.5,
                      dash="dot" if term in ESTABLISHED else "solid"),
            marker=dict(size=7),
            hovertemplate=f"{label}: %{{y:.1f}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="#F7F9FC", plot_bgcolor="#EFF3F8",
        font=dict(family="sans-serif", color="#212121"),
        height=560, width=1100,
        margin=dict(l=60, r=40, t=80, b=140),
        title=dict(text=copy["title"].format(y0=y0, y1=y1),
                   font=dict(size=18), x=0.0, xanchor="left"),
        legend=dict(orientation="h", yanchor="top", y=-0.22,
                    xanchor="left", x=0, font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, dtick=1, range=[y0 - 0.2, y1 + 0.2],
                   tickfont=dict(size=12)),
        yaxis=dict(gridcolor="#D6E4F0",
                   title=dict(text=copy["yaxis"], font=dict(size=12))),
        annotations=[dict(
            text=copy["footnote"],
            xref="paper", yref="paper", x=0, y=-0.18,
            showarrow=False, font=dict(size=11, color="#757575"),
            xanchor="left",
        )],
    )

    out = Path(__file__).resolve().parent / copy["outfile"]
    fig.write_image(out, scale=2)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=("en", "jp"), default="en")
    args = ap.parse_args()
    print(f"Saved: {build(args.lang).name}")
