"""Build a CV quality dataset from PDF files.

The script extracts PDF text, applies the rule-based quality classifier, and
writes JSONL records that can be manually reviewed before model training.

Usage:
    python scripts/build_quality_dataset.py
    python scripts/build_quality_dataset.py --input "../Test CV" --output data/quality/cv_quality.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from NLP.CVExtraction.src.pdf_reader import extract_text_from_pdf  # noqa: E402
from DocumentAI.CVQualityScoring.src.quality import classify_cv_quality  # noqa: E402


def build_dataset(input_paths: list[Path], output_path: Path, synthetic_negatives: bool = True) -> int:
    """Build a weak-labeled Pro/Non Pro dataset from PDF CV inputs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for pdf_path in _iter_pdfs(input_paths):
        try:
            text = extract_text_from_pdf(pdf_path.read_bytes())
            quality = classify_cv_quality(text, extraction={})
        except Exception as exc:
            records.append(
                {
                    "file_path": str(pdf_path),
                    "text": "",
                    "label": "Non Pro",
                    "weak_label": True,
                    "quality_score": 0,
                    "features": {},
                    "error": str(exc),
                }
            )
            continue

        records.append(
            {
                "file_path": str(pdf_path),
                "text": text,
                "label": quality["quality_label"],
                "weak_label": True,
                "quality_score": quality["quality_score"],
                "structure_score": quality["structure_score"],
                "content_score": quality["content_score"],
                "features": quality["features"],
                "issues": quality["issues"],
                "suggestions": quality["suggestions"],
            }
        )

        if synthetic_negatives:
            records.extend(_make_synthetic_non_pro_records(pdf_path, text))

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(records)


def _make_synthetic_non_pro_records(pdf_path: Path, text: str) -> list[dict]:
    """Create weak Non Pro examples until manually labeled data exists."""
    short_text = " ".join(text.split()[:45])
    noisy_text = " ".join(char for char in text[:250])
    examples = [
        (
            "too_short",
            short_text,
            "Synthetic negative: incomplete CV excerpt with missing sections.",
        ),
        (
            "noisy_extraction",
            noisy_text,
            "Synthetic negative: simulated noisy extraction with broken spacing.",
        ),
    ]
    records = []
    for variant, synthetic_text, note in examples:
        quality = classify_cv_quality(synthetic_text, extraction={})
        records.append(
            {
                "file_path": f"{pdf_path}::{variant}",
                "text": synthetic_text,
                "label": "Non Pro",
                "weak_label": True,
                "synthetic": True,
                "quality_score": quality["quality_score"],
                "structure_score": quality["structure_score"],
                "content_score": quality["content_score"],
                "features": quality["features"],
                "issues": quality["issues"],
                "suggestions": quality["suggestions"],
                "note": note,
            }
        )
    return records


def _iter_pdfs(paths: list[Path]):
    """Yield unique PDF files from explicit paths or directories."""
    seen = set()
    for path in paths:
        path = path.resolve()
        if path.is_file() and path.suffix.lower() == ".pdf":
            if path not in seen:
                seen.add(path)
                yield path
        elif path.is_dir():
            for pdf_path in sorted(path.rglob("*.pdf")):
                pdf_path = pdf_path.resolve()
                if pdf_path not in seen:
                    seen.add(pdf_path)
                    yield pdf_path


def parse_args() -> argparse.Namespace:
    """Parse dataset input/output options for weak-label generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        action="append",
        default=None,
        help="PDF file or directory. Can be provided multiple times.",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality.jsonl"),
        help="Output JSONL dataset path.",
    )
    parser.add_argument(
        "--no-synthetic-negatives",
        action="store_true",
        help="Do not add weak synthetic Non Pro examples.",
    )
    return parser.parse_args()


def main() -> None:
    """Build the weak-labeled quality dataset from CLI arguments."""
    args = parse_args()
    inputs = [Path(value) for value in args.input] if args.input else [
        REPO_ROOT / "Backend" / "TalentBridgeAPI" / "test_cv.pdf",
        REPO_ROOT / "Data" / "samples" / "cv",
    ]
    count = build_dataset(inputs, Path(args.output), synthetic_negatives=not args.no_synthetic_negatives)
    print(f"Wrote {count} records to {args.output}")


if __name__ == "__main__":
    main()
