"""Build a balanced local dataset for CV-vs-Non-CV document classification."""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVDocumentClassification.src.preprocessing import supported_files


DEFAULT_CV_SOURCE = Path(r"C:\Users\YassineSBOUI\Downloads\CV")
DEFAULT_NON_CV_SOURCE = Path(r"C:\Users\YassineSBOUI\Downloads\NON_CV")
DEFAULT_OUTPUT_DIR = Path("Data/document_classification")
DEFAULT_EXTRA_CV_DIR = Path("Data/samples/cv")


def collect_by_category(root: Path) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for path in supported_files(root):
        try:
            category = path.relative_to(root).parts[0]
        except IndexError:
            category = "uncategorized"
        grouped.setdefault(category, []).append(path)
    return grouped


def stratified_sample(grouped: dict[str, list[Path]], total: int, seed: int) -> list[tuple[str, Path]]:
    rng = random.Random(seed)
    available = {category: sorted(files) for category, files in grouped.items() if files}
    total_available = sum(len(files) for files in available.values())
    if total_available == 0:
        return []
    target_total = min(total, total_available)

    allocations: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    for category, files in available.items():
        raw = target_total * len(files) / total_available
        base = min(len(files), int(raw))
        allocations[category] = base
        remainders.append((raw - base, category))

    remaining = target_total - sum(allocations.values())
    for _, category in sorted(remainders, reverse=True):
        if remaining <= 0:
            break
        if allocations[category] < len(available[category]):
            allocations[category] += 1
            remaining -= 1

    sampled: list[tuple[str, Path]] = []
    for category, files in available.items():
        rng.shuffle(files)
        sampled.extend((category, path) for path in files[: allocations[category]])
    rng.shuffle(sampled)
    return sampled


def copy_samples(samples: list[tuple[str, Path]], output_root: Path, label: str, *, start_index: int = 1) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (category, source_path) in enumerate(samples, start=start_index):
        safe_category = category.replace(" ", "_")
        extension = source_path.suffix.lower()
        sample_id = f"{label}_{index:05d}"
        destination = output_root / "raw" / label / safe_category / f"{sample_id}{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        rows.append(
            {
                "sample_id": sample_id,
                "label": label,
                "category": category,
                "relative_path": destination.relative_to(output_root).as_posix(),
                "original_path": str(source_path),
                "extension": extension,
            }
        )
    return rows


def write_manifest(output_dir: Path, rows: list[dict[str, str]]) -> None:
    manifest_path = output_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "label", "category", "relative_path", "original_path", "extension"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare balanced CV-vs-Non-CV dataset")
    parser.add_argument("--cv-source", type=Path, default=DEFAULT_CV_SOURCE)
    parser.add_argument("--non-cv-source", type=Path, default=DEFAULT_NON_CV_SOURCE)
    parser.add_argument("--extra-cv-dir", type=Path, default=DEFAULT_EXTRA_CV_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cv-samples", type=int, default=1200)
    parser.add_argument("--non-cv-samples", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.cv_source.exists():
        raise FileNotFoundError(args.cv_source)
    if not args.non_cv_source.exists():
        raise FileNotFoundError(args.non_cv_source)
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.force:
        raise FileExistsError(f"Output dataset already exists. Use --force to rebuild: {args.output_dir}")

    if args.output_dir.exists() and args.force:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cv_samples = stratified_sample(collect_by_category(args.cv_source), args.cv_samples, args.seed)
    non_cv_samples = stratified_sample(collect_by_category(args.non_cv_source), args.non_cv_samples, args.seed + 1)
    rows = copy_samples(cv_samples, args.output_dir, "cv")
    extra_cv_samples: list[tuple[str, Path]] = []
    if args.extra_cv_dir.exists():
        extra_cv_samples = [("local_samples", path) for path in sorted(supported_files(args.extra_cv_dir))]
        rows.extend(copy_samples(extra_cv_samples, args.output_dir, "cv", start_index=len(rows) + 1))
    rows.extend(copy_samples(non_cv_samples, args.output_dir, "non_cv"))
    rows.sort(key=lambda item: (item["label"], item["sample_id"]))
    write_manifest(args.output_dir, rows)

    print(f"Prepared {len(cv_samples)} source CV, {len(extra_cv_samples)} extra CV, and {len(non_cv_samples)} Non-CV samples")
    print(f"Dataset: {args.output_dir}")
    print(f"Manifest: {args.output_dir / 'manifest.csv'}")


if __name__ == "__main__":
    main()
