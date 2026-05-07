# ML Job Segmentation Mini-Project

## What It Does

Groups similar jobs into clusters.

Technology:

```text
MiniBatchKMeans with optional HDBSCAN candidate
```

## Why It Exists

The business objective is to group similar IT job offers by role, location, schedule, skills, and opportunity signals.

## Official Data Source

```text
DW_DataJobs.dbo.vw_ml_segmentation_training
```

## How It Works

1. Load cleaned SQL warehouse jobs.
2. Build text, categorical, and numeric features.
3. Reduce dimensionality with TruncatedSVD.
4. Scale reduced vectors.
5. Train K-Means with multiple `k` values.
6. Optionally try HDBSCAN if installed.
7. Select best clustering by silhouette score.
8. Generate cluster profiles.

The implementation is centralized in:

```text
MachineLearning/SharedML/src/train_ml_objectives.py
Backend/TalentBridgeAPI/scripts/train_ml_objectives.py
```

## Latest SQL-Based Result

```text
Best K: 7
Silhouette: 0.0073
```

Low silhouette is expected because job-market data has overlapping clusters.

## Artifacts

```text
Artifacts/models/ml/job_segmentation_kmeans.pkl
Artifacts/reports/ml/job_cluster_profiles.json
```

## Teacher Validation Checklist

- Uses SQL warehouse data.
- Implementation path is documented.
- Tests multiple cluster counts.
- Produces cluster profiles.
- Explains silhouette limitation.
- Saves trained clustering artifact.
