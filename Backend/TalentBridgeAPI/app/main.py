"""
Talent Bridge recruitment platform API.

POST /extract  — accepts a PDF file, returns structured entity extraction.
GET  /health   — health check.

Pipeline:
  1. Extract text from PDF
  2. Detect language
  3. If non-English → translate to English
  4. Run NER on English text
  5. Clean / post-process entities
  6. Map entities back to original language where possible
  7. Return structured JSON
"""

import re
import sys
from pathlib import Path
from typing import Any, Optional

import spacy
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pydantic import BaseModel


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "Recommendation").exists() and (parent / "NLP").exists() and (parent / "Artifacts").exists():
            return parent
    return current.parents[4]


REPO_ROOT = _find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Recommendation.JobRecommendation.src.matching import build_candidate_profile, fetch_jobs_from_sql, rank_jobs, save_analysis_results
from Recommendation.JobRecommendation.src.matching import get_saved_analysis, list_saved_analyses
from NLP.CVExtraction.src.pdf_reader import extract_text_from_pdf
from DocumentAI.CVQualityScoring.src.quality import classify_cv_quality
from NLP.CVExtraction.src.language_service import (
    detect_language,
    translate_text,
    translate_entity,
    find_original_span,
)
from .platform.api import api_v1_router
from .platform.store import seed_platform


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
MODEL_DIR = REPO_ROOT / "Artifacts" / "models" / "nlp" / "model-best"

nlp = None


def get_model():
    global nlp
    if nlp is None:
        if not MODEL_DIR.exists():
            raise RuntimeError(
                f"Model not found at {MODEL_DIR}. Train the model first."
            )
        try:
            nlp = spacy.load(MODEL_DIR)
        except Exception as e:
            raise RuntimeError(
                f"Model at {MODEL_DIR} could not be loaded. "
                "Restore model-best or retrain the model. "
                f"Original error: {e}"
            ) from e
    return nlp


# ---------------------------------------------------------------------------
# Regex helpers (supplements NER for high-precision structured fields)
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{2,4}[\s\-]?\d{2,4}(?:[\s\-]?\d{1,4})?"
)
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)

FALLBACK_SKILLS = [
    "python", "java", "javascript", "typescript", "sql", "nosql", "c++", "c#",
    "go", "r", "php", "scala", "html", "css", "bash", "powershell",
    "excel", "power bi", "tableau", "looker", "qlik", "dax", "sap",
    "react", "vue", "angular", "next.js", "node.js", "express", "django",
    "flask", "fastapi", "spring boot", "laravel", ".net", "asp.net",
    "mongodb", "postgresql", "mysql", "sql server", "oracle", "redis",
    "elasticsearch", "cassandra", "neo4j", "snowflake", "bigquery",
    "aws", "azure", "gcp", "databricks", "docker", "kubernetes", "terraform",
    "jenkins", "git", "gitlab", "github", "airflow", "spark", "hadoop",
    "kafka", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "keras", "matplotlib", "nltk", "spacy", "nlp", "machine learning",
    "deep learning", "computer vision", "rest", "graphql", "postman", "swagger",
    "figma", "jira", "confluence", "agile", "scrum",
]

# Common CV section headers (EN + FR + AR) that should never be entities
SECTION_HEADERS = {
    # English
    "skills", "skill", "education", "experience", "summary", "profile",
    "objective", "references", "projects", "certifications", "languages",
    "work experience", "professional experience", "personal information",
    "contact", "interests", "hobbies", "achievements", "awards",
    "technical skills", "soft skills", "key skills",
    # French
    "compétences", "competences", "formation", "expérience", "experience",
    "expérience professionnelle", "profil", "objectif", "références",
    "projets", "certifications", "langues", "centres d'intérêt",
    "informations personnelles", "contact", "loisirs", "centres",
    "intégrateur", "développeur",
    # Common sub-headers
    "frontend", "front", "backend", "back", "devops", "outils", "tools",
    "database", "databases", "bases de données", "sécurité", "security",
    "mobile", "sécurité & identité",
}

