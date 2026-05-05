import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from preprocessing import feature_engineering
from utils.streamlit_helpers import load_model_artifacts, load_dataset_from_db

st.set_page_config(page_title="Try It Yourself", page_icon="🧪", layout="wide")
st.title("Try It Yourself — Real-Time Predictions")

reg_pipeline, _, reg_metrics = load_model_artifacts("regression")
cls_pipeline, _, cls_metrics = load_model_artifacts("classification")

if reg_pipeline is None and cls_pipeline is None:
    st.error("No models found. Run `python train_models.py` first.")
    st.stop()

st.sidebar.header("Job Details")

title = st.sidebar.text_input("Job Title", value="Data Scientist")
location = st.sidebar.text_input("Location", value="Remote")
experience_input = st.sidebar.text_input("Experience", value="3-5 years")
skills = st.sidebar.text_area("Skills (comma-separated)", value="Python, SQL, Machine Learning, AWS")
remote = st.sidebar.selectbox("Remote?", ["Yes", "No"])
job_type_input = st.sidebar.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Remote", "Internship"])

submit = st.sidebar.button("Predict", type="primary")

if not submit:
    st.info("Fill in the job details and click **Predict** to see results.")
    st.stop()

try:
    db_df = load_dataset_from_db()
    if db_df.empty:
        st.error("Could not load data from database. Check your connection.")
        st.stop()

    input_df = pd.DataFrame({
        "title": [title],
        "location": [location],
        "experience": [experience_input],
        "skills": [skills],
        "remote": [1 if remote == "Yes" else 0],
        "job_type": [job_type_input],
    })

    for col in db_df.columns:
        if col not in input_df.columns:
            input_df[col] = np.nan

    eng_df = feature_engineering(input_df)

    sal_pred = None
    job_pred = None

    st.subheader("Results")
    col1, col2 = st.columns(2)

    if reg_pipeline is not None:
        X_reg = eng_df.drop(columns=["salary"], errors="ignore")
        sal_pred = reg_pipeline.predict(X_reg)[0]
        with col1:
            st.metric("Predicted Annual Salary", f"${sal_pred:,.0f}")

    if cls_pipeline is not None:
        X_cls = eng_df.drop(columns=["job_type"], errors="ignore")
        job_pred = cls_pipeline.predict(X_cls)[0]
        with col2:
            st.metric("Predicted Job Category", str(job_pred))

    st.divider()
    st.subheader("Export Prediction")
    export_dict = {
        "title": title,
        "location": location,
        "experience": experience_input,
        "skills": skills,
        "remote": remote,
        "job_type": job_type_input,
    }
    if sal_pred is not None:
        export_dict["predicted_salary"] = sal_pred
    if job_pred is not None:
        export_dict["predicted_job_category"] = job_pred

    export_df = pd.DataFrame([export_dict])
    csv = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Prediction as CSV",
        data=csv,
        file_name="my_prediction.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error(f"Prediction failed: {e}")
    st.exception(e)
