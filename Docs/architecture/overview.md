# Talent Bridge Architecture

Talent Bridge is organized as a modular monolith that can evolve into independent services.

Runtime flow:

```text
Frontend/TalentBridgeWeb
-> Backend/TalentBridgeAPI /api/v1 platform routes
-> NLP / DocumentAI / Recommendation modules
-> DataPlatform SQL Server warehouse
-> Artifacts/platform_store.json for local demo state
-> Backend response
-> Frontend UI
```

Analytics/model-training flow:

```text
Data/raw/data_jobs.csv
-> DataPlatform/ETL/SSIS
-> DW_DataJobs SQL Server warehouse
-> DataPlatform/Warehouse/views
-> MachineLearning modules
-> Artifacts/models and Artifacts/reports
```

Dependency direction:

```text
Frontend -> Backend -> Domain Modules -> Shared/DataPlatform outputs
```

The frontend must only call backend APIs. Domain modules must not import FastAPI route code.

Main domains:

- `DataPlatform`: ETL, warehouse views, SQL scripts.
- `BI`: Power BI dashboard assets.
- `NLP`: CV extraction and skill normalization.
- `MachineLearning`: salary regression, job classification, K-Means segmentation.
- `DocumentAI`: CV quality scoring.
- `Recommendation`: semantic matching, job ranking, and explanations.
- `Backend`: API orchestration, auth/RBAC, platform workflows, and technical AI validation endpoints.
- `Frontend`: Vue application.
- `Infrastructure`: scripts, Docker, environment templates, and CI workflow.
- `Artifacts`: generated models, reports, and local JSON demo state.

Platform routes are registered from `Backend/TalentBridgeAPI/app/platform/api.py` and implemented under `Backend/TalentBridgeAPI/app/platform/routers/`.

The local demo store is `Artifacts/platform_store.json`. SQL migration `008_create_platform_business_tables.sql` prepares the future `platform.*` persistence layer.
