# DocumentAI

## Purpose

`DocumentAI/` contains the deep-learning and document-analysis parts of Talent Bridge. These modules work on uploaded documents, especially candidate CV files.

The goal is to answer two questions before the recruitment workflow continues:

```text
1. Is the uploaded document really a CV?
2. If it is a CV, how good is its quality?
```

This separation is important because the platform must not extract entities, score quality, match jobs, or create applications from invalid documents.

## Modules

| Module | Type | Main question | Output |
| --- | --- | --- | --- |
| `CVDocumentClassification/` | Deep Learning CNN | Is this file a real CV? | `accepted`, `rejected`, or `manual_review` |
| `CVQualityScoring/` | Hybrid DL + rules | How good is this CV? | `Excellent`, `Good`, `Average`, `Weak`, `Poor`, plus `Pro / Non Pro` |

## Global Document Flow

```text
PDF upload
-> CVDocumentClassification checks if it is a real CV
-> invalid files are rejected before extraction
-> NLP/CVExtraction extracts text and entities
-> CVQualityScoring grades the CV and returns suggestions
-> Backend stores document_check, extraction, quality, and preview data
-> Candidate/recruiter workflows use the result
```

## Why This Domain Exists

Recruitment platforms receive unstructured documents. A PDF can be a CV, an invoice, a certificate, a contract, or an unrelated file. If the application assumes every file is a CV, all later AI results become unreliable.

The DocumentAI domain protects downstream modules:

- CV extraction is only executed on valid CV files.
- CV quality scoring is only meaningful after document validation.
- Job matching uses cleaner candidate data.
- Recruiters preview and evaluate real CVs, not random files.
- Candidate applications require a validated PDF CV.

## Backend Integration

The main backend integration point is:

```text
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
```

The main platform route is:

```text
POST /api/v1/cv/upload
```

That route performs:

```text
file type check
-> CV/Non-CV classification
-> PDF text extraction
-> NER extraction
-> CV quality scoring
-> store CV metadata and preview
```

## Important Artifacts

```text
Artifacts/models/document_ai/cv_document_classifier/model.pt
Artifacts/models/document_ai/cv_document_classifier/metadata.json
Artifacts/reports/document_ai/cv_document_classifier_metrics.json
Artifacts/models/document_ai/cv_quality_dl/model.pt
Artifacts/models/document_ai/cv_quality_dl/vectorizer.pkl
Artifacts/models/document_ai/cv_quality_dl/scaler.pkl
Artifacts/models/document_ai/cv_quality_dl/metadata.json
Artifacts/reports/document_ai/cv_quality_dl_metrics.json
```

## Validation

```bash
python Tests/smoke/test_cv_document_classifier.py
python Tests/smoke/test_demo_logic.py
python -m compileall -q DocumentAI
```

## Limitations To Explain Honestly

- CV document classification metrics are strong, but the dataset has source-format bias: CV positives are mostly PDFs and Non-CV negatives are mostly TIFFs.
- CV quality DL uses rubric pseudo-labels and controlled synthetic variants, not manually reviewed human labels.
- Both modules are useful for platform behavior and demo validation, but production-level claims require more diverse real-world labeled data.
