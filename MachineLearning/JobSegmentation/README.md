# Job Segmentation

## What This Module Does

This objective groups similar job postings into clusters.

Problem type:

```text
Unsupervised clustering
```

Main technology:

```text
MiniBatchKMeans
```

Optional candidate:

```text
HDBSCAN if installed
```

## Why It Was Built

The project needs a segmentation objective. Job-market data does not always have perfect labels, so clustering helps discover natural groups.

The module answers:

```text
What groups of similar IT jobs exist in the market?
Which clusters have more remote jobs?
Which skills dominate each cluster?
Which countries or roles dominate each cluster?
```

## Official Data Source

Objective-specific SQL view:

```text
DW_DataJobs.dbo.vw_ml_segmentation_training
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
train_job_segmentation
try_hdbscan
cluster_profile
top_values
top_skills
```

## How It Works

```text
load cleaned SQL rows
-> build text/categorical/numeric features
-> apply shared preprocessor
-> reduce dimensionality with TruncatedSVD
-> scale reduced vectors
-> train MiniBatchKMeans for k=4..10
-> optionally try HDBSCAN
-> select best candidate by silhouette score
-> generate cluster profile report
-> save clustering artifact
```

## Why TruncatedSVD Is Used

The feature matrix includes TF-IDF text vectors, which can be high-dimensional and sparse. `TruncatedSVD` reduces the matrix to a smaller dense representation before clustering.

This makes clustering faster and more stable.

## Latest SQL-Based Result

```text
Best K: 7
Silhouette: 0.0073
```

Important interpretation:

```text
The low silhouette is expected because job-market data has overlapping natural groups. A data analyst job can share skills with BI, business analyst, and data engineering roles.
```

## Cluster Profiles

The profile report summarizes each cluster with:

- cluster size
- share percentage
- remote rate
- average salary when available
- top roles
- top countries
- top schedules
- top skills

Report path:

```text
Artifacts/reports/ml/job_cluster_profiles.json
```

## Artifacts

```text
Artifacts/models/ml/job_segmentation_kmeans.pkl
Artifacts/reports/ml/job_cluster_profiles.json
Artifacts/reports/ml/ml_objectives_metrics.json
```

The model artifact stores:

```text
preprocessor
svd
kmeans or hdbscan model
features
algorithm name
best k
silhouette
cluster profile
```

## Run

```bash
cd Backend/TalentBridgeAPI
python scripts/train_ml_objectives.py --source sql --max-rows 60000 --sample-size 24000
```

## Validation Checklist

- Uses SQL warehouse data.
- Tests multiple cluster counts.
- Produces cluster profiles.
- Explains silhouette limitation.
- Saves trained clustering artifact.
