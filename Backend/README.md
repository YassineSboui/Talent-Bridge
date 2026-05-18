# Backend

Main API layer for the Talent Bridge recruitment platform.

The backend orchestrates domain modules and exposes the role-based `/api/v1` platform APIs. Domain AI logic remains in `NLP/`, `DocumentAI/`, `Recommendation/`, and `MachineLearning/` where possible.

Current API project:

- `TalentBridgeAPI`

The project still includes compatibility wrappers and direct technical AI endpoints in `TalentBridgeAPI/app/main.py` for validation:

```text
/extract
/match-jobs
/classify-cv-quality
/analyze-cv-full
/analyses
/analyses/{analysis_id}
```

The role-based platform implementation lives in:

```text
Backend/TalentBridgeAPI/app/platform/
```
