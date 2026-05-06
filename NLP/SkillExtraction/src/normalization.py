"""Normalization helpers shared by CV extraction, matching, and quality scoring."""

from __future__ import annotations

import re


_PUNCT_RE = re.compile(r"[^a-z0-9+#.\s-]")
_SPACE_RE = re.compile(r"\s+")


SKILL_ALIASES = {
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "jupyter notebook": "jupyter",
    "jupyter notebooks": "jupyter",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "advanced excel": "excel",
    "powerbi": "power bi",
    "microsoft power bi": "power bi",
    "ms power bi": "power bi",
    "bi power": "power bi",
    "power query": "power query",
    "powerquery": "power query",
    "power pivot": "power pivot",
    "powerpivot": "power pivot",
    "tableau desktop": "tableau",
    "google data studio": "looker studio",
    "data studio": "looker studio",
    "js": "javascript",
    "java script": "javascript",
    "ecmascript": "javascript",
    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",
    "reactjs": "react",
    "react js": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue js": "vue",
    "vue.js": "vue",
    "vue 3": "vue",
    "nextjs": "next.js",
    "next js": "next.js",
    "nuxtjs": "nuxt",
    "nuxt js": "nuxt",
    "angularjs": "angular",
    "angular js": "angular",
    "springboot": "spring boot",
    "spring": "spring boot",
    "fast api": "fastapi",
    "expressjs": "express",
    "express js": "express",
    "postgresql sql": "postgresql",
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "postgre": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "microsoft sql server": "sql server",
    "sqlserver": "sql server",
    "t sql": "sql",
    "t-sql": "sql",
    "pl sql": "sql",
    "pl-sql": "sql",
    "mysql server": "mysql",
    "mongo db": "mongodb",
    "mongo": "mongodb",
    "elastic search": "elasticsearch",
    "elastic": "elasticsearch",
    "neo4 j": "neo4j",
    "ms azure": "azure",
    "microsoft azure": "azure",
    "amazon web services": "aws",
    "amazon aws": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure devops": "azure devops",
    "dev ops": "devops",
    "devops": "devops",
    "docker compose": "docker",
    "docker-compose": "docker",
    "kubernete": "kubernetes",
    "kubernetes cluster": "kubernetes",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit": "scikit-learn",
    "sci kit learn": "scikit-learn",
    "tf": "tensorflow",
    "tensor flow": "tensorflow",
    "pytorch": "pytorch",
    "py torch": "pytorch",
    "matplot lib": "matplotlib",
    "matplotlib.pyplot": "matplotlib",
    "np": "numpy",
    "pd": "pandas",
    "spark sql": "spark",
    "apache spark": "spark",
    "apache kafka": "kafka",
    "apache airflow": "airflow",
    "apache hadoop": "hadoop",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "ia": "artificial intelligence",
    "dl": "deep learning",
    "cv": "computer vision",
    "nlp": "nlp",
    "k8s": "kubernetes",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "ci/cd pipeline": "ci/cd",
    "jenkin": "jenkins",
    "git hub": "github",
    "git lab": "gitlab",
    "rest api": "rest",
    "restful": "rest",
    "restful api": "rest",
    "api rest": "rest",
    "graphql api": "graphql",
    "web socket": "websocket",
    "web sockets": "websocket",
    "jwt token": "jwt",
    "json web token": "jwt",
    "oauth": "oauth2",
    "oauth 2": "oauth2",
    "oauth2.0": "oauth2",
    "open id connect": "oidc",
    "openid connect": "oidc",
    "key cloak": "keycloak",
    "tailwindcss": "tailwind css",
    "tailwind": "tailwind css",
    "bootstrap 5": "bootstrap",
    "asp net": "asp.net",
    "aspnet": "asp.net",
    "c sharp": "c#",
    "csharp": "c#",
    "dotnet": ".net",
    "dot net": ".net",
    "net": ".net",
    "figma design": "figma",
    "adobe xd": "xd",
    "ms project": "microsoft project",
    "project management": "project management",
    "uml design": "uml",
    "uml": "uml",
    "oop": "object-oriented programming",
    "object oriented programming": "object-oriented programming",
    "poo": "object-oriented programming",
}


def normalize_text(value: str | None) -> str:
    """Lowercase, trim, and collapse whitespace for stable comparisons."""
    if not value:
        return ""
    text = value.lower().strip()
    text = text.replace("/", " ")
    text = _PUNCT_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def normalize_skill(value: str | None) -> str:
    """Normalize one skill label to the closest warehouse representation."""
    text = normalize_text(value)
    if not text:
        return ""
    return SKILL_ALIASES.get(text, text)


def normalize_skills(values: list[str] | tuple[str, ...] | set[str] | None) -> list[str]:
    """Normalize and deduplicate skills while preserving first-seen order."""
    seen = set()
    result = []
    for value in values or []:
        normalized = normalize_skill(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def split_csv_values(value: str | None) -> list[str]:
    """Split SQL STRING_AGG comma output into cleaned values."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item and item.strip()]
