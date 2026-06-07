# Rag-Assist Web (React + TypeScript)

Production frontend for Rag-Assist. Replaces the Streamlit UI.

## Stack

| Concern | Choice |
|---|---|
| Build / dev | **Vite** + React 18 + **TypeScript** |
| Styling | **Tailwind CSS** (theme in `tailwind.config.js`) |
| Routing | **React Router** (`/login`, `/chat`, `/documents`, `/knowledge-base`) |
| Server state | **TanStack Query** (React Query) |
| API client | **Orval** — typed client + React Query hooks generated from the FastAPI OpenAPI spec |
| HTTP | **axios** with an auth interceptor (`src/api/mutator.ts`) |

## Structure

```
web/
├─ openapi.json              # snapshot of the backend OpenAPI spec (input to codegen)
├─ orval.config.ts           # codegen config
└─ src/
   ├─ api/
   │  ├─ mutator.ts          # axios instance: base URL + bearer token + 401 handling
   │  └─ generated/          # GENERATED — do not edit by hand
   ├─ components/            # Layout + reusable UI (Button, Input, Spinner)
   ├─ lib/                   # auth context, query client, types, error helper
   └─ pages/                 # LoginPage, ChatPage, DocumentsPage, KnowledgeBasePage
```

## API client codegen (the "copy JSON, run one command" flow)

The backend serves its OpenAPI spec at `GET /openapi.json`. To regenerate the
typed client + hooks after the API changes:

```bash
# 1. Refresh the spec snapshot from the running backend
curl https://<your-api-host>/openapi.json -o openapi.json

# 2. Generate the client into src/api/generated/
npm run gen
```

> Requires Node ≥ 18.19 (Orval). Use `nvm use 24` if your default Node is older.

Each endpoint becomes a React Query hook, e.g. `useChatRouteChatPost()`,
`useListDocumentsDocumentsGet()`. Request/response types come straight from the
spec, so the UI is type-safe against the backend.

## Develop

```bash
npm install
npm run dev          # http://localhost:5173 — /api is proxied to localhost:8000
```

Set the backend origin for production builds via `VITE_API_URL` (see `.env.example`).

## Build

```bash
npm run build        # tsc type-check + vite production build → dist/
```
