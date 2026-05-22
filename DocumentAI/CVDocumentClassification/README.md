# CV Document Classification

## What This Module Does

This module classifies whether an uploaded document is really a CV before the platform runs CV extraction, CV quality scoring, matching, or application creation.

Internal model labels:

```text
cv
non_cv
uncertain
```

Runtime backend decisions:

```text
accepted
rejected
manual_review
```

The main runtime function is:

```python
from DocumentAI.CVDocumentClassification.src.classifier import classify_document

result = classify_document("candidate_cv.pdf")
```

## Why It Was Built

Without this classifier, any uploaded file could enter the CV pipeline. That would damage every later step:

- NER would try to extract skills and education from non-CV documents.
- CV quality scoring would produce meaningless scores.
- Job matching would use unreliable candidate profiles.
- Applications could be created with invalid files.
- Recruiters would receive bad or irrelevant documents.

This module is therefore the first AI gate in the upload workflow.

## How It Works

The module uses a compact CNN over a rendered document page.

Pipeline:

```text
PDF or image file
-> render first page/frame
-> convert to grayscale
-> resize with padding to fixed image size
-> normalize image to tensor
-> CNN predicts CV probability
-> PDF text evidence guardrail adjusts confidence
-> backend maps result to accepted/rejected/manual_review
```

The visual CNN is useful because CVs often have recognizable page-layout patterns: section blocks, contact header, experience area, education area, and skills lists.

The text-evidence guardrail checks for CV-like terms and contact signals such as:

```text
experience
education
skills
projects
certifications
languages
linkedin
github
email
phone
```

This guardrail reduces false rejection when a real CV layout differs from the visual training set.

## Main Files

```text
DocumentAI/CVDocumentClassification/src/preprocessing.py
DocumentAI/CVDocumentClassification/src/model.py
DocumentAI/CVDocumentClassification/src/classifier.py
DocumentAI/CVDocumentClassification/training/prepare_dataset.py
DocumentAI/CVDocumentClassification/training/train_cv_document_classifier.py
```

File responsibilities:

| File | Responsibility |
| --- | --- |
| `src/preprocessing.py` | Renders PDFs/images, resizes with padding, converts arrays to tensors. |
| `src/model.py` | Defines the compact CNN architecture. |
| `src/classifier.py` | Loads model artifacts and performs runtime classification. |
| `training/prepare_dataset.py` | Builds a balanced dataset and writes `manifest.csv`. |
| `training/train_cv_document_classifier.py` | Trains, validates, thresholds, and saves the CNN. |

## Model Architecture

The model class is:

```text
CvDocumentCnn
```

Architecture summary:

```text
Input: 1-channel grayscale page image
-> Conv2D + BatchNorm + ReLU + MaxPool
-> Conv2D + BatchNorm + ReLU + MaxPool
-> Conv2D + BatchNorm + ReLU + MaxPool
-> Conv2D + BatchNorm + ReLU
-> AdaptiveAvgPool2D
-> Flatten
-> Dropout
-> Linear + ReLU
-> Dropout
-> Linear output logit
-> sigmoid probability of CV
```

Why this architecture:

- compact enough to train locally
- strong enough to learn document layout
- avoids a large heavy vision model for a binary task
- works for both PDFs and images after rendering

## Dataset

Prepared dataset location:

```text
Data/document_classification/
```

Dataset composition used:

```text
2487 CV samples
2484 Non-CV samples
about 348.61 MB
```

Source classes:

```text
CV PDFs -> cv
Non-CV TIFF documents -> non_cv
```

The original CV domain labels are ignored for this binary problem. They could be reused later for a separate CV-domain classification task.

## Prepare Dataset

```bash
python DocumentAI/CVDocumentClassification/training/prepare_dataset.py --cv-samples 2484 --non-cv-samples 2484 --force
```

What this does:

- collects supported CV files
- collects supported Non-CV files
- samples categories proportionally
- copies files under `Data/document_classification/raw/`
- writes `Data/document_classification/manifest.csv`

## Train The Model

```bash
python DocumentAI/CVDocumentClassification/training/train_cv_document_classifier.py --epochs 8 --batch-size 32 --force
```

Training behavior:

- reads `manifest.csv`
- creates stratified train/validation/test splits
- renders documents into cached `.npy` page arrays
- trains `CvDocumentCnn`
- selects probability threshold using validation F1
- evaluates on test set
- saves model, metadata, and metrics

## Artifacts

```text
Artifacts/models/document_ai/cv_document_classifier/model.pt
Artifacts/models/document_ai/cv_document_classifier/metadata.json
Artifacts/reports/document_ai/cv_document_classifier_metrics.json
Artifacts/cache/cv_document_classifier/
```

`metadata.json` stores model configuration such as:

```text
image size
dropout
accept threshold
reject threshold
text evidence thresholds
model name
```

## Metrics

Reported validation/test metrics:

```text
Accuracy: 0.9973
Precision CV: 0.9947
Recall CV: 1.0000
F1 CV: 0.9973
```

Important interpretation:

```text
The numbers show the model performs very well on the prepared validation split, but the source data has format bias because positives are mostly PDF CVs and negatives are mostly TIFF documents.
```

## Runtime Integration

Backend route:

```text
POST /api/v1/cv/upload
```

Backend file:

```text
Backend/TalentBridgeAPI/app/platform/routers/cv_routes.py
```

Runtime behavior:

```text
Non-PDF file -> rejected before classification
Classifier rejected -> upload rejected
Classifier manual_review -> upload rejected with clearer-CV message
Classifier accepted -> extraction and quality scoring continue
```

This means candidate CV enhancement and job application both require a real PDF CV.

## Validation

```bash
python Tests/smoke/test_cv_document_classifier.py
python -m compileall -q DocumentAI/CVDocumentClassification
```

## Limitations And Future Improvements

Current limitation:

```text
CV positives are mostly PDFs.
Non-CV negatives are mostly TIFF images.
```

Future improvements:

- add Non-CV PDFs
- add scanned CV images
- add invoices, contracts, certificates, reports, and letters as negatives
- test on real user-uploaded files
- add manual review workflow instead of only rejecting uncertain files
