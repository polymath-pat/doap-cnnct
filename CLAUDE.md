# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CNNCT is a network connectivity tester - a full-stack web application for probing network connectivity and diagnostics. It consists of a Flask backend, Vite/TypeScript frontend, managed Valkey (Redis) for rate limiting, and is deployed to DigitalOcean via Pulumi.

## Build & Test Commands

All automation is managed through the Makefile:

```bash
make test-all         # Full pipeline: security → unit → infra → e2e → cleanup
make test-security    # Bandit security audit on ./src
make test-unit        # Pytest unit tests
make build-frontend   # Build frontend with Vite (standalone, not needed for infra-up)
make infra-up         # Build containers and start docker-compose (frontend builds inside container)
make infra-down       # Stop containers
make test-e2e         # Run Selenium browser tests
make clean            # Full cleanup (venv + containers + cache)
```

Frontend-specific commands (run from `frontend/` directory):
```bash
npm run dev           # Vite dev server with hot reload
npm run build         # TypeScript compile + Vite bundle
npm run lint          # ESLint
npm run typecheck     # TypeScript type checking
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         FRONTEND (Vite + TypeScript + Tailwind CSS)         │
│  - Glassmorphic UI with 3 tabs: Port Check, DNS, HTTP Diag  │
│  - localStorage for test history                            │
└────────────────────────┬────────────────────────────────────┘
                         │
              [DO App Platform Ingress]
              /api/* → backend-api:8080
              /*     → frontend static site
                         │
┌────────────────────────┴────────────────────────────────────┐
│              BACKEND (Flask + Gunicorn)                     │
│  Routes:                                                    │
│    /healthz         - Health check (rate-limit exempt)      │
│    /cnnct           - TCP port 443 connectivity probe       │
│    /dns/<domain>    - DNS resolution + A records            │
│    /diag            - HTTP diagnostic, speed, status codes  │
│                                                             │
│  Rate Limiting: 100/hour, 20/minute (flask-limiter)         │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │   Managed Valkey    │
              │   (DO Database)     │
              │   Rate limit state  │
              └─────────────────────┘
```

## Local Development

- `make infra-up` builds and starts all containers (frontend builds inside its multi-stage Dockerfile)
- Frontend URL: http://localhost:3000 (Nginx)
- Backend URL: http://localhost:8081 (Flask via Docker)
- Vite dev proxy forwards `/api/*` to `http://127.0.0.1:8080`
- Containers use podman/podman-compose

## Key Files

| File | Purpose |
|------|---------|
| `src/app.py` | Core backend API (4 endpoints) |
| `frontend/src/main.ts` | Frontend UI logic and state |
| `frontend/Dockerfile` | Multi-stage build: Node (build) → Nginx (serve) |
| `backend.Dockerfile` | Python 3.11 + Gunicorn |
| `Makefile` | Build automation and local dev |
| `.github/workflows/ci.yaml` | GitHub Actions CI/CD pipeline |
| `docker-compose.yaml` | Local dev environment |
| `index.ts` | Pulumi infrastructure definition |
| `Pulumi.yaml` | Pulumi project config (runtime: nodejs) |
| `Pulumi.prod.yaml` | Pulumi prod stack config (encryption salt) |
| `package.json` | Root package.json for Pulumi dependencies |
| `tests/unit_test.py` | API unit tests (pytest) |
| `tests/e2e_test.py` | Selenium browser tests |

## CI/CD Pipeline

GitHub Actions pipeline in `.github/workflows/ci.yaml`:

```
┌──────────────┐  ┌─────────────┐
│ Security Scan│  │ Unit Tests  │   ← Run in parallel
└──────┬───────┘  └──────┬──────┘
       └────────┬────────┘
                ▼
       ┌────────────────┐
       │ E2E Browser    │   ← Needs both to pass
       │ Tests          │
       └───────┬────────┘
               ▼
       ┌────────────────┐
       │ Build & Push   │   ← main branch only
       │ Backend Image  │
       └───────┬────────┘
               ▼
       ┌────────────────┐
       │ Pulumi Deploy  │   ← main branch only
       └────────────────┘
```

- Security and unit tests run in parallel with pip caching (`actions/setup-python`)
- E2E tests use podman for both infrastructure and test runner
- Build & Push and Pulumi Deploy only run on pushes to `main`
- Triggers on push to `main` and PRs to `main`, `feature/**`, `fix/**`, `bug/**`

## Infrastructure (Pulumi)

All infrastructure is defined in `index.ts` and managed by Pulumi with a self-hosted S3 backend on DigitalOcean Spaces.

### Resources managed by Pulumi
- **DO App Platform** (`cnnct`) - Backend API service + frontend static site
- **Managed Valkey cluster** - Rate limiting state for the backend
- **DNS CNAME record** - `cnnct.metaciety.net` → app ingress URL

### Pulumi State Backend
- Stored in DO Spaces bucket `doap-cnnct` (SFO3 region)
- Login: `pulumi login 's3://doap-cnnct?endpoint=sfo3.digitaloceanspaces.com'`
- Requires `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION=us-east-1`

### Pulumi Local Usage
```bash
# Set environment
export AWS_ACCESS_KEY_ID=<spaces-access-key>
export AWS_SECRET_ACCESS_KEY=<spaces-secret-key>
export AWS_REGION=us-east-1
export PULUMI_CONFIG_PASSPHRASE=<passphrase>
export DIGITALOCEAN_TOKEN=<do-api-token>

# Login to state backend
pulumi login 's3://doap-cnnct?endpoint=sfo3.digitaloceanspaces.com'

# Preview changes without applying
pulumi preview --stack prod

# Apply changes
pulumi up --stack prod
```

### GitHub Secrets Required
| Secret | Purpose |
|--------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | DO API token (used by doctl and Pulumi provider) |
| `SPACES_ACCESS_KEY` | DO Spaces access key (Pulumi state backend auth) |
| `SPACES_SECRET_KEY` | DO Spaces secret key (Pulumi state backend auth) |
| `PULUMI_PASSPHRASE` | Decrypts Pulumi stack config encryption salt |

## Deployment

- **Production URL:** cnnct.metaciety.net
- **Platform:** DigitalOcean App Platform (SFO3)
- **Container Registry:** DigitalOcean Container Registry (`kadet-cantu`)
- **Database:** Managed Valkey cluster (SFO3)
- **DNS:** Managed in DigitalOcean, CNAME created by Pulumi
- **Backend image tag:** Tagged with git SHA on each deploy
