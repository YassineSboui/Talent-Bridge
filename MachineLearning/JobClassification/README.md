# ML Job Classification Mini-Project

## What It Does

Classifies job signals from cleaned SQL warehouse jobs.

Implemented targets:

```text
remote vs onsite
full-time vs other schedule
```

## Why It Exists

The project objective requires classification of job offers such as remote and full-time jobs. This helps analyze and automate job categorization.

## Official Data Source

```text
DW_DataJobs.dbo.vw_ml_classification_training
```

## How It Works

1. Load SQL warehouse jobs.
2. Build text, categorical, and numeric features.
3. Remove target-leaking fields.
4. Train Logistic Regression and SGD candidates.
5. Select best model by macro F1.

The implementation is centralized in:

```text
MachineLearning/SharedML/src/train_ml_objectives.py
Backend/TalentBridgeAPI/scripts/train_ml_objectives.py
```

## Latest SQL-Based Metrics

Remote classification:

```text
Accuracy: 0.8659
Macro F1: 0.7525
Weighted F1: 0.8860
```

Full-time classification:

```text
Accuracy: 0.7155
Macro F1: 0.6230
Weighted F1: 0.7509
```

## Artifacts

```text
Artifacts/models/ml/remote_classifier_model.pkl
Artifacts/models/ml/full_time_classifier_model.pkl
Artifacts/reports/ml/ml_objectives_metrics.json
```

If old classifier artifacts exist from earlier iterations, they are legacy outputs; the current final classifiers are the remote and full-time artifacts above.

## Teacher Validation Checklist

- Uses cleaned SQL views.
- Implementation path is documented.
- Has two classification targets.
- Avoids target leakage.
- Reports accuracy, macro F1, weighted F1.
- Saves trained classifier artifacts.
