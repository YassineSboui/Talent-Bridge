from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


QUALITY_MODEL_PATH = Path(__file__).resolve().parents[3] / "Artifacts" / "models" / "document_ai" / "cv_quality_model.pkl"
_QUALITY_MODEL_ARTIFACT = None


def predict_with_trained_model(text: str, features: dict[str, Any]) -> dict[str, Any] | None:
    artifact = load_quality_model()
    if not artifact:
        return None
    model = artifact["model"]
    item = [{"text": text, "features": features}]
    try:
        label = model.predict(item)[0]
    except Exception:
        return None
    confidence = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(item)[0]
        classes = list(model.classes_)
        confidence = float(probabilities[classes.index(label)])
    return {
        "label": label,
        "confidence": round(confidence if confidence is not None else 1.0, 4),
        "model_path": str(QUALITY_MODEL_PATH),
    }


def load_quality_model() -> dict[str, Any] | None:
    global _QUALITY_MODEL_ARTIFACT
    if _QUALITY_MODEL_ARTIFACT is not None:
        return _QUALITY_MODEL_ARTIFACT
    if not QUALITY_MODEL_PATH.exists():
        return None
    try:
        with QUALITY_MODEL_PATH.open("rb") as file:
            _QUALITY_MODEL_ARTIFACT = pickle.load(file)
        return _QUALITY_MODEL_ARTIFACT
    except Exception:
        return None
