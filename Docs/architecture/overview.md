# Talent Bridge Architecture

Talent Bridge is organized as a modular monolith that can evolve into independent services.

Runtime flow:

```text
Frontend/TalentBridgeWeb
-> Backend/TalentBridgeAPI
-> NLP / DocumentAI / Recommendation modules
-> DataPlatform SQL Server warehouse
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
- `NLP`: CV extraction, skill normalization, semantic matching.
- `MachineLearning`: salary regression, job classification, K-Means segmentation.
- `DocumentAI`: CV quality scoring.
- `Recommendation`: job ranking and explanations.
- `Backend`: API orchestration.
- `Frontend`: Vue application.
- `Infrastructure`: scripts, Docker, environment, CI/CD placeholders.
- `Artifacts`: generated models and reports.