# Short filler words / fragments that are never valid entities
NOISE_WORDS = {
    "a", "an", "the", "of", "of a", "and", "or", "in", "at", "to", "for",
    "with", "on", "is", "are", "was", "were", "be", "been", "being",
    "de", "la", "le", "les", "du", "des", "un", "une", "et", "ou",
    "en", "à", "par", "pour", "sur", "dans", "est", "sont",
    "front", "back", "end", "web", "app",
    "dynamiques", "centralisée", "sécurisés", "févr",
}

# Punctuation / junk patterns that indicate a bad entity
JUNK_RE = re.compile(r"^[\s\W]{0,3}$")  # 0–3 chars, all punctuation/whitespace
STARTS_WITH_PUNCT = re.compile(r"^[,;:/\)\(\]\[]+\s*")
ENDS_WITH_PUNCT = re.compile(r"\s*[,;:/\(\[\]]+$")


def clean_entity(text: str) -> str:
    """Strip leading/trailing punctuation and junk from an entity string."""
    text = STARTS_WITH_PUNCT.sub("", text)
    text = ENDS_WITH_PUNCT.sub("", text)
    # Remove enclosing parentheses / brackets
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    return text.strip()


def is_valid_entity(text: str, label: str) -> bool:
    """Return False for entities that are clearly noise."""
    cleaned = text.strip()
    # Too short (except for known short tech labels like "C", "R", "Go")
    if len(cleaned) < 2:
        return False
    # Pure punctuation / whitespace
    if JUNK_RE.match(cleaned):
        return False
    # Section headers misclassified as entities
    if cleaned.lower() in SECTION_HEADERS:
        return False
    # Noise filler words
    if cleaned.lower() in NOISE_WORDS:
        return False
    # Contains newlines (multi-line garbage)
    if "\n" in cleaned and label != "Years_of_Experience":
        return False
    # Skills-specific: reject very short non-tech words (< 2 chars) unless known
    if label == "Skills" and len(cleaned) <= 2 and cleaned not in {"C", "R", "Go", "AI", "ML", "JS", "C#"}:
        return False
    return True


def regex_postprocess(text: str, ner_result: dict) -> dict:
    """
    Augment NER results with regex-based extraction for structured fields.
    Catches emails, linkedin, github that NER may miss.
    """
    # Emails
    regex_emails = set(EMAIL_RE.findall(text))
    existing_emails = set(ner_result.get("email_addresses", []))
    ner_result["email_addresses"] = sorted(existing_emails | regex_emails)

    # LinkedIn
    linkedin_matches = LINKEDIN_RE.findall(text)
    if linkedin_matches:
        ner_result["linkedin"] = linkedin_matches[0]

    # GitHub
    github_matches = GITHUB_RE.findall(text)
    if github_matches:
        ner_result["github"] = github_matches[0]

    return ner_result


def extract_known_skills(text: str) -> list[str]:
    """Fallback skill scanner used when NER misses or model is unavailable."""
    haystack = text.lower()
    found = []
    for skill in FALLBACK_SKILLS:
        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill.lower()) + r"(?![a-z0-9+#.])"
        if re.search(pattern, haystack):
            found.append(skill)
    return found


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------
class ExtractionResult(BaseModel):
    name: list[str]
    email_addresses: list[str]
    skills: list[str]
    companies: list[str]
    colleges: list[str]
    degrees: list[str]
    years_of_experience: list[str]
    languages: list[str]
    linkedin: Optional[str] = None
    github: Optional[str] = None
    detected_language: Optional[str] = None
    raw_text: Optional[str] = None


