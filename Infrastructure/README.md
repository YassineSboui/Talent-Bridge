# Infrastructure Mini-Project

## What It Does

Provides local startup, Docker, Compose, environment templates, and CI workflow.

## Main Files

```text
start_talent_bridge.ps1
start_talent_bridge.bat
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
runs Tests/smoke/test_demo_logic.py
builds frontend
```

Run `Tests/smoke/test_platform_workflows.py` and `Tests/integration/test_sql_ml_views.py` locally for the fuller final validation suite.

## Teacher Validation Checklist

- Local launcher exists.
- Dockerfiles exist.
- Docker Compose exists.
- Environment examples exist.
- CI workflow exists.
