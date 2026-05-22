# Salary Prediction

## What This Module Does

This objective predicts yearly salary from cleaned job-market data.

Target column:

```text
salary_year_avg
```

Problem type:

```text
Regression
```

Regression is used because salary is a continuous numeric value.

## Why It Was Built

Salary prediction helps understand how role, location, schedule, skills, company, and job source relate to salary level.

It supports the business question:

```text
Can we estimate a fair salary range from job characteristics?
```

## Official Data Source

Objective-specific SQL view:

```text
DW_DataJobs.dbo.vw_ml_salary_training
```

The central runner reads from:

```text
DW_DataJobs.dbo.vw_ml_jobs
```

and keeps rows where `salary_year_avg` is valid.

## Implementation

Main implementation:

```text
MachineLearning/SharedML/src/train_ml_objectives.py
```

Relevant function:

```text
train_salary_regression
```

Backend launcher:

```text
Backend/TalentBridgeAPI/scripts/train_ml_objectives.py
```

## How It Works

```text
load cleaned SQL rows
-> filter valid salary values
-> remove unrealistic salary outliers
-> build text/categorical/numeric features
-> train candidate regression pipelines
-> compare by RMSE
-> save best model artifact
-> write metrics report
```

Candidate models include:

```text
Ridge regression with log-transformed salary target
RandomForestRegressor candidate when dataset size allows
```

The target is transformed with `log1p` and inverted with `expm1` to reduce the effect of very large salaries.

## Features

Feature groups:

```text
ml_text
job title
short title/category
location and country
portal/source
schedule
remote flag
no-degree flag
health-insurance flag
company name
skills
skill count
posted date parts
title length
```

Preprocessing:

```text
TF-IDF for text
OneHotEncoder for categorical fields
SimpleImputer + StandardScaler for numeric fields
```

## Latest SQL-Based Metrics

```text
R2: 0.5041
MAE: 26051.96
RMSE: 32563.83
```

Interpretation:

- `R2` shows the model captures a useful part of salary variation.
- `MAE` means the average absolute salary error is about 26k.
- salary data is sparse and noisy, so this objective is naturally limited.

## Artifacts

```text
Artifacts/models/ml/salary_regression_model.pkl
Artifacts/reports/ml/ml_objectives_metrics.json
```

## Run

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

## Validation Checklist

- Uses SQL warehouse data.
- Predicts a numeric salary target.
- Reports MAE, RMSE, and R2.
- Saves a model artifact.
- Explains salary sparsity limitation.
