# Talent Bridge Full Project Documentation

## 1. Purpose Of This Document

This document explains the full Talent Bridge project from the beginning to the end. It is written in a logical order, so each part prepares the next one.

The goal is not only to describe files. The goal is to explain:

- what each part of the project does
- why that part exists
- how that part works internally
- how the parts connect together
- what technical choices were made
- what limitations still exist

Talent Bridge is a complete role-based recruitment platform powered by data engineering, business intelligence, NLP, machine learning, document AI, recommendation, backend APIs, and a Vue frontend.

The project can be summarized in one sentence:

```text
Talent Bridge transforms raw IT job-market data into a cleaned SQL warehouse, uses it for BI and ML, then combines CV analysis, document validation, semantic matching, and role-based workflows to support candidates, recruiters, and admins.
```

## 2. The Business Problem

Before understanding the technical solution, it is important to understand the problem.

Recruitment has several practical difficulties:

- job data is often raw, duplicated, incomplete, and hard to analyze
- candidates upload CVs in unstructured PDF format
- recruiters need structured candidate information, not only files
- candidates need to know which jobs match their profile
- candidates also need to know which skills they are missing
- recruiters need to manage applications, notes, decisions, and interviews
- admins need visibility over the platform and AI workflows
- business users need dashboards to understand job-market trends

Talent Bridge solves this by building a full pipeline:

```text
Raw job data
-> SQL warehouse
-> Power BI and ML models
-> Backend API
-> NLP and DocumentAI CV analysis
-> Recommendation and skill-gap analysis
-> Candidate, recruiter, and admin frontend workflows
```

The project is not only a machine learning notebook. It is an end-to-end application where AI modules are connected to real platform behavior.

## 3. High-Level Architecture

The repository is organized by domain. Each major folder has a clear responsibility.

```text
Data/              Raw and sample data
DataPlatform/      ETL, SQL Server warehouse, migrations, SQL views
BI/                Power BI reporting assets
NLP/               CV text extraction, NER, skill normalization
DocumentAI/        CV document validation and CV quality scoring
MachineLearning/   Salary prediction, classification, segmentation, skill-gap logic
Recommendation/    Job matching, ranking, semantic similarity, explanations
Backend/           FastAPI API, auth, RBAC, workflows, orchestration
Frontend/          Vue 3 user interface
Infrastructure/    Startup scripts, Docker, environment examples, CI
Artifacts/         Generated models, reports, and local demo state
Docs/              Documentation
Tests/             Smoke and integration tests
Shared/            Reserved shared utilities and schemas
Tools/             Reserved maintenance tools
```

The dependency direction is intentionally simple:

```text
Frontend -> Backend -> Domain Modules -> DataPlatform outputs / Artifacts
```

This means:

- the frontend does not read SQL directly
- the frontend does not import Python AI modules
- the backend is the orchestrator
- AI modules remain independent from FastAPI route code
- the data warehouse is the foundation for analytics and training

This structure was chosen because a professional project must be understandable, testable, and extendable. If all code were mixed in one folder, the platform would be harder to explain and maintain.

## 4. The Main End-To-End Flow

The project has two important flows.

The first flow is the data and analytics flow:

```text
Data/raw/data_jobs.csv
-> DataPlatform ETL / SSIS
-> SQL Server database DW_DataJobs
-> SQL views
-> Power BI dashboards
-> ML training datasets
```

The second flow is the recruitment platform flow:

```text
Candidate uploads PDF CV
-> backend validates the file
-> DocumentAI checks if it is really a CV
-> NLP extracts text and entities
-> DocumentAI scores CV quality
-> Recommendation compares candidate profile with jobs
-> candidate applies
-> recruiter reviews application
-> recruiter proposes interview slots
-> candidate selects or declines a slot
-> admin monitors platform activity
```

These two flows connect because job discovery and matching depend on the cleaned SQL warehouse jobs.

## 5. Why The Project Starts With Data

The first technical priority is data quality.

Machine learning, BI dashboards, matching, and recommendations are only useful if they are based on clean and consistent data. If the project used raw CSV rows everywhere, each module would need to repeat its own cleaning logic. That would create inconsistent results.

For this reason, the project uses this rule:

```text
Raw CSV is an input.
SQL warehouse views are the official clean output.
```

The raw data lives in:

```text
Data/raw/data_jobs.csv
```

The cleaned warehouse database is:

```text
DW_DataJobs
```

The SQL warehouse creates a stable foundation for:

- Power BI reports
- backend job search
- recommendation data
- salary prediction
- job classification
- job segmentation
- skill demand analysis
- platform analytics

## 6. DataPlatform

### 6.1 What It Does

The `DataPlatform/` module cleans and structures the raw IT job dataset into SQL Server.

Main location:

```text
DataPlatform/
```

Important folders:

```text
DataPlatform/ETL/SSIS/
DataPlatform/Warehouse/views/
DataPlatform/Warehouse/migrations/
DataPlatform/Warehouse/docs/
```

### 6.2 Why It Exists

The data platform exists because all downstream modules need trusted data.

Power BI should not be built directly on a messy CSV. ML models should not train on a different version of the data than the backend uses. Recommendation should not use a separate cleaned dataset that does not match the dashboard.

The SQL warehouse solves this by becoming the shared source of truth.

### 6.3 How It Works

The ETL process follows this logic:

```text
Raw CSV
-> staging tables
-> cleaned dimensions
-> fact tables
-> bridge tables
-> SQL views for consumers
```

Typical warehouse objects include:

```text
fact.job_posting
dim.skill
bridge.job_skill
dim.job_category
dim.location
```

Important SQL views include:

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

The view `dbo.vw_job_matching` is especially important because it exposes cleaned jobs in a shape that the backend and recommendation system can use.

