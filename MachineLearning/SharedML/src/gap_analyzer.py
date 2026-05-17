"""Skill Gap Analyzer — core engine.

Given a candidate's skills and a job's required skills, computes:
- matched skills (candidate already has)
- missing skills grouped by priority (critical / high / medium / low)
- coverage percentage and readiness level
- curated learning resources for each missing skill

Priority classification:
  critical  — missing skill is in the role's core skills (ROLE_CORE_SKILLS)
  high      — missing skill has market demand score > 0.25
  medium    — missing skill has market demand score > 0.08
  low       — low-signal or rare skill
"""

from __future__ import annotations

from dataclasses import dataclass, field

from NLP.SkillExtraction.src.normalization import normalize_skills
from Recommendation.JobRecommendation.src.score_components import (
    ROLE_CORE_SKILLS,
    core_skills_for_role,
)
from MachineLearning.SharedML.src.skill_frequency import get_skill_demand


# ---------------------------------------------------------------------------
# Priority thresholds
# ---------------------------------------------------------------------------
_HIGH_DEMAND_THRESHOLD = 0.25   # skill appears in >25% of market jobs
_MEDIUM_DEMAND_THRESHOLD = 0.08  # skill appears in >8% of market jobs


# ---------------------------------------------------------------------------
# Curated learning resource index (skill -> list of resource labels+urls)
# ---------------------------------------------------------------------------
LEARNING_RESOURCES: dict[str, list[dict[str, str]]] = {
    "python": [
        {"label": "Python.org Tutorial", "url": "https://docs.python.org/3/tutorial/"},
        {"label": "Kaggle Python Course (free)", "url": "https://www.kaggle.com/learn/python"},
    ],
    "sql": [
        {"label": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"},
        {"label": "SQLZoo (interactive)", "url": "https://sqlzoo.net/"},
    ],
    "power bi": [
        {"label": "Microsoft Learn — Power BI", "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"},
    ],
    "tableau": [
        {"label": "Tableau eLearning", "url": "https://www.tableau.com/learn/training"},
    ],
    "excel": [
        {"label": "Microsoft Excel Training", "url": "https://support.microsoft.com/en-us/excel"},
    ],
    "machine learning": [
        {"label": "Coursera ML Specialization (Andrew Ng)", "url": "https://www.coursera.org/specializations/machine-learning-introduction"},
        {"label": "Kaggle Intro to ML (free)", "url": "https://www.kaggle.com/learn/intro-to-machine-learning"},
    ],
    "deep learning": [
        {"label": "fast.ai Deep Learning Course", "url": "https://course.fast.ai/"},
        {"label": "Coursera Deep Learning Specialization", "url": "https://www.coursera.org/specializations/deep-learning"},
    ],
    "scikit-learn": [
        {"label": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
    ],
    "tensorflow": [
        {"label": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials"},
    ],
    "pytorch": [
        {"label": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/"},
    ],
    "pandas": [
        {"label": "Pandas Getting Started", "url": "https://pandas.pydata.org/getting_started.html"},
        {"label": "Kaggle Pandas Course (free)", "url": "https://www.kaggle.com/learn/pandas"},
    ],
    "numpy": [
        {"label": "NumPy Quickstart", "url": "https://numpy.org/doc/stable/user/quickstart.html"},
    ],
    "spark": [
        {"label": "Databricks Free Training", "url": "https://www.databricks.com/learn/training"},
    ],
    "airflow": [
        {"label": "Apache Airflow Docs", "url": "https://airflow.apache.org/docs/"},
    ],
    "docker": [
        {"label": "Docker Get Started", "url": "https://docs.docker.com/get-started/"},
    ],
    "kubernetes": [
        {"label": "Kubernetes Interactive Tutorial", "url": "https://kubernetes.io/docs/tutorials/"},
    ],
    "azure": [
        {"label": "Microsoft Learn — Azure Fundamentals", "url": "https://learn.microsoft.com/en-us/training/paths/az-900-describe-cloud-concepts/"},
    ],
    "aws": [
        {"label": "AWS Skill Builder (free tier)", "url": "https://skillbuilder.aws/"},
    ],
    "gcp": [
        {"label": "Google Cloud Skills Boost", "url": "https://cloudskillsboost.google/"},
    ],
    "statistics": [
        {"label": "Khan Academy Statistics", "url": "https://www.khanacademy.org/math/statistics-probability"},
    ],
    "data analysis": [
        {"label": "Kaggle Data Analysis Course (free)", "url": "https://www.kaggle.com/learn/data-analysis"},
    ],
    "r": [
        {"label": "R for Data Science (free book)", "url": "https://r4ds.hadley.nz/"},
    ],
    "javascript": [
        {"label": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"},
    ],
    "java": [
        {"label": "Oracle Java Tutorials", "url": "https://docs.oracle.com/javase/tutorial/"},
    ],
    "git": [
        {"label": "Pro Git (free book)", "url": "https://git-scm.com/book/en/v2"},
    ],
    "looker studio": [
        {"label": "Google Looker Studio Help", "url": "https://support.google.com/looker-studio"},
    ],
    "kafka": [
        {"label": "Confluent Kafka Tutorials", "url": "https://developer.confluent.io/learn-kafka/"},
    ],
    "nlp": [
        {"label": "HuggingFace NLP Course (free)", "url": "https://huggingface.co/learn/nlp-course/"},
    ],
}

_DEFAULT_RESOURCES: list[dict[str, str]] = [
    {"label": "Search on Coursera", "url": "https://www.coursera.org/search?query={skill}"},
    {"label": "Search on YouTube", "url": "https://www.youtube.com/results?search_query={skill}+tutorial"},
]


def _get_resources(skill: str) -> list[dict[str, str]]:
    resources = LEARNING_RESOURCES.get(skill)
    if resources:
        return resources
    return [
        {"label": r["label"], "url": r["url"].replace("{skill}", skill.replace(" ", "+"))}
        for r in _DEFAULT_RESOURCES
    ]


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GapItem:
    skill: str
    priority: str          # "critical" | "high" | "medium" | "low"
    demand_score: float    # 0-1 market frequency
    is_core: bool          # True if in ROLE_CORE_SKILLS for target role
    resources: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SkillGapResult:
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]            # candidate has but job doesn't require
    coverage_percentage: float         # matched / required * 100
    readiness_level: str               # "perfect" | "strong" | "moderate" | "weak"
    gaps_by_priority: list[GapItem]    # missing skills ordered by priority
    quick_wins: list[str]              # top 3 medium/low priority gaps (easier to acquire)
    core_gaps: list[str]               # critical skills still missing
    job_id: int | None = None
    job_title: str | None = None
    candidate_skills_count: int = 0
    job_skills_count: int = 0


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def analyze_gap(
    candidate_skills: list[str],
    job_skills: list[str],
    target_role: str | None = None,
    job_id: int | None = None,
    job_title: str | None = None,
) -> SkillGapResult:
    """Compute the skill gap between a candidate and a job.

    Args:
        candidate_skills: Normalized list of candidate skills.
        job_skills:        Normalized list of skills required by the job.
        target_role:       Candidate's preferred role (used for core skill lookup).
        job_id:            Optional job ID for context in the result.
        job_title:         Optional job title for display in the result.

    Returns:
        A SkillGapResult with matched skills, prioritized gaps, and resources.
    """
    candidate_set = set(normalize_skills(candidate_skills))
    job_set = set(normalize_skills(job_skills))

    matched = sorted(candidate_set & job_set)
    missing = sorted(job_set - candidate_set)
    extra = sorted(candidate_set - job_set)

    coverage = round(len(matched) / max(len(job_set), 1) * 100, 1)

    if coverage >= 100:
        readiness = "perfect"
    elif coverage >= 70:
        readiness = "strong"
    elif coverage >= 40:
        readiness = "moderate"
    else:
        readiness = "weak"

    core_skills = core_skills_for_role(target_role)

    gaps: list[GapItem] = []
    for skill in missing:
        is_core = skill in core_skills
        demand = get_skill_demand(skill)

        if is_core:
            priority = "critical"
        elif demand >= _HIGH_DEMAND_THRESHOLD:
            priority = "high"
        elif demand >= _MEDIUM_DEMAND_THRESHOLD:
            priority = "medium"
        else:
            priority = "low"

        gaps.append(GapItem(
            skill=skill,
            priority=priority,
            demand_score=demand,
            is_core=is_core,
            resources=_get_resources(skill),
        ))

    # Sort: critical → high → medium → low, then by demand desc within each tier
    _priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda item: (_priority_order[item.priority], -item.demand_score))

    quick_wins = [g.skill for g in gaps if g.priority in ("medium", "low")][:3]
    core_gaps = [g.skill for g in gaps if g.priority == "critical"]

    return SkillGapResult(
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        coverage_percentage=coverage,
        readiness_level=readiness,
        gaps_by_priority=gaps,
        quick_wins=quick_wins,
        core_gaps=core_gaps,
        job_id=job_id,
        job_title=job_title,
        candidate_skills_count=len(candidate_set),
        job_skills_count=len(job_set),
    )


def result_to_dict(result: SkillGapResult) -> dict:
    """Serialize SkillGapResult to a JSON-compatible dict for API responses."""
    return {
        "job_id": result.job_id,
        "job_title": result.job_title,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
        "extra_skills": result.extra_skills,
        "coverage_percentage": result.coverage_percentage,
        "readiness_level": result.readiness_level,
        "candidate_skills_count": result.candidate_skills_count,
        "job_skills_count": result.job_skills_count,
        "core_gaps": result.core_gaps,
        "quick_wins": result.quick_wins,
        "gaps_by_priority": [
            {
                "skill": g.skill,
                "priority": g.priority,
                "demand_score": g.demand_score,
                "is_core": g.is_core,
                "resources": g.resources,
            }
            for g in result.gaps_by_priority
        ],
    }
