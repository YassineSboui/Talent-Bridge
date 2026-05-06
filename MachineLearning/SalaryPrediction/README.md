# ML Salary Prediction Mini-Project

## What It Does

Predicts yearly salary from cleaned SQL warehouse job characteristics.

Target:

```text
salary_year_avg
```

## Why It Exists

The business objective is to estimate fair salary ranges based on role, country, skills, schedule, remote signal, and other job features.

## Official Data Source

```text
DW_DataJobs.dbo.vw_ml_salary_training
```

The full ML runner reads from:

```text
DW_DataJobs.dbo.vw_ml_jobs
```

and filters valid salary rows.

## How It Works

1. Load cleaned SQL warehouse rows.
2. Keep rows with valid salary.
3. Build text, categorical, and numeric features.
4. Train log-transformed regression models.
5. Compare Ridge and RandomForest candidates.
6. Select the best model by RMSE.

## Latest SQL-Based Metrics

```text
R2: 0.5041
MAE: 26,051.96
RMSE: 32,563.83
```

## Artifacts

```text
Artifacts/models/ml/salary_regression_model.pkl
Artifacts/reports/ml/ml_objectives_metrics.json
```

## Run

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --max-rows 60000 --sample-size 24000
```

## Teacher Validation Checklist

- Uses SQL warehouse data, not raw CSV.
- Predicts `salary_year_avg`.
- Reports MAE, RMSE, and R2.
- Saves trained model artifact.
- Explains sparse salary limitation.
