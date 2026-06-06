.PHONY: install api chat ingest ingest-drive

## Install all dependencies (run once)
install:
	uv sync

## Start the FastAPI backend (terminal 1)
api:
	uv run uvicorn api:app --reload --port 8000

## Start the Streamlit UI (terminal 2)
chat:
	uv run streamlit run app.py

## Ingest local folder:  make ingest SOURCE=./docs
ingest:
	uv run python ingest.py --source $(SOURCE)

## Ingest from Google Drive:  make ingest-drive ID=<folder-id>
ingest-drive:
	uv run python ingest.py --drive-folder-id $(ID)
