# Talent Bridge Demo

## Demo Flow

1. Show the ETL foundation in `DataPlatform/ETL/SSIS` and SQL Server `DW_DataJobs`.
2. Open the dashboard at `BI/PowerBI/Mission D'entreprise.pbix`.
3. Start the backend:

```bash
cd Backend/TalentBridgeAPI
python run_server.py serve
```

4. Start the frontend:

```bash
cd Frontend/TalentBridgeWeb
npm run dev
```

5. Open `http://localhost:5173` and sign in with one demo role.

```text
candidate@talentbridge.local / candidate123
recruiter@talentbridge.local / recruiter123
admin@talentbridge.local / admin123
```

6. Candidate flow: upload or select a PDF CV, review AI CV feedback, browse SQL-backed jobs, apply to a job, and check notifications.

7. Recruiter flow: manage jobs, search candidates, open application details, preview the PDF CV, inspect NER extraction, and accept/reject applications.

8. Admin flow: review AI monitoring, platform data, audit/retry tools, and use `Reset demo data` when a clean demo state is needed.

9. Explain the platform pipeline:

```text
CV PDF -> NLP extraction -> CV quality scoring -> semantic matching -> ranked SQL warehouse jobs -> application workflow
```

The role-based platform uses `/api/v1/*` routes and persists local demo state to `Artifacts/platform_store.json`.

## Technical AI Validation Flow

For direct endpoint validation without the UI, use:

```text
POST /extract
POST /match-jobs
POST /classify-cv-quality
POST /analyze-cv-full
```

`/analyze-cv-full` can save BI-ready analysis rows when `save_results=True` and the SQL CV analysis tables exist.

## Recommended Explanation

Talent Bridge starts from raw job data, cleans it through SSIS into SQL Server, visualizes the market in Power BI, applies ML objectives on cleaned warehouse data, and uses NLP/DocumentAI to analyze CVs and recommend jobs.
