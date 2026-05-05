import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from PIL import Image
from visualization import (
    salary_distribution,
    job_type_breakdown,
    experience_vs_salary,
    top_locations,
    skills_wordcloud,
    correlation_heatmap,
)
from utils.streamlit_helpers import load_dataset_from_db

st.set_page_config(page_title="EDA Dashboard", page_icon="📈", layout="wide")
st.title("Exploratory Data Analysis Dashboard")

df = load_dataset_from_db()
if df.empty:
    st.warning("No data loaded. Check your database connection.")
    st.stop()

st.info(f"Loaded {len(df):,} job postings with {len(df.columns)} features.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Salary Distribution")
    buf = salary_distribution(df)
    if buf:
        st.image(Image.open(buf), use_container_width=True)
    else:
        st.info("No salary data available.")

with col2:
    st.subheader("Job Type Breakdown")
    buf = job_type_breakdown(df)
    if buf:
        st.image(Image.open(buf), use_container_width=True)
    else:
        st.info("No job_type data available.")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Experience vs Salary")
    buf = experience_vs_salary(df)
    if buf:
        st.image(Image.open(buf), use_container_width=True)
    else:
        st.info("Insufficient data for experience vs salary plot.")

with col4:
    st.subheader("Top Locations")
    buf = top_locations(df)
    if buf:
        st.image(Image.open(buf), use_container_width=True)
    else:
        st.info("No location data available.")

st.subheader("Skills Word Cloud")
buf = skills_wordcloud(df)
if buf:
    st.image(Image.open(buf), use_container_width=True)
else:
    st.info("No skills column available for word cloud.")

st.subheader("Feature Correlation Heatmap")
buf = correlation_heatmap(df)
if buf:
    st.image(Image.open(buf), use_container_width=True)
else:
    st.info("Insufficient numeric features for correlation heatmap.")

st.divider()
st.subheader("Raw Data Sample")
st.dataframe(df.head(50), use_container_width=True)
