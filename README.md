# Talent Bridge

Talent Bridge is a modular data, BI, NLP, ML, and document-AI project for IT job market analysis and CV-to-job recommendation.

## Architecture

The repository is organized by functional domain:

```text
DataPlatform/      ETL, SQL Server warehouse, SQL views
BI/                Power BI dashboard assets
NLP/               CV extraction, skill extraction, semantic matching
MachineLearning/   Salary prediction, job classification, K-Means segmentation
DocumentAI/        CV quality scoring: Pro / Non Pro
Recommendation/    Job ranking and matching explanations
Shared/            Shared schemas, config, utilities, database helpers
Backend/           FastAPI orchestration API
Frontend/          Vue 3 web application
Infrastructure/    Local scripts, Docker, environment, CI/CD placeholders
Data/              Raw and sample data
Artifacts/         Generated models and reports
Docs/              Architecture, demo, ML, NLP, backend, frontend docs
Tests/             Integration and smoke tests
Tools/             Maintenance scripts and notebooks
```

Detailed architecture document:

```text
Docs/architecture/overview.md
```

## Main Flow

```text
Data/raw/data_jobs.csv
  -> DataPlatform/ETL/SSIS
  -> SQL Server DW_DataJobs
  -> DataPlatform/Warehouse/views
  -> BI, ML, Backend, Recommendation

Frontend/TalentBridgeWeb
  -> Backend/TalentBridgeAPI
  -> NLP/CVExtraction
  -> DocumentAI/CVQualityScoring
  -> Recommendation/JobRecommendation
  -> SQL Server warehouse jobs
  -> Frontend results
```

## Key Projects

| Area | Location | Purpose |
| --- | --- | --- |
| Data warehouse | `DataPlatform/` | SSIS ETL, SQL views, cleaned warehouse outputs |
| BI dashboard | `BI/PowerBI/` | Power BI dashboard and reporting assets |
| Backend API | `Backend/TalentBridgeAPI/` | FastAPI orchestration API |
| Frontend | `Frontend/TalentBridgeWeb/` | Vue 3 user interface |
| NLP extraction | `NLP/CVExtraction/` | PDF text, translation, NER training utilities |
| NLP matching | `NLP/CVMatching/`, `Recommendation/JobRecommendation/` | Embeddings and final job ranking |
| Skill normalization | `NLP/SkillExtraction/` | Skill aliases and text normalization |
| CV quality | `DocumentAI/CVQualityScoring/` | `Pro / Non Pro` scoring and model training |
| ML objectives | `MachineLearning/` | Salary regression, job classification, K-Means segmentation |
| Artifacts | `Artifacts/` | Generated models and reports |

## Run Locally

Recommended launcher:

```powershell
.\Infrastructure\scripts\start_local.ps1
```

Double-click wrapper:

```text
Infrastructure/scripts/start_local.bat
```

Manual backend:

```bash
cd Backend/TalentBridgeAPI
python run_server.py serve
```

Manual frontend:

```bash
cd Frontend/TalentBridgeWeb
npm install
npm run dev
```

URLs:

```text
Frontend: http://localhost:5173
Backend docs: http://localhost:8000/docs
```

## SQL Warehouse

Run SQL scripts from:

```text
DataPlatform/Warehouse/views/
```

Important SQL objects:

```text
dbo.vw_job_matching
cv.analysis_run
cv.analysis_skill
cv.job_match_result
cv.vw_analysis_summary
cv.vw_match_detail
cv.vw_candidate_skill
```

The backend uses `DW_DATAJOBS_CONNECTION_STRING` if provided. Otherwise it defaults to local trusted SQL Server connection for `DW_DataJobs`.

## NLP Matching

Matching is NLP-enhanced and explainable.

It uses:

```text
CV entity extraction
TF-IDF embedding similarity between CV profile and job text
skill score
role score
experience score
education score
location score
opportunity score
```

The final recommendation engine lives in:

```text
Recommendation/JobRecommendation/src/matching.py
```

## ML Objectives

Final ML training should use the cleaned SQL warehouse:

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

CSV fallback is available only for development:

```bash
python scripts/train_ml_objectives.py --source csv --max-rows 60000 --sample-size 24000
```

Latest SQL-based metrics are saved at:

```text
Artifacts/reports/ml/ml_objectives_metrics.json
Artifacts/reports/ml/job_cluster_profiles.json
```

Model artifacts:

```text
Artifacts/models/ml/salary_regression_model.pkl
Artifacts/models/ml/remote_classifier_model.pkl
Artifacts/models/ml/full_time_classifier_model.pkl
Artifacts/models/ml/job_segmentation_kmeans.pkl
```

ML report:

```text
Docs/ml/ML_OBJECTIVES_REPORT.md
```

## CV Quality

Quality scoring module:

```text
DocumentAI/CVQualityScoring/
```

Model artifact:

```text
Artifacts/models/document_ai/cv_quality_model.pkl
```

The current quality model uses bootstrap weak/synthetic labels. It is useful for a demo, but final claims require manually reviewed real CV labels.

## Verification

Backend/domain compile:

```bash
python -m compileall -q Backend/TalentBridgeAPI NLP DocumentAI Recommendation MachineLearning
```

Smoke test:

```bash
python Backend/TalentBridgeAPI/scripts/smoke_test_demo_logic.py
```

Frontend build:

```bash
cd Frontend/TalentBridgeWeb
npm run build
```

## Dependency Rules

Allowed direction:

```text
Frontend -> Backend -> Domain Modules -> Shared/DataPlatform outputs
```

Do not import backend route code into NLP, ML, DocumentAI, Recommendation, or Shared modules.

Frontend must call only backend APIs, never internal Python modules or SQL directly.
