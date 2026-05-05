import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from utils.streamlit_helpers import (
    load_model_artifacts,
    load_dataset_from_db,
    get_sample_predictions,
    plot_shap_summary,
)

st.set_page_config(page_title="Job Classifier", page_icon="🏷️", layout="wide")
st.title("Job Classification — Multi-Class")

pipeline, shap_data, metrics = load_model_artifacts("classification")

if pipeline is None:
    st.error("Job classification model not found. Run `python train_models.py` first.")
    st.stop()

cls_data = metrics
cls_metrics = cls_data.get("metrics", cls_data)
st.subheader("Model Performance")
st.metric("Accuracy", f"{cls_metrics.get('accuracy', 'N/A')}")

st.divider()

st.subheader("Prediction Distribution on Test Data")
try:
    df = load_dataset_from_db()
    if not df.empty and "job_type" in df.columns:
        preds_df = get_sample_predictions(df, "classification", pipeline, n=200)

        fig, ax = plt.subplots(figsize=(8, 5))
        vc = preds_df["predicted"].value_counts()
        sns.barplot(x=vc.index, y=vc.values, ax=ax, palette="Set2")
        ax.set_title("Predicted Job Type Distribution")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        st.pyplot(fig)

        st.dataframe(preds_df.head(50), use_container_width=True)

        csv = preds_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Predictions as CSV",
            data=csv,
            file_name="job_classification_predictions.csv",
            mime="text/csv",
        )
except Exception as e:
    st.warning(f"Could not generate sample predictions: {e}")

st.divider()
st.subheader("SHAP Feature Importance")
shap_img = plot_shap_summary(shap_data)
if shap_img:
    st.image(Image.open(shap_img), use_container_width=True)
else:
    st.info("SHAP explainer not available for this model.")
