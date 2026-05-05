import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
import shap

from preprocessing import feature_engineering, prepare_dataset, build_preprocessor
import config


def train_job_classification(df: pd.DataFrame) -> dict:
    df = feature_engineering(df)
    df = prepare_dataset(df, task="classification")

    X = df.drop(columns=["job_type"])
    y = df["job_type"]

    vc = y.value_counts()
    valid_classes = vc[vc >= 2].index
    mask = y.isin(valid_classes)
    X = X[mask]
    y = y[mask]

    if len(y.unique()) < 2:
        raise ValueError("Classification requires at least 2 classes with 2+ samples each.")

    preprocessor = build_preprocessor(X, exclude_cols=["job_type"])

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=config.RANDOM_STATE
    )
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE, stratify=y
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    config.CLS_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipeline_path = config.CLS_MODEL_DIR / "pipeline.joblib"
    joblib.dump(pipeline, str(pipeline_path))

    with open(config.CLS_MODEL_DIR / "classes.json", "w") as f:
        json.dump({"classes": sorted(y.unique().tolist())}, f, indent=2)

    try:
        X_test_proc = preprocessor.transform(X_test)
        feature_names_out = preprocessor.get_feature_names_out()
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test_proc[:200])
        shap_path = config.CLS_MODEL_DIR / "shap_explainer.joblib"
        joblib.dump({
            "values": shap_values.tolist(),
            "feature_names": list(feature_names_out),
            "classes": list(model.classes_),
        }, str(shap_path))
    except Exception:
        pass

    metrics = {
        "accuracy": round(float(acc), 4),
        "model": "GradientBoostingClassifier",
    }
    with open(config.CLS_MODEL_DIR / "metrics.json", "w") as f:
        json.dump({
            "metrics": metrics,
            "classification_report": report,
        }, f, indent=2)

    return {"pipeline_path": str(pipeline_path), "metrics": metrics}
