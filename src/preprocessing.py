"""
Data Preprocessing Module
==========================
Agricultural Crop-Yield Prediction Capstone

Handles: missing values, duplicates, data-type correction, outlier
treatment, target creation (Yield = Production / Area) and removal of
leakage-prone columns (Production is NEVER used as a model input since
it is used to derive the target).
"""

import pandas as pd
import numpy as np

RAW_PATH = "data/raw/crop_yield_dataset.csv"
PROCESSED_PATH = "data/processed/crop_yield_clean.csv"


def load_raw_data(path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def basic_quality_report(df: pd.DataFrame) -> dict:
    report = {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "n_states": df["State_Name"].nunique(),
        "n_districts": df["District_Name"].nunique(),
        "n_crops": df["Crop"].nunique(),
        "year_range": (int(df["Crop_Year"].min()), int(df["Crop_Year"].max())),
    }
    return report


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply data-quality treatment steps and recompute the target."""
    df = df.copy()

    # ---- 1. Data type correction -------------------------------------
    df["Crop_Year"] = df["Crop_Year"].astype(int)
    for col in ["State_Name", "District_Name", "Season", "Crop"]:
        df[col] = df[col].astype(str).str.strip()

    # ---- 2. Duplicate removal -----------------------------------------
    before = len(df)
    df = df.drop_duplicates()
    dup_removed = before - len(df)

    # ---- 3. Missing value treatment ------------------------------------
    # Drop rows lacking essential numeric fields (Area / Production)
    df = df.dropna(subset=["Area", "Production"])
    # Any remaining missing categorical values -> "Unknown"
    for col in ["State_Name", "District_Name", "Season", "Crop"]:
        df[col] = df[col].fillna("Unknown")

    # ---- 4. Invalid / impossible records --------------------------------
    # Area must be strictly positive to compute yield
    df = df[df["Area"] > 0]
    # Production cannot be negative
    df = df[df["Production"] >= 0]

    # ---- 5. Recompute the TARGET from first principles ------------------
    # Yield = Production / Area   (business definition given in the brief)
    df["Yield_calc"] = df["Production"] / df["Area"]

    # ---- 6. Outlier detection & treatment --------------------------------
    # Crop yield scale differs hugely by crop (e.g. sugarcane vs pulses),
    # so outliers are treated PER CROP using the IQR rule -> caps extreme
    # data-entry errors (e.g. unit mismatches) without erasing genuine
    # high-yield crops.
    q1 = df.groupby("Crop")["Yield_calc"].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby("Crop")["Yield_calc"].transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    lower = (q1 - 3 * iqr).clip(lower=0)
    upper = q3 + 3 * iqr
    df = df[(df["Yield_calc"] >= lower) & (df["Yield_calc"] <= upper)]

    # ---- 7. Drop leakage-prone / irrelevant columns ----------------------
    # 'Production' and the dataset's original 'Yield' column are DROPPED
    # from the feature set because Production is used to derive the
    # target itself (Production as an input would leak the answer).
    df = df.rename(columns={"Yield_calc": "Yield_Target"})
    df = df.drop(columns=["Production", "Yield"], errors="ignore")

    df = df.reset_index(drop=True)
    return df, dup_removed


def run(save: bool = True) -> pd.DataFrame:
    df_raw = load_raw_data()
    report = basic_quality_report(df_raw)
    df_clean, dup_removed = clean_data(df_raw)

    print("=== RAW DATA QUALITY REPORT ===")
    for k, v in report.items():
        print(f"{k}: {v}")
    print(f"\nDuplicates removed: {dup_removed}")
    print(f"Rows after cleaning & outlier treatment: {len(df_clean)} "
          f"({len(df_raw) - len(df_clean)} rows removed, "
          f"{(len(df_raw) - len(df_clean)) / len(df_raw):.2%})")

    if save:
        df_clean.to_csv(PROCESSED_PATH, index=False)
        print(f"\nSaved cleaned dataset -> {PROCESSED_PATH}")

    return df_clean


if __name__ == "__main__":
    run()
