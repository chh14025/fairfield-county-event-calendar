# Fairfield County Events

Aggregates Fairfield County, CT events (town calendars, libraries, festivals, farmers markets, user submissions) into one browsable calendar. See `SPEC.md` for the full specification.

## Quick start

```bash
# Backend (Python 3.11+)
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload        # http://localhost:8000/docs

# Frontend (Node 20+)
cd frontend
npm install
npm run dev                          # http://localhost:5173 (proxies /api to :8000)

make test     # backend tests
make ingest   # run ingestion once (backend/ingest/sources.yaml)
```

## Configuration (backend env vars)

| Var | Default | Purpose |
|---|---|---|
| DATABASE_URL | sqlite:///./dev.db | SQLAlchemy URL; Postgres in prod |
| ADMIN_PASSWORD | changeme | Password for /admin moderation |

## Status

M1 (scaffold) complete: API, models, dedup engine, generic iCal connector + ingestion runner, submission + moderation flow, React frontend shell, tests, CI.
Next (M2): confirm real feed URLs for pilot towns (Fairfield, Westport, Norwalk) + LibCal in `backend/ingest/sources.yaml` and enable them.
