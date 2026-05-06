# Frontend Platform Mini-Project

## What It Does

Vue 3 role-based SaaS frontend for Talent Bridge.

It supports:

```text
Candidate dashboard
Recruiter dashboard
Admin dashboard
CV upload
AI CV feedback
Job marketplace
AI matching results
Applications tracking
```

## Why It Exists

The frontend makes Talent Bridge look and behave like a real recruitment platform, not only an AI test page.

## Main Folders

```text
src/layouts/candidate
src/layouts/recruiter
src/layouts/admin
src/pages/auth
src/pages/candidate
src/pages/recruiter
src/pages/admin
src/modules/auth
src/modules/jobs
src/modules/cv
src/modules/matching
src/modules/applications
src/modules/companies
src/modules/notifications
src/modules/profiles
src/services/api
src/stores
```

## How It Works

1. User logs in with a role.
2. Token and user are stored in `authStore`.
3. API services call `/api/v1/*` backend endpoints.
4. UI renders dashboard behavior based on role.
5. Candidate can apply and upload CV.
6. Recruiter can view candidate matches.
7. Admin can access monitoring APIs.

## Run

```bash
cd Frontend/TalentBridgeWeb
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Teacher Validation Checklist

- Frontend has role-based SaaS structure.
- API layer is separated.
- Auth store exists.
- Candidate/recruiter/admin demo workflows exist.
- Frontend only calls backend APIs.
