# Skill Extraction And Normalization

## What This Module Does

`NLP/SkillExtraction/` standardizes skill names across CVs, jobs, matching, and skill-gap analysis.

Main file:

```text
NLP/SkillExtraction/src/normalization.py
```

The module provides:

```text
normalize_text
normalize_skill
normalize_skills
split_csv_values
```

## Why It Was Built

Skill matching fails when equivalent skills are written differently.

Examples:

```text
python3 -> python
powerbi -> power bi
mssql -> sql server
react.js -> react
nodejs -> node.js
sklearn -> scikit-learn
tf -> tensorflow
k8s -> kubernetes
ci cd -> ci/cd
```

A human knows these are equivalent. The platform needs to normalize them before comparing candidate skills with job skills.

## How It Works

Pipeline:

```text
raw text or skill label
-> lowercase
-> remove unsupported punctuation
-> collapse whitespace
-> map known aliases to canonical names
-> remove duplicates while preserving order
```

For SQL fields, `split_csv_values` splits comma-separated values created by SQL aggregation.

## Alias Dictionary

The central alias dictionary is:

```text
SKILL_ALIASES
```

It includes aliases for:

- programming languages
- BI tools
- databases
- cloud platforms
- DevOps tools
- ML/DL frameworks
- web frameworks
- project-management terms
- API/security terms

## Used By

```text
Recommendation/JobRecommendation/src/matching.py
Recommendation/JobRecommendation/src/semantic_similarity.py
Recommendation/JobRecommendation/src/score_components.py
MachineLearning/SharedML/src/gap_analyzer.py
MachineLearning/SharedML/src/skill_frequency.py
Backend/TalentBridgeAPI/app/normalization.py compatibility wrapper
```

## Why Centralization Matters

If each module had its own normalization rules, the same skill could be treated differently by matching, skill-gap analysis, and backend search.

Central normalization ensures:

- CV skills and job skills use the same vocabulary
- skill overlap scores are more reliable
- skill-gap output is clearer
- BI/ML skill frequency is more consistent
- future aliases can be added in one place

## Validation

```bash
python -m compileall -q NLP/SkillExtraction
python -m pytest Tests/smoke/test_skill_gap.py -v
```

## Future Improvements

- add more aliases from real user CVs
- add multilingual skill aliases
- add version-aware normalization where needed, such as `vue 3` versus `vue`
- add a small unit test table for all important aliases
