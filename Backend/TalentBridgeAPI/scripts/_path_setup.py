from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_root_on_path() -> None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "MachineLearning").exists() and (parent / "NLP").exists():
            repo_root = str(parent)
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            return
