# Document AI CV Quality Mini-Project

## What It Does

Classifies CV quality as:

```text
Pro
Non Pro
```

It also returns:

```text
quality score
confidence
hard gates
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
DocumentAI/CVQualityScoring/src/classifier.py
DocumentAI/CVQualityScoring/src/model_loader.py
DocumentAI/CVQualityScoring/src/quality_model.py
DocumentAI/CVQualityScoring/training/build_quality_dataset.py
DocumentAI/CVQualityScoring/training/generate_quality_seed_dataset.py
DocumentAI/CVQualityScoring/training/merge_manual_labels.py
DocumentAI/CVQualityScoring/training/train_quality_model.py
DocumentAI/CVQualityScoring/training/validate_quality_dataset.py
```

## How It Works

1. Normalize CV text.
2. Extract structure/content features.
3. Apply hard gates for severe issues.
4. Compute explainable rule score.
5. Optionally combine with trained bootstrap classifier.
6. Return feedback and suggestions.

The current trained model is demo-grade. It can use bootstrap, weak, and synthetic labels; strong final claims require manually reviewed real CV labels with `weak_label=false` and `synthetic=false`.

## Model Artifact

```text
Artifacts/models/document_ai/cv_quality_model.pkl
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
- Provides score and feedback.
- Has explainable rules.
- Has model artifact support.
- Has manual labeling workflow for real CV labels.
- Clearly states weak/synthetic label limitation.
