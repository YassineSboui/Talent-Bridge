from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from NLP.CVExtraction.src.pdf_reader import extract_text_from_pdf
from DocumentAI.CVQualityScoring.src.features import extract_quality_features, normalize_cv_text


REPO_ROOT = Path(__file__).resolve().parents[3]


def merge_manual_labels(input_csv: Path, output_jsonl: Path) -> int:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with input_csv.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            label = (row.get("label") or "").strip()
            if label not in {"Pro", "Non Pro"}:
                continue
            pdf_path = (REPO_ROOT / (row.get("file_path") or "")).resolve()
            if not pdf_path.exists():
                continue
            text = extract_text_from_pdf(pdf_path.read_bytes())
            normalized = normalize_cv_text(text)
            records.append({
                "file_path": str(pdf_path),
                "text": text,
                "label": label,
                "weak_label": False,
                "synthetic": False,
                "reviewer": row.get("reviewer") or None,
                "review_date": row.get("review_date") or None,
                "notes": row.get("notes") or None,
                "features": extract_quality_features(normalized, {}),
            })
    with output_jsonl.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "manual_labeling_template.csv"))
    parser.add_argument("--output", default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_manual.jsonl"))
    args = parser.parse_args()
    count = merge_manual_labels(Path(args.input), Path(args.output))
    print(f"Wrote {count} manually labeled CV records to {args.output}")


if __name__ == "__main__":
    main()
