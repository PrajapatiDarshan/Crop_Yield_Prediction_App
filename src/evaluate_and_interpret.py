"""
Model Evaluation & Interpretation Module
==========================================
- Loads the final best model (models/best_model.pkl)
- Produces: actual-vs-predicted plot, residual/error analysis,
  feature-importance plot, and sample predictions.
- Identifies high- and low-productivity districts.
- Performs a light Responsible-AI / bias check across states.
"""

import json
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")

REPORTS_DIR = "reports"
FIG_DIR = "reports/figures"
MODELS_DIR = "models"


def load_artifacts():
    model = joblib.load(f"{MODELS_DIR}/best_model.pkl")
    with open(f"{MODELS_DIR}/best_model_name.json") as f:
        meta = json.load(f)
    test_pred = pd.read_csv(f"{REPORTS_DIR}/test_predictions.csv")
    return model, meta, test_pred


def plot_actual_vs_predicted(df):
    lim = df["Yield_Target"].quantile(0.97)
    sample = df.sample(min(3000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(sample["Yield_Target"], sample["Predicted_Yield"], alpha=0.35, color="#2E7D32", s=18)
    ax.plot([0, lim], [0, lim], "r--", lw=2, label="Perfect Prediction")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Actual Yield"); ax.set_ylabel("Predicted Yield")
    ax.set_title("Actual vs Predicted Crop Yield (Test Set)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/08_actual_vs_predicted.png", dpi=120)
    plt.close()


def plot_residuals(df):
    df = df.copy()
    df["Residual"] = df["Yield_Target"] - df["Predicted_Yield"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.histplot(df["Residual"].clip(df["Residual"].quantile(0.01), df["Residual"].quantile(0.99)),
                 bins=50, kde=True, ax=axes[0], color="#C62828")
    axes[0].set_title("Residual (Error) Distribution")
    axes[0].axvline(0, color="black", linestyle="--")

    lim = df["Yield_Target"].quantile(0.97)
    sample = df.sample(min(3000, len(df)), random_state=42)
    axes[1].scatter(sample["Predicted_Yield"], sample["Yield_Target"] - sample["Predicted_Yield"],
                     alpha=0.35, s=18, color="#5E35B1")
    axes[1].axhline(0, color="black", linestyle="--")
    axes[1].set_xlim(0, lim)
    axes[1].set_xlabel("Predicted Yield"); axes[1].set_ylabel("Residual")
    axes[1].set_title("Residuals vs Predicted Value")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/09_residual_analysis.png", dpi=120)
    plt.close()
    return df


def plot_feature_importance(model, meta):
    try:
        preprocessor = model.named_steps["preprocessor"]
        estimator = model.named_steps["model"]
        num_features = preprocessor.transformers_[0][2]
        cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
        cat_feature_names = list(cat_encoder.get_feature_names_out(preprocessor.transformers_[1][2]))
        all_features = list(num_features) + cat_feature_names

        importances = estimator.feature_importances_
        imp_df = pd.DataFrame({"Feature": all_features, "Importance": importances})

        # Aggregate one-hot importance back to the original categorical column
        def base_name(f):
            for c in ["State_Name", "District_Name", "Crop", "Season"]:
                if f.startswith(c + "_"):
                    return c
            return f
        imp_df["Base_Feature"] = imp_df["Feature"].apply(base_name)
        agg = imp_df.groupby("Base_Feature")["Importance"].sum().sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(8, 5))
        agg.plot(kind="barh", ax=ax, color="#00695C")
        ax.invert_yaxis()
        ax.set_title(f"Feature Importance — {meta.get('best_model')}")
        ax.set_xlabel("Aggregated Importance")
        plt.tight_layout()
        plt.savefig(f"{FIG_DIR}/10_feature_importance.png", dpi=120)
        plt.close()
        agg.to_csv(f"{REPORTS_DIR}/feature_importance.csv")
        return agg
    except Exception as e:
        print(f"Feature importance skipped: {e}")
        return None


def district_productivity(df):
    """Rank districts by average ACTUAL yield to flag high/low productivity areas."""
    district_stats = (
        df.groupby(["State_Name", "District_Name"])
        .agg(Avg_Actual_Yield=("Yield_Target", "mean"),
             Avg_Predicted_Yield=("Predicted_Yield", "mean"),
             Records=("Yield_Target", "count"))
        .reset_index()
        .sort_values("Avg_Actual_Yield", ascending=False)
    )
    district_stats.to_csv(f"{REPORTS_DIR}/district_productivity_ranking.csv", index=False)

    top10 = district_stats.head(10)
    bottom10 = district_stats.tail(10)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.barplot(data=top10, y="District_Name", x="Avg_Actual_Yield", ax=axes[0], color="#2E7D32")
    axes[0].set_title("Top 10 High-Productivity Districts")
    sns.barplot(data=bottom10, y="District_Name", x="Avg_Actual_Yield", ax=axes[1], color="#C62828")
    axes[1].set_title("Bottom 10 Low-Productivity Districts")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/11_district_productivity.png", dpi=120)
    plt.close()
    return district_stats


def responsible_ai_check(df):
    """Simple fairness check: does prediction error vary a lot by state?"""
    df = df.copy()
    df["Abs_Error"] = (df["Yield_Target"] - df["Predicted_Yield"]).abs()
    state_error = df.groupby("State_Name")["Abs_Error"].mean().sort_values(ascending=False)
    state_error.to_csv(f"{REPORTS_DIR}/error_by_state.csv")
    print("\n=== MEAN ABSOLUTE ERROR BY STATE (fairness / bias check) ===")
    print(state_error)
    return state_error


def sample_predictions(df, n=15):
    sample = df.sample(n, random_state=7)[
        ["State_Name", "District_Name", "Crop", "Season", "Crop_Year",
         "Area", "Yield_Target", "Predicted_Yield"]
    ].round(2)
    sample.to_csv(f"{REPORTS_DIR}/sample_predictions.csv", index=False)
    print("\n=== SAMPLE PREDICTIONS ===")
    print(sample.to_string(index=False))
    return sample


def run():
    model, meta, test_pred = load_artifacts()
    print(f"Final model in use: {meta.get('best_model')}")

    plot_actual_vs_predicted(test_pred)
    test_pred_with_res = plot_residuals(test_pred)
    plot_feature_importance(model, meta)
    district_stats = district_productivity(test_pred)
    responsible_ai_check(test_pred)
    sample_predictions(test_pred)

    print("\n=== TOP 5 HIGH-PRODUCTIVITY DISTRICTS ===")
    print(district_stats.head(5).to_string(index=False))
    print("\n=== BOTTOM 5 LOW-PRODUCTIVITY DISTRICTS ===")
    print(district_stats.tail(5).to_string(index=False))
    print("\nAll evaluation figures & tables saved to reports/")


if __name__ == "__main__":
    run()
