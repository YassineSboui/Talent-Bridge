# CV Quality Scoring

## What This Module Does

This module evaluates the quality of a validated CV and gives feedback to the candidate and recruiter.

It returns a five-level quality grade:

```text
Excellent
Good
Average
Weak
Poor
```

It also returns the compatibility label used by earlier project validation:

```text
Pro
Non Pro
```

Main runtime function:

```python
from DocumentAI.CVQualityScoring.src.quality import classify_cv_quality

result = classify_cv_quality(cv_text, extraction=extracted_entities)
```

## Why It Was Built

Recruitment workflows need more than file upload. Candidates need to know if their CV is complete and professional before applying. Recruiters need a quick signal about CV completeness and quality.

This module answers:

- Does the CV have contact information?
- Does it contain skills?
- Does it contain education?
- Does it contain experience or projects?
- Does it have links such as LinkedIn or GitHub?
- Is the text too short, noisy, or repeated?
- Does the CV contain dates and impact evidence?
- What should the candidate improve?

## How It Works

The final scoring system is hybrid:

```text
CV text and NLP extraction
-> text normalization
-> structural/content feature extraction
-> hard gate checks
-> explainable rule score
-> PyTorch MLP score if DL artifact exists
-> optional legacy sklearn model as second opinion
-> blend score and assign grade
-> return issues and suggestions
```

Why hybrid design:

- rules explain what is missing
- hard gates prevent obviously weak CVs from being accepted as high quality
- the DL model learns scoring patterns from feature/text combinations
- the final output stays understandable for candidates and teachers

## Main Files

```text
DocumentAI/CVQualityScoring/src/quality.py
DocumentAI/CVQualityScoring/src/features.py
DocumentAI/CVQualityScoring/src/rules.py
DocumentAI/CVQualityScoring/src/grades.py
DocumentAI/CVQualityScoring/src/dl_quality_model.py
DocumentAI/CVQualityScoring/src/dl_model_loader.py
DocumentAI/CVQualityScoring/src/model_loader.py
DocumentAI/CVQualityScoring/src/quality_model.py
DocumentAI/CVQualityScoring/training/build_pseudo_quality_dataset.py
DocumentAI/CVQualityScoring/training/train_quality_dl_model.py
DocumentAI/CVQualityScoring/training/merge_manual_labels.py
DocumentAI/CVQualityScoring/training/train_quality_model.py
DocumentAI/CVQualityScoring/training/validate_quality_dataset.py
```

File responsibilities:

| File | Responsibility |
| --- | --- |
| `src/quality.py` | Main runtime quality classification and score blending. |
| `src/features.py` | Extracts text length, contacts, sections, noise, repetition, dates, and impact signals. |
| `src/rules.py` | Hard gates, rule score helpers, and confidence logic. |
| `src/grades.py` | Converts numeric score to quality grade and `Pro / Non Pro`. |
| `src/dl_quality_model.py` | Defines the PyTorch MLP architecture. |
| `src/dl_model_loader.py` | Loads DL artifacts and predicts quality score. |
| `src/model_loader.py` | Loads optional legacy sklearn quality model. |
| `src/quality_model.py` | Feature selectors and ordered feature list for model artifacts. |
| `training/build_pseudo_quality_dataset.py` | Builds pseudo-labeled DL dataset from real CV PDFs and variants. |
| `training/train_quality_dl_model.py` | Trains the PyTorch MLP. |
| `training/merge_manual_labels.py` | Converts reviewed labels into JSONL. |
| `training/train_quality_model.py` | Trains the legacy sklearn Pro/Non Pro model. |
| `training/validate_quality_dataset.py` | Summarizes labels, weak labels, synthetic count, and recommendations. |

## Features Used

The module extracts features such as:

```text
has_email
has_phone
has_profile_link
has_skills_section
has_education_section
has_experience_or_projects
has_languages_section
has_certifications_section
section_count
core_section_count
text_length
word_count
noise_ratio
low_noise
repeated_line_ratio
low_repetition
bullet_line_count
has_professional_dates
has_quantified_impact
```

These features are used by rules and by the DL model.

## Hard Gates

Hard gates are severe problems that force or cap the quality decision.

Examples:

```text
CV text is too short.
CV has no reliable contact information.
CV is missing most core sections.
CV extraction is too noisy.
CV contains too much repeated content.
```

Hard gates exist because a neural score should not override obvious quality failures.

## DL Model

Model class:

```text
CvQualityMlp
```

Input:

