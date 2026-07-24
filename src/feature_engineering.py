"""
Feature Engineering Module
===========================
Builds the "Historical_Yield" feature (a lag feature) and other derived
features while strictly avoiding target leakage:
  - Historical_Yield for year Y uses only years < Y for the same
    State + District + Crop + Season combination.
  - Any missing history (first occurrence of a combination) is filled
    using the crop's TRAIN-set average yield only, computed after the
    time-based split so no test information leaks into training.
"""

import pandas as pd
import numpy as np

PROCESSED_PATH = "data/processed/crop_yield_clean.csv"
FEATURED_PATH = "data/processed/crop_yield_features.csv"


def add_historical_yield(df: pd.DataFrame) -> pd.DataFrame:
    """Lag-1 historical yield per State-District-Crop-Season group,
    sorted chronologically so only PAST years inform each row."""
    df = df.sort_values(["State_Name", "District_Name", "Crop", "Season", "Crop_Year"])
    grp_cols = ["State_Name", "District_Name", "Crop", "Season"]
    df["Historical_Yield"] = df.groupby(grp_cols)["Yield_Target"].shift(1)

    # 3-year rolling average of past yields (also lagged, no current-year info)
    df["Historical_Yield_Avg3"] = (
        df.groupby(grp_cols)["Yield_Target"]
        .transform(lambda s: s.shift(1).rolling(window=3, min_periods=1).mean())
    )
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Log-transform of Area (skewed, spans 0.2 to ~800,000)
    df["Area_log"] = np.log1p(df["Area"])
    # Years since dataset start -> captures long-term trend
    df["Years_Since_Start"] = df["Crop_Year"] - df["Crop_Year"].min()
    return df


def fill_missing_history(train: pd.DataFrame, test: pd.DataFrame):
    """Fill missing Historical_Yield / Historical_Yield_Avg3 using
    crop-level average yield computed ONLY on the training split."""
    crop_avg = train.groupby("Crop")["Yield_Target"].mean()
    global_avg = train["Yield_Target"].mean()

    for part in (train, test):
        part["Historical_Yield"] = part["Historical_Yield"].fillna(
            part["Crop"].map(crop_avg)
        ).fillna(global_avg)
        part["Historical_Yield_Avg3"] = part["Historical_Yield_Avg3"].fillna(
            part["Crop"].map(crop_avg)
        ).fillna(global_avg)
    return train, test


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = add_historical_yield(df)
    df = add_derived_features(df)
    return df


def run(save: bool = True) -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH)
    df = build_features(df)
    print("Feature engineering complete.")
    print(f"Rows: {len(df)}, Columns: {list(df.columns)}")
    print(f"Missing Historical_Yield (first-year-in-group rows): "
          f"{df['Historical_Yield'].isnull().sum()} "
          f"({df['Historical_Yield'].isnull().mean():.2%}) -> "
          f"will be filled with train-only crop averages after the split")
    if save:
        df.to_csv(FEATURED_PATH, index=False)
        print(f"Saved -> {FEATURED_PATH}")
    return df


if __name__ == "__main__":
    run()
