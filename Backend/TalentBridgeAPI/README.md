# Backend Platform Mini-Project

## What It Does

This is the main role-based recruitment API.

It exposes:

```text
Auth API
Users/Profile API
Companies API
Jobs API
CV API
Matching API
Applications API
Shortlist API
Notifications API
Admin API
```

## Why It Exists

The backend turns independent AI/NLP/ML modules into a real business application.

It manages users, roles, jobs, applications, shortlists, notifications, audit logs, and AI job monitoring.

## Main Files

```text
Backend/TalentBridgeAPI/app/main.py
Backend/TalentBridgeAPI/app/platform/
```

## How It Works

1. Users authenticate through `/api/v1/auth/*`.
2. Role-based dependencies protect candidate, recruiter, and admin endpoints.
3. Business routes call domain modules for CV quality, extraction, and matching.
4. A local JSON-backed demo store supports runtime workflows.
5. SQL migration `008_create_platform_business_tables.sql` prepares future persistent platform tables.

Runtime demo state is saved at:

```text
Artifacts/platform_store.json
```

The current platform runtime uses this JSON store. The `platform.*` SQL tables are available as the production persistence target, but are not the default runtime repository yet.

## Technical AI Endpoints

The platform uses `/api/v1/*` routes, but direct AI validation endpoints are still available:

```text
POST /extract
POST /match-jobs
POST /classify-cv-quality
POST /analyze-cv-full
GET /analyses
GET /analyses/{analysis_id}
```

## Important Demo Users

```text
candidate@talentbridge.local / candidate123
recruiter@talentbridge.local / recruiter123
admin@talentbridge.local / admin123
```

## Run

```bash
cd Backend/TalentBridgeAPI
python run_server.py serve
```

## Validation

```bash
python Tests/smoke/test_platform_workflows.py
```

## Teacher Validation Checklist

- Backend exposes `/api/v1` role-based APIs.
- Auth and RBAC exist.
- Candidate/recruiter/admin workflows exist.
- Backend consumes AI modules but does not merge them.
- Platform business tables migration exists.
- Demo state persistence is documented separately from production SQL tables.