```text
TF-IDF text features + scaled numeric structural features
```

Architecture summary:

```text
Input vector
-> Linear 256 + BatchNorm + ReLU + Dropout
-> Linear 128 + ReLU + Dropout
-> Linear 64 + ReLU
-> Linear 1
-> continuous 0-100 quality score
```

Why this model:

- MLP is appropriate for mixed tabular + text-vector features
- faster and simpler than large language models
- easy to save and load locally
- produces a continuous score that maps naturally to grades

## Dataset

Main pseudo-labeled dataset:

```text
DocumentAI/CVQualityScoring/data/cv_quality_pseudo_labeled.jsonl
```

Dataset size:

```text
14930 records
2487 real CV PDFs
controlled synthetic variants for Poor, Weak, Average, Good, Excellent calibration
```

Label source:

```text
rubric pseudo-labels + controlled synthetic variants
```

Important honesty note:

```text
The DL model is not trained on manually reviewed human ground-truth quality labels. It uses rubric pseudo-labels and synthetic variants. It is useful for demo guidance, but stronger scientific claims require manual labels.
```

## Build Pseudo-Labeled Dataset

```bash
python DocumentAI/CVQualityScoring/training/build_pseudo_quality_dataset.py
```

What it does:

- reads real CV PDFs
- extracts text
- computes rubric score
- creates synthetic degraded variants
- creates controlled synthetic examples by grade
- writes JSONL training records

## Train DL Model

```bash
python DocumentAI/CVQualityScoring/training/train_quality_dl_model.py
```

Training behavior:

- loads JSONL records with `manual_score`
- builds TF-IDF text features
- builds numeric feature matrix
- scales numeric features
- trains PyTorch MLP
- uses weighted samples by grade
- evaluates MAE, R2, and grade accuracy
- saves artifacts and reports

## Artifacts

```text
Artifacts/models/document_ai/cv_quality_dl/model.pt
Artifacts/models/document_ai/cv_quality_dl/vectorizer.pkl
Artifacts/models/document_ai/cv_quality_dl/scaler.pkl
Artifacts/models/document_ai/cv_quality_dl/metadata.json
Artifacts/reports/document_ai/cv_quality_dl_metrics.json
Artifacts/reports/document_ai/cv_quality_dl_preview.csv
Artifacts/models/document_ai/cv_quality_model.pkl
```

## Current Metrics

Metrics against pseudo-label holdout:

```text
MAE: 2.5206
R2: 0.9594
Grade accuracy: 0.8571
```

Interpretation:

```text
These metrics validate consistency against the rubric pseudo-labels. They do not prove human-level CV quality judgment because no manually reviewed ground-truth dataset is used yet.
```

## Manual Labeling Workflow

Template:

```text
DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

Example row:

```text
file_path,label,reviewer,review_date,notes
Data/samples/cv/Test CV/CV_Riahi_Chaima.pdf,Pro,Yassine,2026-05-05,Complete professional CV
```

Generate manual JSONL:

```bash
python DocumentAI/CVQualityScoring/training/merge_manual_labels.py --input DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

Train legacy model on manual labels:

```bash
python DocumentAI/CVQualityScoring/training/train_quality_model.py --dataset DocumentAI/CVQualityScoring/data/cv_quality_manual.jsonl
```

Recommended minimum before stronger final claims:

```text
20 Pro CVs
20 Non Pro CVs
weak_label=false
synthetic=false
```

## Runtime Output Example

```json
{
  "quality_label": "Pro",
  "quality_grade": "Good",
  "quality_score": 82,
  "rule_score": 78,
  "decision_source": "hybrid_dl_rules",
  "hard_gates": [],
  "issues": [],
  "suggestions": ["Add measurable impact where possible"]
}
```

## Backend Integration

Backend route:

```text
POST /api/v1/cv/upload
```

Backend file:

```text
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
```

The backend stores CV quality results with the uploaded CV record. Candidates see grade and suggestions. Recruiters see quality details inside the application review modal.

## Validation

```bash
python Tests/smoke/test_demo_logic.py
python -m compileall -q DocumentAI/CVQualityScoring
```

## Limitations And Future Improvements

Current limitation:

```text
CV quality labels are pseudo-labels, not human-reviewed ground truth.
```

Future improvements:

- manually label real CVs
- use multiple reviewers and disagreement resolution
- train with `weak_label=false` and `synthetic=false` data
- evaluate separately on real human labels
- add more multilingual CV examples
- improve feedback personalization by target role
