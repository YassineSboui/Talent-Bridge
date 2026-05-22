"""Train a local CV quality classifier.

This is a lightweight neural-network baseline that combines text TF-IDF features
and rule-based structure features. It is intentionally small so it can be
trained on student machines. When enough labeled examples exist, this can be
replaced by a transformer fine-tune without changing the API contract.

Usage:
    python scripts/train_quality_model.py
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import FunctionTransformer


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVQualityScoring.src.features import extract_quality_features, normalize_cv_text  # noqa: E402
from DocumentAI.CVQualityScoring.src.quality_model import FEATURE_NAMES, numeric_selector, text_selector  # noqa: E402


def load_records(dataset_path: Path) -> list[dict]:
    """Load labeled Pro/Non Pro CV records from a JSONL dataset."""
    records = []
    with dataset_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("text") and record.get("label") in {"Pro", "Non Pro"}:
                records.append(record)
    return records


def feature_matrix(records: list[dict]) -> list[dict]:
    """Recompute text and numeric quality features for sklearn training."""
    items = []
    for record in records:
        # Recompute features so older JSONL files automatically benefit from
        # improvements in app.quality without regenerating the dataset first.
        features = extract_quality_features(normalize_cv_text(record.get("text", "")), {})
        items.append({"text": record.get("text", ""), "features": features})
    return items


def train(dataset_path: Path, output_path: Path) -> dict:
    """Train and save the legacy sklearn Pro/Non Pro classifier."""
    records = load_records(dataset_path)
    if len(records) < 2:
        raise RuntimeError("Need at least 2 labeled records to train the quality model.")

    labels = [record["label"] for record in records]
    if len(set(labels)) < 2:
        raise RuntimeError(
            "Need both 'Pro' and 'Non Pro' labels. Edit the generated JSONL labels manually, "
            "or add more CV examples before training."
        )

    x = feature_matrix(records)
    y = labels
    stratify = y if min(y.count(label) for label in set(y)) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    pipeline = Pipeline(
        steps=[
            (
                "features",
                FeatureUnion(
                    transformer_list=[
                        (
                            "text",
                            Pipeline(
                                steps=[
                                    ("select", FunctionTransformer(text_selector, validate=False)),
                                    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)),
                                ]
                            ),
                        ),
                        (
                            "numeric",
                            Pipeline(
                                steps=[
                                    ("select", FunctionTransformer(numeric_selector, validate=False)),
                                    ("scale", StandardScaler()),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                MLPClassifier(
                    hidden_layer_sizes=(32,),
                    activation="tanh",
                    solver="lbfgs",
                    alpha=0.001,
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": pipeline,
        "feature_names": FEATURE_NAMES,
        "labels": sorted(set(y)),
        "training_records": len(records),
        "report": report,
    }
    with output_path.open("wb") as file:
        pickle.dump(artifact, file)

    return {"records": len(records), "labels": sorted(set(y)), "report": report, "output": str(output_path)}


def parse_args() -> argparse.Namespace:
    """Parse dataset and model artifact paths for sklearn training."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=str(REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_expanded.jsonl"),
        help="Input JSONL dataset.",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "Artifacts" / "models" / "document_ai" / "cv_quality_model.pkl"),
        help="Output model artifact.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for sklearn CV quality model training."""
    args = parse_args()
    result = train(Path(args.dataset), Path(args.output))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
