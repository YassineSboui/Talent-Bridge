import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from utils.streamlit_helpers import load_model_artifacts, load_dataset_from_db

st.set_page_config(page_title="Job Segmentation", page_icon="🔵", layout="wide")
st.title("Job Segmentation — K-Means Clustering")

pipeline, _, metrics = load_model_artifacts("segmentation")

if pipeline is None:
    st.error("Segmentation model not found. Run `python train_models.py` first.")
    st.stop()

st.subheader("Model Performance")
c1, c2 = st.columns(2)
c1.metric("Silhouette Score (Train)", f"{metrics.get('silhouette_score_train', 'N/A')}")
c2.metric("Silhouette Score (Test)", f"{metrics.get('silhouette_score_test', 'N/A')}")
st.caption(f"Number of clusters: {metrics.get('n_clusters', 'N/A')}")

st.divider()

st.subheader("Cluster Visualization (PCA)")
try:
    df = load_dataset_from_db()
    if not df.empty:
        df_clean = df.drop(columns=["salary", "job_type"], errors="ignore")
        X_proc = pipeline.named_steps["preprocessor"].transform(df_clean)
        labels = pipeline.named_steps["model"].predict(X_proc)

        pca = PCA(n_components=2, random_state=42)
        X_2d = pca.fit_transform(X_proc)

        viz_df = pd.DataFrame({"PC1": X_2d[:, 0], "PC2": X_2d[:, 1], "Cluster": labels})
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.scatterplot(data=viz_df, x="PC1", y="PC2", hue="Cluster", palette="tab10", alpha=0.6, s=50, ax=ax)
        ax.set_title("Job Segments — PCA 2D Projection")
        st.pyplot(fig)

        n_clusters = metrics.get("n_clusters", 5)
        cluster_sizes = metrics.get("cluster_sizes", {})
        cluster_summary = pd.DataFrame({
            "cluster": list(range(n_clusters)),
            "size": [cluster_sizes.get(i, 0) for i in range(n_clusters)],
        })
        st.subheader("Cluster Sizes")
        st.dataframe(cluster_summary, use_container_width=True)

        st.subheader("Sample Assignments")
        result_df = df.copy()
        result_df["cluster"] = labels
        display_cols = [c for c in ["title", "location", "job_type", "salary", "cluster"] if c in result_df.columns]
        st.dataframe(result_df[display_cols].head(50), use_container_width=True)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Cluster Assignments as CSV",
            data=csv,
            file_name="job_segments.csv",
            mime="text/csv",
        )
except Exception as e:
    st.warning(f"Could not generate cluster visualization: {e}")
