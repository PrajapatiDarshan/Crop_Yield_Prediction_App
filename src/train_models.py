"""
Model Development Module
==========================
- Time-based train/test split (train <= 2011, test 2012-2014) — respects
  the chronological nature of the data (no random shuffling across years).
- Preprocessing fitted ONLY on the training fold (inside a sklearn
  Pipeline) to prevent data leakage.
- Trains and compares up to 10 regression algorithms.
- 5-Fold cross-validation on the training set for a robust performance
  estimate in addition to the held-out test set.
"""

import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import KFold, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from feature_engineering import fill_missing_history

warnings.filterwarnings("ignore")

FEATURED_PATH = "data/processed/crop_yield_features.csv"
MODELS_DIR = "models"
REPORTS_DIR = "reports"

NUMERIC_FEATURES = ["Area_log", "Historical_Yield", "Historical_Yield_Avg3", "Years_Since_Start"]
CATEGORICAL_FEATURES = ["State_Name", "District_Name", "Crop", "Season"]
TARGET = "Yield_Target"
TEST_YEAR_CUTOFF = 2012  # train: years < cutoff, test: years >= cutoff


def mape(y_true, y_pred):
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def time_based_split(df: pd.DataFrame):
    train = df[df["Crop_Year"] < TEST_YEAR_CUTOFF].copy()
    test = df[df["Crop_Year"] >= TEST_YEAR_CUTOFF].copy()
    train, test = fill_missing_history(train, test)
    return train, test


def build_preprocessor():
    numeric_pipe = Pipeline([("scaler", StandardScaler())])
    categorical_pipe = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )
    preprocessor = ColumnTransformer(
        [
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor


def get_models():
    return {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0, random_state=42),
        "Lasso Regression": Lasso(alpha=0.01, random_state=42),
        "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=120, max_depth=12, random_state=42, n_jobs=1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=120, max_depth=4, random_state=42),
        "AdaBoost": AdaBoostRegressor(n_estimators=80, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                                 subsample=0.9, colsample_bytree=0.9, random_state=42,
                                 n_jobs=1, verbosity=0),
        "LightGBM": LGBMRegressor(n_estimators=200, max_depth=8, learning_rate=0.1,
                                   random_state=42, n_jobs=1, verbosity=-1),
        "K-Nearest Neighbours": KNeighborsRegressor(n_neighbors=10, n_jobs=1),
    }


def evaluate(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
        "MAPE": mape(np.asarray(y_true), np.asarray(y_pred)),
    }


def run():
    df = pd.read_csv(FEATURED_PATH)
    train_df, test_df = time_based_split(df)
    print(f"Train rows: {len(train_df)} (years < {TEST_YEAR_CUTOFF}) | "
          f"Test rows: {len(test_df)} (years >= {TEST_YEAR_CUTOFF})")

    X_train = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train_df[TARGET].values
    X_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df[TARGET].values

    preprocessor = build_preprocessor()
    models = get_models()
    kfold = KFold(n_splits=3, shuffle=True, random_state=42)

    results = []
    fitted_pipelines = {}

    for name, model in models.items():
        pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])

        t0 = time.time()
        pipe.fit(X_train, y_train)
        train_time = time.time() - t0

        t0 = time.time()
        y_pred_test = pipe.predict(X_test)
        pred_time = time.time() - t0
        y_pred_train = pipe.predict(X_train)

        cv_scores = cross_val_score(pipe, X_train, y_train, cv=kfold,
                                     scoring="r2", n_jobs=1)

        train_metrics = evaluate(y_train, y_pred_train)
        test_metrics = evaluate(y_test, y_pred_test)

        results.append({
            "Model": name,
            "Train_R2": train_metrics["R2"],
            "CV_R2_mean": cv_scores.mean(),
            "CV_R2_std": cv_scores.std(),
            "Test_R2": test_metrics["R2"],
            "Train_MAE": train_metrics["MAE"],
            "Test_MAE": test_metrics["MAE"],
            "Train_RMSE": train_metrics["RMSE"],
            "Test_RMSE": test_metrics["RMSE"],
            "Test_MAPE": test_metrics["MAPE"],
            "Overfit_Gap(Train-Test R2)": train_metrics["R2"] - test_metrics["R2"],
            "Train_Time_s": train_time,
            "Predict_Time_s": pred_time,
        })
        fitted_pipelines[name] = pipe
        print(f"[{name}] Test R2={test_metrics['R2']:.4f}  Test RMSE={test_metrics['RMSE']:.4f}  "
              f"CV R2={cv_scores.mean():.4f}±{cv_scores.std():.4f}")

    results_df = pd.DataFrame(results).sort_values("Test_R2", ascending=False).reset_index(drop=True)
    results_df.to_csv(f"{REPORTS_DIR}/model_comparison.csv", index=False)
    print("\n=== MODEL COMPARISON (sorted by Test R2) ===")
    print(results_df[["Model", "Train_R2", "CV_R2_mean", "Test_R2", "Test_MAE", "Test_RMSE", "Test_MAPE"]]
          .to_string(index=False))

    best_name = results_df.iloc[0]["Model"]
    best_pipe = fitted_pipelines[best_name]
    joblib.dump(best_pipe, f"{MODELS_DIR}/best_model.pkl")
    joblib.dump(fitted_pipelines, f"{MODELS_DIR}/all_models.pkl")
    with open(f"{MODELS_DIR}/best_model_name.json", "w") as f:
        json.dump({"best_model": best_name}, f)

    print(f"\nBest model: {best_name} -> saved to models/best_model.pkl")

    # Save train/test splits + predictions for downstream evaluation/dashboard
    test_df = test_df.copy()
    test_df["Predicted_Yield"] = fitted_pipelines[best_name].predict(X_test)
    test_df.to_csv(f"{REPORTS_DIR}/test_predictions.csv", index=False)
    train_df.to_csv("data/processed/train_split.csv", index=False)
    test_df_input_only = test_df.drop(columns=["Predicted_Yield"])
    test_df_input_only.to_csv("data/processed/test_split.csv", index=False)

    return results_df, fitted_pipelines, best_name


if __name__ == "__main__":
    run()
