# Document AI CV Quality Mini-Project

## What It Does

Classifies CV quality as:

```text
Excellent
Good
Average
Weak
Poor

Pro
Non Pro
```

It also returns:

```text
quality score
quality grade
confidence
hard gates
DL prediction
positive checks
issues
suggestions
```

## Why It Exists

Recruitment platforms need to help candidates improve CV quality before applying and help recruiters detect incomplete profiles.

## Main Files

```text
DocumentAI/CVQualityScoring/src/quality.py
DocumentAI/CVQualityScoring/src/features.py
DocumentAI/CVQualityScoring/src/rules.py
DocumentAI/CVQualityScoring/src/grades.py
DocumentAI/CVQualityScoring/src/dl_quality_model.py
DocumentAI/CVQualityScoring/src/dl_model_loader.py
DocumentAI/CVQualityScoring/src/classifier.py
DocumentAI/CVQualityScoring/src/model_loader.py
DocumentAI/CVQualityScoring/src/quality_model.py
DocumentAI/CVQualityScoring/training/build_quality_dataset.py
DocumentAI/CVQualityScoring/training/build_pseudo_quality_dataset.py
DocumentAI/CVQualityScoring/training/generate_quality_seed_dataset.py
DocumentAI/CVQualityScoring/training/merge_manual_labels.py
DocumentAI/CVQualityScoring/training/train_quality_dl_model.py
DocumentAI/CVQualityScoring/training/train_quality_model.py
DocumentAI/CVQualityScoring/training/validate_quality_dataset.py
```

## How It Works

1. Normalize CV text.
2. Extract structure/content features.
3. Apply hard gates for severe issues.
4. Compute explainable rule score.
5. Run the PyTorch MLP DL quality model when artifacts exist.
6. Combine DL score and rule score into a final grade.
7. Return feedback and suggestions from explainable rules.

The current DL model is trained on rubric pseudo-labels and controlled synthetic variants. It is useful for demo and platform behavior, but strong scientific claims still require manually reviewed real CV labels with `weak_label=false` and `synthetic=false`.

## Model Artifacts

```text
Artifacts/models/document_ai/cv_quality_dl/model.pt
Artifacts/models/document_ai/cv_quality_dl/vectorizer.pkl
Artifacts/models/document_ai/cv_quality_dl/scaler.pkl
Artifacts/models/document_ai/cv_quality_dl/metadata.json
Artifacts/models/document_ai/cv_quality_model.pkl
```

## Training Dataset

```text
DocumentAI/CVQualityScoring/data/cv_quality_pseudo_labeled.jsonl
```

Current pseudo-labeled dataset size:

```text
14,930 records
2,487 real CV PDFs
controlled synthetic variants for Poor, Weak, Average, Good, Excellent calibration
```

Current DL report:

```text
Artifacts/reports/document_ai/cv_quality_dl_metrics.json
```

## Manual Labeling Workflow

Template:

```text
DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

Docs:

```text
Docs/ml/manual_cv_labeling.md
```

## Validation

```bash
python Tests/smoke/test_demo_logic.py
```

## Teacher Validation Checklist

- Produces `Pro / Non Pro` label.
- Produces `Excellent / Good / Average / Weak / Poor` grade.
- Uses a PyTorch MLP neural network over NLP text features and structural quality features.
- Provides score and feedback.
- Has explainable rules.
- Has model artifact support.
- Has manual labeling workflow for real CV labels.
- Clearly states weak/synthetic label limitation.
