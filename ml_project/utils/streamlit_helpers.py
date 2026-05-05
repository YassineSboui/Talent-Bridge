"""Shared helpers for Streamlit pages."""

import joblib
import json
import os
import io
import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_loader import fetch_jobs
from preprocessing import feature_engineering
import config


def _load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_all_metrics():
    reg = _load_json(config.REG_MODEL_DIR / "metrics.json")
    cls = _load_json(config.CLS_MODEL_DIR / "metrics.json")
    seg = _load_json(config.SEG_MODEL_DIR / "metrics.json")
    return {"regression": reg, "classification": cls, "segmentation": seg}


def load_dataset_from_db(query: str = None):
    try:
        df = fetch_jobs(query=query)
        return feature_engineering(df)
    except Exception as e:
        print(f"DB fetch error: {e}")
        return pd.DataFrame()


def load_model_artifacts(task: str):
    if task == "regression":
        model_dir = config.REG_MODEL_DIR
    elif task == "classification":
        model_dir = config.CLS_MODEL_DIR
    else:
        model_dir = config.SEG_MODEL_DIR

    pipeline_path = model_dir / "pipeline.joblib"
    if not os.path.exists(pipeline_path):
        return None, None, {}

    pipeline = joblib.load(str(pipeline_path))
    metrics = _load_json(model_dir / "metrics.json")

    shap_path = model_dir / "shap_explainer.joblib"
    shap_data = None
    if os.path.exists(shap_path):
        shap_data = joblib.load(str(shap_path))

    return pipeline, shap_data, metrics


def plot_shap_summary(shap_data, max_display: int = 15):
    if shap_data is None:
        return None
    try:
        values = np.array(shap_data["values"])
        feature_names = shap_data["feature_names"]
        fig, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(
            values, features=values, feature_names=feature_names,
            show=False, max_display=max_display, plot_size=None,
        )
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None


def get_sample_predictions(df: pd.DataFrame, task: str, pipeline, n: int = 100) -> pd.DataFrame:
    target_col = {"regression": "salary", "classification": "job_type"}.get(task)

    sample = df.sample(min(n, len(df)), random_state=config.RANDOM_STATE)

    if target_col and target_col in sample.columns:
        X = sample.drop(columns=[target_col], errors="ignore")
        actuals = sample[target_col].values
    else:
        X = sample.copy()
        actuals = None

    preds = pipeline.predict(X)
    result = X.copy()
    result["predicted"] = preds
    if actuals is not None:
        result.insert(0, "actual", actuals)
    return result
