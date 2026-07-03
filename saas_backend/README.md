# SCAS SaaS Backend (V1 Blueprint)

This backend is a modular-monolith foundation for SCAS:

- `auth` and role-aware access hooks (placeholder for JWT/SSO integration)
- `tenant` and school configuration models
- `scheduler` build orchestration with async job states
- `solver` reusable CP-SAT engine extracted from the Streamlit prototype
- `conflicts` artifact generation for review board workflows
- `publish` schedule versioning hooks

## Run

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Auth Flow

1. Register user:
   - `POST /api/v1/auth/register`
2. Login and receive bearer token:
   - `POST /api/v1/auth/token`
3. Attach `Authorization: Bearer <token>` on protected routes.

## Key Endpoints

- `POST /api/v1/build-jobs` create build job
- `GET /api/v1/build-jobs/{job_id}` read job status
- `GET /api/v1/build-jobs/{job_id}/conflicts` read conflict artifacts
- `POST /api/v1/build-jobs/{job_id}/publish` mark output as published
- `POST /api/v1/build-jobs/{job_id}/conflicts/{conflict_index}/resolve` resolve and audit conflict action
- `POST /api/v1/imports/csv` validate SIS-like CSV payloads
