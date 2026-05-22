"""Generate a rich pseudo-labeled CV quality dataset from real CV PDFs.

The labels are deterministic rubric labels, not human ground truth. They are
useful for a demo-grade DL model and should be replaced or audited with manual
labels before making scientific claims.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVQualityScoring.src.features import extract_quality_features, normalize_cv_text  # noqa: E402
from DocumentAI.CVQualityScoring.src.grades import binary_label_from_grade, grade_from_score  # noqa: E402
from DocumentAI.CVQualityScoring.src.rules import quality_hard_gates  # noqa: E402
from NLP.CVExtraction.src.pdf_reader import extract_text_from_pdf  # noqa: E402


DEFAULT_INPUT = REPO_ROOT / "Data" / "document_classification" / "raw" / "cv"
DEFAULT_OUTPUT = REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_pseudo_labeled.jsonl"

ROLES = [
    "Data Analyst", "Software Engineer", "Business Analyst", "Data Engineer", "Project Manager",
    "HR Specialist", "Accountant", "Sales Representative", "Teacher", "Mechanical Engineer",
]
SKILLS = [
    "Python", "SQL", "Excel", "Power BI", "JavaScript", "Communication", "Project Management",
    "Data Analysis", "Reporting", "Customer Service", "Problem Solving", "Teamwork",
]
SCHOOLS = ["University of Tunis", "ESPRIT", "INSAT", "ENIT", "IHEC", "Faculty of Sciences"]
COMPANIES = ["NeoLedge", "Talan", "Vermeg", "Actia", "Telnet", "Ooredoo", "Sofrecom"]


def iter_pdfs(input_dir: Path, limit: int | None = None) -> list[Path]:
    """Return CV PDF paths from an input directory, optionally capped."""
    files = sorted(input_dir.rglob("*.pdf"))
    return files[:limit] if limit else files


def rubric_score(text: str, features: dict[str, Any]) -> tuple[int, dict[str, int]]:
    """Compute the pseudo-label score from explainable CV quality rubric parts."""
    score_parts = {
        "contact": 0,
        "core_sections": 0,
        "structure": 0,
        "professional_depth": 0,
        "readability": 0,
        "impact": 0,
    }
    score_parts["contact"] = 8 * int(features["has_email"]) + 6 * int(features["has_phone"]) + 4 * int(features["has_profile_link"])
    score_parts["core_sections"] = 12 * int(features["has_skills_section"]) + 12 * int(features["has_education_section"]) + 12 * int(features["has_experience_or_projects"])
    score_parts["structure"] = min(12, features["section_count"] * 3) + min(5, features["bullet_line_count"])
    score_parts["professional_depth"] = min(14, int(features["word_count"] / 90)) + 5 * int(features["has_professional_dates"])
    score_parts["readability"] = 8 * int(features["low_noise"]) + 5 * int(features["low_repetition"])
    score_parts["impact"] = 4 * int(features["has_quantified_impact"])
    score = sum(score_parts.values())

    gates = quality_hard_gates(features)
    if gates:
        score = min(score, 54)
    if features["word_count"] < 180:
        score = min(score, 45)
    if features["word_count"] > 1200 and features["low_noise"] and features["core_section_count"] >= 3:
        score += 4
    return max(0, min(int(round(score)), 100)), score_parts


def make_variant(text: str, variant: str) -> str:
    """Create degraded synthetic variants from real CV text for calibration."""
    words = text.split()
    if variant == "poor_short":
        return " ".join(words[:55])
    if variant == "weak_missing_contact":
        cleaned = re.sub(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "", text)
        cleaned = re.sub(r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?){2,5}\d{1,4}", "", cleaned)
        return "\n".join(cleaned.splitlines()[:35])
    if variant == "average_excerpt":
        return " ".join(words[:260])
    if variant == "noisy_repeated":
        excerpt = " ".join(words[:100])
        return "\n".join([excerpt] * 5)
    return text


def record_for_text(file_path: str, text: str, *, category: str, synthetic: bool, variant: str | None = None) -> dict[str, Any]:
    """Build one pseudo-labeled CV quality training record."""
    normalized = normalize_cv_text(text)
    features = extract_quality_features(normalized, {})
    score, score_parts = rubric_score(normalized, features)
    grade = grade_from_score(score)
    return {
        "file_path": file_path,
        "category": category,
        "text": text,
        "manual_score": score,
        "grade": grade,
        "label": binary_label_from_grade(grade),
        "weak_label": True,
        "synthetic": synthetic,
        "variant": variant,
        "score_parts": score_parts,
        "features": features,
        "label_source": "rubric_pseudo_label",
    }


def synthetic_grade_text(grade: str, index: int) -> tuple[str, int]:
    """Generate controlled synthetic CV text for a target quality grade."""
    role = ROLES[index % len(ROLES)]
    name = f"Candidate {grade} {index:03d}"
    skill_line = ", ".join(random.sample(SKILLS, 7))
    school = random.choice(SCHOOLS)
    company = random.choice(COMPANIES)

    if grade == "Excellent":
        score = random.randint(91, 98)
        text = f"""{name}
{role} | Tunis, Tunisia
Email: candidate{index}@example.com | Phone: +216 55 123 45{index % 10}
LinkedIn: linkedin.com/in/candidate-{index} | GitHub: github.com/candidate{index}

