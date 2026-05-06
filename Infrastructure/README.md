# Infrastructure Mini-Project

## What It Does

Provides local startup, Docker, Compose, environment templates, and CI workflow.

## Main Files

```text
Infrastructure/scripts/start_local.ps1
Infrastructure/scripts/start_local.bat
Infrastructure/docker/backend.Dockerfile
Infrastructure/docker/frontend.Dockerfile
Infrastructure/compose/docker-compose.local.yml
Infrastructure/compose/docker-compose.prod.yml
Infrastructure/env/.env.example
Infrastructure/env/backend.env.example
Infrastructure/env/frontend.env.example
Infrastructure/cicd/github-actions/ci.yml
```

## Why It Exists

A professional project must be runnable locally and ready for production deployment planning.

## How It Works

Launcher:

```text
starts backend
starts frontend
opens dashboard
applies SQL views if sqlcmd exists
```

Docker:

```text
backend container runs FastAPI
frontend container serves Vue build with Nginx
```

CI:

```text
compiles Python
runs smoke test
builds frontend
```

## Teacher Validation Checklist

- Local launcher exists.
- Dockerfiles exist.
- Docker Compose exists.
- Environment examples exist.
- CI workflow exists.