def run_full_cv_extraction(original_text: str, include_raw_text: bool = False) -> ExtractionResult:
    """Shared full CV extraction pipeline used by technical and platform APIs."""
    lang = detect_language(original_text)
    translated_text = None

    if lang != "en":
        try:
            translated_text = translate_text(original_text, source_lang=lang)
        except Exception:
            translated_text = None

    ner_text = translated_text if translated_text else original_text
    ner_results_en = _run_ner(ner_text)
    ner_results_orig = _run_ner(original_text) if translated_text else []

    entities = {
        "name": [],
        "email_addresses": [],
        "skills": [],
        "companies": [],
        "colleges": [],
        "degrees": [],
        "years_of_experience": [],
        "languages": [],
    }
    seen = {key: set() for key in entities}

    def _add(key: str, value: str, label: str):
        value = clean_entity(value)
        if not is_valid_entity(value, label):
            return
        norm = value.lower().strip()
        if norm not in seen[key]:
            seen[key].add(norm)
            entities[key].append(value)

    for label, key, raw in ner_results_en:
        if key in KEEP_ORIGINAL and translated_text:
            orig = find_original_span(raw, original_text, ner_text)
            if orig and len(orig) < len(raw) * 3:
                _add(key, orig, label)
            else:
                back = translate_entity(raw, source_lang="en", target_lang=lang)
                _add(key, back if back else raw, label)
        else:
            _add(key, raw, label)

    for label, key, raw in ner_results_orig:
        _add(key, raw, label)

    for skill in extract_known_skills(original_text):
        _add("skills", skill, "Skills")

    entities = regex_postprocess(original_text, entities)
    if translated_text:
        entities = regex_postprocess(translated_text, entities)

    _final_cleanup(entities, original_text)
    return ExtractionResult(**entities, detected_language=lang, raw_text=original_text if include_raw_text else None)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Talent Bridge Recruitment Platform API",
    description=(
        "Role-based recruitment platform API for candidates, recruiters, and admins. "
        "Includes CV extraction, CV quality scoring, NLP matching, job recommendations, "
        "applications, shortlists, notifications, and platform monitoring."
    ),
    version="3.0.0",
)
app.include_router(api_v1_router)

@app.on_event("startup")
def startup_load_model():
    """Pre-load model on startup for fast first request."""
    seed_platform()
    try:
        get_model()
        print(f"Model loaded from {MODEL_DIR}")
    except RuntimeError as e:
        print(f"WARNING: {e}")


@app.get("/health")
def health():
    model_loaded = nlp is not None
    return {"status": "ok", "model_loaded": model_loaded}


