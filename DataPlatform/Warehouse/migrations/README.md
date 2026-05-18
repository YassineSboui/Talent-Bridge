# Warehouse Migrations

Run migrations in numeric order.

Run the migration set below for a full local warehouse/platform setup:

```text
001_create_vw_job_matching.sql
002_create_cv_analysis_tables.sql
003_create_cv_bi_views.sql
004_create_vw_ml_jobs.sql
005_create_vw_ml_salary_training.sql
006_create_vw_ml_classification_training.sql
007_create_vw_ml_segmentation_training.sql
008_create_platform_business_tables.sql
```

Migrations `001` to `007` mirror the view/table scripts used by analytics, BI, matching, and ML. Migration `008` creates `platform.*` business tables for future production persistence and does not mirror a file under `DataPlatform/Warehouse/views`.

The launcher currently applies scripts from `DataPlatform/Warehouse/views` for local development. The role-based demo runtime persists platform state to `Artifacts/platform_store.json` by default.
