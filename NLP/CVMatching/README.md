# NLP CV Matching Mini-Project

## What It Does

This module is responsible for semantic similarity between a CV profile and job offers.

The implementation currently lives in:

```text
Recommendation/JobRecommendation/src/semantic_similarity.py
```

It is documented here because it satisfies the NLP objective:

```text
Matching CV ↔ Job selon score -> embeddings
```

## Why It Exists

Exact skill overlap is not enough. NLP semantic similarity can detect that two profiles are related even when wording differs.

Example:

```text
CV: created dashboards with SQL and Power BI
Job: business intelligence reporting and KPI automation
```

## How It Works

Default:

```text
TF-IDF vector embeddings + cosine similarity
```

Optional:

```text
Sentence-BERT / sentence-transformers
```

Enable optional Sentence-BERT:

```powershell
$env:TALENTBRIDGE_EMBEDDING_BACKEND="sentence-transformers"
$env:TALENTBRIDGE_SENTENCE_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

If the model/package is unavailable, the system falls back to TF-IDF.

## Output

Each match has:

```json
{
  "score_breakdown": {
    "semantic": 78.31,
    "skills": 100.0,
    "role": 100.0
  }
}
```

## Teacher Validation Checklist

- Matching includes an NLP semantic score.
- Semantic score is part of final ranking.
- TF-IDF fallback is deterministic and local.
- Optional Sentence-BERT path exists.
