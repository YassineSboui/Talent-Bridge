from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from MachineLearning.SharedML.src.gap_analyzer import analyze_gap, result_to_dict
from NLP.SkillExtraction.src.normalization import normalize_skills, split_csv_values

from ..security import require_role
from ..store import store


router = APIRouter(prefix="/skill-gap", tags=["Skill Gap"])


def _candidate_skills_and_role(user_id: int) -> tuple[list[str], str | None]:
    """Return normalized candidate skills and preferred role from the platform store."""
    profile = store.candidate_profiles.get(user_id, {})
    raw_skills = profile.get("skills", [])
    preferred_roles = profile.get("preferred_roles") or []
    target_role = preferred_roles[0] if preferred_roles else None
    return normalize_skills(raw_skills), target_role


def _job_skills(job: dict) -> list[str]:
    """Return normalized required skills for a platform job."""
    raw = job.get("required_skills") or []
    if isinstance(raw, str):
        return normalize_skills(split_csv_values(raw))
    return normalize_skills(raw)


@router.get("/jobs/{job_id}")
def candidate_job_gap(
    job_id: int,
    user: dict = Depends(require_role("candidate")),
):
    """Return the skill gap analysis for the logged-in candidate vs a specific job.

    Response includes:
    - matched_skills: skills the candidate already has
    - missing_skills: skills the job requires that the candidate lacks
    - gaps_by_priority: missing skills classified as critical/high/medium/low
    - coverage_percentage: how much of the job's skill set the candidate covers
    - readiness_level: perfect | strong | moderate | weak
    - quick_wins: 3 lower-priority gaps easiest to close
    - core_gaps: critical missing skills for the candidate's target role
    - resources: curated learning links per missing skill
    """
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate_skills, target_role = _candidate_skills_and_role(user["id"])
    job_required = _job_skills(job)

    result = analyze_gap(
        candidate_skills=candidate_skills,
        job_skills=job_required,
        target_role=target_role,
        job_id=job_id,
        job_title=job.get("title"),
    )

    return {"skill_gap": result_to_dict(result)}


@router.get("/top-missing")
def candidate_top_missing_skills(
    limit: int = 10,
    user: dict = Depends(require_role("candidate")),
):
    """Return the most frequently missing skills across all published jobs.

    Aggregates skill gaps from every published job and surfaces the top skills
    the candidate should learn to maximize their overall market fit.

    Each item includes:
    - skill: the skill name
    - missing_in_jobs: number of jobs that require this skill
    - priority: highest priority level seen across all gaps
    - demand_score: market demand frequency (0-1)
    - resources: curated learning links
    """
    candidate_skills, target_role = _candidate_skills_and_role(user["id"])

    published_jobs = [job for job in store.jobs.values() if job.get("status") == "published"]
    if not published_jobs:
        return {"top_missing": [], "total_jobs_analyzed": 0}

    from collections import Counter
    skill_job_count: Counter[str] = Counter()
    skill_best_priority: dict[str, str] = {}
    skill_demand: dict[str, float] = {}
    skill_resources: dict[str, list] = {}

    _priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    for job in published_jobs:
        job_required = _job_skills(job)
        result = analyze_gap(
            candidate_skills=candidate_skills,
            job_skills=job_required,
            target_role=target_role,
            job_id=job.get("id"),
        )
        for gap_item in result.gaps_by_priority:
            skill = gap_item.skill
            skill_job_count[skill] += 1
            current = skill_best_priority.get(skill, "low")
            if _priority_order[gap_item.priority] < _priority_order[current]:
                skill_best_priority[skill] = gap_item.priority
            skill_demand[skill] = max(skill_demand.get(skill, 0.0), gap_item.demand_score)
            if skill not in skill_resources:
                skill_resources[skill] = gap_item.resources

    top = sorted(skill_job_count.items(), key=lambda item: -item[1])[:limit]

    return {
        "top_missing": [
            {
                "skill": skill,
                "missing_in_jobs": count,
                "priority": skill_best_priority.get(skill, "low"),
                "demand_score": skill_demand.get(skill, 0.0),
                "resources": skill_resources.get(skill, []),
            }
            for skill, count in top
        ],
        "total_jobs_analyzed": len(published_jobs),
        "candidate_skills_count": len(candidate_skills),
    }
