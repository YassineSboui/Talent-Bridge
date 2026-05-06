"""Validate and summarize the CV quality dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def validate(dataset_path: Path) -> dict:
    records = []
    errors = []
    with dataset_path.open("r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append({"line": line_num, "error": str(exc)})
                continue
            records.append(record)

    labels = Counter(record.get("label") for record in records)
    weak = sum(1 for record in records if record.get("weak_label"))
    synthetic = sum(1 for record in records if record.get("synthetic"))
    missing_text = [record.get("file_path") for record in records if not record.get("text")]
    invalid_labels = [record.get("file_path") for record in records if record.get("label") not in {"Pro", "Non Pro"}]

    recommendations = []
    if labels.get("Non Pro", 0) < 10:
        recommendations.append("Add at least 10 real manually labeled Non Pro CV examples.")
    if labels.get("Pro", 0) < 10:
        recommendations.append("Add at least 10 real manually labeled Pro CV examples.")
    if weak:
        recommendations.append("Review weak labels and set weak_label=false after manual validation.")
    if synthetic:
        recommendations.append("Replace synthetic examples with real CVs before reporting final model metrics.")

    return {
        "dataset": str(dataset_path),
        "records": len(records),
        "labels": dict(labels),
        "weak_label_count": weak,
        "synthetic_count": synthetic,
        "missing_text_count": len(missing_text),
        "invalid_label_count": len(invalid_labels),
        "json_errors": errors,
        "recommendations": recommendations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_expanded.jsonl"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(validate(Path(args.dataset)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
