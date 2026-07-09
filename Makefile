.PHONY: dev backend-dev frontend-dev test lint ingest

dev:
	@echo "Run in two terminals:"
	@echo "  make backend-dev   # http://localhost:8000"
	@echo "  make frontend-dev  # http://localhost:5173"

backend-dev:
	cd backend && uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest -q

ingest:
	cd backend && python -m ingest.runner
