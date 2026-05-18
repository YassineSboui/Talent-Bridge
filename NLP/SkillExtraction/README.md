# Skill Extraction And Normalization Mini-Project

## What It Does

This module standardizes skill names across CVs and jobs.

Examples:

```text
python3 -> python
powerbi -> power bi
mssql -> sql server
react.js -> react
nodejs -> node.js
```

## Why It Exists

Matching fails if equivalent skills are written differently. Normalization improves skill overlap, semantic matching, reports, and recommendations.

## Main File

```text
NLP/SkillExtraction/src/normalization.py
```

## How It Works

1. Text is lowercased and cleaned.
2. Known aliases are mapped to canonical skill names.
3. Duplicates are removed while preserving order.

## Used By

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/score_components.py
Backend/TalentBridgeAPI/app/normalization.py compatibility wrapper
```

## Teacher Validation Checklist

- Skill aliases are centralized.
- CV skills and job skills use the same canonical form.
- Matching benefits from normalization.
- No duplicated normalization logic across modules.
