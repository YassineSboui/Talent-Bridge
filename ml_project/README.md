# Job Listings ML Platform

End-to-end machine learning pipeline for job postings stored in SQL Server, with a Streamlit multi-page web application.

## ML Objectives

| Task | Model | Key Metrics |
|---|---|---|
| **Salary Prediction** | Gradient Boosting Regressor | RMSE, R², MAE |
| **Job Classification** | Gradient Boosting Classifier | Accuracy |
| **Job Segmentation** | K-Means Clustering | Silhouette Score |

## Features

- **Direct SQL Server ingestion** — Connects to SSMS via `pyodbc` with no hardcoded credentials
- **Automated feature engineering** — Parses experience ranges, normalizes salaries, extracts title signals, counts skills
- **SHAP explainability** — Saved as model artifacts; rendered as summary plots in the UI
- **Interactive EDA dashboard** — Salary distributions, job type breakdowns, skills word cloud, correlation heatmap
- **"Try It Yourself" page** — Real-time salary estimate and job category prediction from user input
- **CSV export** — Download predictions from every model page
- **Model performance cards** — Side-by-side comparison on the home page

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.10 – 3.12 |
| **SQL Server** | Any version (2017+) with a table containing job listings |
| **ODBC Driver** | [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (or newer) |
| **pip** | Included with Python; upgrade with `python -m pip install --upgrade pip` |

Verify the driver is installed:

```bash
# Windows (PowerShell)
Get-OdbcDriver -Name "ODBC Driver*" -Platform "64-bit"

# Linux
odbcinst -d -q
```

---

## Project Structure

```
ml_project/
├── Home.py                              # Streamlit entry point — overview + performance cards
├── config.py                            # Centralized settings (paths, DB, hyperparams)
├── data_loader.py                       # SQL Server connection string builder & data fetch
├── preprocessing.py                     # feature_engineering(), prepare_dataset(), build_preprocessor()
├── visualization.py                     # 6 EDA chart generators (returns PNG buffers)
├── train_models.py                      # CLI script — orchestrates training of all 3 models
├── requirements.txt                     # Python package dependencies
├── .env.example                         # Template for environment variables
├── README.md                            # This file
│
├── data/                                # Local data cache (optional)
│   └── README.md
│
├── notebooks/                           # Jupyter notebooks for exploration
│   └── README.md
│
├── models/
│   ├── salary_regression/
│   │   ├── pipeline.joblib              # Trained scikit-learn Pipeline (preprocessor + model)
│   │   ├── shap_explainer.joblib        # SHAP values + feature names for explainability
│   │   └── metrics.json                 # RMSE, R², MAE
│   ├── job_classification/
│   │   ├── pipeline.joblib              # Trained scikit-learn Pipeline
│   │   ├── shap_explainer.joblib        # SHAP values + feature names + class labels
│   │   ├── metrics.json                 # Accuracy + full classification report
│   │   └── classes.json                 # List of valid job type classes
│   └── job_segmentation/
│       ├── pipeline.joblib              # Trained scikit-learn Pipeline (preprocessor + KMeans)
│       └── metrics.json                 # Silhouette scores (train/test), cluster sizes
│
├── pages/
│   ├── 1_Dashboard.py                   # EDA: salary dist, job types, experience vs salary,
│   │                                    #          top locations, word cloud, correlation heatmap
│   ├── 2_Salary_Predictor.py            # Regression metrics, sample predictions, SHAP plot, CSV export
│   ├── 3_Job_Classifier.py              # Classification accuracy, prediction bar chart, SHAP plot, CSV export
│   ├── 4_Segmentation.py                # K-Means PCA visualization, cluster sizes, assignments, CSV export
│   └── 5_Try_It_Yourself.py             # Interactive sidebar form → real-time salary + category prediction
│
└── utils/
    ├── __init__.py
    └── streamlit_helpers.py             # Shared loaders, SHAP rendering, sample prediction generator
```

---

## Step-by-Step Setup

### 1. Clone / Navigate

```bash
cd ml_project
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Database Connection

Copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
DB_SERVER=your_server_name_or_ip
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_DRIVER=ODBC Driver 17 for SQL Server
JOB_TABLE=your_job_listings_table
```

> **Trusted (Windows) Authentication:** Leave `DB_USERNAME` and `DB_PASSWORD` empty. The connection string will automatically use `Trusted_Connection=yes`.

### 5. Verify the Database Connection (optional)

Run a quick Python check:

```bash
python -c "from data_loader import fetch_jobs; print(fetch_jobs().head())"
```

If you see a DataFrame, the connection works.

### 6. Train All Models

```bash
python train_models.py
```

This single command:
1. Fetches data from SQL Server
2. Engineers features automatically
3. Trains the **Salary Regression** model (Gradient Boosting)
4. Trains the **Job Classification** model (Gradient Boosting)
5. Trains the **Job Segmentation** model (K-Means)
6. Saves pipelines, SHAP artifacts, and metrics to `models/`

Expected output:

```
============================================================
  Job Listings ML Pipeline — Training
============================================================

[Step 1] Fetching data from SQL Server...
  Loaded 10,000 rows, 12 columns.

[Step 2] Training Salary Regression model...
  RMSE:  15234.56
  R²:    0.8523
  MAE:   10567.89

[Step 3] Training Job Classification model...
  Accuracy: 0.9123

[Step 4] Training Job Segmentation model...
  Silhouette (test): 0.4521
  Clusters:          5

============================================================
  All models trained and saved successfully!
============================================================
```

### 7. Launch the Streamlit App

```bash
streamlit run Home.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Streamlit Pages

### Home (`Home.py`)
Overview of the platform. Displays model performance cards (R², RMSE, Accuracy, Silhouette) side by side, plus a quick preview of the raw data from the database.

### Dashboard (`1_Dashboard.py`)
Exploratory Data Analysis with 6 visualizations:
- **Salary Distribution** — Histogram with KDE
- **Job Type Breakdown** — Pie chart of job categories
- **Experience vs Salary** — Scatter plot with regression line
- **Top Locations** — Horizontal bar chart of top 10 locations
- **Skills Word Cloud** — Frequency-based word cloud from the skills column
- **Correlation Heatmap** — Pearson correlation matrix of numeric features

### Salary Predictor (`2_Salary_Predictor.py`)
Regression model page showing RMSE, R², and MAE metrics. Displays a table of sample predictions (actual vs predicted) on test data with a CSV download button. Includes a SHAP summary plot explaining which features most influence salary predictions.

### Job Classifier (`3_Job_Classifier.py`)
Classification model page showing accuracy. Displays a bar chart of predicted job type distribution on test data, a sample predictions table, and a SHAP summary plot for feature importance. Includes CSV export.

### Segmentation (`4_Segmentation.py`)
Clustering page showing train/test silhouette scores. Visualizes job clusters in 2D using PCA, displays cluster size distribution, and shows sample assignments with original job data. Includes CSV export of all cluster assignments.

### Try It Yourself (`5_Try_It_Yourself.py`)
Interactive form in the sidebar. Enter a job title, location, experience level, skills, remote status, and job type. Click **Predict** to get:
- Predicted annual salary (if regression model is available)
- Predicted job category (if classification model is available)

Results can be exported as a single-row CSV file.

---

## Troubleshooting

### ODBC Driver Not Found

**Error:** `Data source name not found and no default driver specified`

**Fix:** Install the ODBC Driver for SQL Server.

- **Windows:** Download from [Microsoft's official page](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install -y odbcinst1-2 unixodbc
  sudo apt-get install -y msodbcsql17
  ```
- **macOS:**
  ```bash
  brew tap microsoft/mssql-release
  brew install msodbcsql17
  ```

Verify installation:
```bash
python -c "import pyodbc; print(pyodbc.drivers())"
```

### Module Import Errors in Streamlit Pages

**Error:** `ModuleNotFoundError: No module named 'preprocessing'`

**Fix:** The `sys.path.insert` at the top of each page should handle this. If it fails, run from the `ml_project/` directory:
```bash
cd ml_project
streamlit run Home.py
```

### Model Not Found

**Error:** `Salary regression model not found. Run python train_models.py first.`

**Fix:** Run the training script:
```bash
python train_models.py
```
Verify that `models/salary_regression/pipeline.joblib` exists after training.

### Empty Data / No Data Loaded

**Symptom:** Dashboard shows "No data loaded" or data preview is empty.

**Fix:**
1. Check `.env` has correct `DB_SERVER`, `DB_DATABASE`, and credentials
2. Verify `JOB_TABLE` matches your actual table name
3. Test the connection manually:
   ```bash
   python -c "from data_loader import fetch_jobs; df = fetch_jobs(); print(df.shape)"
   ```
4. If using Windows Authentication, ensure `DB_USERNAME` and `DB_PASSWORD` are empty

### SHAP Plot Not Showing

**Symptom:** Page says "SHAP explainer not available for this model."

**Fix:** SHAP artifacts are generated during training. Re-run:
```bash
python train_models.py
```
If the issue persists (e.g., with very small datasets), the model pages will still show metrics and predictions — only the SHAP plot is skipped.

### Classification Requires At Least 2 Classes

**Error:** `Classification requires at least 2 classes with 2+ samples each.`

**Fix:** Your `job_type` column has insufficient variety. Ensure your data contains at least 2 distinct job types, each with at least 2 occurrences. You can either:
- Enrich your dataset with more diverse job types
- Modify the classification logic in `models/train_classification.py` to relax this constraint

### Memory Error During Training

**Symptom:** Out of memory when fitting Gradient Boosting on large datasets.

**Fix:** Reduce the number of estimators in `train_regression.py` or `train_classification.py`:
```python
# Change n_estimators from 500 to 100
model = GradientBoostingRegressor(n_estimators=100, max_depth=5, ...)
```
Or limit the dataset size in `data_loader.py`:
```python
df = fetch_jobs(limit=20000)  # Reduce from 50000
```

### Streamlit Port Already in Use

**Error:** `Port 8501 is in use`

**Fix:** Run on a different port:
```bash
streamlit run Home.py --server.port 8502
```

---

## Customization

### Change the Number of Clusters

Edit `config.py`:
```python
N_CLUSTERS = 8  # Default is 5
```

Then retrain: `python train_models.py`

### Use a Different ML Model

Edit the respective training file. For example, to use Random Forest for regression, change `models/train_regression.py`:

```python
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor(n_estimators=500, random_state=config.RANDOM_STATE, n_jobs=-1)
```

### Add Custom SQL Query

Instead of `SELECT TOP N * FROM table`, pass a custom query:

```python
# In data_loader.py or directly in Python:
from data_loader import fetch_jobs
df = fetch_jobs(query="SELECT TOP 10000 title, location, salary, job_type FROM jobs WHERE posted_date > '2024-01-01'")
```
