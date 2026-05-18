# NLP

Natural Language Processing domain.

Contains CV extraction and skill extraction utilities.

Semantic CV-job matching is documented in `NLP/CVMatching/`, but the current implementation lives in `Recommendation/JobRecommendation/src/` so final ranking and explanations stay in one recommendation domain.

NLP modules expose plain Python functions/services. They should not import FastAPI route code.
