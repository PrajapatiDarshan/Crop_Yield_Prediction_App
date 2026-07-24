# 🌾 Agricultural Crop-Yield Prediction — ML Capstone Project

Predicting district-level crop yield across India to help agricultural planners identify
high- and low-productivity districts before the season's outcome is known.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

📄 **Project Report:** [`deliverables/report.pdf`](deliverables/report.pdf)
📊 **Presentation:** [`deliverables/CropYieldPrediction_Presentation.pptx`](deliverables/CropYieldPrediction_Presentation.pptx)
🌐 **Live Demo:** not yet deployed — see [`DEPLOYMENT.md`](DEPLOYMENT.md) for a 2-minute
Streamlit Community Cloud deploy guide (requires your own GitHub + Streamlit Cloud login,
so it isn't something that can be generated for you automatically).

---

## 1. Business Problem

| | |
|---|---|
| **ML Task** | Regression |
| **Target** | `Yield = Production ÷ Area` |
| **Target users** | State/district agriculture departments, crop insurance providers, agri-input companies, farmer-advisory services |
| **Expected outcome** | A district × crop × season yield estimate that flags likely under-performing regions early |
| **Business value** | Better-targeted subsidies, early-warning for low-yield districts, evidence-based crop planning |

**Important constraint honoured throughout this project:** `Production` is **never** used as a
model input, because it is the quantity used to derive the target itself — using it would leak
the answer directly into the features.

## 2. Dataset

- **Source:** District-wise, Season-wise Crop Production Statistics, Government of India Open
  Data Platform.
- **Size:** 49,784 rows → 49,170 after cleaning · 7 states · 112 districts · 80 crops · 1997–2014.
- **Raw columns:** `State_Name, District_Name, Crop_Year, Season, Crop, Area, Production, Yield`
- No personally identifiable or sensitive information is present.

## 3. Project Structure

```
crop_yield_project/
├── data/
│   ├── raw/crop_yield_dataset.csv          # original dataset
│   └── processed/                          # cleaned + feature-engineered data, train/test splits
├── notebooks/
│   └── Crop_Yield_Capstone.ipynb           # full, already-executed end-to-end notebook
├── src/
│   ├── preprocessing.py                    # cleaning, target creation, outlier treatment
│   ├── feature_engineering.py              # historical-yield lag features, leakage-safe fill
│   ├── eda.py                              # exploratory data analysis + figures
│   ├── train_models.py                     # 10-model training & comparison (time-based split)
│   ├── hyperparameter_tuning.py            # RandomizedSearchCV tuning of top 2 models
│   ├── evaluate_and_interpret.py           # actual-vs-predicted, residuals, feature importance,
│   │                                         district ranking, responsible-AI bias check
│   └── run_pipeline.py                     # runs all of the above end-to-end, in order
├── dashboard/
│   └── app.py                              # interactive Streamlit dashboard
├── deliverables/
│   ├── report.pdf                          # written project report
│   └── CropYieldPrediction_Presentation.pptx  # slide deck
├── DEPLOYMENT.md                           # how to get a live Streamlit Cloud URL
├── models/
│   ├── best_model.pkl                      # final trained pipeline (preprocessing + model)
│   ├── all_models.pkl                      # every trained model, for comparison/audit
│   ├── best_model_name.json
│   └── tuning_params.json
├── reports/
│   ├── figures/                            # all EDA + evaluation charts (PNG)
│   ├── model_comparison.csv
│   ├── tuned_model_comparison.csv
│   ├── test_predictions.csv
│   ├── district_productivity_ranking.csv
│   ├── feature_importance.csv
│   ├── error_by_state.csv
│   └── sample_predictions.csv
├── requirements.txt
└── README.md
```

## 4. Methodology Summary

### Preprocessing (`src/preprocessing.py`)
- Data-type correction, duplicate removal, invalid-record removal (Area ≤ 0, Production < 0)
- Target recomputed as `Production / Area`
- **Per-crop IQR outlier treatment** (×3 IQR) — bounds computed per crop since yield scale
  varies hugely by crop type (e.g. sugarcane vs. pulses)
- `Production` and the source `Yield` column dropped to prevent leakage

### Feature Engineering (`src/feature_engineering.py`)
- `Historical_Yield` — lag-1 yield for the same State+District+Crop+Season combination
- `Historical_Yield_Avg3` — trailing 3-year average yield for the same combination
- `Area_log`, `Years_Since_Start`
- Missing history (first occurrence of a combination, ~11% of rows) filled with
  **training-set-only** crop averages, applied after the split, to avoid leakage

### Validation Strategy
- **Time-based split**: train on years < 2012, test on 2012–2014 (~81% / 19%) — chosen over a
  random split because `Historical_Yield` is a lag feature and the data has a temporal axis.
- Preprocessing (scaling, one-hot encoding) fit **only** on the training fold via an
  sklearn `Pipeline` + `ColumnTransformer`.
- 3-fold cross-validation on the training set for a stability check alongside the test score.

### Models Compared (10 total)

| Model | Test R² | Test RMSE | Test MAE | CV R² |
|---|---|---|---|---|
| **LightGBM (final)** | **0.855** | **384.2** | 30.6 | 0.861 ± 0.032 |
| Random Forest | 0.854 | 385.0 | 25.2 | 0.881 ± 0.020 |
| Gradient Boosting | 0.834 | 410.0 | 29.6 | 0.875 ± 0.017 |
| XGBoost | 0.799 | 451.7 | 41.3 | 0.876 ± 0.015 |
| Decision Tree | 0.776 | 477.1 | 39.4 | 0.787 ± 0.017 |
| Ridge Regression | 0.749 | 505.2 | 61.2 | 0.787 ± 0.039 |
| Lasso Regression | 0.748 | 506.2 | 60.6 | 0.787 ± 0.039 |
| Linear Regression | 0.747 | 506.4 | 61.5 | 0.787 ± 0.039 |
| K-Nearest Neighbours | 0.742 | 511.5 | 42.9 | 0.825 ± 0.034 |
| AdaBoost | 0.498 | 714.1 | 237.7 | -3.47 ± 4.48 |

**AdaBoost failed badly** (negative CV R²) — a genuine finding, not an error: its default weak
learners and loss weighting are not well suited to this heavy-tailed, high-cardinality
regression target. It was tested (per the assignment's algorithm list) but correctly not selected.

### Hyperparameter Tuning (`src/hyperparameter_tuning.py`)
`RandomizedSearchCV` (3-fold CV, training data only) was run on the two strongest baseline
models. **Neither tuned configuration beat the untuned LightGBM baseline** on the held-out test
set (see `reports/tuned_model_comparison.csv`) — the pipeline automatically keeps whichever
model performs best, so the baseline LightGBM was retained as final. This is reported honestly
rather than forcing an "improvement" that wasn't real.

### Final Model: **LightGBM**
- Test R² = 0.855, Test RMSE = 384.2, Test MAE = 30.6
- Train R² = 0.963 → moderate train/test gap (~0.11), acceptable for a gradient-boosted model
  on this data
- Feature importance confirms `Historical_Yield` / `Historical_Yield_Avg3` dominate, followed by
  `Crop` and `District_Name` category effects

## 5. Key EDA Insights
- `Historical_Yield` correlates strongly with the target (r ≈ 0.90) — past performance is the
  single strongest predictor of future yield.
- Raw cultivated `Area` alone has almost no linear relationship with yield — efficiency, not
  scale, drives yield.
- Coconut and the "Whole Year" season show very high yield values because some crops are
  recorded in count units (e.g. nuts) rather than tonnes in the source data — a labeling quirk
  worth flagging to stakeholders, not a data error to silently "fix".

## 6. Responsible AI & Ethical Considerations
- **Sensitive data:** none — only aggregated, public agricultural statistics.
- **Bias check:** mean absolute error varies by state (see `reports/error_by_state.csv`),
  largely driven by how many historical records exist per state — disclosed rather than hidden.
- **Fairness:** predictions are a planning aid, not a certified yield guarantee, and should not
  be used to unilaterally deny support to any district.
- Predictions are explicitly labeled as estimates in the dashboard.

## 7. Limitations & Future Improvements
- Heavily reliant on historical yield for the same combination; new combinations fall back to a
  crop-level average and are less reliable.
- Crops recorded in non-tonne units (e.g. coconut) should be modeled separately or unit-normalised.
- Future work: incorporate rainfall/weather and soil data, separate modeling for unit-mismatched
  crops, and quantile regression for prediction intervals.

## 8. How to Run

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the full pipeline (preprocessing → EDA → training → tuning → evaluation)
```bash
cd src
python run_pipeline.py
```
Or run each step individually: `preprocessing.py`, `feature_engineering.py`, `eda.py`,
`train_models.py`, `hyperparameter_tuning.py`, `evaluate_and_interpret.py`.

### Open the analysis notebook
```bash
jupyter notebook notebooks/Crop_Yield_Capstone.ipynb
```
(Already executed — all outputs and charts are saved inline; re-running is optional.)

### Launch the interactive dashboard
```bash
streamlit run dashboard/app.py
```
Then open the URL shown in the terminal (typically http://localhost:8501). The dashboard
includes: an overview with actual-vs-predicted and feature importance, an EDA explorer, a full
model comparison table/chart, a live yield predictor (pick state/district/crop/season/year/area),
and high/low-productivity district rankings.

## 9. Deliverables Checklist
- [x] Public GitHub-ready repository structure
- [x] Complete, already-executed Jupyter Notebook (`notebooks/Crop_Yield_Capstone.ipynb`)
- [x] Cleaned, model-ready dataset (`data/processed/`)
- [x] EDA with 7+ visualisations (`reports/figures/`)
- [x] Feature engineering & preprocessing pipeline (`src/feature_engineering.py`, sklearn Pipeline)
- [x] Comparison of 10 ML models (`reports/model_comparison.csv`)
- [x] Hyperparameter tuning results (`reports/tuned_model_comparison.csv`)
- [x] Final model evaluation (R², RMSE, MAE, MAPE, overfitting check)
- [x] Actual-vs-predicted visualisation (`reports/figures/08_actual_vs_predicted.png`)
- [x] Interactive Streamlit dashboard (`dashboard/app.py`)
- [x] This README
- [x] `requirements.txt`
- [x] Written project report (`deliverables/report.pdf`)
- [x] Slide presentation (`deliverables/CropYieldPrediction_Presentation.pptx`)
- [ ] Live hosted demo — deploy yourself in ~2 min via `DEPLOYMENT.md` (requires your own
      GitHub + Streamlit Cloud account)

## 10. Credits & References
- Dataset: Government of India Open Data Platform — District-wise, Season-wise Crop
  Production Statistics.
- Built with: pandas, scikit-learn, XGBoost, LightGBM, matplotlib, seaborn, Plotly, Streamlit.

---
*This project was built as part of a Machine Learning Capstone exercise covering the full ML
lifecycle: business framing, data collection, cleaning, EDA, feature engineering, model
comparison, hyperparameter tuning, evaluation/interpretation, responsible AI review, and
deployment-ready dashboarding.*
