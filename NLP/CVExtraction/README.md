# NLP CV Extraction Mini-Project

## What It Does

This module extracts structured information from candidate CV PDFs.

It detects and extracts:

```text
name
email
skills
companies
colleges
languages
LinkedIn / GitHub links
```

## Why It Exists

Recruitment workflows need structured candidate profiles. Raw PDFs are not directly useful for matching, filtering, or recommendations.

## Main Files

```text
NLP/CVExtraction/src/pdf_reader.py
NLP/CVExtraction/src/language_service.py
NLP/CVExtraction/training/clean_data.py
NLP/CVExtraction/training/prepare_data.py
NLP/CVExtraction/training/train_ner_model.py
Artifacts/models/nlp/model-best/
```

## How It Works

1. PDF text is extracted using PyMuPDF.
2. Language detection checks if translation is needed.
3. spaCy NER extracts candidate entities.
4. Regex post-processing improves contacts and links.
5. Skill fallback scanning improves robustness when NER misses technical terms.

## Inputs

```text
PDF CV files
Data/raw/CV_Ners.jsonl for training
```

## Outputs

```json
{
  "skills": ["python", "sql", "power bi"],
  "degrees": ["master"],
  "years_of_experience": ["2 years"],
  "email_addresses": ["candidate@example.com"]
}
```

## How To Validate

Use backend extraction route:

```text
POST /extract
```

Or run the global smoke test:

```bash
python Tests/smoke/test_demo_logic.py
```

## Teacher Validation Checklist

- PDF text extraction works.
- NER model loads.
- Skills and contacts are extracted.
- Extraction result is used by matching and CV quality.
- The module is independent from frontend code.