### 6.4 How It Is Validated

The SQL views can be checked with:

```bash
python Tests/integration/test_sql_ml_views.py
```

The expected idea is that the required SQL views exist and can be queried.

## 7. BI And Power BI

### 7.1 What It Does

The `BI/` module contains the Power BI reporting part of the project.

Main file:

```text
BI/PowerBI/Mission D'entreprise.pbix
```

The BI layer visualizes the IT job market.

It can analyze:

- salary trends
- job categories
- job source distribution
- country and location distribution
- remote, hybrid, and on-site trends
- demanded technical skills
- opportunity indicators

### 7.2 Why It Exists

BI exists because business users need a visual understanding of the job market before making decisions.

For example:

- which skills are most demanded
- which locations have more opportunities
- what salary ranges appear in the data
- what job categories dominate the market
- how remote jobs are distributed

This is different from the candidate/recruiter platform. The platform handles operational workflows. Power BI handles analytical understanding.

### 7.3 How It Works

Power BI reads from the SQL Server warehouse produced by `DataPlatform/`.

The BI layer should not do heavy cleaning itself. Cleaning belongs in SQL and ETL. Power BI should focus on visuals, measures, and business interpretation.

The relationship is:

```text
DataPlatform SQL warehouse
-> Power BI model
-> DAX measures
-> dashboard pages and visuals
```

### 7.4 Role-Based Power BI Access In The Platform

The web platform does not embed Power BI reports with Azure service principal tokens.

Instead, it uses external role-based buttons:

```text
Candidate -> candidate Power BI report URL
Recruiter -> recruiter Power BI report URL
Admin -> admin Power BI report URL
```

This choice was made because true Power BI Embedded requires correct Azure and Power BI tenant alignment. In this project context, the Azure personal account and Power BI work/school tenant are separate, so external links are simpler and safer.

The default URLs can be overridden with environment variables:

```text
TALENTBRIDGE_POWERBI_CANDIDATE_URL
TALENTBRIDGE_POWERBI_RECRUITER_URL
TALENTBRIDGE_POWERBI_ADMIN_URL
```

The backend endpoint used by the frontend is:

```text
GET /api/v1/admin/powerbi
```

Even though the route is under the admin router internally, it returns only the report link allowed for the authenticated role:

```text
Candidate -> candidate dashboard link only
Recruiter -> recruiter dashboard link only
Admin -> full admin dashboard link only
```

If the environment variables are empty, the application falls back to the configured project report URL.

No Azure App Registration, service principal, embed token, Power BI iframe, or `powerbi-client` frontend dependency is required for this simplified setup.

For real role isolation, each role should have its own report or workspace permissions in Power BI.

## 8. MachineLearning

### 8.1 What It Does

The `MachineLearning/` module contains the classical ML objectives and shared ML utilities.

The main objectives are:

- salary prediction
- job classification
- job segmentation
- skill-gap support utilities

Main locations:

```text
MachineLearning/SalaryPrediction/
MachineLearning/JobClassification/
MachineLearning/JobSegmentation/
MachineLearning/SharedML/
```

### 8.2 Why It Exists

The project needs to show that cleaned job data can be used not only for dashboards but also for predictive and analytical models.

The ML objectives answer different questions:

```text
Regression: can we estimate a numeric salary?
Classification: can we predict a category or job mode?
Clustering: can we discover groups of similar jobs?
Skill-gap analysis: can we identify missing candidate skills for a target job?
```

### 8.3 How The ML Training Works

Training should use the SQL warehouse by default:

```text
DW_DataJobs.dbo.vw_ml_jobs
```

The main training script is:

```text
MachineLearning/SharedML/src/train_ml_objectives.py
```

From the backend project, it can be run with:

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

CSV fallback exists only for development:

```bash
python scripts/train_ml_objectives.py --source csv --max-rows 60000 --sample-size 24000
```

This fallback is useful if SQL Server is not available on a local machine, but final project explanation should emphasize that SQL is the official source.

### 8.4 Salary Prediction

Salary prediction is a regression problem.

Why regression? Because salary is numeric and continuous.

The model uses job-related features such as title, description, skills, location, seniority signals, and structured warehouse fields when available.

The output is an estimated salary value or salary-related prediction.

### 8.5 Job Classification

Job classification is a supervised classification problem.

Classification is appropriate when the target is a label.

Examples include:

- remote, hybrid, or on-site
- full-time or not full-time
- job category labels

The point is to show that cleaned warehouse data can support categorical predictions.

### 8.6 Job Segmentation

Job segmentation uses clustering, especially K-Means.

Why clustering? Because sometimes there is no manual label. The model discovers groups of similar jobs based on text and structured features.

The result can help explain market segments such as:

- data roles
- web development roles
- infrastructure roles
- business intelligence roles
- management or senior roles

### 8.7 ML Artifacts

Model artifacts are saved under:

```text
Artifacts/models/ml/
```

Example artifacts:

```text
salary_regression_model.pkl
remote_classifier_model.pkl
full_time_classifier_model.pkl
job_segmentation_kmeans.pkl
```

Reports are saved under:

```text
Artifacts/reports/ml/
```

Example reports:

```text
ml_objectives_metrics.json
job_cluster_profiles.json
```

Latest SQL-based metrics recorded for the ML objectives:

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

Important metric interpretation:

- salary regression is limited by sparse salary coverage in job postings
- classification excludes target-leaking fields so the task remains realistic
- K-Means silhouette is low because job-market categories naturally overlap

## 9. NLP Domain

The NLP domain handles text understanding.

In Talent Bridge, NLP is needed because CVs and job descriptions are mostly unstructured text.

Main NLP areas:

- CV PDF text extraction
- language detection and translation fallback
- named entity recognition
- regex post-processing
- skill extraction and normalization
- CV-to-job semantic matching support

