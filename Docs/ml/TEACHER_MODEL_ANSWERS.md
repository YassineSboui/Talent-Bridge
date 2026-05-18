# Teacher Model Answers

This file gives short answers for the teacher about what technique/model is used in each AI part of Talent Bridge.

## Classical Machine Learning Models

| Objective | What it predicts | Technique used | Input data | Why this choice |
| --- | --- | --- | --- | --- |
| Salary regression | Estimated salary for a job posting | Scikit-learn regression pipeline with text/vector features and structured job features | Cleaned SQL warehouse view `dbo.vw_ml_jobs` | Regression is appropriate because salary is a continuous numeric target. |
| Remote job classification | Whether a job is remote/hybrid/on-site | Scikit-learn classification pipeline | Cleaned SQL warehouse view `dbo.vw_ml_jobs` | Classification is appropriate because the target is categorical. |
| Full-time classification | Whether a job is full-time or not | Scikit-learn classification pipeline | Cleaned SQL warehouse view `dbo.vw_ml_jobs` | Classification is appropriate because the target is a label. |
| Job segmentation | Groups similar jobs into clusters | K-Means clustering | Cleaned SQL warehouse view `dbo.vw_ml_jobs` | Clustering is appropriate because it discovers groups without a manual target label. |

The ML models are trained from the cleaned data warehouse, not directly from the raw CSV. The raw CSV is only a fallback for development.

## Deep Learning Models

| Module | What it does | Model/technique used | Training data | Important note |
| --- | --- | --- | --- | --- |
| CV document classification | Checks if an uploaded file is really a CV before accepting it | Small CNN image classifier over the rendered first page of the document | CV PDFs and non-CV document images copied under `Data/document_classification/` | A text-evidence guardrail is also used at runtime to reduce false accepts. |
| CV quality scoring | Gives a CV quality score and grade: `Excellent`, `Good`, `Average`, `Weak`, `Poor` | PyTorch MLP using TF-IDF text features plus structural CV features | Real CV text with rubric pseudo-labels and controlled synthetic variants | The model was not trained on human-reviewed labels; labels are rubric-based pseudo-labels. |

The CV quality system is hybrid: rules are used for hard checks and explainable suggestions, while the DL model helps estimate the final quality score.

## NLP Models And Techniques

| NLP part | What it does | Model/technique used | Fine-tuning/training answer |
| --- | --- | --- | --- |
| CV text extraction | Reads text from uploaded PDF CVs | PDF text extraction utilities | No ML fine-tuning; this is document text extraction. |
| Language detection/translation support | Detects language and can normalize text before extraction | Language service utilities with fallback behavior | No project-specific fine-tuning. |
| Named Entity Recognition on CVs | Extracts entities such as skills, education, experience, names, emails, and phone numbers | spaCy NER pipeline plus regex post-processing | The NER model is trained/fine-tuned on CV annotation data stored in `Data/raw/CV_Ners.jsonl`. |
| Skill extraction | Detects and normalizes technical skills | Rule/dictionary normalization plus extracted NER entities | No deep model fine-tuning; it uses normalization rules and known skill terms. |
| CV-job semantic matching | Compares candidate profile/CV text with job descriptions | TF-IDF cosine similarity by default; optional Sentence-BERT if installed/configured | Default mode is not fine-tuned; Sentence-BERT is optional pre-trained embedding usage. |
| Job recommendation ranking | Produces final ranked recommendations | Weighted scoring combining semantic similarity, skill fit, role fit, experience, education, location, and opportunity signals | It is an explainable ranking system, not a single black-box deep model. |

## Short Oral Defense Answer

I used three main AI families in the project. For classical ML, I trained salary regression, remote classification, full-time classification, and K-Means job segmentation from the cleaned SQL data warehouse. For deep learning, I used a CNN to classify whether a document is a real CV and a PyTorch MLP to score CV quality from text and structural features. For NLP, I used PDF text extraction, spaCy NER fine-tuned on CV annotations, regex/rule post-processing, skill normalization, and TF-IDF semantic similarity for CV-job matching, with optional Sentence-BERT embeddings if available.

The important limitation is that the CV quality DL model uses rubric pseudo-labels, not manually reviewed human labels, so it is useful for demonstration and guidance but should be improved with real labeled CV quality data for production.
