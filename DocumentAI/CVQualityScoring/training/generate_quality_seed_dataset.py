"""Generate a larger bootstrap Pro / Non Pro CV quality dataset.

This creates synthetic but realistic IT CV examples for project bootstrapping.
It should be replaced or validated with real manually labeled CVs before using
model metrics as final scientific results.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVQualityScoring.src.quality import classify_cv_quality  # noqa: E402


random.seed(42)

PROFILES = [
    {
        "role": "Data Analyst",
        "skills": ["SQL", "Python", "Power BI", "Excel", "Tableau", "DAX", "Data Cleaning"],
        "projects": ["sales dashboard", "customer segmentation", "KPI monitoring report"],
    },
    {
        "role": "Business Analyst",
        "skills": ["UML", "Scrum", "Jira", "SQL", "Process Modeling", "User Stories", "Power BI"],
        "projects": ["requirements workshop", "process optimization", "functional specification"],
    },
    {
        "role": "Software Engineer",
        "skills": ["JavaScript", "Vue", "React", "Node.js", "FastAPI", "Docker", "Git"],
        "projects": ["web application", "REST API", "authentication module"],
    },
    {
        "role": "Data Engineer",
        "skills": ["Python", "SQL", "Spark", "Airflow", "Azure", "Databricks", "Docker"],
        "projects": ["ETL pipeline", "data lake ingestion", "warehouse optimization"],
    },
    {
        "role": "Machine Learning Engineer",
        "skills": ["Python", "Scikit-Learn", "TensorFlow", "PyTorch", "NLP", "MLflow", "FastAPI"],
        "projects": ["classification model", "recommendation system", "model serving API"],
    },
]

NAMES = [
    "Amine Trabelsi", "Nour Ben Ali", "Sarra Mansour", "Karim Haddad", "Lina Ferchichi",
    "Youssef Gharbi", "Meriem Saidi", "Anis Jlassi", "Rania Kallel", "Omar Mezni",
]

SCHOOLS = ["ESPRIT", "INSAT", "ENIT", "FST Tunis", "IHEC Carthage", "ISG Tunis"]
COMPANIES = ["NeoLedge", "Sofiatech", "Telnet", "Vermeg", "Talan", "Actia", "Ooredoo"]


def make_pro_cv(index: int) -> str:
    profile = random.choice(PROFILES)
    name = NAMES[index % len(NAMES)]
    school = random.choice(SCHOOLS)
    company = random.choice(COMPANIES)
    project = random.choice(profile["projects"])
    skills = ", ".join(profile["skills"])
    return f"""{name}
{profile['role']} · Tunis
Email: {name.lower().replace(' ', '.')}@example.com
Phone: +216 {random.randint(20, 99)} {random.randint(100, 999)} {random.randint(100, 999)}
LinkedIn: linkedin.com/in/{name.lower().replace(' ', '-')}
GitHub: github.com/{name.lower().replace(' ', '')}

PROFESSIONAL SUMMARY
Motivated {profile['role']} with {random.randint(1, 6)} years of experience in IT projects, data-driven decision making, and agile teamwork. Strong ability to translate business needs into reliable technical solutions.

SKILLS
{skills}

EXPERIENCE
{company} - {profile['role']}
2022 - Present
- Built and maintained a {project} used by business stakeholders.
- Collaborated with cross-functional teams using agile methods.
- Improved reporting quality, delivery speed, and documentation.

Internship - Junior {profile['role']}
2021 - 2022
- Participated in data preparation, testing, and technical documentation.
- Delivered dashboards and scripts for internal teams.

EDUCATION
Engineering Degree in Computer Science - {school}
Bachelor in Information Systems - University of Tunis

PROJECTS
Academic project: {project} using {profile['skills'][0]}, {profile['skills'][1]}, and {profile['skills'][2]}.

LANGUAGES
Arabic: Native
French: Professional
English: Professional

CERTIFICATIONS
Scrum Fundamentals · Microsoft Data Fundamentals · Git/GitHub Training
"""


def make_non_pro_cv(index: int) -> str:
    variants = [
        f"""{NAMES[index % len(NAMES)]}
looking job computer
skills python sql java
worked many things
please contact me
""",
        f"""cv cv cv cv cv
name {NAMES[index % len(NAMES)]}
good worker serious motivated dynamic motivated dynamic motivated dynamic
school yes
job yes
skills many software computer internet
""",
        f"""{NAMES[index % len(NAMES)]}
{random.choice(['Data', 'IT', 'Web'])}
I know Excel. I know computer. I want internship. No phone no email.
""",
        " ".join(list(f"{NAMES[index % len(NAMES)]} bad extraction curriculum vitae skills java sql experience education")),
        f"""{NAMES[index % len(NAMES)]}
Email missing
Phone missing
SKILLS
good communication
""",
        f"""{NAMES[index % len(NAMES)]}
{random.choice(['Python Python Python', 'SQL SQL SQL', 'Java Java Java'])}
{random.choice(['experience experience experience', 'education education education'])}
""",
    ]
    return random.choice(variants)


def record_from_text(text: str, label: str, index: int, synthetic_type: str) -> dict:
    quality = classify_cv_quality(text, extraction={})
    return {
        "file_path": f"synthetic://{synthetic_type}/{index}",
        "text": text,
        "label": label,
        "weak_label": True,
        "synthetic": True,
        "quality_score": quality["quality_score"],
        "structure_score": quality["structure_score"],
        "content_score": quality["content_score"],
        "features": quality["features"],
        "issues": quality["issues"],
        "suggestions": quality["suggestions"],
    }


def generate(count_per_class: int) -> list[dict]:
    records = []
    for index in range(count_per_class):
        records.append(record_from_text(make_pro_cv(index), "Pro", index, "pro"))
        records.append(record_from_text(make_non_pro_cv(index), "Non Pro", index, "non_pro"))
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-per-class", type=int, default=40)
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_seed.jsonl"),
    )
    parser.add_argument(
        "--merge-output",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_expanded.jsonl"),
    )
    parser.add_argument(
        "--base",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality.jsonl"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    seed_records = generate(args.count_per_class)

    with output.open("w", encoding="utf-8") as file:
        for record in seed_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    merged_records = []
    base_path = Path(args.base)
    if base_path.exists():
        with base_path.open("r", encoding="utf-8") as file:
            merged_records.extend(json.loads(line) for line in file if line.strip())
    merged_records.extend(seed_records)

    merge_output = Path(args.merge_output)
    with merge_output.open("w", encoding="utf-8") as file:
        for record in merged_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(seed_records)} seed records to {output}")
    print(f"Wrote {len(merged_records)} merged records to {merge_output}")


if __name__ == "__main__":
    main()
