"""
Master pipeline: runs all steps in order.

Usage:
    python run_server.py          # Full pipeline: clean -> convert -> train -> serve
    python run_server.py train    # Only training (data must be prepared)
    python run_server.py serve    # Only start API server (model must be trained)
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
SCRIPTS = PROJECT_ROOT / "scripts"


def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "Artifacts").exists() and (parent / "Recommendation").exists():
            return parent
    return PROJECT_ROOT


def run_step(name: str, script: Path):
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, str(script)], cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"\nFAILED at step: {name}")
        sys.exit(1)
    print(f"\n  ✓ {name} complete")


def install_deps():
    """Install requirements if not already satisfied."""
    print("Checking dependencies...")
    req_file = PROJECT_ROOT / "requirements.txt"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
        check=True,
    )
    print("Dependencies OK\n")


def serve():
    """Start the FastAPI server."""
    repo_root = find_repo_root()
    model_path = repo_root / "Artifacts" / "models" / "nlp" / "model-best"
    if not model_path.exists():
        print(
            f"WARNING: No trained NER model at {model_path}. "
            "CV extraction will run without the spaCy NER model, but platform "
            "routes such as login, jobs, and applications can still run."
        )

    print(f"\n{'='*60}")
    print("  Starting CV NER API server")
    print(f"  Model: {model_path}")
    print(f"  Endpoint: http://localhost:8000/extract")
    print(f"  Docs:     http://localhost:8000/docs")
    print(f"{'='*60}\n")

    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--reload-dir", str(PROJECT_ROOT),
            "--reload-dir", str(repo_root / "Recommendation"),
            "--reload-dir", str(repo_root / "DocumentAI"),
            "--reload-dir", str(repo_root / "NLP"),
        ],
        cwd=str(PROJECT_ROOT),
    )


def main():
    args = sys.argv[1:]

    if "serve" in args:
        serve()
        return

    if "train" in args:
        run_step("Train NER Model", SCRIPTS / "train_model.py")
        print("\nDone! Run 'python run_server.py serve' to start the API.")
        return

    # Full pipeline
    install_deps()
    run_step("1/3 — Clean Data", SCRIPTS / "clean_data.py")
    run_step("2/3 — Convert to spaCy Format", SCRIPTS / "prepare_data.py")
    run_step("3/3 — Train NER Model", SCRIPTS / "train_model.py")

    print(f"\n{'='*60}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Model saved to: {PROJECT_ROOT / 'models' / 'model-best'}")
    print(f"  Start API with: python run_server.py serve")
    print(f"  API docs at:    http://localhost:8000/docs")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
