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

5. Upload a sample CV from `Data/samples/cv/` or `Backend/TalentBridgeAPI/test_cv.pdf`.

6. Explain the pipeline:

```text
CV PDF -> NLP extraction -> CV quality scoring -> NLP semantic matching -> ranked SQL warehouse jobs -> saved BI-ready analysis
```

## Recommended Explanation

Talent Bridge starts from raw job data, cleans it through SSIS into SQL Server, visualizes the market in Power BI, applies ML objectives on cleaned warehouse data, and uses NLP/DocumentAI to analyze CVs and recommend jobs.
