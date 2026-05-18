"""Train a compact CNN for CV-vs-Non-CV document classification."""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from DocumentAI.CVDocumentClassification.src.model import CvDocumentCnn
from DocumentAI.CVDocumentClassification.src.preprocessing import array_to_tensor, document_to_array


DEFAULT_DATA_DIR = Path("Data/document_classification")
DEFAULT_MODEL_DIR = Path("Artifacts/models/document_ai/cv_document_classifier")
DEFAULT_REPORT_DIR = Path("Artifacts/reports/document_ai")
DEFAULT_CACHE_DIR = Path("Artifacts/cache/cv_document_classifier")


class DocumentDataset(Dataset):
    def __init__(self, rows: list[dict[str, str]], data_dir: Path, cache_dir: Path, image_size: tuple[int, int]) -> None:
        self.rows = rows
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.image_size = image_size

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        sample_id = row["sample_id"]
        cache_path = self.cache_dir / f"{sample_id}_{self.image_size[0]}x{self.image_size[1]}.npy"
        if cache_path.exists():
            array = np.load(cache_path)
        else:
            document_path = self.data_dir / row["relative_path"]
            array = document_to_array(document_path, image_size=self.image_size)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, array)
        label = 1.0 if row["label"] == "cv" else 0.0
        return array_to_tensor(array), torch.tensor(label, dtype=torch.float32)


def read_manifest(data_dir: Path) -> list[dict[str, str]]:
    manifest_path = data_dir / "manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def split_rows(rows: list[dict[str, str]], seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    labels = [row["label"] for row in rows]
    train_rows, remaining_rows = train_test_split(rows, test_size=0.3, random_state=seed, stratify=labels)
    remaining_labels = [row["label"] for row in remaining_rows]
    val_rows, test_rows = train_test_split(remaining_rows, test_size=0.5, random_state=seed, stratify=remaining_labels)
    return list(train_rows), list(val_rows), list(test_rows)


def run_epoch(model, loader, criterion, optimizer, device: torch.device) -> float:
    model.train(optimizer is not None)
    total_loss = 0.0
    total_samples = 0
    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = criterion(logits, labels)
        if optimizer is not None:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * inputs.size(0)
        total_samples += inputs.size(0)
    return total_loss / max(total_samples, 1)


def predict(model, loader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    labels: list[float] = []
    probabilities: list[float] = []
    with torch.no_grad():
        for inputs, batch_labels in loader:
            logits = model(inputs.to(device))
            batch_probabilities = torch.sigmoid(logits).cpu().numpy()
            labels.extend(batch_labels.numpy().tolist())
            probabilities.extend(batch_probabilities.tolist())
    return np.asarray(labels, dtype=np.int32), np.asarray(probabilities, dtype=np.float32)


def best_threshold(labels: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    candidates = np.linspace(0.2, 0.8, 61)
    scored = [(float(threshold), f1_score(labels, probabilities >= threshold, zero_division=0)) for threshold in candidates]
    return max(scored, key=lambda item: item[1])


def metrics_for(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(np.int32)
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 4),
        "precision_cv": round(float(precision_score(labels, predictions, zero_division=0)), 4),
        "recall_cv": round(float(recall_score(labels, predictions, zero_division=0)), 4),
        "f1_cv": round(float(f1_score(labels, predictions, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(labels, predictions).tolist(),
        "classification_report": classification_report(labels, predictions, target_names=["non_cv", "cv"], zero_division=0, output_dict=True),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CV-vs-Non-CV CNN classifier")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--image-height", type=int, default=160)
    parser.add_argument("--image-width", type=int, default=224)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    set_seed(args.seed)
    torch.set_num_threads(max(1, args.cpu_threads))

    rows = read_manifest(args.data_dir)
    if len(rows) < 100:
        raise ValueError("Dataset is too small for training")
    train_rows, val_rows, test_rows = split_rows(rows, args.seed)
    image_size = (args.image_height, args.image_width)

    train_loader = DataLoader(DocumentDataset(train_rows, args.data_dir, args.cache_dir, image_size), batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(DocumentDataset(val_rows, args.data_dir, args.cache_dir, image_size), batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(DocumentDataset(test_rows, args.data_dir, args.cache_dir, image_size), batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CvDocumentCnn(dropout=args.dropout).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)

    best_state = None
    best_val_f1 = -1.0
    stale_epochs = 0
    history = []

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = run_epoch(model, val_loader, criterion, None, device)
        val_labels, val_probabilities = predict(model, val_loader, device)
        threshold, val_f1 = best_threshold(val_labels, val_probabilities)
        history.append({"epoch": epoch, "train_loss": round(train_loss, 5), "val_loss": round(val_loss, 5), "val_f1": round(float(val_f1), 4), "threshold": round(threshold, 3)})
        print(f"epoch={epoch} train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_f1={val_f1:.4f} threshold={threshold:.3f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                break

    if best_state is None:
        raise RuntimeError("Training did not produce a model state")
    model.load_state_dict(best_state)

    val_labels, val_probabilities = predict(model, val_loader, device)
    threshold, _ = best_threshold(val_labels, val_probabilities)
    test_labels, test_probabilities = predict(model, test_loader, device)
    test_metrics = metrics_for(test_labels, test_probabilities, threshold)

    accept_threshold = max(0.7, threshold)
    reject_threshold = min(0.35, max(0.1, threshold - 0.2))

    if args.model_dir.exists() and args.force:
        shutil.rmtree(args.model_dir)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.model_dir / "model.pt")

    metadata = {
        "model_name": "cv_document_cnn",
        "task": "cv_vs_non_cv_document_classification",
        "image_size": [args.image_height, args.image_width],
        "dropout": args.dropout,
        "positive_label": "cv",
        "negative_label": "non_cv",
        "decision_threshold": round(float(threshold), 4),
        "accept_threshold": round(float(accept_threshold), 4),
        "reject_threshold": round(float(reject_threshold), 4),
        "strong_text_evidence_threshold": 0.65,
        "moderate_text_evidence_threshold": 0.45,
        "text_evidence_probability_floor": 0.88,
        "text_evidence_manual_review_floor": 0.55,
        "train_samples": len(train_rows),
        "validation_samples": len(val_rows),
        "test_samples": len(test_rows),
        "device": str(device),
    }
    (args.model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = {"metadata": metadata, "history": history, "test_metrics": test_metrics}
    report_path = args.report_dir / "cv_document_classifier_metrics.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"model_dir": str(args.model_dir), "report": str(report_path), "test_metrics": test_metrics}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Training failed: {exc}", file=sys.stderr)
        raise
