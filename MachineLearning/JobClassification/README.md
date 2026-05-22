# Job Classification

## What This Module Does

This objective classifies job posting signals from cleaned warehouse data.

Implemented targets:

```text
remote vs onsite/non-remote
full-time vs other schedule
```

Problem type:

```text
Supervised classification
```

Classification is used because the targets are labels.

## Why It Was Built

The project needs a classification objective. Remote work and full-time schedule are useful business categories in job-market analysis.

The module answers:

```text
Can we classify remote work from job features?
Can we classify full-time jobs from job features?
```

## Official Data Source

Objective-specific SQL view:

```text
DW_DataJobs.dbo.vw_ml_classification_training
```

Central runner source:

```text
DW_DataJobs.dbo.vw_ml_jobs
```

## Implementation

Main implementation:

```text
MachineLearning/SharedML/src/train_ml_objectives.py
```

Relevant functions:

```text
train_remote_classifier
train_full_time_classifier
train_classifier
classification_metrics
```

## How It Works

```text
load cleaned SQL rows
-> prepare reusable feature columns
-> remove target-leaking features
-> split train/test data
-> train candidate classifiers
-> evaluate accuracy, macro F1, weighted F1
-> select best model by macro F1
-> save model artifacts
```

Candidate classifiers:

```text
LogisticRegression
SGDClassifier with log-loss and elasticnet penalty
```

Why target leakage is removed:

```text
A model should not learn the answer from a field that directly contains the target. For example, full-time classification excludes schedule_primary and is_full_time from features.
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

Metric interpretation:

- accuracy shows global correctness
- macro F1 is important when classes are imbalanced
- weighted F1 accounts for class frequency

## Artifacts

```text
Artifacts/models/ml/remote_classifier_model.pkl
Artifacts/models/ml/full_time_classifier_model.pkl
Artifacts/reports/ml/ml_objectives_metrics.json
```

If old classifier artifacts exist from earlier iterations, they are legacy outputs. The current final classifiers are the remote and full-time artifacts above.

## Run

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

## Validation Checklist

- Uses cleaned SQL views.
- Implements two classification targets.
- Avoids target leakage.
- Reports accuracy, macro F1, and weighted F1.
- Saves trained classifier artifacts.
