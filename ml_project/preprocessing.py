import re
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer


def _parse_experience(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return np.nan
    if "month" in s:
        return nums[0] / 12.0
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2.0
    return nums[0]


def _parse_salary(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace(",", "").replace("$", "").lower()
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return np.nan
    val = nums[0] if len(nums) == 1 else (nums[0] + nums[1]) / 2.0
    if "k" in s:
        val *= 1_000
    if "hour" in s or "/hr" in s:
        val *= 2_080
    if "month" in s:
        val *= 12
    return val


def _normalize_job_type(val) -> str:
    if pd.isna(val):
        return "unknown"
    s = str(val).strip().lower()
    if any(k in s for k in ["remote", "wfh", "work from home", "telecommute"]):
        return "remote"
    if any(k in s for k in ["full-time", "fulltime", "full_time", "permanent"]):
        return "full-time"
    if any(k in s for k in ["part-time", "parttime", "part_time"]):
        return "part-time"
    if any(k in s for k in ["contract", "freelance", "temporary", "temp", "consultant"]):
        return "contract"
    if any(k in s for k in ["intern", "internship", "apprentice"]):
        return "internship"
    return s if s else "unknown"


def _normalize_remote(val) -> int:
    if pd.isna(val):
        return 0
    s = str(val).strip().lower()
    return 1 if s in {"yes", "true", "1", "y", "remote"} else 0


def build_preprocessor(df: pd.DataFrame, exclude_cols: list | None = None) -> ColumnTransformer:
    exclude = set(exclude_cols or [])
    numeric_features = [c for c in df.select_dtypes(include=["number"]).columns if c not in exclude]
    categorical_features = [c for c in df.select_dtypes(include=["object"]).columns if c not in exclude]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numeric_features:
        transformers.append(("num", numeric_transformer, numeric_features))
    if categorical_features:
        transformers.append(("cat", categorical_transformer, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "title" in df.columns or "job_title" in df.columns:
        col = "job_title" if "job_title" in df.columns else "title"
        df[col] = df[col].fillna("").astype(str)
        df["title_length"] = df[col].str.len()
        df["title_word_count"] = df[col].str.split().str.len()
        df["is_senior"] = df[col].str.contains(
            r"(?i:senior|lead|principal|director|manager|head|chief|vp|cto|ceo|cfo)", regex=True, na=False
        ).astype(int)
        df["is_engineer"] = df[col].str.contains(
            r"(?i:engineer|developer|architect|programmer|sre|devops)", regex=True, na=False
        ).astype(int)

    exp_cols = [c for c in df.columns if c.lower() in {"experience", "exp", "years", "yrs", "seniority", "experience_years"}]
    if exp_cols:
        primary = exp_cols[0]
        df["experience_years"] = df[primary].apply(_parse_experience)
    else:
        df["experience_years"] = np.nan

    if "salary_year_avg" in df.columns:
        df["salary_year_avg"] = df["salary_year_avg"].astype(float)
        if "salary_hour_avg" in df.columns:
            df["salary_hour_avg"] = df["salary_hour_avg"].astype(float)
            df["salary"] = df["salary_year_avg"].fillna(df["salary_hour_avg"] * 2080)
        else:
            df["salary"] = df["salary_year_avg"]
    elif "salary" in df.columns:
        df["salary"] = df["salary"].apply(_parse_salary)

    if "city" in df.columns:
        df["city"] = df["city"].fillna("Unknown").astype(str)
        df["is_remote_location"] = df["city"].str.contains(
            r"(?i:remote|wfh|anywhere|worldwide|global)", regex=True, na=False
        ).astype(int)
    elif "location" in df.columns:
        df["location"] = df["location"].fillna("Unknown").astype(str)
        df["is_remote_location"] = df["location"].str.contains(
            r"(?i:remote|wfh|anywhere|worldwide|global)", regex=True, na=False
        ).astype(int)

    if "skills" in df.columns:
        df["skills"] = df["skills"].fillna("").astype(str)
        df["skill_count"] = df["skills"].apply(lambda x: len([s for s in x.split(",") if s.strip()]))

    if "remote" in df.columns:
        df["remote"] = df["remote"].apply(_normalize_remote)

    if "job_type" in df.columns:
        df["job_type"] = df["job_type"].apply(_normalize_job_type)

    if "posted_date" in df.columns:
        df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
        df["days_since_posted"] = (pd.Timestamp.now() - df["posted_date"]).dt.days

    drop_cols = [
        "id", "job_posting_key", "posted_date", "company_name", "description", "url",
        "salary_year_avg", "salary_hour_avg", "no_degree_mention", "has_health_insurance",
        "has_salary_info",
    ]
    existing = [c for c in drop_cols if c in df.columns]
    if "experience_years" in df.columns and "experience" in existing:
        existing.remove("experience")
    df = df.drop(columns=existing, errors="ignore")

    return df


def prepare_dataset(df: pd.DataFrame, task: str = "regression") -> pd.DataFrame:
    df = df.copy()

    if task == "regression":
        df = df.dropna(subset=["salary"])
        df = df[df["salary"] > 0]
    elif task == "classification":
        df = df.dropna(subset=["job_type"])
        df = df[df["job_type"] != "unknown"]
        vc = df["job_type"].value_counts()
        rare = vc[vc < 2].index
        if len(rare) > 0:
            df = df[~df["job_type"].isin(rare)]
    elif task == "clustering":
        pass

    return df
