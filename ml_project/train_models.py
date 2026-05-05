import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import json
from data_loader import fetch_jobs
from models.train_regression import train_salary_regression
from models.train_classification import train_job_classification
from models.train_segmentation import train_job_segmentation
import config


def main():
    print("=" * 60)
    print("  Job Listings ML Pipeline — Training")
    print("=" * 60)

    print("\n[Step 1] Fetching data from SQL Server...")
    try:
        df = fetch_jobs()
    except Exception as e:
        print(f"  ERROR: Failed to fetch data — {e}")
        print("  Fix: Ensure .env is configured with correct DB credentials.")
        return

    print(f"  Loaded {len(df):,} rows, {df.shape[1]} columns.")
    print(f"  Columns: {list(df.columns)}")

    print("\n[Step 2] Training Salary Regression model...")
    reg_result = train_salary_regression(df)
    print(f"  RMSE:  {reg_result['metrics']['rmse']}")
    print(f"  R²:    {reg_result['metrics']['r2']}")
    print(f"  MAE:   {reg_result['metrics']['mae']}")

    print("\n[Step 3] Training Job Classification model...")
    cls_result = train_job_classification(df)
    print(f"  Accuracy: {cls_result['metrics']['accuracy']}")

    print("\n[Step 4] Training Job Segmentation model...")
    seg_result = train_job_segmentation(df)
    print(f"  Silhouette (test): {seg_result['metrics']['silhouette_score_test']}")
    print(f"  Clusters:          {seg_result['metrics']['n_clusters']}")

    summary = {
        "regression": reg_result["metrics"],
        "classification": cls_result["metrics"],
        "segmentation": seg_result["metrics"],
    }
    summary_path = config.MODELS_DIR / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("  All models trained and saved successfully!")
    print(f"  Models: {config.MODELS_DIR}")
    print(f"  Summary: {summary_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
