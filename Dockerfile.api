FROM python:3.11-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml .
COPY core/ core/
COPY rag/ rag/
COPY providers/ providers/
COPY services/ services/
COPY api/ api/
COPY ingest_cli.py .
RUN uv pip install --system --no-cache \
    langgraph langchain langchain-groq langchain-community langchain-text-splitters \
    langchain-ollama langchain-google-genai pinecone psycopg2-binary \
    pypdf python-docx fastapi uvicorn python-multipart pydantic-settings python-dotenv requests
RUN mkdir -p uploads
# Verify the app starts cleanly at build time
RUN python -c "from api.main import app; print('startup OK')"
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
