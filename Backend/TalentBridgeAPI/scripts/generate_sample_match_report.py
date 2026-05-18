"""Generate a JSON report of matches for available sample CV PDFs."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from fastapi import UploadFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import analyze_cv_full  # noqa: E402


ROLE_HINTS = [
    ("analyst", "Data Analyst"),
    ("business", "Business Analyst"),
    ("scientist", "Data Scientist"),
    ("machine", "Machine Learning Engineer"),
    ("developpeur", "Software Engineer"),
    ("développeur", "Software Engineer"),
    ("developer", "Software Engineer"),
    ("full-stack", "Software Engineer"),
    ("data engineer", "Data Engineer"),
]


async def generate_report(pdf_paths: list[Path], output_path: Path, limit: int, max_candidates: int) -> list[dict]:
    rows = []
    for pdf_path in pdf_paths:
        target_role = _guess_role(pdf_path.name)
        with pdf_path.open("rb") as file:
            result = await analyze_cv_full(
                UploadFile(filename=pdf_path.name, file=file),
                target_role=target_role,
                preferred_country=None,
                remote_preference="any",
                limit=limit,
                max_candidates=max_candidates,
                save_results=False,
            )
        rows.append(
            {
                "file": str(pdf_path),
                "target_role": target_role,
                "quality_label": result["quality"]["quality_label"],
                "quality_score": result["quality"]["quality_score"],
                "skills": (result.get("candidate_profile") or {}).get("skills", [])[:20],
                "top_matches": [
                    {
                        "rank": idx + 1,
                        "job_id": match["job_id"],
                        "job_title": match["job_title"],
                        "company": match["company"],
                        "country": match["country"],
                        "match_score": match["match_score"],
                        "semantic_score": (match.get("score_breakdown") or {}).get("semantic"),
                        "matched_skills": match["matched_skills"],
                        "missing_skills": match["missing_skills"][:10],
                    }
                    for idx, match in enumerate(result.get("matches", []))
                ],
                "matching_error": result.get("matching_error"),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return rows


def _guess_role(file_name: str) -> str:
    normalized = file_name.lower()
    for needle, role in ROLE_HINTS:
        if needle in normalized:
            return role
    return "Data Analyst"


def _default_pdfs() -> list[Path]:
    paths = [PROJECT_ROOT / "test_cv.pdf"]
    test_dir = WORKSPACE_ROOT / "Test CV"
    if test_dir.exists():
        paths.extend(sorted(test_dir.glob("*.pdf")))
    return [path for path in paths if path.exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", default=None, help="PDF file. Can be repeated.")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "reports" / "sample_match_report.json"),
    )
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_paths = [Path(path) for path in args.input] if args.input else _default_pdfs()
    rows = asyncio.run(generate_report(pdf_paths, Path(args.output), args.limit, args.max_candidates))
    print(f"Wrote {len(rows)} sample CV match reports to {args.output}")


if __name__ == "__main__":
    main()
