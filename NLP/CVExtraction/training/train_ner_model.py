"""
Step 3: Train the NER model.

- Auto-detects GPU availability
- Uses spaCy's own config generator for maximum compatibility
- Patches the generated config with optimized hyperparameters
- Runs training via spaCy CLI
- Evaluates on dev set
"""

import subprocess
import sys
import json
import re
import os
from pathlib import Path

import spacy


def has_gpu():
    """Return whether PyTorch can see a CUDA GPU for spaCy training."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def generate_base_config(config_path):
    """Use spaCy's init config to generate a valid base config."""
    cmd = [
        sys.executable, "-m", "spacy", "init", "config",
        str(config_path),
        "--lang", "en",
        "--pipeline", "ner",
        "--optimize", "accuracy",
        "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Config generation failed:\n{result.stderr}")
        sys.exit(1)
    return config_path


def patch_config(config_path, train_path, dev_path):
    """
    Patch the generated config with:
    - Correct data paths
    - Optimized hyperparameters for our dataset
    """
    text = config_path.read_text(encoding="utf-8")

    train_str = str(train_path).replace("\\", "/")
    dev_str = str(dev_path).replace("\\", "/")
    max_steps = os.getenv("CV_NER_MAX_STEPS")
    eval_frequency = os.getenv("CV_NER_EVAL_FREQUENCY", "100")

    # Simple line-by-line replacement for paths
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("train") and "=" in stripped and "corpus" not in stripped:
            key = stripped.split("=")[0].strip()
            if key == "train":
                lines[i] = f'train = "{train_str}"'
        elif stripped.startswith("dev") and "=" in stripped and "corpus" not in stripped:
            key = stripped.split("=")[0].strip()
            if key == "dev":
                lines[i] = f'dev = "{dev_str}"'
        elif stripped.startswith("eval_frequency = "):
            lines[i] = f"eval_frequency = {eval_frequency}"
        elif max_steps and stripped.startswith("max_steps = "):
            lines[i] = f"max_steps = {int(max_steps)}"
        elif stripped == "progress_bar = false":
            lines[i] = "progress_bar = true"
    text = "\n".join(lines)

    config_path.write_text(text, encoding="utf-8")
    print(f"Patched config at: {config_path}")


def main():
    """Generate config, train the spaCy NER model, and evaluate it."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    config_dir = project_root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    model_dir = project_root / "models"

    train_path = data_dir / "train.spacy"
    dev_path = data_dir / "dev.spacy"

    if not train_path.exists() or not dev_path.exists():
        print("ERROR: train.spacy / dev.spacy not found. Run prepare_data.py first.")
        sys.exit(1)

    gpu = has_gpu()
    use_gpu = gpu
    print(f"GPU available: {gpu}")

    # Generate and patch config
    config_path = config_dir / "config.cfg"
    generate_base_config(config_path)
    patch_config(config_path, train_path, dev_path)

    # Ensure en_core_web_lg is installed
    try:
        spacy.load("en_core_web_lg")
    except OSError:
        print("Downloading en_core_web_lg vectors...")
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_lg"],
            check=True,
        )

    # Train
    train_cmd = [
        sys.executable, "-m", "spacy", "train",
        str(config_path),
        "--output", str(model_dir),
    ]
    if use_gpu:
        train_cmd.extend(["--gpu-id", "0"])

    print(f"\nStarting training...\n")
    result = subprocess.run(train_cmd)

    if result.returncode != 0:
        print("Training failed!")
        sys.exit(1)

    # Evaluate best model
    best_model = model_dir / "model-best"
    if best_model.exists():
        print(f"\n{'='*60}")
        print(f"Training complete! Best model: {best_model}")
        print(f"{'='*60}")

        eval_cmd = [
            sys.executable, "-m", "spacy", "evaluate",
            str(best_model), str(dev_path),
            "--output", str(model_dir / "metrics.json"),
        ]
        if use_gpu:
            eval_cmd.extend(["--gpu-id", "0"])
        print(f"\nEvaluating on dev set...\n")
        subprocess.run(eval_cmd)

        # Print metrics
        metrics_path = model_dir / "metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text())
            print(f"\n{'='*60}")
            print("EVALUATION RESULTS")
            print(f"{'='*60}")
            print(f"Overall F1: {metrics.get('ents_f', 0):.2f}")
            print(f"Precision:  {metrics.get('ents_p', 0):.2f}")
            print(f"Recall:     {metrics.get('ents_r', 0):.2f}")
            per_type = metrics.get("ents_per_type", {})
            if per_type:
                print(f"\nPer-entity scores:")
                for label, scores in sorted(per_type.items()):
                    f1 = scores.get("f", 0)
                    p = scores.get("p", 0)
                    r = scores.get("r", 0)
                    print(f"  {label:25s}  P={p:.2f}  R={r:.2f}  F1={f1:.2f}")
    else:
        print("WARNING: model-best not found after training.")


if __name__ == "__main__":
    main()
