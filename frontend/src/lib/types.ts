// Hand-written types for endpoints whose FastAPI responses have no declared
// schema in the OpenAPI spec (so the generated client returns `unknown`).

export interface LoginResponse {
  access_token: string;
  user?: { id?: string; email?: string };
}

export interface KnowledgeBaseDoc {
  source: string;
  chunks: number;
  store: string;
}

export interface SkippedFile {
  file: string;
  reason: string;
}

export interface JobStatus {
  id: string;
  status: string;
  files_found: number;
  files_done: number;
  files_stored: number;
  chunks_total: number;
  current_file: string | null;
  skipped: SkippedFile[];
  log: string[];
  error: string | null;
  finished_at: string | null;
}