PROFESSIONAL SUMMARY
Results-driven {role} with 5 years of experience delivering measurable business impact, analytics, documentation, and cross-functional projects.

SKILLS
{skill_line}

EXPERIENCE
{company} - Senior {role}
2021 - Present
- Delivered 12 dashboards and automated reports used by 80 business users.
- Improved processing time by 35% through better workflows and documentation.
- Coordinated agile delivery with product, data, and operations teams.

Previous Company - {role}
2019 - 2021
- Built reusable templates, trained junior colleagues, and improved reporting quality.

EDUCATION
Master Degree - {school} - 2018

PROJECTS
Portfolio project using Python, SQL, Power BI, and documented APIs.

LANGUAGES
Arabic native, French professional, English professional

CERTIFICATIONS
Scrum Fundamentals, Microsoft Data Fundamentals, Git/GitHub Training
"""
    elif grade == "Good":
        score = random.randint(76, 88)
        text = f"""{name}
{role}
Email: candidate{index}@example.com | Phone: +216 22 456 78{index % 10}
LinkedIn: linkedin.com/in/candidate-good-{index}

SUMMARY
Motivated {role} with practical experience in business projects, reporting, teamwork, and technical documentation.

SKILLS
{skill_line}

EXPERIENCE
{company} - {role}
2022 - Present
- Participated in reporting, analysis, planning, and operational improvement tasks.
- Collaborated with team members and documented project deliverables.

EDUCATION
Bachelor Degree - {school} - 2021

PROJECTS
Academic and professional projects using {SKILLS[index % len(SKILLS)]} and {SKILLS[(index + 3) % len(SKILLS)]}.

LANGUAGES
Arabic, French, English
"""
    elif grade == "Average":
        score = random.randint(56, 72)
        text = f"""{name}
{role}
Email: candidate{index}@example.com

PROFILE
I am looking for a job as {role}. I worked on different projects and can learn quickly.

SKILLS
{', '.join(random.sample(SKILLS, 4))}

EXPERIENCE
Internship - {company}
2023
- Helped with reports and daily tasks.

EDUCATION
{school}

LANGUAGES
Arabic, French
"""
    elif grade == "Weak":
        score = random.randint(36, 53)
        text = f"""{name}
{role}
Phone: +216 99 111 22{index % 10}

SKILLS
computer, office, communication

EXPERIENCE
worked in projects and internships

EDUCATION
university studies
"""
    else:
        score = random.randint(12, 32)
        text = f"""{name}
looking for job
computer internet office
good worker motivated serious
"""
    return text, score


def synthetic_grade_records(count_per_grade: int) -> list[dict[str, Any]]:
    """Generate balanced synthetic records for all quality grades."""
    records = []
    for grade in ["Excellent", "Good", "Average", "Weak", "Poor"]:
        for index in range(count_per_grade):
            text, score = synthetic_grade_text(grade, index)
            normalized = normalize_cv_text(text)
            features = extract_quality_features(normalized, {})
            records.append(
                {
                    "file_path": f"synthetic://quality_grade/{grade.lower()}/{index}",
                    "category": "synthetic_quality_calibration",
                    "text": text,
                    "manual_score": score,
                    "grade": grade,
                    "label": binary_label_from_grade(grade),
                    "weak_label": True,
                    "synthetic": True,
                    "variant": "controlled_grade",
                    "score_parts": {},
                    "features": features,
                    "label_source": "controlled_synthetic_grade",
                }
            )
    return records


def build_dataset(input_dir: Path, output_path: Path, limit: int | None = None, seed: int = 42, synthetic_per_grade: int = 300) -> dict[str, Any]:
    """Build the full pseudo-labeled CV quality JSONL dataset."""
    random.seed(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    pdfs = iter_pdfs(input_dir, limit)

    for pdf_path in pdfs:
        category = pdf_path.parent.name
        try:
            text = extract_text_from_pdf(pdf_path.read_bytes())
        except Exception as exc:
            errors.append({"file_path": str(pdf_path), "error": str(exc)})
            continue
        if not text.strip():
            errors.append({"file_path": str(pdf_path), "error": "empty_text"})
            continue

        records.append(record_for_text(str(pdf_path), text, category=category, synthetic=False))
        for variant in ["poor_short", "weak_missing_contact", "average_excerpt", "noisy_repeated"]:
            variant_text = make_variant(text, variant)
            records.append(record_for_text(f"{pdf_path}::{variant}", variant_text, category=category, synthetic=True, variant=variant))

    records.extend(synthetic_grade_records(synthetic_per_grade))
    random.shuffle(records)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    grade_counts: dict[str, int] = {}
    for record in records:
        grade_counts[record["grade"]] = grade_counts.get(record["grade"], 0) + 1
    return {"records": len(records), "real_pdfs": len(pdfs), "errors": len(errors), "grades": grade_counts, "output": str(output_path)}


def main() -> None:
    """CLI entry point for building the pseudo-labeled quality dataset."""
    parser = argparse.ArgumentParser(description="Build pseudo-labeled CV quality dataset")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--synthetic-per-grade", type=int, default=300)
    args = parser.parse_args()
    print(json.dumps(build_dataset(args.input, args.output, args.limit, args.seed, args.synthetic_per_grade), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
