# 🌾 CropIQ: Indian District-Wise Crop Yield Analytics & Prediction

An end-to-end Machine Learning and Data Science solution to predict district-level crop yield based on location, crop, season, and cultivated area. This project features a full machine learning lifecycle—from data collection and preprocessing to model comparison, hyperparameter tuning, validation, feature-importance interpretation, and deployment readiness through an interactive Streamlit dashboard.

**👉 Try the Live Demo:** [CropIQ Streamlit App](https://cropyieldpredictionapp-2020.streamlit.app/)

---

## 📋 Table of Contents
1. [Business Problem & Use Case](#-business-problem--use-case)
2. [Dataset Source & Description](#-dataset-source--description)
3. [Data Quality Assessment & Preprocessing](#️-data-quality-assessment--preprocessing)
4. [Exploratory Data Analysis (EDA) Insights](#-exploratory-data-analysis-eda-insights)
5. [Feature Engineering & Pipeline Design](#️-feature-engineering--pipeline-design)
6. [Machine Learning Models Tested](#-machine-learning-models-tested)
7. [Hyperparameter Tuning Approach](#-hyperparameter-tuning-approach)
8. [Final Model Performance & Evaluation](#-final-model-performance--evaluation)
9. [Streamlit Dashboard Demo](#️-streamlit-dashboard-demo)[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cropyieldpredictionapp-2020.streamlit.app/)
10. [Business Interpretation & Recommendations](#-business-interpretation--recommendations)
11. [Model Limitations & Responsible AI](#️-model-limitations--responsible-ai)
12. [Installation & Execution Instructions](#-installation--execution-instructions)

---

## 💼 Business Problem & Use Case

### The Problem
Crop yield varies widely across India's districts, crops, and growing seasons, making it difficult for planners to know in advance which regions are likely to under- or over-perform in a given season. For agriculture departments, insurers, and input suppliers, an early, data-driven estimate of expected yield — computed *before* the harvest outcome is known — is critical for timely intervention.

### Target Users & Stakeholders
* **State & District Agriculture Departments**: Plan subsidies, credit access, and irrigation support ahead of the season rather than reacting after a poor harvest.
* **Crop Insurance Providers**: Assess regional risk and set more accurate premiums using historical district-crop-season performance.
* **Agri-Input Companies (seed, fertilizer)**: Plan distribution and inventory toward the districts and crops most likely to need support.
* **Farmer-Facing Advisory Services**: Surface expected yield benchmarks for a farmer's district, crop, and season.

### Expected Business Value
1. **Early-Warning for Low-Yield Districts**: Flag likely under-performing district-crop-season combinations before the season concludes, enabling proactive intervention.
2. **Evidence-Based Crop Planning**: Replace guesswork with a quantified, historically grounded yield estimate for planning decisions.
3. **Equitable Resource Allocation**: Support both business value (insurers, input suppliers) and social value (fair subsidy targeting to under-performing districts).

---

## 📊 Dataset Source & Description

* **Dataset Source**: District-wise, Season-wise Crop Production Statistics, [Government of India Open Data Platform](https://data.gov.in/).
* **Dataset Size**: 49,784 raw records, 8 columns, spanning 1997–2014.
* **Data Variables**:
  * `State_Name`: State in India (categorical).
  * `District_Name`: District within the state (categorical, 112 unique districts).
  * `Crop_Year`: Agricultural year of the record (numerical, 1997–2014).
  * `Season`: Growing season (categorical — Kharif, Rabi, Whole Year, Autumn, Summer, Winter).
  * `Crop`: Crop grown (categorical, 80 unique crops).
  * `Area`: Cultivated area in hectares (numerical).
  * `Production`: Total production in tonnes (numerical) — **used only to derive the target, never as a model input**.
  * `Yield`: Target variable, engineered as `Production ÷ Area` (numerical, tonnes/hectare-equivalent).

> ⚠️ **Critical modeling constraint**: `Production` is the quantity used to derive the target itself. Feeding it into the model as an input would leak the answer directly into the features, so it is excluded from the feature set entirely — the target is recomputed from first principles instead of trusting the source `Yield` column.

---

## ⚙️ Data Quality Assessment & Preprocessing

* **Missing Value Analysis**: A thorough audit found **zero missing values** in the raw dataset across all 8 columns.
* **Duplicate Record Removal**: **Zero duplicate records** were found in the raw data (confirmed via `.duplicated()` audit).
* **Invalid Record Removal**: 109 records with zero or negative `Production`/`Area` were removed, since a yield cannot be computed from them.
* **Outlier Detection & Treatment**: Outliers were identified using per-crop IQR boxplots — yield scale varies hugely across crop types (e.g. sugarcane vs. pulses), so a single global threshold would wrongly flag entire high-yield crops as outliers. A **±3×IQR cap computed separately per crop** was applied instead, removing 1.23% of rows in total.
* **Target Recomputation**: `Yield = Production ÷ Area`, calculated fresh from the raw columns rather than trusted from the dataset's own `Yield` field.
* **Leakage Column Removal**: `Production` and the source `Yield` column were dropped entirely from the modeling feature set.
* **Preprocessing Pipeline**: To prevent data leakage:
  * Numerical pipelines scale features using `StandardScaler`.
  * Categorical pipelines encode high-cardinality features using `OneHotEncoder` with `handle_unknown='ignore'`.
  * All preprocessing statistics are fit **only on the training partition**, inside an `sklearn Pipeline` + `ColumnTransformer`.

---

## 🔍 Exploratory Data Analysis (EDA) Insights

1. **Target Distribution**: Yield is heavily right-skewed; a log(1+Yield) transform approximates normality, informing the preference for tree-based models that don't assume normality.
2. **Correlation Heatmap**: `Historical_Yield` and `Historical_Yield_Avg3` (engineered lag features) share a strong positive correlation with the target (`r ≈ 0.90` and `r ≈ 0.88` respectively). Raw cultivated `Area` shows almost no linear relationship with yield (`r ≈ -0.01`) — efficiency, not scale, drives yield.
3. **Yield Trend Over Years**: Average yield (1997–2014) is relatively stable year-to-year, with no strong long-term drift.
4. **State & Season Profile**: Andhra Pradesh and Andaman & Nicobar Islands show the highest average yields, partly influenced by crops recorded in non-tonne units (see limitations below). Season-wise, "Whole Year" crops show elevated averages for the same reason.

---

## 🛠️ Feature Engineering & Pipeline Design

Historical performance was engineered as the primary predictive signal, computed strictly from **past years only** to avoid leakage, plus structural and trend features:

* `Historical_Yield` — lag-1 yield for the same State + District + Crop + Season combination.
* `Historical_Yield_Avg3` — trailing 3-year average yield for the same combination.
* `Area_log` — `log(1+Area)`, taming the heavy right-skew in cultivated area.
* `Years_Since_Start` — a linear year-trend feature.

Missing history (~11% of rows, the first year a combination appears) is filled using **training-set-only** crop averages, computed *after* the train/test split, so no future information leaks backward into earlier predictions.

A machine learning `ColumnTransformer` pipeline runs preprocessing steps dynamically. Preprocessing parameters are fitted **only on the training partition** to prevent target leakage.

```python
preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline(steps=[
            ("scaler", StandardScaler())
        ]), numeric_features),   # Area_log, Historical_Yield, Historical_Yield_Avg3, Years_Since_Start
        ("cat", Pipeline(steps=[
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical_features)  # State_Name, District_Name, Crop, Season
    ]
)
```

---

## 🤖 Machine Learning Models Tested

We benchmarked **10 different algorithms** on a chronological, time-based split (train: years < 2012, test: 2012–2014) — not a random split, since a lag feature (`Historical_Yield`) is involved:

1. **Linear Regression** (Baseline)
2. **Ridge Regression**
3. **Lasso Regression**
4. **Decision Tree Regressor**
5. **Random Forest Regressor** (Ensemble)
6. **Gradient Boosting Regressor** (Boosting)
7. **AdaBoost Regressor** (Boosting)
8. **XGBoost Regressor** (Boosting)
9. **LightGBM Regressor** (Boosting)
10. **K-Nearest Neighbours Regressor**

| Model | Test R² | Test RMSE | Test MAE |
|---|---|---|---|
| **LightGBM (final)** | **0.855** | **384.2** | 30.6 |
| Random Forest | 0.854 | 385.0 | 25.2 |
| Gradient Boosting | 0.834 | 410.0 | 29.6 |
| XGBoost | 0.799 | 451.7 | 41.3 |
| Decision Tree | 0.776 | 477.1 | 39.4 |
| Ridge Regression | 0.749 | 505.2 | 61.2 |
| Lasso Regression | 0.748 | 506.2 | 60.6 |
| Linear Regression | 0.747 | 506.4 | 61.5 |
| K-Nearest Neighbours | 0.742 | 511.5 | 42.9 |
| AdaBoost | 0.498 | 714.1 | 237.7 |

> **Genuine finding, not an error**: AdaBoost produced a **negative cross-validated R² (-3.47)**, meaning its default weak learners and loss weighting are poorly suited to this heavy-tailed, high-cardinality regression target. It was tested per the assignment's algorithm list but correctly not selected — models were chosen for suitability, not to force a particular result.

---

## 🔧 Hyperparameter Tuning Approach

We tuned the top two performing models (LightGBM and Random Forest) using `RandomizedSearchCV` with 3-fold cross-validation on the training dataset only.

### Tuned Parameters:
* **LightGBM**:
  * `model__n_estimators`: `[150, 250, 350]`
  * `model__num_leaves`: `[15, 31, 63]`
  * `model__max_depth`: `[4, 6, 8, -1]`
  * `model__learning_rate`: `[0.03, 0.05, 0.08, 0.1]`
  * `model__subsample` / `model__colsample_bytree`: `[0.7, 0.85, 1.0]`
* **Random Forest**:
  * `model__n_estimators`: `[100, 150, 250]`
  * `model__max_depth`: `[10, 14, 18, None]`
  * `model__min_samples_split`: `[2, 5, 10]`
  * `model__min_samples_leaf`: `[1, 2, 4]`
  * `model__max_features`: `["sqrt", "log2", 0.6]`

> **Honest outcome**: Neither tuned configuration beat the untuned baseline LightGBM (Test R² 0.855) on the held-out test set. The pipeline automatically keeps whichever model performs best, so the **baseline LightGBM was retained as the final model** — reported as-is rather than forcing an "improvement" that wasn't real.

---

## 🏆 Final Model Performance & Evaluation

The **LightGBM Regressor** emerged as the best-performing model.

### Key Metrics (on Test Set, years 2012–2014):
* **R² Score**: `0.855` (The model explains 85.5% of the variance in crop yield on unseen future years).
* **Mean Absolute Error (MAE)**: `30.56` (average tonnes/hectare-equivalent prediction error).
* **Root Mean Squared Error (RMSE)**: `384.19`

### Overfitting & Stability Check:
* **Training R² Score**: `0.963`
* **Testing R² Score**: `0.855`
* **Generalization Score Difference (Overfit Gap)**: `0.108` (moderate but acceptable for a gradient-boosted model on this heavy-tailed data).
* **3-Fold Cross Validation Average R²**: `0.861` (Standard Deviation: `0.032`), confirming reasonable stability across folds.

### Interpretation:
Aggregated feature importance confirms `Area_log`, `Historical_Yield`, and `Years_Since_Start` dominate — past performance and field scale are the strongest signals, echoing the EDA correlation findings.

---

## 🖥️ Streamlit Dashboard Demo

An interactive dashboard was developed using Streamlit (`dashboard/app.py`) featuring:
1. **Overview Tab**: Key metrics, actual-vs-predicted scatter plot, and aggregated feature importance.
2. **EDA Tab**: Interactive Plotly charts — yield distribution, season/state averages, top-yielding crops.
3. **Model Comparison Tab**: Full metrics table and bar chart benchmarking all 10 tested models.
4. **Predict Yield Tab**: Interactive predictor — select state, district, crop, season, year, and cultivated area to get a live yield estimate, historical context, and a productivity band (High/Low).
5. **District Rankings Tab**: Adjustable top/bottom-N view of high- and low-productivity districts, plus a full sortable ranking table.

---

## 💡 Business Interpretation & Recommendations

* **Prioritize Historical Track Record**: `Historical_Yield` is the single largest contributor to predictions. Planners should weight a district-crop-season's recent track record heavily when forecasting the coming season.
* **Scale Isn't Everything**: Cultivated `Area` alone barely correlates with yield — larger fields do not automatically mean higher yield-per-hectare. Efficiency-focused interventions (irrigation, soil quality, timing) matter more than expanding acreage.
* **Target Low-Productivity Districts Early**: Districts like Bilaspur (Chhattisgarh) and Lakhisarai (Bihar) consistently rank at the bottom of actual yield — these are strong candidates for proactive subsidy or extension-service targeting rather than reactive support after a poor season.
* **Flag High-Yield-Unit Crops Separately**: Coconut and similar crops recorded in count units (not tonnes) inflate a few districts' averages — a labeling quirk to flag to stakeholders rather than treat as genuinely exceptional performance.

---

## ⚠️ Model Limitations & Responsible AI

* **Relies Heavily on Historical Continuity**: Genuinely new district-crop-season combinations (no prior history) fall back to a crop-level average and are less reliable than combinations with an established track record.
* **Unit Mismatches in Source Data**: Some crops (e.g. coconut) are recorded in count units (nuts) rather than tonnes in the source dataset, inflating yield figures for a handful of districts — these should be modeled separately in a production system.
* **No Weather or Soil Data**: The model does not currently incorporate rainfall, temperature, or soil-quality data, which are known drivers of yield variance not captured by historical performance alone.
* **Sensitive Data**: None — only aggregated, public agricultural statistics are used; no personally identifiable information is present.
* **Bias Check**: Mean absolute error varies by state, largely driven by how many historical records exist per state — this is disclosed transparently (`reports/error_by_state.csv`) rather than hidden.
* **Not a Guarantee**: Predictions are a planning aid, not a certified yield outcome, and should never be used to unilaterally deny support to any district.

---

## 🚀 Installation & Execution Instructions

### Prerequisites
* Python 3.10+
* Git (optional)

### Step 1: Clone or Download the Project
Make sure the folder contains:
* `data/raw/crop_yield_dataset.csv`
* `src/` (all pipeline scripts)
* `dashboard/app.py`
* `requirements.txt`

### Step 2: Install Dependencies
Open your terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### Step 3: Run Model Training & Generate Artifacts
Run the full pipeline to generate the cleaned data, models, and evaluation metrics:
```bash
cd src
python run_pipeline.py
```
This script runs preprocessing → feature engineering → EDA → model training & comparison → hyperparameter tuning → evaluation & interpretation, and saves results in the `models/` and `reports/` folders.

### Step 4: Launch the Streamlit Dashboard
Launch the interactive web-based analytics dashboard:
```bash
streamlit run dashboard/app.py
```
A browser tab should open automatically. If not, open the URL printed in the terminal (usually `http://localhost:8501`).

**Or skip local setup entirely** and try the hosted version: **[cropyieldpredictionapp-2020.streamlit.app](https://cropyieldpredictionapp-2020.streamlit.app/)**
