# NLP

## Purpose

`NLP/` contains the natural language processing parts of Talent Bridge. These modules transform unstructured CV and job text into structured information that can be used by the backend, DocumentAI, recommendation, and skill-gap analysis.

The domain answers questions such as:

```text
What text is inside the PDF CV?
What language is the CV written in?
What skills, education, companies, names, and contacts are mentioned?
How can different skill spellings be normalized?
How can CV text and job text be compared semantically?
```

## Modules

| Module | Purpose |
| --- | --- |
| `CVExtraction/` | Extracts text and entities from uploaded CV PDFs. |
| `SkillExtraction/` | Normalizes technical skill names and aliases. |
| `CVMatching/` | Documents the NLP semantic matching objective. Final implementation lives in `Recommendation/JobRecommendation/`. |

## Global NLP Flow

```text
PDF CV
-> extract text with PyMuPDF
-> detect language
-> translate if needed
-> run spaCy NER
-> apply regex post-processing
-> normalize skills
-> provide structured extraction to backend
-> matching, CV quality, applications, and recruiter review use the result
```

## Why NLP Exists In This Project

CVs and job descriptions are text-heavy and unstructured. The platform cannot match a candidate to a job using raw PDF files directly.

NLP creates structured signals:

- skills for matching and skill-gap analysis
- contact information for recruiter review
- education and experience for candidate profile construction
- semantic text for BERT/TF-IDF matching
- normalized terms for stable comparisons

## Separation Rule

NLP modules expose plain Python functions and services. They should not import FastAPI route code.

Allowed dependency direction:

```text
Backend -> NLP
Recommendation -> NLP normalization helpers
NLP -> no frontend/backend route imports
```

## Validation

```bash
python -m compileall -q NLP
python Tests/smoke/test_demo_logic.py
```

For semantic matching validation:

```bash
python Recommendation/JobRecommendation/src/test_bert_integration.py
```
