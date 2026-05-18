"""Inference API for the CV-vs-Non-CV document classifier."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import fitz
import torch

from .model import CvDocumentCnn
from .preprocessing import array_to_tensor, document_to_array


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_DIR = REPO_ROOT / "Artifacts" / "models" / "document_ai" / "cv_document_classifier"

CV_TEXT_TERMS = {
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "languages",
    "profile",
    "summary",
    "employment",
    "work history",
    "linkedin",
    "github",
    "competences",
    "compétences",
    "experience professionnelle",
    "expérience professionnelle",
    "formation",
    "projets",
    "certifications",
    "langues",
}


def _load_metadata(model_dir: str | Path) -> dict[str, Any]:
    metadata_path = Path(model_dir) / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing classifier metadata: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def load_model(model_dir: str | Path = DEFAULT_MODEL_DIR, *, device: str | None = None) -> tuple[CvDocumentCnn, dict[str, Any], torch.device]:
    model_path = Path(model_dir) / "model.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"Missing CV document classifier model: {model_path}")

    metadata = _load_metadata(model_dir)
    runtime_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = CvDocumentCnn(dropout=float(metadata.get("dropout", 0.25)))
    model.load_state_dict(torch.load(model_path, map_location=runtime_device))
    model.to(runtime_device)
    model.eval()
    return model, metadata, runtime_device


def extract_pdf_text(document_path: str | Path, *, max_pages: int = 2) -> str:
    path = Path(document_path)
    if path.suffix.lower() != ".pdf":
        return ""
    try:
        with fitz.open(path) as pdf:
            return "\n".join(pdf.load_page(index).get_text("text") for index in range(min(pdf.page_count, max_pages)))
    except Exception:
        return ""


def cv_text_evidence_score(text: str) -> float:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if not normalized:
        return 0.0
    term_hits = sum(1 for term in CV_TEXT_TERMS if term in normalized)
    email_hit = 1 if re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", normalized) else 0
    phone_hit = 1 if re.search(r"(?:\+?\d[\s().-]*){8,}", normalized) else 0
    url_hit = 1 if "linkedin" in normalized or "github" in normalized or re.search(r"https?://|www\.", normalized) else 0
    length_score = min(len(normalized) / 2500, 1.0)
    section_score = min(term_hits / 5, 1.0)
    contact_score = min((email_hit + phone_hit + url_hit) / 2, 1.0)
    return round((0.55 * section_score) + (0.3 * contact_score) + (0.15 * length_score), 4)


def classify_document(
    document_path: str | Path,
    *,
    model_dir: str | Path = DEFAULT_MODEL_DIR,
    accept_threshold: float | None = None,
    reject_threshold: float | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    """Classify a document as CV, Non-CV, or uncertain."""
    model, metadata, runtime_device = load_model(model_dir, device=device)
    image_size = tuple(metadata.get("image_size", [160, 224]))
    array = document_to_array(document_path, image_size=(int(image_size[0]), int(image_size[1])))
    tensor = array_to_tensor(array).unsqueeze(0).to(runtime_device)

    with torch.no_grad():
        probability_cv = torch.sigmoid(model(tensor)).item()

    text = extract_pdf_text(document_path)
    text_evidence = cv_text_evidence_score(text)
    if text_evidence >= float(metadata.get("strong_text_evidence_threshold", 0.65)):
        probability_cv = max(probability_cv, float(metadata.get("text_evidence_probability_floor", 0.88)))
    elif text_evidence >= float(metadata.get("moderate_text_evidence_threshold", 0.45)):
        probability_cv = max(probability_cv, float(metadata.get("text_evidence_manual_review_floor", 0.55)))

    cv_threshold = float(accept_threshold if accept_threshold is not None else metadata.get("accept_threshold", 0.75))
    non_cv_threshold = float(reject_threshold if reject_threshold is not None else metadata.get("reject_threshold", 0.4))

    if probability_cv >= cv_threshold:
        label = "cv"
        decision = "accepted"
        is_cv = True
        confidence = probability_cv
    elif probability_cv <= non_cv_threshold:
        label = "non_cv"
        decision = "rejected"
        is_cv = False
        confidence = 1.0 - probability_cv
    else:
        label = "uncertain"
        decision = "manual_review"
        is_cv = False
        confidence = max(probability_cv, 1.0 - probability_cv)

    return {
        "label": label,
        "is_cv": is_cv,
        "decision": decision,
        "confidence": round(float(confidence), 4),
        "cv_probability": round(float(probability_cv), 4),
        "text_evidence_score": text_evidence,
        "model": metadata.get("model_name", "cv_document_cnn"),
    }
