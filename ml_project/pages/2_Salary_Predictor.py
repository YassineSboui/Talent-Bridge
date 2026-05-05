import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from PIL import Image
from utils.streamlit_helpers import (
    load_model_artifacts,
    load_dataset_from_db,
    get_sample_predictions,
    plot_shap_summary,
)

st.set_page_config(page_title="Salary Predictor", page_icon="💰", layout="wide")
st.title("Salary Prediction — Regression")

pipeline, shap_data, metrics = load_model_artifacts("regression")

if pipeline is None:
    st.error("Salary regression model not found. Run `python train_models.py` first.")
    st.stop()

reg_metrics = metrics
st.subheader("Model Performance")
c1, c2, c3 = st.columns(3)
c1.metric("RMSE", f"${reg_metrics.get('rmse', 'N/A'):,.2f}")
c2.metric("R² Score", f"{reg_metrics.get('r2', 'N/A')}")
c3.metric("MAE", f"${reg_metrics.get('mae', 'N/A'):,.2f}")

st.divider()

st.subheader("Sample Predictions on Test Data")
try:
    df = load_dataset_from_db()
    if not df.empty and "salary" in df.columns:
        preds_df = get_sample_predictions(df, "regression", pipeline, n=200)
        st.dataframe(preds_df.head(50), use_container_width=True)

        csv = preds_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Predictions as CSV",
            data=csv,
            file_name="salary_predictions.csv",
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
