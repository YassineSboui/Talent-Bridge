import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, root_mean_squared_error, r2_score, mean_absolute_error
import shap

from preprocessing import feature_engineering, prepare_dataset, build_preprocessor
import config


def train_salary_regression(df: pd.DataFrame) -> dict:
    df = feature_engineering(df)
    df = prepare_dataset(df, task="regression")

    X = df.drop(columns=["salary"])
    y = df["salary"]

    preprocessor = build_preprocessor(X, exclude_cols=["salary"])

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=config.RANDOM_STATE
    )
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    config.REG_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipeline_path = config.REG_MODEL_DIR / "pipeline.joblib"
    joblib.dump(pipeline, str(pipeline_path))

    try:
        X_test_proc = preprocessor.transform(X_test)
        feature_names_out = preprocessor.get_feature_names_out()
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test_proc[:200])
        shap_path = config.REG_MODEL_DIR / "shap_explainer.joblib"
        joblib.dump({
            "values": shap_values.tolist(),
            "feature_names": list(feature_names_out),
        }, str(shap_path))
    except Exception:
        pass

    metrics = {
        "rmse": round(float(rmse), 2),
        "r2": round(float(r2), 4),
        "mae": round(float(mae), 2),
        "model": "GradientBoostingRegressor",
    }
    with open(config.REG_MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return {"pipeline_path": str(pipeline_path), "metrics": metrics}
