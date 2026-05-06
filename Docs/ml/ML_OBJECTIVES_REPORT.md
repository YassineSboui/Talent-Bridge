# Machine Learning Objectives Report

The three ML objectives are trained from the cleaned SQL warehouse view `dbo.vw_ml_jobs`.

Training command:

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --max-rows 60000 --sample-size 24000
```

CSV mode exists only as a development fallback:

```bash
python scripts/train_ml_objectives.py --source csv --max-rows 60000 --sample-size 24000
```

Artifacts:

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

Latest SQL-based metrics:

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

Notes:

- Salary regression is limited by sparse salary coverage.
- Classification excludes target-leaking fields.
- K-Means silhouette is low because job-market data has overlapping natural groups.
