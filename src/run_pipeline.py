"""
Master Pipeline Runner
========================
Runs the full end-to-end pipeline in the correct order:
  1. Preprocessing
  2. Feature Engineering
  3. EDA (figures)
  4. Model Training & Comparison
  5. Hyperparameter Tuning
  6. Evaluation & Interpretation

Usage:
    python src/run_pipeline.py
"""

import sys
import time

sys.path.insert(0, "src")

import preprocessing
import feature_engineering
import eda
import train_models
import hyperparameter_tuning
import evaluate_and_interpret


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    t0 = time.time()

    section("STEP 1/6 — DATA PREPROCESSING")
    preprocessing.run()

    section("STEP 2/6 — FEATURE ENGINEERING")
    feature_engineering.run()

    section("STEP 3/6 — EXPLORATORY DATA ANALYSIS")
    eda.run()

    section("STEP 4/6 — MODEL TRAINING & COMPARISON")
    train_models.run()

    section("STEP 5/6 — HYPERPARAMETER TUNING")
    hyperparameter_tuning.run()

    section("STEP 6/6 — EVALUATION & INTERPRETATION")
    evaluate_and_interpret.run()

    print(f"\nPipeline completed in {time.time() - t0:.1f} seconds.")
    print("Launch the dashboard with: streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
