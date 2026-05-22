# CV Extraction

## What This Module Does

`NLP/CVExtraction/` extracts structured information from candidate CV PDFs.

It detects and extracts:

```text
name
email addresses
phone numbers
skills
companies worked at
college or school names
languages
LinkedIn link
GitHub link
raw text
```

The output is used by:

- candidate CV enhancement
- CV quality scoring
- job recommendation
- recruiter application review
- skill-gap analysis
- saved analysis records

## Why It Was Built

A CV PDF is not structured data. The platform needs structured candidate information before it can rank jobs, explain matches, detect missing skills, or help recruiters review applications.

For example, matching needs a clean list of candidate skills. Recruiters need to see extracted contact information and NER results. CV quality scoring needs text and section evidence.

This module converts a PDF into useful candidate profile data.

## Runtime Flow

```text
PDF bytes
-> extract readable text with PyMuPDF
-> clean PDF extraction artifacts
-> detect language
-> translate text to English when needed
-> run spaCy NER model
-> apply regex post-processing for contacts and links
-> apply skill fallback scanning
-> return structured extraction result
```

## Main Files

```text
NLP/CVExtraction/src/pdf_reader.py
NLP/CVExtraction/src/language_service.py
NLP/CVExtraction/training/clean_data.py
NLP/CVExtraction/training/prepare_data.py
NLP/CVExtraction/training/train_ner_model.py
Artifacts/models/nlp/model-best/
```

File responsibilities:

| File | Responsibility |
| --- | --- |
| `src/pdf_reader.py` | Extracts and cleans text from PDF bytes using PyMuPDF. |
| `src/language_service.py` | Detects language, chunks long text, translates, and maps entity spans when possible. |
| `training/clean_data.py` | Cleans Prodigy JSONL NER records, removes garbled zones, remaps spans, and balances rare labels. |
| `training/prepare_data.py` | Converts cleaned JSONL annotations into spaCy `.spacy` train/dev files. |
| `training/train_ner_model.py` | Generates spaCy config, trains the NER model, and evaluates it. |

## PDF Text Extraction

Implementation:

```text
NLP/CVExtraction/src/pdf_reader.py
```

How it works:

```text
open PDF with PyMuPDF
-> extract page text
-> if page text is too short, try block extraction
-> join pages
-> fix ligatures and punctuation artifacts
-> remove control characters
-> return cleaned text
```

Why PyMuPDF:

- works locally
- reads text-based PDFs efficiently
- provides page and block extraction options
- does not require an external OCR service

## Language Detection And Translation

Implementation:

```text
NLP/CVExtraction/src/language_service.py
```

Why it exists:

```text
The NER model is trained mainly for English-style entity extraction. If a CV is not English, translation can make extraction more consistent.
```

Main behavior:

- detect language using `langdetect`
- default to English if detection fails
- split long text into chunks before translation
- translate using `deep_translator.GoogleTranslator`
- translate short entities when needed
- try to map translated entities back to original text spans

## NER Model

Technology:

```text
spaCy NER
```

Training data:

```text
Data/raw/CV_Ners.jsonl
```

Entity labels include:

```text
Skills
Companies_Worked_At
College_Name
Years_of_Experience
Degree
Languages
Name
Email_Address
```

Training pipeline:

```text
Data/raw/CV_Ners.jsonl
-> clean_data.py
-> cleaned.jsonl
-> prepare_data.py
-> train.spacy / dev.spacy
-> train_ner_model.py
-> Artifacts/models/nlp/model-best/
```

## Training Step 1: Clean NER Data

```bash
python NLP/CVExtraction/training/clean_data.py
```

What it does:

- detects garbled zones from bad PDF extraction
- removes duplicated CV content
- remaps entity spans after text changes
- drops records with too few usable spans
- oversamples rare entity labels lightly
- writes cleaned JSONL data

## Training Step 2: Prepare spaCy Data

```bash
python NLP/CVExtraction/training/prepare_data.py
```

What it does:

- creates spaCy `Doc` objects
- aligns character spans to token boundaries
- drops misaligned spans safely
- performs stratified train/dev split
- writes `train.spacy` and `dev.spacy`

## Training Step 3: Train NER Model

```bash
python NLP/CVExtraction/training/train_ner_model.py
```

What it does:

- detects GPU availability
- generates spaCy NER config
- patches paths and hyperparameters
- downloads `en_core_web_lg` if needed
- trains model through spaCy CLI
- evaluates on dev set

Optional environment variables:

```text
CV_NER_MAX_STEPS
CV_NER_EVAL_FREQUENCY
```

## Output Example

```json
{
  "skills": ["python", "sql", "power bi"],
  "degrees": ["master"],
  "years_of_experience": ["2 years"],
  "email_addresses": ["candidate@example.com"],
  "languages": ["english", "french"]
}
```

## Backend Integration

Main platform route using extraction:

```text
POST /api/v1/cv/upload
```

Technical validation routes:

```text
POST /extract
POST /analyze-cv-full
```

`/api/v1/cv/upload` is the production-style route used by the Vue frontend. It validates the document first, then runs extraction and quality scoring.

## Validation

```bash
python Tests/smoke/test_demo_logic.py
python -m compileall -q NLP/CVExtraction
```

## Limitations And Future Improvements

- PyMuPDF extracts text from text-based PDFs; scanned image-only CVs may need OCR.
- Translation depends on external translator availability.
- NER performance depends on the quality and diversity of annotated CV data.
- Regex and skill fallback improve robustness but do not replace high-quality NER labels.
- Future work should add more multilingual annotations and scanned-CV OCR support.
