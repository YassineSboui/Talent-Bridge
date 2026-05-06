# DataPlatform Mini-Project

## What It Does

This mini-project cleans and structures the raw IT job dataset into a SQL Server data warehouse.

It converts:

```text
Data/raw/data_jobs.csv
```

into a star-schema warehouse in:

```text
DW_DataJobs
```

## Why It Exists

The whole project must be based on reliable cleaned data. Power BI, ML, matching, and backend APIs should consume SQL warehouse outputs instead of raw CSV.

## Main Folders

```text
DataPlatform/ETL/SSIS/
DataPlatform/Warehouse/views/
DataPlatform/Warehouse/migrations/
DataPlatform/Warehouse/docs/
```

## How It Works

1. SSIS creates or prepares the database.
2. SSIS loads raw CSV rows into staging.
3. SSIS populates dimension tables.
4. SSIS populates fact and bridge tables.
5. SQL views expose clean datasets for matching, BI, ML, and platform workflows.

## Important SQL Views

```text
dbo.vw_job_matching
dbo.vw_ml_jobs
dbo.vw_ml_salary_training
dbo.vw_ml_classification_training
dbo.vw_ml_segmentation_training
cv.vw_analysis_summary
cv.vw_match_detail
cv.vw_candidate_skill
```

## How To Validate

Run SQL view check:

```bash
python Tests/integration/test_sql_ml_views.py
```

Expected output:

```text
SQL ML/matching views exist
```

## Teacher Validation Checklist

- Raw data is not used directly by final ML.
- SQL warehouse exists.
- Matching and ML views exist.
- Power BI can consume warehouse tables/views.
- DataPlatform is independent from frontend/backend UI code.
