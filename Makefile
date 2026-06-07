.PHONY: install api ingest ingest-drive web web-install gen

# ── Backend (agent-service) ────────────────────────────────────────────────

## Install backend dependencies (run once)
install:
	cd agent-service && uv sync

## Start the FastAPI backend — http://localhost:8000/docs
api:
	cd agent-service && uv run uvicorn api.main:app --reload --port 8000

## Ingest a local folder:  make ingest SOURCE=./my-docs
ingest:
	cd agent-service && uv run python ingest_cli.py --source $(SOURCE)

## Ingest from Google Drive:  make ingest-drive ID=<folder-id>
ingest-drive:
	cd agent-service && uv run python ingest_cli.py --drive-folder-id $(ID)

# ── Frontend ───────────────────────────────────────────────────────────────

## Install frontend dependencies (run once)
web-install:
	cd frontend && npm install

## Start the React dev server — http://localhost:5173
web:
	cd frontend && npm run dev

## Regenerate the typed API client from the backend OpenAPI spec
gen:
	cd frontend && npm run gen
