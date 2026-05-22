# Job Recommendation And Semantic Matching

## What This Module Does

`Recommendation/JobRecommendation/` ranks jobs for candidates and can support recruiter-side candidate matching.

It combines NLP semantic similarity with structured recruitment signals:

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

The output is an explainable ranked list, not only a black-box score.

## Why It Was Built

Recruitment matching cannot rely only on keywords.

Candidates need to know:

- which jobs fit their profile
- why a job is recommended
- which skills are missing
- how ready they are for a job

Recruiters need to know:

- why a candidate is relevant
- which skills match
- where the profile is weak
- whether role, experience, and location are aligned

This module provides the matching and explanation layer between CV extraction and platform workflows.

## Main Files

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/score_components.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/explainer.py
Recommendation/JobRecommendation/src/repository.py
Recommendation/JobRecommendation/src/ranking_service.py
Recommendation/JobRecommendation/src/bert_comparison.py
Recommendation/JobRecommendation/src/test_bert_integration.py
```

File responsibilities:

| File | Responsibility |
| --- | --- |
| `matching.py` | Builds candidate profile, fetches SQL jobs, scores jobs, ranks jobs, saves analysis results. |
| `score_components.py` | Computes skills, role, experience, education, location, opportunity scores, and match caps. |
| `semantic_similarity.py` | Builds semantic text and computes BERT or TF-IDF similarity. |
| `explainer.py` | Converts score components into human-readable explanations. |
| `repository.py` | Re-exports SQL persistence functions. |
| `ranking_service.py` | Re-exports ranking and scoring services. |
| `bert_comparison.py` | Demonstrates BERT versus TF-IDF behavior. |
| `test_bert_integration.py` | Validates that semantic matching works. |

## End-To-End Matching Flow

```text
CV extraction result
-> build CandidateProfile
-> load jobs from SQL warehouse or platform store
-> normalize candidate and job skills
-> build candidate semantic text
-> build job semantic text
-> compute BERT semantic similarity if available
-> fallback to TF-IDF similarity if unavailable
-> compute structured component scores
-> apply weak-match caps
-> generate explanation
-> sort by final score
-> return top matches
```

## Candidate Profile

The matching engine creates a normalized `CandidateProfile` from extraction output.

Fields include:

```text
name
email
preferred_country
remote_preference
seniority_level
skills
languages
linkedin
semantic_text
```

Years of experience are inferred from NER text like `2 years` or `5 years`. Seniority is then mapped to:

```text
intern
junior
mid
senior
lead
```

## Job Source

The recommendation engine can load cleaned jobs from SQL Server view:

```text
DW_DataJobs.dbo.vw_job_matching
```

The SQL connection defaults to:

```text
Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DW_DataJobs;Trusted_Connection=yes;TrustServerCertificate=yes;
```

Override with:

```text
DW_DATAJOBS_CONNECTION_STRING
```

## Final Score Formula

```text
35% skills
25% NLP semantic similarity
15% role
10% experience
5% education
5% location
5% opportunity
```

Why this formula:

- skills are the strongest recruitment signal
- semantic similarity captures meaning beyond exact keywords
- role fit prevents unrelated recommendations
- experience fit avoids seniority mismatch
- education/location/opportunity provide secondary signals

## Score Components

### Skills Score

Compares normalized candidate skills and job skills.

It uses:

- direct skill overlap
- role-core skill coverage
- low-signal skill protection
- caps for very small job skill lists

### Semantic Score

Uses BERT/SentenceTransformer when available.

Fallback is TF-IDF + cosine similarity.

### Role Score

Compares target role against job category and job title.

It also recognizes related roles such as:

```text
data analyst <-> business analyst
data scientist <-> machine learning engineer
data engineer <-> cloud engineer
```

### Experience Score

Infers job seniority from title/category and compares it with candidate seniority.

### Education Score

Uses extracted degrees and job no-degree flag.

### Location Score

Compares preferred country and remote preference with job location and remote signal.

### Opportunity Score

Rewards positive opportunity signals:

```text
salary available
remote work
no degree required
health insurance
```

## Match Caps

Match caps prevent weak false positives.

Examples:

- if role matches but skills are weak, final score is capped
- if there are no matched job skills, final score is capped
- if only one weak skill matches, final score is capped
- if role is not aligned, final score is capped

This makes the ranking more realistic and prevents semantic similarity alone from over-scoring a bad match.

## BERT Semantic Matching

Primary implementation:

```text
Recommendation/JobRecommendation/src/semantic_similarity.py
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Dependency pin:

