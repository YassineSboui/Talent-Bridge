# Data

Raw and sample data.

- `raw`: original source files such as `data_jobs.csv` and `CV_Ners.jsonl`.
- `samples/cv`: sample CV PDFs.
- `document_classification`: balanced local sample for CV-vs-Non-CV document classification.

Production logic should not consume raw data directly except for ETL or fallback development runs.
