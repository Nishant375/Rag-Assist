.PHONY: install api chat ingest ingest-drive

## Install all dependencies (run once)
install:
	uv sync

## Start the FastAPI backend — http://localhost:8000/docs
api:
	uv run uvicorn api.main:app --reload --port 8000

## Start the Streamlit UI — http://localhost:8501
chat:
	uv run streamlit run ui/main.py

## Ingest a local folder:  make ingest SOURCE=./my-docs
ingest:
	uv run python ingest_cli.py --source $(SOURCE)

## Ingest from Google Drive:  make ingest-drive ID=<folder-id>
ingest-drive:
	uv run python ingest_cli.py --drive-folder-id $(ID)
