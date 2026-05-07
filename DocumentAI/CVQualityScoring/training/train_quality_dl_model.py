"""Train a PyTorch MLP CV quality scoring model."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVQualityScoring.src.dl_quality_model import CvQualityMlp  # noqa: E402
from DocumentAI.CVQualityScoring.src.grades import grade_from_score  # noqa: E402
from DocumentAI.CVQualityScoring.src.quality_model import FEATURE_NAMES  # noqa: E402


DEFAULT_DATASET = REPO_ROOT / "DocumentAI" / "CVQualityScoring" / "data" / "cv_quality_pseudo_labeled.jsonl"
DEFAULT_MODEL_DIR = REPO_ROOT / "Artifacts" / "models" / "document_ai" / "cv_quality_dl"
DEFAULT_REPORT_DIR = REPO_ROOT / "Artifacts" / "reports" / "document_ai"


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_records(dataset_path: Path) -> list[dict]:
    records = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("text") and record.get("manual_score") is not None:
                records.append(record)
    if len(records) < 200:
        raise ValueError("Need at least 200 records for DL quality training")
    return records


def numeric_matrix(records: list[dict]) -> np.ndarray:
    matrix = []
    for record in records:
        features = record.get("features", {})
        matrix.append([float(features.get(name, 0) or 0) for name in FEATURE_NAMES])
    return np.asarray(matrix, dtype=np.float32)


def build_inputs(vectorizer: TfidfVectorizer, scaler: StandardScaler, records: list[dict], *, fit: bool = False) -> np.ndarray:
    texts = [record.get("text", "") for record in records]
    numeric = numeric_matrix(records)
    if fit:
        text_features = vectorizer.fit_transform(texts).toarray().astype(np.float32)
        numeric_features = scaler.fit_transform(numeric).astype(np.float32)
    else:
        text_features = vectorizer.transform(texts).toarray().astype(np.float32)
        numeric_features = scaler.transform(numeric).astype(np.float32)
    return np.hstack([text_features, numeric_features]).astype(np.float32)


def sample_weights(records: list[dict]) -> np.ndarray:
    counts = Counter(record.get("grade") for record in records)
    return np.asarray([1.0 / max(counts.get(record.get("grade"), 1), 1) for record in records], dtype=np.float32) * len(records) / len(counts)


def run_epoch(model, loader, criterion, optimizer, device: torch.device) -> float:
    model.train(optimizer is not None)
    total_loss = 0.0
    total = 0
    for batch in loader:
        inputs, targets, weights = batch
        inputs = inputs.to(device)
        targets = targets.to(device)
        weights = weights.to(device)
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
        predictions = model(inputs)
        loss = (criterion(predictions, targets) * weights).mean()
        if optimizer is not None:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * inputs.size(0)
        total += inputs.size(0)
    return total_loss / max(total, 1)


def predict_scores(model, inputs: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    predictions = []
    with torch.no_grad():
        for start in range(0, len(inputs), 256):
            batch = torch.from_numpy(inputs[start : start + 256]).to(device)
            predictions.extend(model(batch).cpu().numpy().tolist())
    return np.asarray([max(0, min(value, 100)) for value in predictions], dtype=np.float32)


def evaluate(targets: np.ndarray, predictions: np.ndarray) -> dict:
    target_grades = [grade_from_score(score) for score in targets]
    predicted_grades = [grade_from_score(score) for score in predictions]
    return {
        "mae": round(float(mean_absolute_error(targets, predictions)), 4),
        "r2": round(float(r2_score(targets, predictions)), 4),
        "grade_accuracy": round(float(accuracy_score(target_grades, predicted_grades)), 4),
        "classification_report": classification_report(target_grades, predicted_grades, zero_division=0, output_dict=True),
    }


def write_preview(records: list[dict], targets: np.ndarray, predictions: np.ndarray, output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file_path", "category", "synthetic", "target_score", "predicted_score", "target_grade", "predicted_grade"])
        writer.writeheader()
        for record, target, prediction in zip(records[:250], targets[:250], predictions[:250]):
            writer.writerow(
                {
                    "file_path": record.get("file_path"),
                    "category": record.get("category"),
                    "synthetic": record.get("synthetic"),
                    "target_score": round(float(target), 2),
                    "predicted_score": round(float(prediction), 2),
                    "target_grade": grade_from_score(target),
                    "predicted_grade": grade_from_score(prediction),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CV quality DL model")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--max-features", type=int, default=2500)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    set_seed(args.seed)
    torch.set_num_threads(max(1, args.cpu_threads))
    records = load_records(args.dataset)
    grade_labels = [record.get("grade") for record in records]
    train_records, temp_records = train_test_split(records, test_size=0.3, random_state=args.seed, stratify=grade_labels)
    temp_grade_labels = [record.get("grade") for record in temp_records]
    val_records, test_records = train_test_split(temp_records, test_size=0.5, random_state=args.seed, stratify=temp_grade_labels)

    vectorizer = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2), min_df=2, max_df=0.92)
    scaler = StandardScaler()
    x_train = build_inputs(vectorizer, scaler, train_records, fit=True)
    x_val = build_inputs(vectorizer, scaler, val_records)
    x_test = build_inputs(vectorizer, scaler, test_records)
    y_train = np.asarray([record["manual_score"] for record in train_records], dtype=np.float32)
    y_val = np.asarray([record["manual_score"] for record in val_records], dtype=np.float32)
    y_test = np.asarray([record["manual_score"] for record in test_records], dtype=np.float32)

    train_weights = sample_weights(train_records)
    val_weights = np.ones(len(val_records), dtype=np.float32)
    train_loader = DataLoader(TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train), torch.from_numpy(train_weights)), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(x_val), torch.from_numpy(y_val), torch.from_numpy(val_weights)), batch_size=args.batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CvQualityMlp(input_size=x_train.shape[1], dropout=args.dropout).to(device)
    criterion = nn.SmoothL1Loss(reduction="none")
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.001)

    best_state = None
    best_val_mae = float("inf")
    stale = 0
    history = []
    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = run_epoch(model, val_loader, criterion, None, device)
        val_predictions = predict_scores(model, x_val, device)
        val_mae = mean_absolute_error(y_val, val_predictions)
        history.append({"epoch": epoch, "train_loss": round(train_loss, 5), "val_loss": round(val_loss, 5), "val_mae": round(float(val_mae), 4)})
        print(f"epoch={epoch} train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_mae={val_mae:.4f}")
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= args.patience:
                break

    if best_state is None:
        raise RuntimeError("Training failed to produce a model")
    model.load_state_dict(best_state)
    test_predictions = predict_scores(model, x_test, device)
    metrics = evaluate(y_test, test_predictions)

    if args.model_dir.exists() and args.force:
        shutil.rmtree(args.model_dir)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.model_dir / "model.pt")
    with (args.model_dir / "vectorizer.pkl").open("wb") as handle:
        pickle.dump(vectorizer, handle)
    with (args.model_dir / "scaler.pkl").open("wb") as handle:
        pickle.dump(scaler, handle)

    metadata = {
        "model_name": "cv_quality_mlp",
        "task": "cv_quality_score_regression_and_grade_classification",
        "input_size": int(x_train.shape[1]),
        "text_features": int(len(vectorizer.get_feature_names_out())),
        "numeric_features": len(FEATURE_NAMES),
        "dropout": args.dropout,
        "training_records": len(records),
        "train_samples": len(train_records),
        "validation_samples": len(val_records),
        "test_samples": len(test_records),
        "label_source": "rubric_pseudo_labels_plus_synthetic_variants",
        "grades": ["Excellent", "Good", "Average", "Weak", "Poor"],
        "device": str(device),
    }
    (args.model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = {"metadata": metadata, "history": history, "test_metrics": metrics}
    report_path = args.report_dir / "cv_quality_dl_metrics.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_preview(test_records, y_test, test_predictions, args.report_dir / "cv_quality_dl_predictions_preview.csv")

    print(json.dumps({"model_dir": str(args.model_dir), "report": str(report_path), "test_metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
