"""
Exploratory Data Analysis Module
=================================
Generates descriptive statistics and saves visualisations (matplotlib /
seaborn) to reports/figures/. Prints business-oriented observations to
the console / notebook.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
FEATURED_PATH = "data/processed/crop_yield_features.csv"
FIG_DIR = "reports/figures"


def load():
    return pd.read_csv(FEATURED_PATH)


def descriptive_stats(df: pd.DataFrame):
    print("=== DESCRIPTIVE STATISTICS (Yield_Target) ===")
    print(df["Yield_Target"].describe())
    print("\n=== TOP 10 STATES BY AVERAGE YIELD ===")
    print(df.groupby("State_Name")["Yield_Target"].mean().sort_values(ascending=False).head(10))
    print("\n=== TOP 10 CROPS BY AVERAGE YIELD ===")
    print(df.groupby("Crop")["Yield_Target"].mean().sort_values(ascending=False).head(10))
    print("\n=== SEASON-WISE AVERAGE YIELD ===")
    print(df.groupby("Season")["Yield_Target"].mean().sort_values(ascending=False))


def plot_distribution(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.histplot(df["Yield_Target"], bins=60, kde=True, ax=axes[0], color="#2E7D32")
    axes[0].set_title("Distribution of Crop Yield")
    axes[0].set_xlabel("Yield (tonnes/hectare)")

    sns.histplot(np.log1p(df["Yield_Target"]), bins=60, kde=True, ax=axes[1], color="#1565C0")
    axes[1].set_title("Distribution of log(1+Yield)")
    axes[1].set_xlabel("log(1+Yield)")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/01_yield_distribution.png", dpi=120)
    plt.close()


def plot_boxplots(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x="Season", y="Yield_Target", ax=ax, palette="viridis")
    ax.set_title("Yield Distribution by Season (outlier check)")
    ax.set_ylim(0, df["Yield_Target"].quantile(0.97))
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/02_yield_by_season_boxplot.png", dpi=120)
    plt.close()


def plot_correlation(df):
    num_cols = ["Yield_Target", "Area", "Area_log", "Historical_Yield",
                "Historical_Yield_Avg3", "Crop_Year", "Years_Since_Start"]
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0, ax=ax)
    ax.set_title("Correlation Heatmap (numeric features)")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/03_correlation_heatmap.png", dpi=120)
    plt.close()
    return corr


def plot_bivariate(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sample = df.sample(min(4000, len(df)), random_state=42)
    sns.scatterplot(data=sample, x="Area_log", y="Yield_Target", alpha=0.4, ax=axes[0], color="#EF6C00")
    axes[0].set_ylim(0, df["Yield_Target"].quantile(0.97))
    axes[0].set_title("Area (log) vs Yield")

    sns.scatterplot(data=sample, x="Historical_Yield", y="Yield_Target", alpha=0.4, ax=axes[1], color="#6A1B9A")
    lim = df["Yield_Target"].quantile(0.97)
    axes[1].set_xlim(0, lim); axes[1].set_ylim(0, lim)
    axes[1].set_title("Historical Yield vs Current Yield")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/04_bivariate_scatter.png", dpi=120)
    plt.close()


def plot_trend(df):
    trend = df.groupby("Crop_Year")["Yield_Target"].mean()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    trend.plot(marker="o", ax=ax, color="#2E7D32")
    ax.set_title("Average Crop Yield Trend Over Years (1997-2014)")
    ax.set_ylabel("Average Yield")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/05_yield_trend_over_years.png", dpi=120)
    plt.close()


def plot_state_bar(df):
    state_avg = df.groupby("State_Name")["Yield_Target"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    state_avg.plot(kind="bar", ax=ax, color="#1565C0")
    ax.set_title("Average Yield by State")
    ax.set_ylabel("Average Yield")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/06_avg_yield_by_state.png", dpi=120)
    plt.close()


def plot_pairplot(df):
    sample = df.sample(min(1500, len(df)), random_state=42)
    cols = ["Yield_Target", "Area_log", "Historical_Yield", "Years_Since_Start"]
    g = sns.pairplot(sample[cols], diag_kind="kde", plot_kws={"alpha": 0.4, "s": 15})
    g.fig.suptitle("Pair Plot of Key Numeric Features", y=1.02)
    g.savefig(f"{FIG_DIR}/07_pairplot.png", dpi=110)
    plt.close()


def run():
    df = load()
    descriptive_stats(df)
    plot_distribution(df)
    plot_boxplots(df)
    corr = plot_correlation(df)
    plot_bivariate(df)
    plot_trend(df)
    plot_state_bar(df)
    plot_pairplot(df)
    print("\nAll EDA figures saved to reports/figures/")
    print("\nKey correlation with target:\n", corr["Yield_Target"].sort_values(ascending=False))


if __name__ == "__main__":
    run()
