"""Runtime loader for the PyTorch CV quality DL model."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .dl_quality_model import CvQualityMlp
from .grades import binary_label_from_grade, grade_from_score
from .quality_model import FEATURE_NAMES


REPO_ROOT = Path(__file__).resolve().parents[3]
QUALITY_DL_MODEL_DIR = REPO_ROOT / "Artifacts" / "models" / "document_ai" / "cv_quality_dl"
_QUALITY_DL_ARTIFACT: dict[str, Any] | None = None


def load_quality_dl_model(model_dir: str | Path = QUALITY_DL_MODEL_DIR) -> dict[str, Any] | None:
    global _QUALITY_DL_ARTIFACT
    if _QUALITY_DL_ARTIFACT is not None:
        return _QUALITY_DL_ARTIFACT

    model_dir = Path(model_dir)
    model_path = model_dir / "model.pt"
    metadata_path = model_dir / "metadata.json"
    vectorizer_path = model_dir / "vectorizer.pkl"
    scaler_path = model_dir / "scaler.pkl"
    if not all(path.exists() for path in [model_path, metadata_path, vectorizer_path, scaler_path]):
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        with vectorizer_path.open("rb") as handle:
            vectorizer = pickle.load(handle)
        with scaler_path.open("rb") as handle:
            scaler = pickle.load(handle)

        model = CvQualityMlp(input_size=int(metadata["input_size"]), dropout=float(metadata.get("dropout", 0.25)))
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        _QUALITY_DL_ARTIFACT = {"model": model, "metadata": metadata, "vectorizer": vectorizer, "scaler": scaler, "model_dir": str(model_dir)}
        return _QUALITY_DL_ARTIFACT
    except Exception:
        return None


def predict_with_dl_quality_model(text: str, features: dict[str, Any]) -> dict[str, Any] | None:
    artifact = load_quality_dl_model()
    if not artifact:
        return None

    vectorizer = artifact["vectorizer"]
    scaler = artifact["scaler"]
    model = artifact["model"]
    metadata = artifact["metadata"]

    numeric = np.asarray([[float(features.get(name, 0) or 0) for name in FEATURE_NAMES]], dtype=np.float32)
    numeric_scaled = scaler.transform(numeric)
    text_features = vectorizer.transform([text]).toarray().astype(np.float32)
    inputs = np.hstack([text_features, numeric_scaled]).astype(np.float32)

    with torch.no_grad():
        raw_score = model(torch.from_numpy(inputs)).item()

    score = int(round(max(0, min(raw_score, 100))))
    grade = grade_from_score(score)
    label = binary_label_from_grade(grade)
    confidence = min(0.99, 0.58 + abs(score - 55) / 100)
    return {
        "label": label,
        "grade": grade,
        "score": score,
        "confidence": round(float(confidence), 4),
        "model_name": metadata.get("model_name", "cv_quality_mlp"),
        "model_dir": artifact["model_dir"],
        "trained_on": metadata.get("training_records"),
        "label_source": metadata.get("label_source", "pseudo_labels"),
    }