## 10. NLP CV Extraction

### 10.1 What It Does

The `NLP/CVExtraction/` module extracts structured information from candidate CV PDFs.

Main files:

```text
NLP/CVExtraction/src/pdf_reader.py
NLP/CVExtraction/src/language_service.py
NLP/CVExtraction/training/clean_data.py
NLP/CVExtraction/training/prepare_data.py
NLP/CVExtraction/training/train_ner_model.py
Artifacts/models/nlp/model-best/
```

It extracts information such as:

- name
- email
- phone number
- skills
- companies
- education
- colleges
- languages
- LinkedIn and GitHub links

### 10.2 Why It Exists

A PDF CV is not directly useful for matching or filtering.

Recruiters and algorithms need structured data. For example, matching needs a list of candidate skills. The recruiter modal needs extracted information. The CV quality module needs text and structural signals.

Therefore, the CV extraction module converts raw document text into structured information.

### 10.3 How It Works

The extraction flow is:

```text
PDF file
-> extract text with PyMuPDF
-> detect language
-> apply translation fallback if needed
-> run spaCy NER model
-> apply regex post-processing
-> apply skill scanner fallback
-> return structured extraction result
```

spaCy NER extracts learned entities from the CV text. Regex post-processing improves deterministic fields such as emails, phone numbers, and URLs. Skill scanning is added because technical skills can be missed by NER if the model did not learn all variants.

### 10.4 Why Rules And NER Are Combined

NER is flexible but not perfect. Rules are strict but reliable for patterns like emails.

Combining both gives better practical behavior:

```text
NER -> flexible entity extraction
Regex -> reliable contact and URL extraction
Skill dictionary -> robust technical skill coverage
```

## 11. NLP Skill Extraction And Normalization

### 11.1 What It Does

The `NLP/SkillExtraction/` module normalizes skill names.

Main file:

```text
NLP/SkillExtraction/src/normalization.py
```

It helps convert different spellings or aliases into consistent skill names.

For example:

```text
js -> javascript
py -> python
powerbi -> power bi
sql server -> sql
```

### 11.2 Why It Exists

Matching fails if the same skill appears in many forms.

For example, a CV might say `PowerBI`, while a job says `Power BI`. A human knows these are the same. The system must normalize them to compare correctly.

### 11.3 How It Works

The module applies text normalization, aliases, and known skill terms. Its output is used by:

- CV extraction
- recommendation scoring
- skill-gap analysis
- recruiter candidate search

## 12. DocumentAI Domain

The DocumentAI domain handles AI tasks related to documents themselves.

Talent Bridge has two major DocumentAI modules:

```text
DocumentAI/CVDocumentClassification/
DocumentAI/CVQualityScoring/
```

These are separate because they answer different questions:

```text
CV document classification: is this uploaded file really a CV?
CV quality scoring: if it is a CV, how good is it?
```

This separation is important. A file must first be accepted as a real CV before the platform gives quality advice or allows an application.

## 13. CV Document Classification

### 13.1 What It Does

The CV document classifier checks whether an uploaded document looks like a real CV.

Possible internal labels:

```text
cv
non_cv
uncertain
```

Runtime decisions are converted into:

```text
accepted
rejected
manual_review
```

### 13.2 Why It Exists

Without this module, a candidate could upload any PDF or document. The platform might then try to extract CV entities from invoices, contracts, screenshots, or unrelated documents.

That would create bad results for:

- NER extraction
- CV quality scoring
- job matching
- applications
- recruiter review

So the classifier protects the whole downstream workflow.

### 13.3 How It Works

Main files:

```text
DocumentAI/CVDocumentClassification/src/preprocessing.py
DocumentAI/CVDocumentClassification/src/model.py
DocumentAI/CVDocumentClassification/src/classifier.py
DocumentAI/CVDocumentClassification/training/prepare_dataset.py
DocumentAI/CVDocumentClassification/training/train_cv_document_classifier.py
```

The flow is:

```text
PDF or image document
-> render first page
-> convert page to fixed-size grayscale image
-> compact CNN predicts CV / Non-CV / uncertain
-> runtime text evidence checks important CV words
-> backend accepts, rejects, or asks for clearer CV
```

The compact CNN is a deep learning model because it learns visual document layout patterns.

The runtime text-evidence guardrail exists because the dataset has a limitation: positives are mostly CV PDFs and negatives are mostly TIFF documents. Rendering both as page images reduces format bias, but a stronger future dataset should include more Non-CV PDFs and scanned CVs.

### 13.4 Training Data And Metrics

The local dataset is under:

```text
Data/document_classification/
```

Dataset size used:

```text
2487 CV samples
2484 Non-CV samples
```

Reported metrics:

```text
Accuracy: 0.9973
Precision CV: 0.9947
Recall CV: 1.0000
F1 CV: 0.9973
```

Important limitation:

```text
The metrics are strong on the validation split, but the source data has format bias because CV positives are mostly PDFs and Non-CV negatives are mostly TIFFs.
```

### 13.5 Backend Integration

The backend uses this classifier in:

```text
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
```

The important route is:

```text
POST /api/v1/cv/upload
```

This route rejects invalid uploads before extraction or application creation.

## 14. CV Quality Scoring

### 14.1 What It Does

The CV quality module grades the quality of an accepted CV.

It returns five quality grades:

```text
Excellent
Good
Average
Weak
Poor
```

It also returns the compatibility label:

```text
Pro
Non Pro
```

Other returned information includes:

- quality score
- rule score
- DL prediction
- decision source
- confidence
- positive checks
- issues
- suggestions

### 14.2 Why It Exists

Candidates need more than a file upload. They need guidance.

Recruiters also benefit from quick signals about whether a CV is complete, professional, and useful.

