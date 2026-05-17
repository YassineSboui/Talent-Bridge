"""Skill demand frequency model.

Parses Data/raw/data_jobs.csv to compute how often each skill appears
across all job postings. The resulting demand scores (0-1) are used by
the Skill Gap Analyzer to classify missing skills as high/medium/low
priority based on actual market demand.

Usage:
    python -m MachineLearning.SharedML.src.skill_frequency
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

from NLP.SkillExtraction.src.normalization import normalize_skill


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO_ROOT / "Data" / "raw" / "data_jobs.csv"
ARTIFACT_PATH = REPO_ROOT / "Artifacts" / "models" / "skill_gap" / "skill_frequency.json"

# Cached in-memory so we only load once per process
_DEMAND_CACHE: dict[str, float] | None = None


def _parse_skills_column(raw: str) -> list[str]:
    """Parse the job_skills column which may be a Python list literal or CSV."""
    if not raw or str(raw).strip() in ("", "nan", "None"):
        return []
    raw = str(raw).strip()
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(s) for s in parsed if s]
    except (ValueError, SyntaxError):
        pass
    return [s.strip() for s in raw.split(",") if s.strip()]


def build_skill_frequency(csv_path: Path = DEFAULT_CSV) -> dict[str, float]:
    """Count skill occurrences across job postings and normalize to 0-1 demand scores.

    Returns a dict mapping normalized skill name -> demand score (0.0 to 1.0),
    where 1.0 means the skill appears in every job posting.
    """
    import pandas as pd  # imported here so the module loads without pandas installed

    df = pd.read_csv(csv_path, usecols=["job_skills"], low_memory=False)
    counter: Counter[str] = Counter()
    total_jobs = 0

    for raw in df["job_skills"].dropna():
        skills = _parse_skills_column(str(raw))
        if skills:
            total_jobs += 1
            for skill in skills:
                normalized = normalize_skill(skill)
                if normalized:
                    counter[normalized] += 1

    if total_jobs == 0:
        return {}

    return {skill: round(count / total_jobs, 4) for skill, count in counter.items()}


def save_skill_frequency(csv_path: Path = DEFAULT_CSV, output_path: Path = ARTIFACT_PATH) -> dict[str, float]:
    """Build and persist the skill frequency artifact. Returns the demand dict."""
    demand = build_skill_frequency(csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(demand, fh, indent=2, ensure_ascii=False)
    print(f"[skill_frequency] Saved {len(demand)} skills to {output_path}")
    return demand


def load_skill_frequency(artifact_path: Path = ARTIFACT_PATH) -> dict[str, float]:
    """Load skill demand scores from the artifact file.

    Falls back to building from CSV if the artifact is missing.
    """
    global _DEMAND_CACHE
    if _DEMAND_CACHE is not None:
        return _DEMAND_CACHE
    if artifact_path.exists():
        with open(artifact_path, encoding="utf-8") as fh:
            _DEMAND_CACHE = json.load(fh)
    else:
        # Fallback: build on the fly if CSV exists
        if DEFAULT_CSV.exists():
            _DEMAND_CACHE = build_skill_frequency()
        else:
            _DEMAND_CACHE = {}
    return _DEMAND_CACHE


def get_skill_demand(skill: str, artifact_path: Path = ARTIFACT_PATH) -> float:
    """Return the market demand score (0-1) for a normalized skill name."""
    demand = load_skill_frequency(artifact_path)
    normalized = normalize_skill(skill)
    return demand.get(normalized, 0.0)


if __name__ == "__main__":
    save_skill_frequency()