```text
sentence-transformers>=2.6.1,<3.0.0
```

Environment override:

```powershell
$env:TALENTBRIDGE_SENTENCE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

How BERT scoring works:

```text
candidate semantic text + job semantic texts
-> SentenceTransformer encodes all texts
-> normalized embeddings
-> dot product cosine similarity
-> score scaled to 0-100
```

The model is lazy-loaded once and cached in memory.

## TF-IDF Fallback

If `sentence-transformers` is not installed or the model cannot load, the module falls back to:

```text
TfidfVectorizer(ngram_range=(1, 2), max_features=12000)
cosine_similarity
```

This keeps the application usable without internet/model download access.

## Explainability

Explanations are generated in:

```text
Recommendation/JobRecommendation/src/explainer.py
```

Example explanation items:

```text
Matched 5 skills: python, sql, power bi, excel, statistics
Missing 3 listed job skills
High NLP semantic similarity between CV profile and job text
Exact role category match
Experience level is compatible
Location or remote preference matches
```

## Saved Analysis Support

The module can save technical analysis results into SQL `cv.*` tables when those tables exist.

Main functions:

```text
save_analysis_results
list_saved_analyses
get_saved_analysis
```

Related SQL views:

```text
cv.vw_analysis_summary
cv.vw_match_detail
cv.vw_candidate_skill
```

This is used by technical endpoints such as:

```text
POST /analyze-cv-full
GET /analyses
GET /analyses/{analysis_id}
```

## Skill-Gap Analysis

Candidate-facing skill-gap endpoints are implemented in the backend, with core logic in MachineLearning:

```text
Backend/TalentBridgeAPI/app/platform/routers/skill_gap_routes.py
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
```

Endpoints:

```text
GET /api/v1/skill-gap/jobs/{job_id}
GET /api/v1/skill-gap/top-missing
```

Skill-gap output includes:

- matched skills
- missing skills
- priority levels
- market demand score
- readiness level
- quick wins
- core gaps
- learning resources

## Backend And Frontend Integration

Backend matching routes:

```text
Backend/TalentBridgeAPI/app/platform/routers/matching_routes.py
Backend/TalentBridgeAPI/app/platform/routers/skill_gap_routes.py
```

Frontend API module:

```text
Frontend/TalentBridgeWeb/src/modules/matching/matching.api.js
```

Candidate behavior:

- sees job recommendations and skill-gap guidance
- does not see exact internal match score

Recruiter/admin behavior:

- can see matching scores and explanations for decision support

## Validation

```bash
python Recommendation/JobRecommendation/src/test_bert_integration.py
python -m pytest Tests/smoke/test_skill_gap.py -v
python Tests/smoke/test_demo_logic.py
python Tests/smoke/test_platform_workflows.py
python -m compileall -q Recommendation MachineLearning
```

Expected BERT integration behavior:

```text
Model loads when dependencies/model are available.
ML job scores higher than unrelated accounting job.
Scores stay within 0-100.
Empty inputs return safe zero/empty results.
```

## Limitations And Future Improvements

- BERT model availability depends on compatible dependencies and model download/cache access.
- TF-IDF fallback is less semantically rich than BERT but keeps local execution stable.
- Matching weights are explainable heuristics and should be calibrated with real recruiter/candidate feedback.
- Candidate skill-gap quality depends on accurate CV extraction and normalized job skills.
- Future work could learn ranking weights from real application outcomes.

## Teacher Explanation

This module uses NLP semantic matching and explainable ranking. BERT/SentenceTransformer compares candidate and job meaning through embeddings. TF-IDF provides a deterministic fallback. The final match score combines semantic similarity with structured recruitment signals, making the result useful and explainable instead of purely black-box.