The quality module helps answer:

```text
Is the CV complete?
Does it contain contact information?
Does it mention skills?
Does it show experience and education?
Is it detailed enough?
What should the candidate improve?
```

### 14.3 How It Works

Main files:

```text
DocumentAI/CVQualityScoring/src/quality.py
DocumentAI/CVQualityScoring/src/features.py
DocumentAI/CVQualityScoring/src/rules.py
DocumentAI/CVQualityScoring/src/grades.py
DocumentAI/CVQualityScoring/src/dl_quality_model.py
DocumentAI/CVQualityScoring/src/dl_model_loader.py
DocumentAI/CVQualityScoring/src/classifier.py
DocumentAI/CVQualityScoring/training/train_quality_dl_model.py
```

The runtime flow is:

```text
Extracted CV text
-> normalize text
-> extract structural features
-> apply hard rule gates
-> compute rule score
-> run PyTorch MLP if artifacts exist
-> blend DL score and rule score
-> assign final grade
-> generate issues and suggestions
```

The model is hybrid:

```text
Rules -> explainability and hard gates
DL model -> learned quality estimation
Final output -> blended score and grade
```

This hybrid design was chosen because a pure black-box model would not explain what the candidate should improve. Rules allow the platform to say things like: add contact information, add skills, add education, add experience details, or improve content length.

### 14.4 Training Data And Honest Limitation

The pseudo-labeled dataset is:

```text
DocumentAI/CVQualityScoring/data/cv_quality_pseudo_labeled.jsonl
```

Dataset size:

```text
14930 records
2487 real CV PDFs
controlled synthetic variants
```

Reported DL metrics against pseudo-label holdout:

```text
MAE: 2.5206
R2: 0.9594
Grade accuracy: 0.8571
```

Important scientific limitation:

```text
The CV quality DL model uses rubric pseudo-labels and controlled synthetic variants. It was not trained on manually reviewed human ground-truth quality labels.
```

Therefore, the correct explanation is:

```text
The model is useful for demonstration, guidance, and platform behavior, but final scientific claims require a manually labeled CV quality dataset.
```

### 14.5 Manual CV Quality Labeling Workflow

The project includes a workflow to replace weak or synthetic labels with real reviewed CV labels.

Template file:

```text
DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

Example row:

```text
file_path,label,reviewer,review_date,notes
Data/samples/cv/Test CV/CV_Riahi_Chaima.pdf,Pro,Yassine,2026-05-05,Complete professional CV
```

Generate manual JSONL labels:

```bash
python DocumentAI/CVQualityScoring/training/merge_manual_labels.py --input DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

Train on manual labels:

```bash
python DocumentAI/CVQualityScoring/training/train_quality_model.py --dataset DocumentAI/CVQualityScoring/data/cv_quality_manual.jsonl
```

Recommended minimum before making stronger final claims:

```text
20 Pro CVs
20 Non Pro CVs
weak_label=false
synthetic=false
```

## 15. Recommendation And Matching

### 15.1 What It Does

The `Recommendation/JobRecommendation/` module ranks jobs for candidates and can support recruiter-side candidate matching.

