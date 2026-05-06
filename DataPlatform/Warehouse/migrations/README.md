# Warehouse Migrations

Run migrations in numeric order.

Current migration set mirrors `DataPlatform/Warehouse/views`:

```text
001_create_vw_job_matching.sql
002_create_cv_analysis_tables.sql
003_create_cv_bi_views.sql
004_create_vw_ml_jobs.sql
005_create_vw_ml_salary_training.sql
006_create_vw_ml_classification_training.sql
007_create_vw_ml_segmentation_training.sql
```

The launcher currently applies scripts from `DataPlatform/Warehouse/views` for local development.
