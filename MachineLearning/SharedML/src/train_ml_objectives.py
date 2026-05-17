"""Train the three project Machine Learning objectives.

Objectives from projet_data_jobs_objectifs.md:
1. Salary prediction -> Regression
2. Job classification -> Classification (remote + schedule type)
3. Job segmentation -> K-Means clustering

The script can read the warehouse SQL view or the raw project CSV. It saves
model artifacts and report-ready metrics so the ML part is reproducible.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge, SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import TransformedTargetRegressor


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO_ROOT / "Data" / "raw" / "data_jobs.csv"
DEFAULT_MODELS_DIR = REPO_ROOT / "Artifacts" / "models" / "ml"
DEFAULT_REPORTS_DIR = REPO_ROOT / "Artifacts" / "reports" / "ml"


CSV_COLUMNS = [
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "job_work_from_home",
    "search_location",
    "job_posted_date",
    "job_no_degree_mention",
    "job_health_insurance",
    "job_country",
    "salary_year_avg",
    "salary_hour_avg",
    "company_name",
    "job_skills",
    "job_type_skills",
]

TEXT_COLUMNS = ["job_title", "job_title_short", "company_name", "job_skills", "job_type_skills"]
CATEGORICAL_COLUMNS = ["job_title_short", "job_country", "schedule_primary", "portal_family"]
NUMERIC_COLUMNS = [
    "is_remote",
    "is_full_time",
    "no_degree_mention",
    "has_health_insurance",
    "posted_year",
    "posted_month",
    "posted_dayofweek",
    "skill_count",
    "title_length",
]


def main() -> None:
    args = parse_args()
    models_dir = Path(args.models_dir)
    reports_dir = Path(args.reports_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    df = load_jobs(args)
    prepared = prepare_jobs(df)
    if args.sample_size and len(prepared) > args.sample_size:
        prepared = prepared.sample(args.sample_size, random_state=args.random_state)

    results = {
        "dataset": {
            "rows": int(len(prepared)),
            "source": args.source,
            "csv_path": str(args.csv) if args.source == "csv" else None,
        },
        "salary_regression": train_salary_regression(prepared, models_dir, args.random_state),
        "remote_classification": train_remote_classifier(prepared, models_dir, args.random_state),
        "full_time_classification": train_full_time_classifier(prepared, models_dir, args.random_state),
        "job_segmentation": train_job_segmentation(prepared, models_dir, reports_dir, args.random_state),
    }

    metrics_path = reports_dir / "ml_objectives_metrics.json"
    metrics_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Saved ML metrics to {metrics_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["sql", "csv"], default="sql", help="Official source is sql. csv is a development fallback only.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--max-rows", type=int, default=150000, help="Rows loaded from CSV. Use 0 for all rows.")
    parser.add_argument("--sample-size", type=int, default=60000, help="Random sample used for training after loading. Use 0 for all loaded rows.")
    parser.add_argument("--models-dir", default=str(DEFAULT_MODELS_DIR))
    parser.add_argument("--reports-dir", default=str(DEFAULT_REPORTS_DIR))
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def load_jobs(args: argparse.Namespace) -> pd.DataFrame:
    if args.source == "sql":
        return load_jobs_from_sql(max_rows=args.max_rows)
    max_rows = None if args.max_rows == 0 else args.max_rows
    return pd.read_csv(args.csv, usecols=CSV_COLUMNS, nrows=max_rows, low_memory=False)


def load_jobs_from_sql(max_rows: int = 150000) -> pd.DataFrame:
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for --source sql") from exc

    top_sql = "" if max_rows == 0 else f"TOP ({max_rows})"
    connection_string = os.getenv(
        "DW_DATAJOBS_CONNECTION_STRING",
        "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DW_DataJobs;Trusted_Connection=yes;TrustServerCertificate=yes;",
    )
    query = f"""
        SELECT {top_sql}
            job_title_short,
            job_title,
            CONCAT(ISNULL(city, ''), ', ', ISNULL(job_country, '')) AS job_location,
            job_via,
            job_schedule_type,
            job_work_from_home,
            job_country AS search_location,
            job_posted_date,
            job_no_degree_mention,
            job_health_insurance,
            job_country,
            salary_year_avg,
            salary_hour_avg,
            company_name,
            job_skills,
            job_type_skills
        FROM dbo.vw_ml_jobs
        ORDER BY job_posted_date DESC, job_posting_key DESC;
    """
    sqlalchemy_url = os.getenv("DW_DATAJOBS_SQLALCHEMY_URL")
    if sqlalchemy_url:
        try:
            from sqlalchemy import create_engine
            with create_engine(sqlalchemy_url).connect() as connection:
                return pd.read_sql(query, connection)
        except Exception:
            pass
    with pyodbc.connect(connection_string) as connection:
        return pd.read_sql(query, connection)


def prepare_jobs(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for column in CSV_COLUMNS:
        if column not in data.columns:
            data[column] = np.nan

    data["is_remote"] = data["job_work_from_home"].map(to_bool).astype(float)
    data["no_degree_mention"] = data["job_no_degree_mention"].map(to_bool).astype(float)
    data["has_health_insurance"] = data["job_health_insurance"].map(to_bool).astype(float)
    data["schedule_primary"] = data["job_schedule_type"].fillna("unknown").map(primary_schedule)
    data["is_full_time"] = data["schedule_primary"].eq("full-time").astype(float)
    data["portal_family"] = data["job_via"].fillna("unknown").map(portal_family)
    data["skill_count"] = data["job_skills"].fillna("").map(count_skills).astype(float)
    data["title_length"] = data["job_title"].fillna("").astype(str).str.len().astype(float)

    posted = pd.to_datetime(data["job_posted_date"], errors="coerce")
    data["posted_year"] = posted.dt.year.fillna(posted.dt.year.median()).fillna(2023).astype(float)
    data["posted_month"] = posted.dt.month.fillna(0).astype(float)
    data["posted_dayofweek"] = posted.dt.dayofweek.fillna(0).astype(float)

    for column in TEXT_COLUMNS + CATEGORICAL_COLUMNS:
        data[column] = data[column].fillna("unknown").astype(str).str.slice(0, 1200)

    data["ml_text"] = (
        data["job_title"].fillna("") + " "
        + data["job_title_short"].fillna("") + " "
        + data["job_location"].fillna("") + " "
        + data["job_country"].fillna("") + " "
        + data["job_via"].fillna("") + " "
        + data["job_skills"].fillna("") + " "
        + data["job_type_skills"].fillna("") + " "
        + data["company_name"].fillna("")
    ).map(clean_text)
    return data


def train_salary_regression(df: pd.DataFrame, models_dir: Path, random_state: int) -> dict[str, Any]:
    salary_df = df[pd.to_numeric(df["salary_year_avg"], errors="coerce").notna()].copy()
    salary_df["salary_year_avg"] = pd.to_numeric(salary_df["salary_year_avg"], errors="coerce")
    salary_df = salary_df[(salary_df["salary_year_avg"] >= 10000) & (salary_df["salary_year_avg"] <= 400000)]
    if len(salary_df) < 200:
        return {"status": "skipped", "reason": "Not enough salary rows", "rows": int(len(salary_df))}

    features = feature_columns()
    x = salary_df[features]
    y = salary_df["salary_year_avg"].astype(float)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.22, random_state=random_state)

    candidates = []
    for alpha in [0.5, 1.0, 3.0, 10.0, 30.0]:
        model = TransformedTargetRegressor(
            regressor=Pipeline([
                ("preprocess", make_preprocessor(features, text_features=9000, min_frequency=8)),
                ("regressor", Ridge(alpha=alpha, random_state=random_state)),
            ]),
            func=np.log1p,
            inverse_func=np.expm1,
        )
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        candidates.append((f"ridge_alpha_{alpha}", model, regression_metrics(y_test, pred)))

    if len(salary_df) <= 18000:
        forest = RandomForestRegressor(
            n_estimators=160,
            min_samples_leaf=4,
            max_features="sqrt",
            n_jobs=-1,
            random_state=random_state,
        )
        model = TransformedTargetRegressor(
            regressor=Pipeline([
                ("preprocess", make_preprocessor(features, text_features=3500, min_frequency=12)),
                ("regressor", forest),
            ]),
            func=np.log1p,
            inverse_func=np.expm1,
        )
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        candidates.append(("random_forest_log_salary", model, regression_metrics(y_test, pred)))

    best_name, best_model, best_metrics = min(candidates, key=lambda item: item[2]["rmse"])
    output_path = models_dir / "salary_regression_model.pkl"
    save_pickle({"model": best_model, "model_name": best_name, "features": features, "metrics": best_metrics}, output_path)
    return {
        "status": "trained",
        "objective": "Prédiction du salaire",
        "technology": "Regression",
        "target": "salary_year_avg",
        "rows": int(len(salary_df)),
        "best_model": best_name,
        "metrics": best_metrics,
        "candidates": {name: metrics for name, _, metrics in candidates},
        "features_used": features,
        "artifact": str(output_path),
    }


def train_remote_classifier(df: pd.DataFrame, models_dir: Path, random_state: int) -> dict[str, Any]:
    data = df[df["is_remote"].notna()].copy()
    return train_classifier(
        data,
        target_column="is_remote",
        target_name="remote_vs_onsite",
        objective="Classification remote / non remote",
        output_path=models_dir / "remote_classifier_model.pkl",
        random_state=random_state,
        excluded_features={"is_remote"},
    )


def train_full_time_classifier(df: pd.DataFrame, models_dir: Path, random_state: int) -> dict[str, Any]:
    data = df[df["is_full_time"].notna()].copy()
    return train_classifier(
        data,
        target_column="is_full_time",
        target_name="full_time_vs_other",
        objective="Classification full-time / autre type de job",
        output_path=models_dir / "full_time_classifier_model.pkl",
        random_state=random_state,
        excluded_features={"schedule_primary", "is_full_time"},
    )


def train_classifier(
    data: pd.DataFrame,
    target_column: str,
    target_name: str,
    objective: str,
    output_path: Path,
    random_state: int,
    excluded_features: set[str] | None = None,
) -> dict[str, Any]:
    if len(data) < 500 or data[target_column].nunique() < 2:
        return {"status": "skipped", "reason": "Not enough labeled rows", "rows": int(len(data))}

    features = feature_columns(excluded_features or set())
    x = data[features]
    y = data[target_column]
    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.22,
        random_state=random_state,
        stratify=stratify,
    )

    candidates = []
    if len(data) <= 25000:
        for c_value in [0.3, 1.0]:
            model = Pipeline([
                ("preprocess", make_preprocessor(features, text_features=7000, min_frequency=8)),
                (
                    "classifier",
                    LogisticRegression(
                        C=c_value,
                        max_iter=900,
                        class_weight="balanced",
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            ])
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            metrics = classification_metrics(y_test, pred)
            candidates.append((f"logistic_c_{c_value}", model, metrics))

    alpha_values = [1e-5, 1e-4, 1e-3]
    if len(data) > 25000:
        alpha_values = [1e-4, 3e-4, 1e-3]
    for alpha in alpha_values:
        model = Pipeline([
            ("preprocess", make_preprocessor(features, text_features=9000, min_frequency=8)),
            (
                "classifier",
                SGDClassifier(
                    loss="log_loss",
                    penalty="elasticnet",
                    alpha=alpha,
                    l1_ratio=0.08,
                    class_weight="balanced",
                    max_iter=2000,
                    tol=1e-4,
                    n_jobs=-1,
                    random_state=random_state,
                ),
            ),
        ])
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        metrics = classification_metrics(y_test, pred)
        candidates.append((f"sgd_elasticnet_alpha_{alpha}", model, metrics))

    best_name, best_model, best_metrics = max(candidates, key=lambda item: item[2]["macro_f1"])
    save_pickle({"model": best_model, "model_name": best_name, "features": features, "metrics": best_metrics}, output_path)
    return {
        "status": "trained",
        "objective": objective,
        "technology": "Classification",
        "target": target_name,
        "rows": int(len(data)),
        "class_distribution": {str(k): int(v) for k, v in data[target_column].value_counts().items()},
        "best_model": best_name,
        "metrics": best_metrics,
        "candidates": {name: metrics for name, _, metrics in candidates},
        "features_used": features,
        "excluded_leakage_features": sorted(excluded_features or []),
        "artifact": str(output_path),
    }


def train_job_segmentation(df: pd.DataFrame, models_dir: Path, reports_dir: Path, random_state: int) -> dict[str, Any]:
    data = df.copy()
    if len(data) < 1000:
        return {"status": "skipped", "reason": "Not enough rows", "rows": int(len(data))}

    features = feature_columns()
    x = data[features]
    preprocessor = make_preprocessor(features, text_features=7000, min_frequency=10)
    matrix = preprocessor.fit_transform(x)
    n_components = max(2, min(80, matrix.shape[1] - 1))
    svd = TruncatedSVD(n_components=n_components, random_state=random_state)
    reduced = svd.fit_transform(matrix)
    reduced = StandardScaler().fit_transform(reduced)

    candidates = []
    for k_value in range(4, 11):
        model = MiniBatchKMeans(
            n_clusters=k_value,
            random_state=random_state,
            batch_size=2048,
            n_init=12,
        )
        labels = model.fit_predict(reduced)
        sil = silhouette_score(reduced, labels)
        candidates.append((k_value, model, float(sil)))

    hdbscan_result = try_hdbscan(reduced, data, random_state)

    best_k, best_kmeans, best_silhouette = max(candidates, key=lambda item: item[2])
    labels = best_kmeans.predict(reduced)
    algorithm = "K-Means"
    artifact_model_key = "kmeans"
    selected_model = best_kmeans
    selected_score = best_silhouette
    selected_k = int(best_k)
    if hdbscan_result and hdbscan_result["silhouette"] > best_silhouette:
        labels = hdbscan_result["labels"]
        algorithm = "HDBSCAN"
        artifact_model_key = "hdbscan"
        selected_model = hdbscan_result["model"]
        selected_score = hdbscan_result["silhouette"]
        selected_k = hdbscan_result["cluster_count"]
    profile = cluster_profile(data, labels)
    profile_path = reports_dir / "job_cluster_profiles.json"
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")

    artifact = {
        "preprocessor": preprocessor,
        "svd": svd,
        artifact_model_key: selected_model,
        "features": features,
        "algorithm": algorithm,
        "best_k": selected_k,
        "silhouette": selected_score,
        "cluster_profile": profile,
    }
    output_path = models_dir / "job_segmentation_kmeans.pkl"
    save_pickle(artifact, output_path)
    return {
        "status": "trained",
        "objective": "Segmentation des jobs similaires",
        "technology": algorithm,
        "rows": int(len(data)),
        "best_k": selected_k,
        "silhouette_score": round(selected_score, 4),
        "candidates": {str(k): round(score, 4) for k, _, score in candidates},
        "hdbscan_candidate": None if not hdbscan_result else {
            "cluster_count": hdbscan_result["cluster_count"],
            "noise_count": hdbscan_result["noise_count"],
            "silhouette_score": round(hdbscan_result["silhouette"], 4),
        },
        "artifact": str(output_path),
        "profile_report": str(profile_path),
        "clusters": profile,
    }


def try_hdbscan(reduced: np.ndarray, data: pd.DataFrame, random_state: int) -> dict[str, Any] | None:
    try:
        import hdbscan
    except Exception:
        return None
    min_cluster_size = max(25, min(250, len(data) // 100))
    model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=max(5, min_cluster_size // 4))
    labels = model.fit_predict(reduced)
    non_noise = labels != -1
    cluster_count = len(set(labels[non_noise]))
    if cluster_count < 2:
        return None
    valid_mask = labels != -1
    if np.sum(valid_mask) < 200 or len(set(labels[valid_mask])) < 2:
        return None
    score = silhouette_score(reduced[valid_mask], labels[valid_mask])
    return {
        "model": model,
        "labels": labels,
        "cluster_count": int(cluster_count),
        "noise_count": int(np.sum(labels == -1)),
        "silhouette": float(score),
    }


def make_preprocessor(features: list[str], text_features: int, min_frequency: int) -> ColumnTransformer:
    categorical_columns = [column for column in CATEGORICAL_COLUMNS if column in features]
    numeric_columns = [column for column in NUMERIC_COLUMNS if column in features]
    return ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    max_features=text_features,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
                "ml_text",
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", min_frequency=min_frequency),
                categorical_columns,
            ),
            (
                "numeric",
                Pipeline([
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler(with_mean=False)),
                ]),
                numeric_columns,
            ),
        ],
        remainder="drop",
    )


def feature_columns(exclude: set[str] | None = None) -> list[str]:
    exclude = exclude or set()
    return [column for column in ["ml_text", *CATEGORICAL_COLUMNS, *NUMERIC_COLUMNS] if column not in exclude]


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    y_pred = np.maximum(y_pred, 0)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mae = mean_absolute_error(y_true, y_pred)
    median_salary = float(np.median(y_true)) or 1.0
    return {
        "rmse": round(float(rmse), 2),
        "mae": round(float(mae), 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "mae_vs_median_salary_pct": round(float(mae / median_salary * 100), 2),
    }


def classification_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, Any]:
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "report": round_report(report),
    }


def cluster_profile(df: pd.DataFrame, labels: np.ndarray) -> list[dict[str, Any]]:
    profiled = df.copy()
    profiled["cluster"] = labels
    salary = pd.to_numeric(profiled["salary_year_avg"], errors="coerce")
    profiled["salary_year_avg_numeric"] = salary
    clusters = []
    for cluster_id in sorted(profiled["cluster"].unique()):
        group = profiled[profiled["cluster"] == cluster_id]
        clusters.append(
            {
                "cluster": int(cluster_id),
                "size": int(len(group)),
                "share_pct": round(float(len(group) / len(profiled) * 100), 2),
                "remote_rate_pct": round(float(group["is_remote"].mean() * 100), 2),
                "avg_salary_year": round(float(group["salary_year_avg_numeric"].mean()), 2) if group["salary_year_avg_numeric"].notna().any() else None,
                "top_roles": top_values(group["job_title_short"], 6),
                "top_countries": top_values(group["job_country"], 5),
                "top_schedules": top_values(group["schedule_primary"], 4),
                "top_skills": top_skills(group["job_skills"], 10),
            }
        )
    return clusters


def top_values(values: pd.Series, limit: int) -> list[dict[str, Any]]:
    counts = values.fillna("unknown").astype(str).value_counts().head(limit)
    return [{"value": str(index), "count": int(count)} for index, count in counts.items()]


def top_skills(values: pd.Series, limit: int) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for value in values.fillna(""):
        for skill in parse_skills(value):
            counter[skill] += 1
    return [{"skill": skill, "count": int(count)} for skill, count in counter.most_common(limit)]


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def primary_schedule(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    if not text or text == "nan":
        return "unknown"
    first = re.split(r"[,;/|]", text)[0].strip()
    return first or "unknown"


def portal_family(value: Any) -> str:
    text = str(value or "unknown").lower()
    text = re.sub(r"^via\s+", "", text).strip()
    for marker in ["linkedin", "indeed", "beBee".lower(), "glassdoor", "ziprecruiter", "company site"]:
        if marker in text:
            return marker
    return text[:40] or "unknown"


def count_skills(value: Any) -> int:
    return len(parse_skills(value))


def parse_skills(value: Any) -> list[str]:
    text = str(value or "")
    skills = [item.strip(" '\"[]{}") for item in re.split(r"[,;]", text) if item.strip(" '\"[]{}")]
    return [skill for skill in skills if skill.lower() not in {"nan", "none", "unknown"}]


def clean_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def round_report(report: dict[str, Any]) -> dict[str, Any]:
    rounded = {}
    for key, value in report.items():
        if isinstance(value, dict):
            rounded[key] = {inner_key: round(float(inner_value), 4) for inner_key, inner_value in value.items()}
        else:
            rounded[key] = round(float(value), 4)
    return rounded


def save_pickle(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file:
        pickle.dump(payload, file)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ML training failed: {exc}", file=sys.stderr)
        raise
