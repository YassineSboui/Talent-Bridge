import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

REG_MODEL_DIR = MODELS_DIR / "salary_regression"
CLS_MODEL_DIR = MODELS_DIR / "job_classification"
SEG_MODEL_DIR = MODELS_DIR / "job_segmentation"

DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_DATABASE = os.getenv("DB_DATABASE", "")
DB_USERNAME = os.getenv("DB_USERNAME", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
JOB_TABLE = os.getenv("JOB_TABLE", "job_listings")

N_CLUSTERS = 5
RANDOM_STATE = 42
TEST_SIZE = 0.2

for d in [DATA_DIR, REG_MODEL_DIR, CLS_MODEL_DIR, SEG_MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)
