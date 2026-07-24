"""
Hyperparameter Tuning Module
=============================
Tunes the two strongest models from the initial comparison (LightGBM and
Random Forest) using RandomizedSearchCV. Tuning is performed only on the
TRAINING split (via cross-validation) — the held-out test set (2012-2014)
is never touched during search, avoiding leakage into hyperparameter
selection.
"""

import json
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import RandomizedSearchCV, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from lightgbm import LGBMRegressor

from feature_engineering import fill_missing_history
from train_models import (
    NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET, TEST_YEAR_CUTOFF, mape
)

warnings.filterwarnings("ignore")

FEATURED_PATH = "data/processed/crop_yield_features.csv"
MODELS_DIR = "models"
REPORTS_DIR = "reports"


def build_preprocessor():
    numeric_pipe = Pipeline([("scaler", StandardScaler())])
    categorical_pipe = Pipeline([("onehot", OneHotEncoder(handle_unknown="ignore"))])
    return ColumnTransformer([
        ("num", numeric_pipe, NUMERIC_FEATURES),
        ("cat", categorical_pipe, CATEGORICAL_FEATURES),
    ])


def evaluate(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
        "MAPE": mape(np.asarray(y_true), np.asarray(y_pred)),
    }


def run():
    df = pd.read_csv(FEATURED_PATH)
    train_df = df[df["Crop_Year"] < TEST_YEAR_CUTOFF].copy()
    test_df = df[df["Crop_Year"] >= TEST_YEAR_CUTOFF].copy()
    train_df, test_df = fill_missing_history(train_df, test_df)

    X_train = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train_df[TARGET].values
    X_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df[TARGET].values

    kfold = KFold(n_splits=3, shuffle=True, random_state=42)
    tuning_results = {}
    tuned_pipelines = {}

    # ---------------- LightGBM ----------------
    lgbm_space = {
        "model__n_estimators": [150, 250, 350],
        "model__num_leaves": [15, 31, 63],
        "model__max_depth": [4, 6, 8, -1],
        "model__learning_rate": [0.03, 0.05, 0.08, 0.1],
        "model__subsample": [0.7, 0.85, 1.0],
        "model__colsample_bytree": [0.7, 0.85, 1.0],
    }
    lgbm_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", LGBMRegressor(random_state=42, n_jobs=1, verbosity=-1)),
    ])
    lgbm_search = RandomizedSearchCV(
        lgbm_pipe, lgbm_space, n_iter=12, cv=kfold, scoring="r2",
        random_state=42, n_jobs=1, verbose=1,
    )
    print("Tuning LightGBM ...")
    lgbm_search.fit(X_train, y_train)
    tuning_results["LightGBM (Tuned)"] = lgbm_search.best_params_
    tuned_pipelines["LightGBM (Tuned)"] = lgbm_search.best_estimator_
    print("Best LightGBM params:", lgbm_search.best_params_)

    # ---------------- Random Forest ----------------
    rf_space = {
        "model__n_estimators": [100, 150, 250],
        "model__max_depth": [10, 14, 18, None],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2, 4],
        "model__max_features": ["sqrt", "log2", 0.6],
    }
    rf_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", RandomForestRegressor(random_state=42, n_jobs=1)),
    ])
    rf_search = RandomizedSearchCV(
        rf_pipe, rf_space, n_iter=8, cv=kfold, scoring="r2",
        random_state=42, n_jobs=1, verbose=1,
    )
    print("Tuning Random Forest ...")
    rf_search.fit(X_train, y_train)
    tuning_results["Random Forest (Tuned)"] = rf_search.best_params_
    tuned_pipelines["Random Forest (Tuned)"] = rf_search.best_estimator_
    print("Best RF params:", rf_search.best_params_)

    # ---------------- Evaluate tuned models on held-out test set ----------------
    rows = []
    for name, pipe in tuned_pipelines.items():
        y_pred_train = pipe.predict(X_train)
        y_pred_test = pipe.predict(X_test)
        train_m = evaluate(y_train, y_pred_train)
        test_m = evaluate(y_test, y_pred_test)
        rows.append({
            "Model": name, "Train_R2": train_m["R2"], "Test_R2": test_m["R2"],
            "Test_MAE": test_m["MAE"], "Test_RMSE": test_m["RMSE"], "Test_MAPE": test_m["MAPE"],
            "Overfit_Gap": train_m["R2"] - test_m["R2"],
        })
        print(f"[{name}] Test R2={test_m['R2']:.4f}  Test RMSE={test_m['RMSE']:.4f}")

    tuned_df = pd.DataFrame(rows).sort_values("Test_R2", ascending=False)
    tuned_df.to_csv(f"{REPORTS_DIR}/tuned_model_comparison.csv", index=False)

    best_name = tuned_df.iloc[0]["Model"]
    best_pipe = tuned_pipelines[best_name]

    # Compare against the untuned baseline comparison saved earlier
    baseline_df = pd.read_csv(f"{REPORTS_DIR}/model_comparison.csv")
    baseline_best_r2 = baseline_df["Test_R2"].max()
    tuned_best_r2 = tuned_df["Test_R2"].max()

    print(f"\nBaseline best Test R2: {baseline_best_r2:.4f}")
    print(f"Tuned best Test R2:    {tuned_best_r2:.4f}")

    if tuned_best_r2 >= baseline_best_r2:
        joblib.dump(best_pipe, f"{MODELS_DIR}/best_model.pkl")
        with open(f"{MODELS_DIR}/best_model_name.json", "w") as f:
            json.dump({"best_model": best_name, "tuned": True}, f)
        print(f"Tuned model '{best_name}' improved performance -> saved as final best_model.pkl")
        test_df = test_df.copy()
        test_df["Predicted_Yield"] = best_pipe.predict(X_test)
        test_df.to_csv(f"{REPORTS_DIR}/test_predictions.csv", index=False)
    else:
        print("Tuning did not beat the baseline best model; keeping baseline as final model.")

    with open(f"{MODELS_DIR}/tuning_params.json", "w") as f:
        json.dump(tuning_results, f, indent=2, default=str)

    return tuned_df


if __name__ == "__main__":
    run()
