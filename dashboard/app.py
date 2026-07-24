"""
Crop Yield Intelligence Dashboard
===================================
An interactive Streamlit dashboard for the Agricultural Crop-Yield
Prediction capstone project.

Run with:  streamlit run dashboard/app.py
"""

import json
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Crop Yield Intelligence",
    page_icon="\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# DESIGN TOKENS  (Agricultural theme — deep field-green + harvest-gold,
# deliberately avoiding the generic cream/terracotta AI-default palette)
# ---------------------------------------------------------------------------
COLOR_BG = "#F7F5EF"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARY = "#1B4332"       # deep forest green
COLOR_PRIMARY_LIGHT = "#2D6A4F"
COLOR_ACCENT = "#E9C46A"        # harvest gold
COLOR_ACCENT2 = "#588157"       # sage green
COLOR_SOIL = "#7F5539"          # soil brown
COLOR_TEXT = "#1B1B18"
COLOR_MUTED = "#6B7061"
COLOR_HIGH = "#2D6A4F"
COLOR_LOW = "#BC6C25"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {COLOR_TEXT};
}}
.stApp {{
    background-color: {COLOR_BG};
}}
h1, h2, h3 {{
    font-family: 'Fraunces', serif;
    color: {COLOR_PRIMARY};
    letter-spacing: -0.01em;
}}
.hero {{
    background: linear-gradient(120deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_LIGHT} 100%);
    border-radius: 18px;
    padding: 2.4rem 2.6rem;
    color: #F7F5EF;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}}
.hero:before {{
    content: "";
    position: absolute;
    right: -60px; top: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: {COLOR_ACCENT}22;
}}
.hero h1 {{
    color: #FFFFFF;
    font-size: 2.4rem;
    margin-bottom: 0.3rem;
}}
.hero p {{
    color: #E7E5DA;
    font-size: 1.05rem;
    max-width: 640px;
}}
.eyebrow {{
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    color: {COLOR_ACCENT};
    font-weight: 600;
    margin-bottom: 0.4rem;
}}
.metric-card {{
    background: {COLOR_PANEL};
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    border: 1px solid #E5E2D8;
    box-shadow: 0 1px 3px rgba(27,67,50,0.06);
}}
.metric-card .label {{
    font-size: 0.78rem;
    color: {COLOR_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}}
.metric-card .value {{
    font-family: 'Fraunces', serif;
    font-size: 1.8rem;
    color: {COLOR_PRIMARY};
    font-weight: 700;
}}
.band-high {{ color: {COLOR_HIGH}; font-weight: 700; }}
.band-low {{ color: {COLOR_LOW}; font-weight: 700; }}
.section-title {{
    border-left: 5px solid {COLOR_ACCENT};
    padding-left: 0.7rem;
    margin: 1.6rem 0 0.8rem 0;
}}
[data-testid="stSidebar"] {{
    background-color: {COLOR_PRIMARY};
}}
[data-testid="stSidebar"] * {{
    color: #F7F5EF !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: {COLOR_PANEL};
    border-radius: 10px 10px 0 0;
    padding: 8px 18px;
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    background-color: {COLOR_PRIMARY} !important;
    color: white !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=COLOR_TEXT),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=[COLOR_PRIMARY, COLOR_ACCENT, COLOR_ACCENT2, COLOR_SOIL, "#A98467", "#457B9D"],
    title_font=dict(family="Fraunces, serif", size=18, color=COLOR_PRIMARY),
)


# ---------------------------------------------------------------------------
# DATA / MODEL LOADING
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/crop_yield_features.csv")
    test_pred = pd.read_csv("reports/test_predictions.csv")
    comparison = pd.read_csv("reports/model_comparison.csv")
    district_rank = pd.read_csv("reports/district_productivity_ranking.csv")
    try:
        feat_imp = pd.read_csv("reports/feature_importance.csv")
    except FileNotFoundError:
        feat_imp = None
    return df, test_pred, comparison, district_rank, feat_imp


@st.cache_resource
def load_model():
    model = joblib.load("models/best_model.pkl")
    with open("models/best_model_name.json") as f:
        meta = json.load(f)
    return model, meta


df, test_pred, comparison, district_rank, feat_imp = load_data()
model, meta = load_model()

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">Machine Learning Capstone &middot; Regression</div>
        <h1>🌾 Crop Yield Intelligence</h1>
        <p>Predicting district-level crop yield across {df['State_Name'].nunique()} states,
        {df['District_Name'].nunique()} districts and {df['Crop'].nunique()} crops
        ({int(df['Crop_Year'].min())}–{int(df['Crop_Year'].max())}), to help agricultural
        planners spot high- and low-productivity districts before the season starts.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# TOP METRIC ROW
# ---------------------------------------------------------------------------
best_row = comparison.sort_values("Test_R2", ascending=False).iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    (c1, "Best Model", meta.get("best_model", "-")),
    (c2, "Test R²", f"{best_row['Test_R2']:.3f}"),
    (c3, "Test RMSE", f"{best_row['Test_RMSE']:.1f}"),
    (c4, "Test MAE", f"{best_row['Test_MAE']:.1f}"),
    (c5, "Records Modeled", f"{len(df):,}"),
]
for col, label, value in metrics:
    with col:
        st.markdown(
            f"""<div class="metric-card"><div class="label">{label}</div>
            <div class="value">{value}</div></div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab_overview, tab_eda, tab_models, tab_predict, tab_districts = st.tabs(
    ["📊 Overview", "🔎 EDA", "🏆 Model Comparison", "🔮 Predict Yield", "📍 District Rankings"]
)

# ===== OVERVIEW =====
with tab_overview:
    st.markdown('<div class="section-title"><h3>Actual vs Predicted Yield (Test Set)</h3></div>', unsafe_allow_html=True)
    lim = test_pred["Yield_Target"].quantile(0.97)
    sample = test_pred.sample(min(3000, len(test_pred)), random_state=42)
    fig = px.scatter(
        sample, x="Yield_Target", y="Predicted_Yield", opacity=0.45,
        hover_data=["State_Name", "District_Name", "Crop", "Crop_Year"],
        labels={"Yield_Target": "Actual Yield", "Predicted_Yield": "Predicted Yield"},
    )
    fig.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines",
                              line=dict(color=COLOR_SOIL, dash="dash"), name="Perfect Prediction"))
    fig.update_xaxes(range=[0, lim]); fig.update_yaxes(range=[0, lim])
    fig.update_layout(**PLOTLY_LAYOUT, height=460)
    st.plotly_chart(fig, width='stretch')

    colA, colB = st.columns(2)
    with colA:
        st.markdown('<div class="section-title"><h3>Yield Trend Over Years</h3></div>', unsafe_allow_html=True)
        trend = df.groupby("Crop_Year")["Yield_Target"].mean().reset_index()
        fig2 = px.line(trend, x="Crop_Year", y="Yield_Target", markers=True)
        fig2.update_traces(line_color=COLOR_PRIMARY)
        fig2.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig2, width='stretch')
    with colB:
        st.markdown('<div class="section-title"><h3>Feature Importance</h3></div>', unsafe_allow_html=True)
        if feat_imp is not None:
            feat_imp_sorted = feat_imp.sort_values(feat_imp.columns[1], ascending=True)
            fig3 = px.bar(feat_imp_sorted, x=feat_imp.columns[1], y=feat_imp.columns[0], orientation="h")
            fig3.update_traces(marker_color=COLOR_ACCENT2)
            fig3.update_layout(**PLOTLY_LAYOUT, height=380)
            st.plotly_chart(fig3, width='stretch')
        else:
            st.info("Feature importance not available for this model.")

# ===== EDA =====
with tab_eda:
    st.markdown('<div class="section-title"><h3>Explore the Dataset</h3></div>', unsafe_allow_html=True)
    colA, colB = st.columns(2)
    with colA:
        fig4 = px.histogram(df[df["Yield_Target"] < df["Yield_Target"].quantile(0.97)],
                             x="Yield_Target", nbins=60, title="Yield Distribution")
        fig4.update_traces(marker_color=COLOR_PRIMARY_LIGHT)
        fig4.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig4, width='stretch')
    with colB:
        season_avg = df.groupby("Season")["Yield_Target"].mean().sort_values(ascending=False).reset_index()
        fig5 = px.bar(season_avg, x="Season", y="Yield_Target", title="Average Yield by Season")
        fig5.update_traces(marker_color=COLOR_ACCENT)
        fig5.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig5, width='stretch')

    colC, colD = st.columns(2)
    with colC:
        state_avg = df.groupby("State_Name")["Yield_Target"].mean().sort_values(ascending=False).reset_index()
        fig6 = px.bar(state_avg, x="State_Name", y="Yield_Target", title="Average Yield by State")
        fig6.update_traces(marker_color=COLOR_SOIL)
        fig6.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig6, width='stretch')
    with colD:
        top_crops = df.groupby("Crop")["Yield_Target"].mean().sort_values(ascending=False).head(10).reset_index()
        fig7 = px.bar(top_crops, x="Yield_Target", y="Crop", orientation="h", title="Top 10 Crops by Avg Yield")
        fig7.update_traces(marker_color=COLOR_ACCENT2)
        fig7.update_layout(**PLOTLY_LAYOUT, height=380, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig7, width='stretch')

    st.caption(
        "Note: Coconut and 'Whole Year' season values are naturally very high because "
        "production for some crops is recorded in count units (e.g. nuts) rather than "
        "tonnes in the source dataset — a known quirk of this open dataset worth flagging "
        "to stakeholders rather than treating as a modelling error."
    )

# ===== MODEL COMPARISON =====
with tab_models:
    st.markdown('<div class="section-title"><h3>Model Comparison</h3></div>', unsafe_allow_html=True)
    show_cols = ["Model", "Train_R2", "CV_R2_mean", "Test_R2", "Test_MAE", "Test_RMSE", "Test_MAPE",
                 "Overfit_Gap(Train-Test R2)", "Train_Time_s"]
    st.dataframe(
        comparison[show_cols].sort_values("Test_R2", ascending=False).style.format(precision=3),
        width='stretch', hide_index=True,
    )

    fig8 = px.bar(
        comparison.sort_values("Test_R2", ascending=False),
        x="Model", y="Test_R2", title="Test R² by Model", color="Test_R2",
        color_continuous_scale=[COLOR_ACCENT, COLOR_PRIMARY],
    )
    fig8.update_layout(**PLOTLY_LAYOUT, height=420, coloraxis_showscale=False)
    st.plotly_chart(fig8, width='stretch')

    st.info(
        f"**Final selected model: {meta.get('best_model')}** — chosen for the best held-out "
        f"Test R² while keeping a reasonable train/test gap. Hyperparameter tuning was "
        f"attempted on the top two models (see reports/tuned_model_comparison.csv); it did "
        f"not exceed the baseline configuration on this dataset, so the baseline was kept — "
        f"an honest, real-world outcome rather than a forced improvement."
    )

# ===== PREDICT =====
with tab_predict:
    st.markdown('<div class="section-title"><h3>Predict Crop Yield</h3></div>', unsafe_allow_html=True)
    st.write("Select a state, district, crop, season and year to estimate the expected yield (tonnes / hectare-equivalent).")

    col1, col2, col3 = st.columns(3)
    with col1:
        state_sel = st.selectbox("State", sorted(df["State_Name"].unique()))
        districts = sorted(df.loc[df["State_Name"] == state_sel, "District_Name"].unique())
        district_sel = st.selectbox("District", districts)
    with col2:
        crop_sel = st.selectbox("Crop", sorted(df["Crop"].unique()))
        season_sel = st.selectbox("Season", sorted(df["Season"].unique()))
    with col3:
        year_sel = st.number_input("Crop Year", min_value=1997, max_value=2025, value=2015, step=1)
        area_sel = st.number_input("Cultivated Area (hectares)", min_value=0.1, value=100.0, step=10.0)

    if st.button("🔮 Predict Yield", type="primary"):
        hist = df[
            (df["State_Name"] == state_sel) & (df["District_Name"] == district_sel)
            & (df["Crop"] == crop_sel) & (df["Season"] == season_sel)
        ].sort_values("Crop_Year")

        if len(hist) > 0:
            historical_yield = hist["Yield_Target"].iloc[-1]
            historical_yield_avg3 = hist["Yield_Target"].tail(3).mean()
        else:
            crop_avg = df.loc[df["Crop"] == crop_sel, "Yield_Target"].mean()
            historical_yield = crop_avg if not np.isnan(crop_avg) else df["Yield_Target"].mean()
            historical_yield_avg3 = historical_yield

        input_row = pd.DataFrame([{
            "Area_log": np.log1p(area_sel),
            "Historical_Yield": historical_yield,
            "Historical_Yield_Avg3": historical_yield_avg3,
            "Years_Since_Start": year_sel - int(df["Crop_Year"].min()),
            "State_Name": state_sel,
            "District_Name": district_sel,
            "Crop": crop_sel,
            "Season": season_sel,
        }])

        prediction = model.predict(input_row)[0]

        district_avg = district_rank.loc[
            district_rank["District_Name"] == district_sel, "Avg_Actual_Yield"
        ]
        overall_median = district_rank["Avg_Actual_Yield"].median()
        band = "High" if prediction >= overall_median else "Low"
        band_class = "band-high" if band == "High" else "band-low"

        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(
                f'<div class="metric-card"><div class="label">Predicted Yield</div>'
                f'<div class="value">{prediction:,.2f}</div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(
                f'<div class="metric-card"><div class="label">Historical Yield (last known)</div>'
                f'<div class="value">{historical_yield:,.2f}</div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(
                f'<div class="metric-card"><div class="label">Productivity Band</div>'
                f'<div class="value {band_class}">{band}</div></div>', unsafe_allow_html=True)

        st.caption(
            "Productivity band is relative to the median district-level average yield "
            "observed in the historical data, not an absolute agronomic threshold."
        )

# ===== DISTRICT RANKINGS =====
with tab_districts:
    st.markdown('<div class="section-title"><h3>High- & Low-Productivity Districts</h3></div>', unsafe_allow_html=True)
    top_n = st.slider("Number of districts to show", 5, 30, 10)

    colA, colB = st.columns(2)
    with colA:
        top = district_rank.sort_values("Avg_Actual_Yield", ascending=False).head(top_n)
        fig9 = px.bar(top, x="Avg_Actual_Yield", y="District_Name", orientation="h",
                      title=f"Top {top_n} High-Productivity Districts", color_discrete_sequence=[COLOR_HIGH])
        fig9.update_layout(**PLOTLY_LAYOUT, height=max(380, top_n * 22),
                            yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig9, width='stretch')
    with colB:
        bottom = district_rank.sort_values("Avg_Actual_Yield", ascending=True).head(top_n)
        fig10 = px.bar(bottom, x="Avg_Actual_Yield", y="District_Name", orientation="h",
                       title=f"Bottom {top_n} Low-Productivity Districts", color_discrete_sequence=[COLOR_LOW])
        fig10.update_layout(**PLOTLY_LAYOUT, height=max(380, top_n * 22))
        st.plotly_chart(fig10, width='stretch')

    st.markdown('<div class="section-title"><h3>Full District Ranking Table</h3></div>', unsafe_allow_html=True)
    st.dataframe(
        district_rank.sort_values("Avg_Actual_Yield", ascending=False).style.format(precision=2),
        width='stretch', hide_index=True, height=420,
    )

st.markdown(
    f"""<hr style="border-color:#E5E2D8; margin-top:2rem;">
    <p style="color:{COLOR_MUTED}; font-size:0.85rem;">
    Agricultural Crop-Yield Prediction · ML Capstone Project · Data: District-wise, Season-wise
    Crop Production Statistics, Government of India Open Data Platform.
    </p>""",
    unsafe_allow_html=True,
)
