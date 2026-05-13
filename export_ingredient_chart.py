import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

ASSETS = Path("dashboard/assets")
df = pd.read_csv(ASSETS / "nb07_ingredient_surge.csv", parse_dates=["week_start"])
df["year"] = df["week_start"].dt.year
df_yr = df[df["year"] <= 2026].groupby(["year","term"])["interest"].mean().reset_index()

ESTABLISHED = ["ヒアルロン酸", "セラミド"]
EN_NAMES = {
    "ナイアシンアミド": "Niacinamide", "レチノール": "Retinol",
    "グルタチオン": "Glutathione", "ビタミンC 美容": "Vitamin C",
    "トラネキサム酸": "Tranexamic acid", "アゼライン酸": "Azelaic acid",
    "エクソソーム": "Exosomes", "ヒアルロン酸": "Hyaluronic acid",
    "セラミド": "Ceramide", "レチナール": "Retinal",
}
COLORS = {
    "ナイアシンアミド": "#2E7D32", "レチノール": "#1565C0",
    "グルタチオン": "#6A1B9A", "ビタミンC 美容": "#E65100",
    "トラネキサム酸": "#00695C", "アゼライン酸": "#AD1457",
    "エクソソーム": "#4E342E", "ヒアルロン酸": "#4A90B8",
    "セラミド": "#90A4AE", "レチナール": "#78909C",
}

fig = go.Figure()
fig.add_vrect(x0=2019.8, x1=2021.2, fillcolor="#E0E0E0",
              opacity=0.6, layer="below", line_width=0,
              annotation_text="COVID", annotation_position="top left",
              annotation_font_size=11, annotation_font_color="#888888")

# Sort ingredients by their 2026 average interest, highest to lowest
order_2026 = (
    df_yr[df_yr["year"] == 2026]
    .groupby("term")["interest"].mean()
    .sort_values(ascending=False)
    .index.tolist()
)
# Fall back to any terms missing 2026 data
all_terms_ordered = order_2026 + [t for t in df_yr["term"].unique() if t not in order_2026]

for term in all_terms_ordered:
    d = df_yr[df_yr["term"] == term]
    en = EN_NAMES.get(term, term)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["interest"].round(1),
        name=en,
        mode="lines+markers",
        line=dict(color=COLORS.get(term, "#90A4AE"), width=2.5,
                  dash="dot" if term in ESTABLISHED else "solid"),
        marker=dict(size=7),
        hovertemplate=f"{en}: %{{y:.1f}}<extra></extra>",
    ))

fig.update_layout(
    paper_bgcolor="#F7F9FC", plot_bgcolor="#EFF3F8",
    font=dict(family="sans-serif", color="#212121"),
    height=560, width=1100,
    margin=dict(l=60, r=40, t=80, b=140),
    title=dict(
        text="Japanese Beauty: Ingredient Search Surge 2019–2026<br><sup>Google Trends Japan · avg annual search interest (0–100) · Beauty Pulse</sup>",
        font=dict(size=18), x=0.0, xanchor="left",
    ),
    legend=dict(orientation="h", yanchor="top", y=-0.22,
                xanchor="left", x=0, font=dict(size=11),
                bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, dtick=1, range=[2018.8, 2026.2],
               tickfont=dict(size=12)),
    yaxis=dict(gridcolor="#D6E4F0",
               title=dict(text="Avg search interest (0–100)", font=dict(size=12))),
    annotations=[dict(
        text="Dashed = established pre-COVID  ·  Solid = post-COVID breakouts",
        xref="paper", yref="paper", x=0, y=-0.18,
        showarrow=False, font=dict(size=11, color="#757575"),
        xanchor="left",
    )],
)

fig.write_image("ingredient_surge_linkedin.png", scale=2)
print("Saved: ingredient_surge_linkedin.png")
