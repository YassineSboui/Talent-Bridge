import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from utils.streamlit_helpers import load_all_metrics, load_dataset_from_db

st.set_page_config(
    page_title="Job Listings ML Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Job Listings ML Platform")
st.markdown(
    "End-to-end machine learning pipeline for job postings analysis. "
    "Navigate using the sidebar to explore models, dashboards, and predictions."
)

metrics = load_all_metrics()

has_models = metrics["regression"] and metrics["classification"] and metrics["segmentation"]

if has_models:
    st.subheader("Model Performance Overview")
    col1, col2, col3 = st.columns(3)

    with col1:
        reg = metrics["regression"]
        st.metric("Salary Regression — R²", f"{reg.get('r2', 'N/A')}")
        st.metric("RMSE", f"{reg.get('rmse', 'N/A')}")
        st.metric("MAE", f"{reg.get('mae', 'N/A')}")
        st.caption(f"Model: {reg.get('model', 'N/A')}")

    with col2:
        cls_data = metrics["classification"]
        cls_metrics = cls_data.get("metrics", cls_data)
        st.metric("Job Classification — Accuracy", f"{cls_metrics.get('accuracy', 'N/A')}")
        st.caption(f"Model: {cls_metrics.get('model', cls_data.get('model', 'N/A'))}")

    with col3:
        seg = metrics["segmentation"]
        st.metric("Segmentation — Silhouette", f"{seg.get('silhouette_score_test', 'N/A')}")
        st.metric("Clusters", f"{seg.get('n_clusters', 'N/A')}")
        st.caption(f"Model: {seg.get('model', 'N/A')}")
else:
    st.warning(
        "No trained models detected. Run `python train_models.py` first to train and save all models, "
        "or ensure the models directory contains saved pipelines."
    )

st.divider()

st.subheader("Quick Data Preview")
try:
    df = load_dataset_from_db()
    if not df.empty:
        st.dataframe(df.head(20), use_container_width=True)
        st.caption(f"Total rows: {len(df)} | Total columns: {len(df.columns)}")
    else:
        st.info("No data available. Configure your database connection in .env and retry.")
except Exception as e:
    st.info(f"Could not load data preview: {e}")
