import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from preprocessing import feature_engineering, build_preprocessor
import config


def train_job_segmentation(df: pd.DataFrame, n_clusters: int = None) -> dict:
    n_clusters = n_clusters or config.N_CLUSTERS
    df = feature_engineering(df)
    X = df.drop(columns=["salary", "job_type"], errors="ignore")

    preprocessor = build_preprocessor(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=config.RANDOM_STATE, n_init=10)
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", kmeans)])

    X_train, X_test = train_test_split(X, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE)

    pipeline.fit(X_train)

    X_train_proc = preprocessor.transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    train_labels = kmeans.labels_
    test_labels = kmeans.predict(X_test_proc)

    sil_train = silhouette_score(X_train_proc, train_labels)
    sil_test = silhouette_score(X_test_proc, test_labels)

    cluster_sizes = {int(k): int(v) for k, v in pd.Series(train_labels).value_counts().sort_index().items()}

    config.SEG_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipeline_path = config.SEG_MODEL_DIR / "pipeline.joblib"
    joblib.dump(pipeline, str(pipeline_path))

    metrics = {
        "silhouette_score_train": round(float(sil_train), 4),
        "silhouette_score_test": round(float(sil_test), 4),
        "n_clusters": n_clusters,
        "cluster_sizes": cluster_sizes,
        "model": "KMeans",
    }
    with open(config.SEG_MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return {"pipeline_path": str(pipeline_path), "metrics": metrics}
