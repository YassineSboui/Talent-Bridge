# NLP CV Matching

## What This Module Represents

This folder documents the NLP objective for CV-to-job semantic matching.

The current implementation lives in:

```text
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/matching.py
```

It remains documented here because the project objective is NLP-based CV-job matching:

```text
Matching CV <-> Job using semantic score and embeddings
```

## Why Semantic Matching Is Needed

Exact skill overlap is not enough.

Example:

```text
CV: created dashboards with SQL and Power BI
Job: business intelligence reporting and KPI automation
```

The exact words are not identical, but the meaning is related. Semantic matching helps detect that relationship.

## Current Implementation

Primary semantic backend:

```text
Sentence-BERT / sentence-transformers
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Fallback backend:

```text
TF-IDF n-gram vectorization + cosine similarity
```

The fallback exists so the application still works if the transformer package or model is unavailable.

## How It Works

```text
candidate extraction/profile
-> weighted candidate semantic text
-> job row
-> weighted job semantic text
-> normalize text
-> try SentenceTransformer embeddings
-> compute cosine similarity
-> if BERT unavailable, use TF-IDF cosine similarity
-> scale score to 0-100
-> combine with skill, role, experience, education, location, opportunity scores
```

## Semantic Text Construction

Candidate semantic text uses:

- target role
- skills
- degrees
- companies
- languages
- years of experience
- raw CV text excerpt

Job semantic text uses:

- job title
- category
- company
- country/city
- skills
- skill categories
- schedule
- remote/on-site signal
- salary availability
- degree requirement signal

Important fields are repeated in the semantic text to give them more weight.

## Configuration

Environment override:

```powershell
$env:TALENTBRIDGE_SENTENCE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

Dependency pin:

```text
sentence-transformers>=2.6.1,<3.0.0
```

The `2.x` pin is intentional for compatibility with the tested backend `transformers` stack.

## Final Recommendation Score

Semantic similarity is one part of the final score:

```text
35% skills
25% NLP semantic similarity
15% role
10% experience
5% education
5% location
5% opportunity
```

## Output Example

```json
{
  "score_breakdown": {
    "semantic": 78.31,
    "skills": 100.0,
    "role": 100.0,
    "experience": 90.0
  },
  "explanation": [
    "Matched 5 skills: python, sql, power bi, excel, statistics",
    "High NLP semantic similarity between CV profile and job text"
  ]
}
```

## Validation

```bash
python Recommendation/JobRecommendation/src/test_bert_integration.py
python Tests/smoke/test_demo_logic.py
```

## Teacher Explanation

This is NLP because it compares the meaning of candidate text and job text. It uses Sentence-BERT embeddings when available and TF-IDF cosine similarity as a deterministic fallback. The semantic score is explainable and is not the only decision factor.
