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
4. In-memory store supports demo workflows.
5. SQL migration exists for future persistent platform tables.

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
