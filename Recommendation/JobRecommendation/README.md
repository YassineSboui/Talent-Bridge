# Recommendation Job Matching Mini-Project

## What It Does

Ranks jobs for candidates and candidates for recruiters.

It combines:

```text
skills score
NLP semantic similarity
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
3. Semantic NLP similarity is computed.
4. Structured scoring is computed.
5. Weak matches are capped to avoid false positives.
6. Explanation text is generated.
7. Results are ranked by final score.

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

## Validation

```bash
python Tests/smoke/test_demo_logic.py
python Tests/smoke/test_platform_workflows.py
```

## Teacher Validation Checklist

- Matching uses NLP semantic score.
- Matching is explainable.
- Matching uses SQL/platform jobs.
- Weak false-positive matches are capped.
- Candidate and recruiter workflows both use matching.
