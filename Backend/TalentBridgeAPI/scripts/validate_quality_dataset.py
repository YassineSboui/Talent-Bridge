from _path_setup import ensure_repo_root_on_path
ensure_repo_root_on_path()

from DocumentAI.CVQualityScoring.training.validate_quality_dataset import main


if __name__ == "__main__":
    main()