@app.get("/analyses")
def analyses(limit: int = 50):
    """List recent CV analyses saved in SQL Server."""
    try:
        return {"analyses": list_saved_analyses(limit=limit)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load saved analyses: {str(e)}")


@app.get("/analyses/{analysis_id}")
def analysis_detail(analysis_id: int):
    """Return one saved CV analysis with skills and matched jobs."""
    try:
        result = get_saved_analysis(analysis_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load saved analysis: {str(e)}")
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


LABEL_TO_KEY = {
    "Name": "name",
    "Email_Address": "email_addresses",
    "Skills": "skills",
    "Companies_Worked_At": "companies",
    "College_Name": "colleges",
    "Degree": "degrees",
    "Years_of_Experience": "years_of_experience",
    "Languages": "languages",
}

# Entity types where the original-language value should be preserved
# (e.g. "Licence en Informatique" is more useful than "Bachelor of CS")
KEEP_ORIGINAL = {"name", "colleges", "degrees", "companies"}

# Entity types that are usually language-agnostic (tech terms, proper nouns)
UNIVERSAL = {"email_addresses", "skills"}


def _run_ner(text: str) -> list[tuple[str, str, str]]:
    """Run spaCy NER and return [(label, key, raw_text), ...]."""
    try:
        model = get_model()
    except RuntimeError:
        return []
    doc = model(text)
    results = []
    for ent in doc.ents:
        key = LABEL_TO_KEY.get(ent.label_)
        if key:
            results.append((ent.label_, key, ent.text))
    return results


@app.post("/extract", response_model=ExtractionResult)
async def extract_cv(
    file: UploadFile = File(...),
    include_raw_text: bool = False,
):
    """
    Upload a PDF CV and extract structured information.
    Automatically detects language and translates to English for NER
    if the CV is not in English.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Upload a .pdf file.",
        )

    # Read PDF
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB).")

    # Extract text from PDF
    try:
        original_text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract text from PDF: {str(e)}",
        )

    if not original_text or len(original_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Could not extract meaningful text from the PDF.",
        )

    return run_full_cv_extraction(original_text, include_raw_text=include_raw_text)


@app.post("/match-jobs")
async def match_jobs(
    file: UploadFile = File(...),
    target_role: str = Form(...),
    preferred_country: Optional[str] = Form(None),
    remote_preference: str = Form("any"),
    limit: int = Form(10),
    max_candidates: int = Form(5000),
    save_results: bool = Form(False),
):
    """
    Extract a CV profile, load candidate jobs from SQL Server, and return the
    best explainable job matches.

    Requires SQL view dbo.vw_job_matching. Create it with:
    DataPlatform/Warehouse/views/01_create_vw_job_matching.sql
    """
    extraction = await extract_cv(file, include_raw_text=True)
    extraction_data = _model_to_dict(extraction)
    raw_text = extraction_data.get("raw_text") or ""
    quality = classify_cv_quality(raw_text, extraction_data)
    candidate = build_candidate_profile(
        extraction_data,
        target_role=target_role,
        preferred_country=preferred_country,
        remote_preference=remote_preference,
    )
    extraction_data["raw_text"] = None

    try:
        jobs = fetch_jobs_from_sql(
            target_role=target_role,
            max_candidates=max_candidates,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to load jobs from SQL Server: {str(e)}",
        )

    matches = rank_jobs(candidate, jobs, limit=limit)
    analysis_id = None
    save_error = None
    if save_results:
        try:
            analysis_id = save_analysis_results(
                candidate,
                extraction_data,
                quality,
                matches,
                file_name=file.filename,
            )
        except Exception as e:
            save_error = str(e)

    return {
        "analysis_id": analysis_id,
        "candidate_profile": _candidate_to_dict(candidate),
        "quality": quality,
        "jobs_considered": len(jobs),
        "matches": matches,
        "save_error": save_error,
    }


@app.post("/classify-cv-quality")
async def classify_cv_quality_endpoint(
    file: UploadFile = File(...),
    save_results: bool = Form(False),
):
    """Classify a CV as Pro / Non Pro and return improvement suggestions."""
    extraction = await extract_cv(file, include_raw_text=True)
    extraction_data = _model_to_dict(extraction)
    raw_text = extraction_data.get("raw_text") or ""
    quality = classify_cv_quality(raw_text, extraction_data)
    extraction_data["raw_text"] = None
    analysis_id = None
    save_error = None
    if save_results:
        candidate = build_candidate_profile(extraction_data)
        try:
            analysis_id = save_analysis_results(
                candidate,
                extraction_data,
                quality,
                [],
                file_name=file.filename,
            )
        except Exception as e:
            save_error = str(e)

    return {
        "analysis_id": analysis_id,
        "quality": quality,
        "extraction_summary": extraction_data,
        "save_error": save_error,
    }


@app.post("/analyze-cv-full")
async def analyze_cv_full(
    file: UploadFile = File(...),
    target_role: Optional[str] = Form(None),
    preferred_country: Optional[str] = Form(None),
    remote_preference: str = Form("any"),
    limit: int = Form(10),
    max_candidates: int = Form(5000),
    save_results: bool = Form(False),
):
    """Return CV extraction, CV quality, and optional SQL job matches."""
    extraction = await extract_cv(file, include_raw_text=True)
    extraction_data = _model_to_dict(extraction)
    raw_text = extraction_data.get("raw_text") or ""
    quality = classify_cv_quality(raw_text, extraction_data)

    matches = []
    matching_error = None
    candidate = None
    jobs_considered = 0
    analysis_id = None
    save_error = None
    if target_role:
        candidate = build_candidate_profile(
            extraction_data,
            target_role=target_role,
            preferred_country=preferred_country,
            remote_preference=remote_preference,
        )
        extraction_data["raw_text"] = None
        try:
            jobs = fetch_jobs_from_sql(
                target_role=target_role,
                max_candidates=max_candidates,
            )
            jobs_considered = len(jobs)
            matches = rank_jobs(candidate, jobs, limit=limit)
        except Exception as e:
            matching_error = str(e)
    else:
        candidate = build_candidate_profile(
            extraction_data,
            preferred_country=preferred_country,
            remote_preference=remote_preference,
        )
        extraction_data["raw_text"] = None

    if save_results and candidate:
        try:
            analysis_id = save_analysis_results(
                candidate,
                extraction_data,
                quality,
                matches,
                file_name=file.filename,
            )
        except Exception as e:
            save_error = str(e)

    return {
        "analysis_id": analysis_id,
        "extraction": extraction_data,
        "quality": quality,
        "candidate_profile": _candidate_to_dict(candidate) if candidate else None,
        "jobs_considered": jobs_considered,
        "matches": matches,
        "matching_error": matching_error,
        "save_error": save_error,
    }


def _final_cleanup(entities: dict, original_text: str) -> None:
    """Post-NER cleanup: remove dups, substrings, misclassified items."""

    # Remove github/linkedin URLs from names
    entities["name"] = [
        n for n in entities["name"]
        if "github.com" not in n.lower() and "linkedin.com" not in n.lower()
    ]

    # --- Cross-field dedup: move company names from skills to companies ---
    # Only move items that are clearly NOT tech skills
    _KNOWN_TECH = {
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css",
        "react", "vue", "vue 3", "angular", "next.js", "nuxt", "svelte", "node.js",
        "express", "node.js/express", "django", "flask", "fastapi", "spring boot",
        ".net", "asp.net", "laravel", "rails", "docker", "kubernetes", "k8s",
        "aws", "azure", "gcp", "git", "github", "gitlab", "ci/cd", "ci", "cd",
        "jenkins", "terraform", "ansible", "linux", "nginx", "apache",
        "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "kafka",
        "rabbitmq", "graphql", "rest", "rest api", "grpc", "websocket",
        "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy",
        "spacy", "nlp", "ml", "ai", "deep learning", "machine learning",
        "opencv", "matplotlib", "spark", "hadoop", "airflow",
        "oauth2", "jwt", "keycloak", "oidc", "rbac", "ldap", "saml",
        "postman", "swagger", "jira", "confluence", "figma", "sketch",
        "android", "ios", "flutter", "react native", "unity", "ar",
        "mern stack", "mean stack", "full-stack", "full‑stack", "frontend",
        "backend", "devops", "agile", "scrum", "tdd", "microservices",
        "redstart", "mathematics",
    }

    _WORK_INDICATORS = re.compile(
        r"(stage\b|intern|stagiaire|travaillé|worked\s+at|employé|"
        r"consultant|poste|contrat|cdi|cdd|freelance|alternance|"
        r"expérience\n|experience\n)",
        re.IGNORECASE,
    )
    skills_to_remove = set()
    for skill in entities["skills"]:
        sl = skill.lower().strip()
        # Never move known tech skills
        if sl in _KNOWN_TECH:
            continue
        # Check if this "skill" appears in original text near work indicators
        try:
            pattern = re.compile(
                re.escape(skill) + r".{0,50}" + _WORK_INDICATORS.pattern + r"|"
                + _WORK_INDICATORS.pattern + r".{0,50}" + re.escape(skill),
                re.IGNORECASE,
            )
            if pattern.search(original_text):
                skills_to_remove.add(sl)
                if sl not in {c.lower() for c in entities["companies"]}:
                    entities["companies"].append(skill)
        except re.error:
            continue

    # Detect education institutions misclassified as skills
    _EDU_INDICATORS = re.compile(
        r"(université|university|école|school|institut|institute|"
        r"formation|diplôme|degree|licence|master|"
        r"ingénieur|baccalauréat|bac\b|campus)",
        re.IGNORECASE,
    )
    for skill in entities["skills"]:
        sl = skill.lower().strip()
        if sl in skills_to_remove or sl in _KNOWN_TECH:
            continue
        try:
            pattern = re.compile(
                re.escape(skill) + r".{0,40}" + _EDU_INDICATORS.pattern + r"|"
                + _EDU_INDICATORS.pattern + r".{0,40}" + re.escape(skill),
                re.IGNORECASE,
            )
            if pattern.search(original_text):
                skills_to_remove.add(sl)
                if sl not in {c.lower() for c in entities["colleges"]}:
                    entities["colleges"].append(skill)
        except re.error:
            continue

    # Remove misclassified items from skills
    entities["skills"] = [s for s in entities["skills"] if s.lower() not in skills_to_remove]

    # --- Remove generic French words that leaked into skills ---
    entities["skills"] = [
        s for s in entities["skills"]
        if not re.match(r"^(REST\s+)?sécurisés?$", s, re.IGNORECASE)
        and s.lower() not in {"mathematics", "of a"}
    ]

    # Deduplicate languages (e.g. "Arabic" and "Arabe" are the same)
    _LANG_ALIASES = {
        "arabe": "Arabic", "arab": "Arabic", "arabic": "Arabic",
        "français": "French", "francais": "French", "french": "French",
        "anglais": "English", "english": "English",
        "allemand": "German", "german": "German",
        "espagnol": "Spanish", "spanish": "Spanish",
        "italien": "Italian", "italian": "Italian",
        "chinois": "Chinese", "chinese": "Chinese",
        "japonais": "Japanese", "japanese": "Japanese",
        "portugais": "Portuguese", "portuguese": "Portuguese",
        "russe": "Russian", "russian": "Russian",
        "turc": "Turkish", "turkish": "Turkish",
    }
    seen_langs = set()
    clean_langs = []
    for lang_val in entities["languages"]:
        canonical = _LANG_ALIASES.get(lang_val.lower().strip(), lang_val)
        if canonical.lower() not in seen_langs:
            seen_langs.add(canonical.lower())
            clean_langs.append(canonical)
    entities["languages"] = clean_langs

    # Remove entities that are substrings of longer entities in the same category
    for key in ["skills", "companies", "colleges", "degrees"]:
        items = entities[key]
        if len(items) <= 1:
            continue
        lower_items = [i.lower() for i in items]
        filtered = []
        for i, item in enumerate(items):
            li = lower_items[i]
            # Keep if no other item fully contains this one (unless same)
            is_substring = any(
                li != lj and li in lj
                for j, lj in enumerate(lower_items)
            )
            if not is_substring:
                filtered.append(item)
        entities[key] = filtered


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Support both Pydantic v1 and v2 serialization APIs."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _candidate_to_dict(candidate: Any) -> dict[str, Any]:
    if candidate is None:
        return {}
    return {
        "name": candidate.name,
        "email": candidate.email,
        "target_role": candidate.target_role,
        "preferred_country": candidate.preferred_country,
        "remote_preference": candidate.remote_preference,
        "years_of_experience": candidate.years_of_experience,
        "seniority_level": candidate.seniority_level,
        "skills": candidate.skills,
        "degrees": candidate.degrees,
        "languages": candidate.languages,
        "linkedin": candidate.linkedin,
        "github": candidate.github,
    }
