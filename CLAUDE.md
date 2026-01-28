# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CNNCT is a network connectivity tester - a full-stack web application for probing network connectivity and diagnostics. It consists of a Flask backend, Vite/TypeScript frontend, Redis for rate limiting, and is deployed to DigitalOcean via Pulumi.

## Build & Test Commands

All automation is managed through the Makefile:

```bash
make test-all         # Full pipeline: security → unit → infra → e2e → cleanup
make test-security    # Bandit security audit on ./src
make test-unit        # Pytest unit tests
make build-frontend   # Build React app with Vite
make infra-up         # Start Docker Compose (backend + redis + frontend)
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
                    [Nginx Proxy]
                    /api/* → backend:8080
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
              │   REDIS/VALKEY      │
              │   Rate limit state  │
              └─────────────────────┘
```

## Local Development

- Frontend URL: http://localhost:3000 (Nginx)
- Backend URL: http://localhost:8081 (Flask via Docker)
- Vite dev proxy forwards `/api/*` to `http://127.0.0.1:8080`

## Key Files

| File | Purpose |
|------|---------|
| `src/app.py` | Core backend API (4 endpoints) |
| `frontend/src/main.ts` | Frontend UI logic and state |
| `Makefile` | Build automation and CI integration |
| `.github/workflows/ci.yaml` | GitHub Actions CI/CD pipeline |
| `docker-compose.yaml` | Local dev environment |
| `index.ts` | Pulumi infrastructure definition |
| `tests/unit_test.py` | API unit tests (pytest) |
| `tests/e2e_test.py` | Selenium browser tests |

## CI/CD Pipeline

GitHub Actions pipeline (sequential):
1. Security Audit → Bandit scans `/src`
2. Unit Tests → Pytest
3. E2E Testing → Selenium browser automation
4. Build & Push → Docker image to DigitalOcean registry
5. Deploy → Pulumi infrastructure update

Triggers on push to `main` and PRs to `main`, `feature/**`, `fix/**`, `bug/**`.

## Deployment

- Production: cnnct.metaciety.net (auto-deploys on main merge)
- Infrastructure: DigitalOcean App Platform via Pulumi
- Container Registry: DigitalOcean Container Registry (DOCR)
- Database: Managed DigitalOcean Valkey cluster
