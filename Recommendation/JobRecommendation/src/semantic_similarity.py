from __future__ import annotations

import os
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from NLP.SkillExtraction.src.normalization import normalize_text


_SENTENCE_TRANSFORMER_MODEL = None


def candidate_semantic_text(extraction: dict[str, Any], target_role: str | None) -> str:
    skills = " ".join(extraction.get("skills", []) or [])
    degrees = " ".join(extraction.get("degrees", []) or [])
    companies = " ".join(extraction.get("companies", []) or [])
    languages = " ".join(extraction.get("languages", []) or [])
    years = " ".join(extraction.get("years_of_experience", []) or [])
    raw_excerpt = (extraction.get("raw_text") or "")[:1500]
    parts = [
        " ".join([target_role or ""] * 4),
        " ".join([skills] * 4),
        " ".join([degrees] * 2),
        companies,
        languages,
        years,
        raw_excerpt,
    ]
    return " ".join(part for part in parts if part).strip()


def job_semantic_text(job: dict[str, Any]) -> str:
    title = str(job.get("job_title") or "")
    category = str(job.get("category_name") or "")
    skills = str(job.get("skills_csv") or "")
    skill_categories = str(job.get("skill_categories_csv") or "")
    parts = [
        " ".join([title] * 4),
        " ".join([category] * 4),
        job.get("company_name"),
        job.get("country"),
        job.get("city"),
        " ".join([skills] * 4),
        " ".join([skill_categories] * 2),
        job.get("schedule_types_csv"),
        "remote" if bool(job.get("is_work_from_home")) else "onsite hybrid",
        "salary available" if bool(job.get("has_salary_info")) else "",
        "no degree required" if bool(job.get("no_degree_mention")) else "degree may be required",
    ]
    return " ".join(str(part) for part in parts if part).strip()


def semantic_similarity_scores(candidate_semantic_text_value: str, jobs: list[dict[str, Any]]) -> list[float]:
    if not jobs:
        return []
    candidate_text = normalize_text(candidate_semantic_text_value)
    job_texts = [normalize_text(job_semantic_text(job)) for job in jobs]
    if not candidate_text or not any(job_texts):
        return [0.0 for _ in jobs]
    transformer_scores = _sentence_transformer_scores(candidate_text, job_texts)
    if transformer_scores is not None:
        return transformer_scores
    documents = [candidate_text, *job_texts]
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=12000, sublinear_tf=True)
        matrix = vectorizer.fit_transform(documents)
        raw_scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    except ValueError:
        return [0.0 for _ in jobs]
    return [round(scale_semantic_similarity(float(score)), 2) for score in raw_scores]


def scale_semantic_similarity(score: float) -> float:
    score = max(0.0, min(score, 1.0))
    return min(100.0, (score ** 0.42) * 100.0)


def _sentence_transformer_scores(candidate_text: str, job_texts: list[str]) -> list[float] | None:
    """Optional Sentence-BERT path.

    Enabled only when `TALENTBRIDGE_EMBEDDING_BACKEND=sentence-transformers`
    and the package/model are available locally. Otherwise TF-IDF remains the
    deterministic default fallback.
    """
    if os.getenv("TALENTBRIDGE_EMBEDDING_BACKEND", "tfidf").lower() not in {"sentence-transformers", "sentence_transformers", "sbert"}:
        return None
    model = _load_sentence_transformer()
    if model is None:
        return None
    embeddings = model.encode([candidate_text, *job_texts], normalize_embeddings=True, show_progress_bar=False)
    candidate_vector = embeddings[0]
    job_vectors = embeddings[1:]
    raw_scores = np.dot(job_vectors, candidate_vector)
    return [round(max(0.0, min(float(score), 1.0)) * 100.0, 2) for score in raw_scores]


def _load_sentence_transformer():
    global _SENTENCE_TRANSFORMER_MODEL
    if _SENTENCE_TRANSFORMER_MODEL is not None:
        return _SENTENCE_TRANSFORMER_MODEL
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None
    model_name = os.getenv("TALENTBRIDGE_SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    try:
        _SENTENCE_TRANSFORMER_MODEL = SentenceTransformer(model_name)
        return _SENTENCE_TRANSFORMER_MODEL
    except Exception:
        return None
