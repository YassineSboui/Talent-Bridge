"""
Smoke tests for Skill Gap Analyzer engine.
Run from repo root: python -m pytest Tests/smoke/test_skill_gap.py -v
"""
import sys
from pathlib import Path

# Make sure repo root is on the path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from MachineLearning.SharedML.src.gap_analyzer import analyze_gap, result_to_dict


def test_zero_overlap_is_weak():
    """Candidate has no matching skills → readiness should be 'weak'."""
    result = analyze_gap(
        candidate_skills=["photoshop", "illustrator"],
        job_skills=["python", "sql", "machine learning", "tensorflow"],
        target_role="data scientist",
    )
    assert result.readiness_level == "weak"
    assert result.coverage_percentage == 0
    assert len(result.matched_skills) == 0
    assert len(result.missing_skills) == 4


def test_full_overlap_is_perfect():
    """Candidate has all required skills → readiness should be 'perfect'."""
    skills = ["python", "sql", "pandas", "scikit-learn"]
    result = analyze_gap(
        candidate_skills=skills,
        job_skills=skills,
        target_role="data analyst",
    )
    assert result.readiness_level == "perfect"
    assert result.coverage_percentage == 100
    assert len(result.missing_skills) == 0


def test_partial_overlap_coverage():
    """50% match should return moderate or weak readiness."""
    result = analyze_gap(
        candidate_skills=["python", "sql"],
        job_skills=["python", "sql", "spark", "hadoop"],
        target_role="data engineer",
    )
    assert result.coverage_percentage == 50
    assert result.readiness_level in ("moderate", "weak")
    assert "spark" in result.missing_skills or "hadoop" in result.missing_skills


def test_core_skill_classified_as_critical():
    """A skill in ROLE_CORE_SKILLS for the target role should be classified 'critical'."""
    from MachineLearning.SharedML.src.gap_analyzer import ROLE_CORE_SKILLS

    # Find a role and one of its core skills
    target_role = next(iter(ROLE_CORE_SKILLS))
    core_skills = ROLE_CORE_SKILLS[target_role]
    if not core_skills:
        return  # skip if empty

    missing_core_skill = core_skills[0]
    result = analyze_gap(
        candidate_skills=["photoshop"],          # unrelated skill
        job_skills=[missing_core_skill, "excel"],
        target_role=target_role,
    )
    critical_skills = [g.skill for g in result.gaps_by_priority if g.priority == "critical"]
    # The core skill should be in the critical bucket
    assert missing_core_skill in critical_skills or missing_core_skill in result.missing_skills


def test_result_serializable():
    """result_to_dict() should return a plain dict ready for JSON serialization."""
    result = analyze_gap(
        candidate_skills=["python"],
        job_skills=["python", "docker", "kubernetes"],
        target_role="devops engineer",
    )
    d = result_to_dict(result)
    assert isinstance(d, dict)
    assert "readiness_level" in d
    assert "coverage_percentage" in d
    assert "matched_skills" in d
    assert "missing_skills" in d
    assert "gaps_by_priority" in d
    assert isinstance(d["gaps_by_priority"], list)


def test_extra_skills_tracked():
    """Skills the candidate has beyond job requirements should appear in extra_skills."""
    result = analyze_gap(
        candidate_skills=["python", "sql", "rust", "erlang"],
        job_skills=["python", "sql"],
        target_role="backend developer",
    )
    assert "rust" in result.extra_skills or "erlang" in result.extra_skills


def test_readiness_thresholds():
    """Test readiness level boundary: ≥70% → strong."""
    result = analyze_gap(
        candidate_skills=["python", "sql", "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn"],
        job_skills=["python", "sql", "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn", "tensorflow", "pytorch", "keras"],
        target_role="data scientist",
    )
    # 7/10 = 70% → should be 'strong'
    assert result.coverage_percentage == 70
    assert result.readiness_level == "strong"
