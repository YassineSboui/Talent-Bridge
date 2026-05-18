# Document AI CV Document Classification Mini-Project

## What It Does

Classifies whether an uploaded document is really a CV before running extraction.

Output labels:

```text
cv
non_cv
uncertain
```

## Why It Exists

The extraction pipeline should not assume every uploaded PDF is a CV. This classifier protects downstream CV extraction, quality scoring, matching, and applications from invalid uploads.

## Data

The local training dataset is a balanced sample copied into:

```text
Data/document_classification/
```

Source classes:

```text
CV PDFs -> cv
Non-CV TIFF documents -> non_cv
```

The source CV domain labels are ignored for this binary task. They can be reused later for CV domain classification.

## Main Files

```text
DocumentAI/CVDocumentClassification/src/preprocessing.py
DocumentAI/CVDocumentClassification/src/model.py
DocumentAI/CVDocumentClassification/src/classifier.py
DocumentAI/CVDocumentClassification/training/prepare_dataset.py
DocumentAI/CVDocumentClassification/training/train_cv_document_classifier.py
```

## How It Works

1. Render the first page of a PDF or image document.
2. Convert it to a fixed-size grayscale page image.
3. Train a compact CNN on balanced CV and Non-CV samples.
4. Select a validation threshold by F1 score.
5. Use lightweight PDF text evidence as a runtime guardrail for real CV uploads with layouts unlike the training set.
6. Return `accepted`, `rejected`, or `manual_review` at runtime.

## Prepare Data

```bash
python DocumentAI/CVDocumentClassification/training/prepare_dataset.py --cv-samples 2484 --non-cv-samples 2484
```

## Train

```bash
python DocumentAI/CVDocumentClassification/training/train_cv_document_classifier.py --epochs 8 --batch-size 32 --force
```

## Artifacts

```text
Artifacts/models/document_ai/cv_document_classifier/model.pt
Artifacts/models/document_ai/cv_document_classifier/metadata.json
Artifacts/reports/document_ai/cv_document_classifier_metrics.json
```

## Runtime Usage

```python
from DocumentAI.CVDocumentClassification.src.classifier import classify_document

result = classify_document("candidate_cv.pdf")
```

## Platform Integration

The backend calls this classifier in:

```text
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
```

`POST /api/v1/cv/upload` now validates the file before extraction. Candidate CV enhancement and job applications both use this route, so a Non-CV upload is rejected before NER extraction or application creation.

## Teacher Validation Checklist

- Uses a real DL model, not only rules.
- Validates document type before CV extraction.
- Trains on balanced CV and Non-CV samples.
- Handles both PDF and image documents through the same rendered-page representation.
- Saves metrics and model artifacts.

## Current Limitation

The available positives are CV PDFs and the available negatives are TIFF document images. Rendering both to page images reduces file-format bias, but a stronger future dataset should add Non-CV PDFs and scanned CV images. The runtime text-evidence guardrail exists because real uploaded PDFs may have layouts that differ from the source CV corpus.
