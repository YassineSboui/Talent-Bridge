"""Smoke-test CV quality and matching behavior without SQL Server.

The goal is not scientific evaluation. It protects the demo from obvious false
positives: weak CVs should be Non Pro, and one-skill job overlaps should not
look like excellent matches.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.matching import build_candidate_profile, rank_jobs  # noqa: E402
from app.quality import classify_cv_quality  # noqa: E402


GOOD_CV = """
Yassine Demo
yassine.demo@example.com | +216 22 333 444 | linkedin.com/in/yassine | github.com/yassine

Professional Experience
Data Analyst Intern, Demo Company, 2023-2024
- Built SQL dashboards and automated Power BI reporting for weekly business KPIs.
- Cleaned datasets with Python, pandas, Excel, and SQL Server.

Projects
- Sales analytics dashboard with SQL, Power BI, Python, and statistics.
- Customer segmentation project using Python and scikit-learn.

Skills
SQL, Python, Excel, Power BI, Tableau, data analysis, statistics, pandas, scikit-learn

Education
Bachelor degree in Computer Science, Demo University, 2024

Languages
French, English, Arabic
"""

SHORT_BAD_CV = """John. Python. available."""

NO_CONTACT_CV = """
Professional Experience
Software Developer Intern

Skills
Python, JavaScript, React, SQL

Education
Computer Science Bachelor

Projects
Built a web application and a small dashboard.
"""


def run_quality_checks() -> list[dict]:
    cases = [
        ("complete_professional_cv", GOOD_CV, "Pro"),
        ("too_short_cv", SHORT_BAD_CV, "Non Pro"),
        ("missing_contact_cv", NO_CONTACT_CV, "Non Pro"),
    ]
    rows = []
    for name, text, expected in cases:
        result = classify_cv_quality(text, {})
        rows.append(
            {
                "case": name,
                "expected": expected,
                "actual": result["quality_label"],
                "score": result["quality_score"],
                "confidence": result.get("confidence"),
                "passed": result["quality_label"] == expected,
                "hard_gates": result.get("hard_gates", []),
            }
        )
    return rows


def run_matching_checks() -> list[dict]:
    candidate = build_candidate_profile(
        {
            "name": ["Yassine Demo"],
            "email_addresses": ["yassine.demo@example.com"],
            "skills": ["SQL", "Python", "Power BI", "Excel", "Pandas", "Statistics"],
            "degrees": ["Bachelor Computer Science"],
            "languages": ["French", "English"],
            "years_of_experience": ["2 years"],
        },
        target_role="Data Analyst",
    )
    jobs = [
        {
            "job_posting_key": 1,
            "job_title": "Data Analyst",
            "category_name": "Data Analyst",
            "company_name": "Strong Analytics",
            "country": "France",
            "skills_csv": "SQL,Python,Power BI,Excel",
            "has_salary_info": True,
            "is_work_from_home": True,
            "no_degree_mention": False,
        },
        {
            "job_posting_key": 2,
            "job_title": "Data Analyst",
            "category_name": "Data Analyst",
            "company_name": "Weak One Skill",
            "country": "France",
            "skills_csv": "CSS",
            "has_salary_info": True,
            "is_work_from_home": True,
            "no_degree_mention": True,
        },
        {
            "job_posting_key": 3,
            "job_title": "Frontend Engineer",
            "category_name": "Software Engineer",
            "company_name": "Wrong Role",
            "country": "France",
            "skills_csv": "React,JavaScript,CSS",
            "has_salary_info": True,
            "is_work_from_home": False,
            "no_degree_mention": False,
        },
        {
            "job_posting_key": 4,
            "job_title": "Data Analyst",
            "category_name": "Data Analyst",
            "company_name": "No Structured Skills",
            "country": "France",
            "skills_csv": "",
            "has_salary_info": True,
            "is_work_from_home": True,
            "no_degree_mention": True,
        },
    ]
    ranked = rank_jobs(candidate, jobs, limit=4)
    checks = {
        1: lambda score: score >= 85,
        2: lambda score: score <= 58,
        3: lambda score: score <= 59,
        4: lambda score: score <= 72,
    }
    return [
        {
            "job_id": item["job_id"],
            "job_title": item["job_title"],
            "score": item["match_score"],
            "skills_score": item["score_breakdown"]["skills"],
            "semantic_score": item["score_breakdown"]["semantic"],
            "matched_skills": item["matched_skills"],
            "passed": checks[item["job_id"]](item["match_score"]),
        }
        for item in sorted(ranked, key=lambda row: row["job_id"])
    ]


def main() -> None:
    quality = run_quality_checks()
    matching = run_matching_checks()
    payload = {"quality": quality, "matching": matching}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if not all(row["passed"] for row in quality + matching):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