Main files:

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/score_components.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/explainer.py
Recommendation/JobRecommendation/src/repository.py
Recommendation/JobRecommendation/src/ranking_service.py
```

### 15.2 Why It Exists

A recruitment platform needs more than keyword search.

Candidates need to know which jobs fit them. Recruiters need to understand why a candidate is relevant. The system also needs to explain recommendations instead of returning a mysterious score.

### 15.3 How Matching Works

The matching engine combines several signals:

```text
skills score
semantic similarity score
role score
experience score
education score
location score
opportunity score
```

Final weighting:

```text
35% skills
25% NLP semantic similarity
15% role
10% experience
5% education
5% location
5% opportunity
```

The general flow is:

```text
Candidate profile from CV/profile
-> cleaned jobs from SQL/platform repository
-> normalize skills and text
-> compute semantic similarity
-> compute structured scores
-> cap weak false-positive matches
-> generate explanation
-> rank results
```

### 15.4 BERT Semantic Matching

The semantic matching module is:

```text
Recommendation/JobRecommendation/src/semantic_similarity.py
```

The default transformer model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The dependency is pinned as:

```text
sentence-transformers>=2.6.1,<3.0.0
```

This pin is intentional because the tested backend stack uses a compatible `transformers` version.

If the transformer model cannot load, the system falls back to TF-IDF similarity. This is important because the application should remain usable even without model download or internet access.

### 15.5 Why Matching Is Explainable

Matching is not only a score. The recruiter and candidate need to understand the reasons.

For example, an explanation may mention:

- matched skills
- missing skills
- role alignment
- experience alignment
- location alignment
- semantic similarity between CV and job text

This makes the recommendation more transparent and defensible.

## 16. Skill-Gap Analysis

### 16.1 What It Does

Skill-gap analysis tells a candidate what is missing for a selected job.

Backend endpoints:

```text
GET /api/v1/skill-gap/jobs/{job_id}
GET /api/v1/skill-gap/top-missing
```

Core files:

```text
Backend/TalentBridgeAPI/app/platform/routers/skill_gap_routes.py
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
Frontend/TalentBridgeWeb/src/modules/matching/matching.api.js
```

### 16.2 Why It Exists

A candidate should not only know whether they match a job. They should know how to improve.

Skill-gap analysis changes the product from a simple matching tool into a guidance tool.

It answers:

```text
Which required skills do I already have?
Which skills am I missing?
Which missing skills are most important?
Which gaps are quick wins?
Which gaps are core blockers?
What should I learn next?
```

### 16.3 How It Works

The skill-gap engine compares candidate skills against job skills.

It returns:

- matched skills
- missing skills
- priority levels
- market demand score
- readiness level
- quick wins
- core gaps
- curated learning resources

The frontend displays this to candidates in the job discovery experience.

## 17. Backend API

### 17.1 What It Does

The backend is the central orchestrator of the platform.

Main location:

```text
Backend/TalentBridgeAPI/
```

Main files and folders:

```text
Backend/TalentBridgeAPI/app/main.py
Backend/TalentBridgeAPI/app/platform/api.py
Backend/TalentBridgeAPI/app/platform/routers/
Backend/TalentBridgeAPI/app/platform/store.py
Backend/TalentBridgeAPI/app/platform/schemas.py
Backend/TalentBridgeAPI/run_server.py
```

### 17.2 Why It Exists

The AI modules alone do not make a product. The backend turns them into a real application by managing:

- authentication
- role-based access control
- users and profiles
- companies
- jobs
- CV uploads
- CV validation
- CV extraction
- CV quality scoring
- matching
- applications
- shortlists
- notifications
- interview scheduling
- admin monitoring
- audit records
- Power BI role links

### 17.3 Main API Areas

The backend exposes `/api/v1/*` routes for the platform:

```text
Auth API
Users/Profile API
Companies API
Jobs API
CV API
Matching API
Skill Gap API
Applications API
Shortlist API
Notifications API
Admin API
```

It also keeps technical AI validation endpoints:

```text
POST /extract
POST /match-jobs
POST /classify-cv-quality
POST /analyze-cv-full
GET /analyses
GET /analyses/{analysis_id}
```

These older/direct endpoints are useful for testing AI parts without using the full frontend.

`POST /analyze-cv-full` can also save BI-ready CV analysis rows when `save_results=True` and the SQL CV analysis tables exist.

### 17.4 Authentication And RBAC

The platform has three main roles:

```text
candidate
recruiter
admin
```

Demo accounts:

```text
candidate@talentbridge.local / candidate123
recruiter@talentbridge.local / recruiter123
admin@talentbridge.local / admin123
```

RBAC means role-based access control.

It ensures that:

- candidates access candidate workflows
- recruiters access recruiter workflows
- admins access admin workflows
- candidates cannot manage recruiter applications
- recruiters cannot access admin reset tools
- admins can supervise the whole platform

### 17.5 Backend Data Persistence

The local demo runtime state is saved in:

```text
Artifacts/platform_store.json
```

This JSON store supports demo workflows without requiring full production database persistence.

SQL migration `008_create_platform_business_tables.sql` prepares `platform.*` tables for future production persistence, but the current runtime uses the JSON store by default.

This distinction is important:

```text
SQL warehouse -> official job/analytics/ML data foundation
Artifacts/platform_store.json -> local demo platform state
platform.* SQL tables -> prepared future production persistence target
```

### 17.6 Backend CV Upload Flow

The backend CV upload route is:

```text
POST /api/v1/cv/upload
```

It performs this sequence:

```text
Receive uploaded file
-> reject non-PDF file types
-> run CV document classifier
-> reject Non-CV or uncertain documents
-> extract text and entities with NLP
-> score CV quality
-> store CV record with extraction, quality, document_check, and preview data
```

This matters because the application flow requires a valid CV before applying.

### 17.7 Backend Job Discovery

Candidate job discovery uses:

```text
GET /api/v1/jobs
```

The backend reads jobs from SQL warehouse views when available. It supports pagination and filtering. The frontend loads jobs lazily, 20 by 20.

If SQL is unavailable, the platform can use fallback demo data so the UI remains usable.

### 17.8 Backend Application Workflow

Applications connect candidates and jobs.

Important behavior:

- candidate must select or upload a valid PDF CV
- backend prevents duplicate applications
- candidate cannot apply with an invalid or Non-CV document
- recruiter can inspect the application
- recruiter can add notes
- recruiter can reject or propose interviews
- candidate receives notifications

### 17.9 Interview Scheduling Workflow

The interview workflow supports multiple proposed time slots.

Important endpoints:

```text
POST /api/v1/recruiter/applications/{application_id}/interview-slots
POST /api/v1/applications/{application_id}/interview-slots/select
POST /api/v1/applications/{application_id}/interview-slots/decline
```

The lifecycle is:

```text
Recruiter proposes future slots
-> application status becomes InterviewTimeProposed
-> candidate chooses one slot or declines all
-> if declined, recruiter can re-propose
-> if selected, status becomes InterviewRequested
-> notifications are sent to both sides
```

The backend validates that proposed slots are in the future.

### 17.10 Admin Workflows

The admin role can:

- view platform monitoring
- inspect users
- inspect jobs
- inspect applications
- view AI jobs and audit information
- retry failed operations when supported
- reset demo data
- access admin Power BI role link

Admin exists because a real platform needs supervision and operational control.

## 18. Frontend Web Application

### 18.1 What It Does

The frontend is a Vue 3 SaaS-style role-based web application.

Main location:

```text
Frontend/TalentBridgeWeb/
```

Main files and folders:

```text
Frontend/TalentBridgeWeb/src/App.vue
Frontend/TalentBridgeWeb/src/main.js
Frontend/TalentBridgeWeb/src/styles.css
Frontend/TalentBridgeWeb/src/modules/auth/
Frontend/TalentBridgeWeb/src/modules/jobs/
Frontend/TalentBridgeWeb/src/modules/cv/
Frontend/TalentBridgeWeb/src/modules/matching/
Frontend/TalentBridgeWeb/src/modules/applications/
Frontend/TalentBridgeWeb/src/modules/companies/
Frontend/TalentBridgeWeb/src/modules/notifications/
Frontend/TalentBridgeWeb/src/modules/profiles/
Frontend/TalentBridgeWeb/src/modules/admin/
Frontend/TalentBridgeWeb/src/services/api/http.js
Frontend/TalentBridgeWeb/src/stores/authStore.js
```

### 18.2 Why It Exists

The frontend makes the project usable by different users.

Without the frontend, the project would only be API endpoints and scripts. The frontend demonstrates the real business workflows and role separation.

### 18.3 How It Works

The frontend flow is:

```text
User logs in
-> auth token and user are stored in authStore
-> frontend calls backend /api/v1 routes
-> UI changes based on user role
-> user performs candidate, recruiter, or admin workflows
```

The frontend only talks to the backend. It does not read SQL, does not run Python models, and does not access internal artifacts directly.

### 18.4 Candidate Experience

The candidate role includes:

- profile management
- PDF CV upload
- CV document validation
- CV quality feedback
- job discovery
- skill-gap analysis
- job application with selected CV
- application tracking
- notifications
- interview slot selection or decline
- candidate-only Power BI button

Important rule:

```text
The candidate does not see the internal numeric matching score.
```

This is intentional because an exact internal score can be misleading. The candidate sees guidance and explanations instead.

### 18.5 Recruiter Experience

The recruiter role includes:

- company management
- job management
- candidate search
- application review
- PDF CV preview
- NER extraction details
- CV quality details
- matching score and explanation
- recruiter notes
- rejection workflow
- interview slot proposal workflow
- recruiter-only Power BI button

The recruiter can see more internal information than the candidate because recruiters need decision support.

### 18.6 Admin Experience

The admin role includes:

- monitoring dashboard
- user overview
- job overview
- application overview
- AI job monitoring
- audit tools
- demo reset
- admin-only full Power BI link

The admin role exists to supervise the whole platform.

### 18.7 Frontend Styling

The frontend uses a dark SaaS visual style.

Special UI work includes:

- role-based dashboards
- profile modal and dropdown
- candidate job discovery cards
- application status labels
- PDF CV preview area
- recruiter application modal
- interview slot cards
- styled `datetime-local` inputs
- skill-gap readiness and missing-skill panels

## 19. Application Workflows In Detail

### 19.1 Candidate CV Enhancement Flow

This flow is for improving a CV, not necessarily applying to a job.

```text
Candidate opens Enhance CV
-> uploads PDF
-> backend checks PDF type
-> DocumentAI validates real CV
-> NLP extracts content
-> CV quality module grades it
-> frontend shows grade, issues, and suggestions
```

Why it exists:

```text
Candidates need feedback before applying, and the platform needs validated structured CV data.
```

### 19.2 Candidate Job Application Flow

This flow is separate from CV enhancement.

```text
Candidate opens Looking for Job
-> jobs load from backend
-> candidate selects or uploads a valid CV
-> candidate applies to a job
-> backend prevents duplicate application
-> backend stores application
-> candidate sees Applied state and notifications
```

Why application CV is separate:

```text
A candidate may enhance multiple CVs, but an application must be linked to a specific valid PDF CV.
```

### 19.3 Recruiter Review Flow

```text
Recruiter opens applications
-> selects application
-> previews PDF CV
-> checks extracted NER entities
-> checks CV quality
-> checks matching score and explanation
-> writes notes
-> rejects or proposes interview slots
```

Why it exists:

```text
Recruiters need decision support and a structured way to move applications forward.
```

### 19.4 Interview Flow

```text
Recruiter proposes slots
-> candidate receives notification
-> candidate selects one slot or declines all with reason
-> recruiter can re-propose if declined
-> final accepted slot is stored
```

Why it exists:

```text
Interview scheduling is a real recruitment workflow and makes the platform more complete than a simple recommendation demo.
```

### 19.5 Admin Reset Flow

```text
Admin opens admin tools
-> clicks reset demo data
-> local platform store is reset
-> demo returns to a clean state
```

Why it exists:

```text
During demonstrations, repeated applications and state changes can make the platform messy. Reset gives a clean reproducible demo.
```

## 20. Artifacts

The `Artifacts/` folder stores generated outputs.

Examples:

```text
Artifacts/models/nlp/model-best/
Artifacts/models/ml/
Artifacts/models/document_ai/cv_document_classifier/
Artifacts/models/document_ai/cv_quality_dl/
Artifacts/reports/ml/
Artifacts/reports/document_ai/
Artifacts/platform_store.json
```

Why this folder exists:

```text
Source code and generated outputs should not be mixed. Artifacts are outputs from training, validation, or local runtime.
```

## 21. Infrastructure

### 21.1 What It Does

The `Infrastructure/` module provides startup scripts, Docker assets, environment examples, and CI configuration.

Important files:

```text
start_talent_bridge.ps1
start_talent_bridge.bat
Infrastructure/scripts/start_local.ps1
Infrastructure/scripts/start_local.bat
Infrastructure/docker/backend.Dockerfile
Infrastructure/docker/frontend.Dockerfile
Infrastructure/compose/docker-compose.local.yml
Infrastructure/compose/docker-compose.prod.yml
Infrastructure/env/.env.example
Infrastructure/env/backend.env.example
Infrastructure/env/frontend.env.example
Infrastructure/cicd/github-actions/ci.yml
```

### 21.2 Why It Exists

A project should be easy to run and validate. Infrastructure scripts avoid forcing the user to manually remember many commands.

### 21.3 How To Run Locally

Recommended launcher:

```powershell
.\start_talent_bridge.ps1
```

Run with validation checks:

```powershell
.\start_talent_bridge.ps1 -RunChecks
```

Useful options:

```powershell
.\start_talent_bridge.ps1 -SkipSql
.\start_talent_bridge.ps1 -SkipDashboard
.\start_talent_bridge.ps1 -SkipBrowser
.\start_talent_bridge.ps1 -NoInstall
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

## 22. Tests And Validation

Testing exists to prove that the system still works after changes.

Important validation commands:

```bash
python -m compileall -q Backend/TalentBridgeAPI NLP DocumentAI Recommendation MachineLearning Tests
python Tests/smoke/test_demo_logic.py
python Tests/smoke/test_cv_document_classifier.py
python Tests/smoke/test_platform_workflows.py
python -m pytest Tests/smoke/test_skill_gap.py -v
python Recommendation/JobRecommendation/src/test_bert_integration.py
python Tests/integration/test_sql_ml_views.py
```

Frontend build validation:

```bash
cd Frontend/TalentBridgeWeb
npm run build
```

Mini-project validation matrix:

| Mini-project | Folder | Main objective | Validation artifact |
| --- | --- | --- | --- |
| Data warehouse / ETL | `DataPlatform/` | Clean raw jobs and load SQL Server warehouse | SSIS packages and SQL views |
| BI dashboard | `BI/` | Visualize IT job market trends | Power BI `.pbix` |
| NLP CV extraction | `NLP/CVExtraction/` | Extract entities from CV PDFs | spaCy model and API extraction |
| Skill extraction / normalization | `NLP/SkillExtraction/` | Normalize skills across CVs/jobs | alias-normalized skill lists |
| NLP CV-job matching | `NLP/CVMatching/`, `Recommendation/` | Compute CV-job similarity and score | match results with score breakdown |
| ML salary prediction | `MachineLearning/` | Predict salary from SQL warehouse jobs | regression metrics and model |
| ML job classification | `MachineLearning/` | Classify remote/full-time job signals | classification metrics and models |
| ML job segmentation | `MachineLearning/` | Cluster similar jobs | cluster profiles and report |
| Document AI CV quality | `DocumentAI/` | Grade CV quality and classify `Pro` / `Non Pro` | DL quality score, grade, and suggestions |
| Backend platform | `Backend/` | Role-based recruitment API | `/api/v1` routes |
| Frontend platform | `Frontend/` | Role-based SaaS UI | Vue app build and role workflows |
| Infrastructure | `Infrastructure/` | Local/deployment scripts | launcher, Docker, Compose, CI |

Key smoke tests:

```text
Tests/smoke/test_demo_logic.py
Tests/smoke/test_cv_document_classifier.py
Tests/smoke/test_platform_workflows.py
Tests/smoke/test_skill_gap.py
Tests/integration/test_sql_ml_views.py
```

`test_platform_workflows.py` is especially important because it checks the role-based business flow, including interview scheduling.

## 23. Security And Access Control Notes

The project includes role separation, but it is still a demo platform.

Implemented concepts:

- login routes
- role-based access control
- candidate/recruiter/admin separation
- endpoint protection by role
- recruiter ownership checks for applications
- admin-only tools

Production improvements still needed:

- stronger password hashing
- production JWT expiration and refresh handling
- database-backed sessions or user persistence
- production-grade secrets management
- stricter file scanning and storage policies
- full SQL persistence for platform workflows

## 24. Why Some Design Decisions Were Made

### 24.1 Why Use A Modular Monolith

Talent Bridge is organized as a modular monolith.

This means the project is one repository, but each domain has its own folder and responsibility.

This was chosen because:

- it is easier to run locally
- it is easier to demonstrate
- modules remain separated
- future migration to services is possible
- development is faster than managing many microservices

### 24.2 Why Use SQL Warehouse Before ML

ML should use cleaned data, not raw CSV.

The warehouse provides:

- consistent cleaning
- reusable views
- stable schemas
- BI compatibility
- backend compatibility

### 24.3 Why Use Hybrid CV Quality

CV quality needs explainability.

A pure neural model could output a score but not explain why. Rules can explain issues clearly. The DL model adds learned scoring behavior. The hybrid design gives both.

### 24.4 Why Use BERT With TF-IDF Fallback

BERT/SentenceTransformer gives better semantic similarity than simple keyword overlap.

However, transformer models can fail to load if dependencies or model downloads are unavailable. TF-IDF fallback keeps the application usable.

### 24.5 Why Candidate Does Not See Internal Match Score

Internal scores can be misunderstood. A score like `72%` may look exact even though it is based on weighted signals and available data.

Candidates receive guidance, matched skills, missing skills, and explanations instead. Recruiters and admins can see scores because they need operational decision support.

### 24.6 Why Power BI Is External Link Based

Embedded Power BI requires correct tenant, workspace, service principal, and permission setup. Because the account context does not support this cleanly, external role-based links are safer for the project.

## 25. Important Limitations

The project is functional, but it has honest limitations.

### 25.1 CV Quality Labels

The CV quality model uses rubric pseudo-labels and synthetic variants, not manually reviewed human labels.

Impact:

```text
The model is useful for guidance and demo behavior, but not enough for strong scientific claims about real-world CV quality.
```

Future improvement:

```text
Create a manually labeled dataset with human-reviewed CV quality labels.
```

### 25.2 CV Document Classifier Dataset Bias

The CV document classifier has strong validation metrics, but the dataset has source-format bias:

```text
CV positives: mostly PDFs
Non-CV negatives: mostly TIFFs
```

Future improvement:

```text
Add Non-CV PDFs, scanned CV images, and more diverse real-world documents.
```

### 25.3 Platform Persistence

The runtime demo platform state currently uses:

```text
Artifacts/platform_store.json
```

SQL `platform.*` tables are prepared but not the default runtime persistence layer yet.

Future improvement:

```text
Replace JSON demo persistence with SQL repositories.
```

### 25.4 Power BI Role Security

The frontend has role-specific buttons, but true report-level security must be enforced in Power BI itself.

Future improvement:

```text
Use separate reports/workspaces or Power BI permissions per role.
```

### 25.5 BERT Runtime Dependency

BERT semantic matching depends on compatible packages and model availability.

Future improvement:

```text
Pre-cache the sentence-transformer model or package it for deployment.
```

## 26. How To Explain The Project In A Presentation

A clear presentation order is:

1. Start with the business problem: recruitment needs clean data, CV understanding, matching, and role-based workflows.
2. Explain the architecture: each folder is a separate domain with clear responsibility.
3. Explain the data foundation: raw CSV is cleaned into SQL Server warehouse.
4. Explain BI: Power BI reads the warehouse to visualize job-market trends.
5. Explain ML: salary regression, classification, and segmentation train from SQL views.
6. Explain NLP: PDF text extraction, language handling, NER, regex, and skill normalization.
7. Explain DocumentAI: first validate whether the file is a CV, then score CV quality.
8. Explain recommendation: combine skills, BERT semantic similarity, and structured scoring.
9. Explain skill-gap: show missing skills and learning priorities to candidates.
10. Explain backend: FastAPI connects all modules into secure workflows.
11. Explain frontend: Vue provides candidate, recruiter, and admin experiences.
12. Demonstrate the workflow: candidate upload, job application, recruiter review, interview scheduling, admin monitoring.
13. Finish with validation and honest limitations.

## 27. Complete Demo Script

Start the application:

```powershell
.\start_talent_bridge.ps1
```

Open:

```text
http://localhost:5173
```

Candidate demo:

```text
Login as candidate@talentbridge.local / candidate123
-> upload a PDF CV
-> show CV validation and quality grade
-> open Looking for Job
-> load job recommendations
-> open skill-gap analysis
-> apply using a valid CV
-> check application state and notifications
```

Recruiter demo:

```text
Login as recruiter@talentbridge.local / recruiter123
-> open applications
-> preview candidate CV PDF
-> inspect extracted NER data
-> inspect CV quality
-> inspect matching explanation
-> propose multiple interview slots
```

Candidate interview demo:

```text
Return to candidate
-> see proposed interview slots
-> select one slot or decline all
```

Admin demo:

```text
Login as admin@talentbridge.local / admin123
-> inspect monitoring and platform data
-> inspect audit/admin tools
-> open admin Power BI link
-> reset demo data if needed
```

## 28. Important Files To Know

Root and architecture:

```text
README.md
Docs/architecture/overview.md
Docs/FULL_PROJECT_DOCUMENTATION.md
```

Backend:

```text
Backend/TalentBridgeAPI/app/main.py
Backend/TalentBridgeAPI/app/platform/api.py
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
Backend/TalentBridgeAPI/app/platform/routers/job_routes.py
Backend/TalentBridgeAPI/app/platform/routers/application_routes.py
Backend/TalentBridgeAPI/app/platform/routers/skill_gap_routes.py
Backend/TalentBridgeAPI/app/platform/routers/admin_routes.py
Backend/TalentBridgeAPI/app/platform/store.py
Backend/TalentBridgeAPI/run_server.py
```

Frontend:

```text
Frontend/TalentBridgeWeb/src/App.vue
Frontend/TalentBridgeWeb/src/styles.css
Frontend/TalentBridgeWeb/src/services/api/http.js
Frontend/TalentBridgeWeb/src/stores/authStore.js
Frontend/TalentBridgeWeb/src/modules/
```

Data and BI:

```text
Data/raw/data_jobs.csv
DataPlatform/Warehouse/views/
DataPlatform/Warehouse/migrations/
BI/PowerBI/Mission D'entreprise.pbix
```

NLP:

```text
NLP/CVExtraction/src/pdf_reader.py
NLP/CVExtraction/src/language_service.py
NLP/CVExtraction/training/train_ner_model.py
NLP/SkillExtraction/src/normalization.py
```

DocumentAI:

```text
DocumentAI/CVDocumentClassification/src/classifier.py
DocumentAI/CVQualityScoring/src/quality.py
DocumentAI/CVQualityScoring/src/dl_quality_model.py
```

Recommendation and skill gap:

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/explainer.py
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
```

Validation:

```text
Tests/smoke/test_demo_logic.py
Tests/smoke/test_cv_document_classifier.py
Tests/smoke/test_platform_workflows.py
Tests/smoke/test_skill_gap.py
Tests/integration/test_sql_ml_views.py
```

## 29. Final Summary

Talent Bridge is a complete recruitment intelligence platform.

It starts with raw job data and turns it into a SQL data warehouse. That warehouse feeds Power BI dashboards, ML models, backend job discovery, and recommendation workflows.

On the candidate side, the platform validates uploaded PDF CVs, rejects invalid documents, extracts structured CV information, grades CV quality, recommends jobs, shows skill gaps, and manages applications.

On the recruiter side, the platform supports job and application management, CV preview, NER inspection, CV quality review, matching explanations, notes, rejection, and interview slot proposals.

On the admin side, the platform supports monitoring, audit visibility, data overview, demo reset, and role-based Power BI access.

Technically, the project combines:

- SQL data warehousing
- Power BI
- FastAPI
- Vue 3
- NLP extraction
- spaCy NER
- skill normalization
- CNN document classification
- PyTorch MLP CV quality scoring
- BERT/SentenceTransformer semantic matching
- TF-IDF fallback
- classical ML regression, classification, and clustering
- role-based application workflows

The most important architectural idea is separation of responsibility:

```text
DataPlatform cleans data.
BI visualizes data.
MachineLearning trains predictive models.
NLP extracts text meaning.
DocumentAI validates and scores CV documents.
Recommendation ranks jobs and explains matches.
Backend orchestrates workflows and security.
Frontend gives each role a usable interface.
Tests validate the platform.
```

This separation makes the project easier to explain, easier to test, and easier to improve.
