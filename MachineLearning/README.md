# MachineLearning

## Purpose

`MachineLearning/` contains the classical ML objectives and shared ML utilities for Talent Bridge.

The project has three required ML objectives:

```text
1. Salary prediction with regression
2. Job classification with supervised classifiers
3. Job segmentation with clustering
```

It also contains shared skill-gap utilities used by the candidate-facing recommendation workflow.

## Why This Domain Exists

The data warehouse should not only feed dashboards. It should also support predictive and analytical models.

Machine learning helps answer:

- Can we estimate salary from job features?
- Can we classify remote/full-time job signals?
- Can we group similar jobs into market segments?
- Can we estimate skill demand to prioritize candidate skill gaps?

## Official Data Source

Final ML training should use SQL Server warehouse views, not raw CSV.

Main source view:

```text
DW_DataJobs.dbo.vw_ml_jobs
```

Objective-specific views:

```text
DW_DataJobs.dbo.vw_ml_salary_training
DW_DataJobs.dbo.vw_ml_classification_training
DW_DataJobs.dbo.vw_ml_segmentation_training
```

CSV fallback exists only for development:

```text
Data/raw/data_jobs.csv
```

## Main Implementation

```text
MachineLearning/SharedML/src/train_ml_objectives.py
Backend/TalentBridgeAPI/scripts/train_ml_objectives.py
```

The backend script is a launcher/wrapper. The reusable implementation lives in `MachineLearning/SharedML/src/train_ml_objectives.py`.

## Training Flow

```text
SQL warehouse view dbo.vw_ml_jobs
-> load rows
-> prepare text/categorical/numeric features
-> train salary regression
-> train remote classifier
-> train full-time classifier
-> train job segmentation model
-> save model artifacts
-> save metrics and cluster reports
```

## Shared Feature Engineering

The ML runner builds:

```text
ml_text
categorical features
numeric features
remote flag
full-time flag
schedule primary
portal family
skill count
title length
posted year/month/day-of-week
```

Feature preprocessing uses:

```text
TF-IDF for text
OneHotEncoder for categorical values
SimpleImputer + StandardScaler for numeric values
```

## Run Training

SQL mode, official:

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

CSV mode, development fallback only:

```bash
python scripts/train_ml_objectives.py --source csv --max-rows 60000 --sample-size 24000
```

## Outputs

Model artifacts:

```text
Artifacts/models/ml/salary_regression_model.pkl
Artifacts/models/ml/remote_classifier_model.pkl
Artifacts/models/ml/full_time_classifier_model.pkl
Artifacts/models/ml/job_segmentation_kmeans.pkl
```

Reports:

```text
Artifacts/reports/ml/ml_objectives_metrics.json
Artifacts/reports/ml/job_cluster_profiles.json
```

## Latest SQL-Based Metrics

| Model | Metric | Value |
| --- | --- | --- |
| Salary regression | R2 | `0.5041` |
| Salary regression | MAE | `26051.96` |
| Salary regression | RMSE | `32563.83` |
| Remote classification | Macro F1 | `0.7525` |
| Remote classification | Accuracy | `0.8659` |
| Full-time classification | Macro F1 | `0.6230` |
| Full-time classification | Accuracy | `0.7155` |
| Job segmentation | Best K | `7` |
| Job segmentation | Silhouette | `0.0073` |

Metric interpretation:

- salary prediction is limited by sparse salary coverage in public job postings
- classifiers avoid target-leaking fields so validation is more realistic
- job segmentation has low silhouette because job-market groups naturally overlap

## Skill-Gap Shared ML

Skill-gap files:

```text
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
```

Purpose:

```text
skill_frequency.py -> estimates market demand for each skill
gap_analyzer.py -> compares candidate skills with job skills and prioritizes missing skills
```

Skill-gap output includes:

- matched skills
- missing skills
- extra candidate skills
- coverage percentage
- readiness level
- critical/high/medium/low priority gaps
- quick wins
- core gaps
- learning resources

## Validation

```bash
python -m compileall -q MachineLearning
python -m pytest Tests/smoke/test_skill_gap.py -v
python Tests/integration/test_sql_ml_views.py
```

## Submodules

| Folder | Objective |
| --- | --- |
| `SalaryPrediction/` | Salary regression documentation. |
| `JobClassification/` | Remote and full-time classification documentation. |
| `JobSegmentation/` | K-Means segmentation documentation. |
| `SharedML/` | Shared training, skill frequency, and skill-gap engines. |

## Teacher Explanation

The classical ML part uses cleaned SQL warehouse data. Salary prediction is regression because the target is numeric. Remote and full-time detection are classification because the targets are labels. Job segmentation is clustering because it discovers groups without manual labels. Skill-gap analysis uses normalized skills and market frequency to prioritize missing skills.
