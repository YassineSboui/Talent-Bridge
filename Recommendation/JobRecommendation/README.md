# Recommendation Job Matching Mini-Project

## What It Does

Ranks jobs for candidates and candidates for recruiters.

It combines:

```text
skills score
BERT/SentenceTransformer semantic similarity
TF-IDF fallback similarity
role score
experience score
education score
location score
opportunity score
```

## Why It Exists

Recruitment requires explainable recommendations, not only black-box similarity. Candidates need to know why a job matches. Recruiters need to understand why a candidate is recommended.

## Main Files

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/score_components.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/explainer.py
Recommendation/JobRecommendation/src/repository.py
Recommendation/JobRecommendation/src/ranking_service.py
```

## How It Works

1. Candidate profile is built from CV extraction or platform profile.
2. Job rows are converted into matching-ready objects.
3. Semantic NLP similarity is computed with `sentence-transformers/all-MiniLM-L6-v2` by default.
4. Structured scoring is computed.
5. Weak matches are capped to avoid false positives.
6. Explanation text is generated.
7. Results are ranked by final score.

If `sentence-transformers` or the configured model is unavailable, `semantic_similarity.py` falls back to TF-IDF similarity so the platform remains usable.

## Final Score

```text
35% skills
25% NLP semantic similarity
15% role
10% experience
5% education
5% location
5% opportunity
```

## BERT Semantic Matching

Primary implementation:

```text
Recommendation/JobRecommendation/src/semantic_similarity.py
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Environment override:

```powershell
$env:TALENTBRIDGE_SENTENCE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

Dependency pin:

```text
sentence-transformers>=2.6.1,<3.0.0
```

The `2.x` pin is intentional for compatibility with the current `transformers` stack used by the backend and spaCy transformer tooling.

## Skill Gap Analysis

Candidate-facing skill-gap analysis is exposed by the backend at:

```text
GET /api/v1/skill-gap/jobs/{job_id}
GET /api/v1/skill-gap/top-missing
```

Core engine:

```text
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
```

It returns matched skills, missing skills, priority levels, market demand score, readiness level, quick wins, core gaps, and curated learning resources.

## Validation

```bash
python Recommendation/JobRecommendation/src/test_bert_integration.py
python -m pytest Tests/smoke/test_skill_gap.py -v
python Tests/smoke/test_demo_logic.py
python Tests/smoke/test_platform_workflows.py
```

## Teacher Validation Checklist

- Matching uses NLP semantic score.
- BERT semantic matching loads when dependencies are installed.
- TF-IDF fallback keeps matching available if the transformer is unavailable.
- Candidate skill-gap endpoints explain missing skills and learning priorities.
- Matching is explainable.
- Matching uses SQL/platform jobs.
- Weak false-positive matches are capped.
- Candidate and recruiter workflows both use matching.
