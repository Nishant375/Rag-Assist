import { useState, useRef, useEffect, type ChangeEvent, type DragEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  useUploadIngestUploadPost,
  useStoreIngestStoreUploadIdPost,
  useStatusIngestStatusJobIdGet,
} from "@/api/generated/ingest/ingest";
import { getListDocumentsDocumentsGetQueryKey } from "@/api/generated/documents/documents";
import type { BodyUploadIngestUploadPost, IngestStarted } from "@/api/generated/model";
import type { JobStatus } from "@/lib/types";
import { getErrorMessage } from "@/lib/error";
import { Button } from "@/components/ui/Button";

const ACCEPT = /\.(pdf|docx|pptx|txt|md)$/i;

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function DocumentsPage() {
  const qc = useQueryClient();
  const [staged, setStaged] = useState<File[]>([]);
  const [drag, setDrag] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const logRef = useRef<HTMLPreElement>(null);

  const upload = useUploadIngestUploadPost();
  const store = useStoreIngestStoreUploadIdPost();

  const statusQuery = useStatusIngestStatusJobIdGet(jobId ?? "", {
    query: {
      enabled: !!jobId,
      // Poll every second for a live feel until the job finishes.
      refetchInterval: (q) => {
        const j = q.state.data as JobStatus | undefined;
        return j?.finished_at ? false : 1000;
      },
    },
  });
  const job = statusQuery.data as JobStatus | undefined;
  const running = !!jobId && !job?.finished_at;
  const busy = upload.isPending || store.isPending || running;
  const rawErr = upload.error ?? store.error;
  const errorMsg = rawErr ? getErrorMessage(rawErr, "Upload failed") : "";

  // Auto-refresh the KB list once ingestion actually finishes.
  const refreshedRef = useRef<string | null>(null);
  useEffect(() => {
    if (job?.finished_at && refreshedRef.current !== jobId) {
      refreshedRef.current = jobId;
      void qc.invalidateQueries({ queryKey: getListDocumentsDocumentsGetQueryKey() });
    }
  }, [job?.finished_at, jobId, qc]);

  // Keep the live log scrolled to the latest line.
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [job?.log?.length]);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const accepted = Array.from(list).filter((f) => ACCEPT.test(f.name));
    setStaged((s) => [...s, ...accepted]);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDrag(false);
    addFiles(e.dataTransfer.files);
  }

  async function ingest() {
    if (staged.length === 0 || busy) return;
    setJobId(null);
    refreshedRef.current = null;
    const body = { files: staged } as unknown as BodyUploadIngestUploadPost;
    const up = (await upload.mutateAsync({ data: body })) as { upload_id: string };
    const started = (await store.mutateAsync({ uploadId: up.upload_id })) as IngestStarted;
    setStaged([]);
    setJobId(started.job_id);
  }

  // Human-readable phase for the live status banner.
  const phase = upload.isPending
    ? "Uploading files…"
    : store.isPending
      ? "Starting ingestion…"
      : running
        ? `Processing${job?.current_file ? ` ${job.current_file}` : ""} (${job?.files_done ?? 0}/${job?.files_found ?? 0})…`
        : job?.finished_at
          ? "Done"
          : "";

  const pct = job?.files_found ? Math.round((job.files_done / job.files_found) * 100) : upload.isPending ? 15 : 0;

  return (
    <div className="min-h-0 flex-1 overflow-y-auto py-5">
      <h3 className="mb-1 text-[15px] font-semibold text-gray-50">Upload documents</h3>
      <p className="mb-4 text-[13px] text-muted">
        PDF, DOCX, PPTX, TXT, or MD. They'll be embedded and added to your knowledge base.
        Scanned PDFs and images inside documents are read via OCR.
      </p>

      <div
        className={`rounded-2xl border-2 border-dashed bg-panel px-6 py-10 text-center transition ${
          drag ? "border-brand" : "border-border"
        } ${busy ? "pointer-events-none opacity-60" : "cursor-pointer"}`}
        onClick={() => !busy && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!busy) setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => !busy && onDrop(e)}
      >
        <div className="mb-2.5 text-4xl">📂</div>
        <div className="text-base font-semibold text-gray-50">Drag &amp; drop or click to browse</div>
        <div className="mt-1 text-xs text-faint">PDF · DOCX · PPTX · TXT · MD</div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.pptx,.txt,.md"
          className="hidden"
          onChange={(e: ChangeEvent<HTMLInputElement>) => addFiles(e.target.files)}
        />
      </div>

      {errorMsg && (
        <div className="mt-3.5 rounded-lg border border-red-900 bg-red-950/60 px-3.5 py-2.5 text-[13px] text-red-300">
          {errorMsg}
        </div>
      )}

      {/* Staged files (before ingest) */}
      {staged.map((f, i) => (
        <div key={i} className="card mt-2 flex items-center justify-between px-3.5 py-2.5">
          <span className="text-[13px] text-gray-200">📄 {f.name}</span>
          <span className="flex items-center gap-2 text-[11px] text-faint">
            {fmtSize(f.size)}
            <button
              className="rounded px-2 py-1 text-muted hover:bg-red-950 hover:text-red-300 disabled:opacity-40"
              onClick={() => setStaged((s) => s.filter((_, j) => j !== i))}
              disabled={busy}
              aria-label="Remove"
            >
              ✕
            </button>
          </span>
        </div>
      ))}

      {staged.length > 0 && (
        <Button variant="primary" className="mt-4" onClick={ingest} loading={busy}>
          {busy ? "Working…" : `Upload & ingest ${staged.length} file(s)`}
        </Button>
      )}

      {/* ── Live status panel ───────────────────────────────────────────── */}
      {(busy || job) && (
        <div className="card mt-4 p-4">
          <div className="mb-2 flex items-center gap-2 text-[13px] font-medium text-gray-100">
            {busy && <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand/40 border-t-brand" />}
            <span>{phase}</span>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-bg">
            <div
              className={`h-full rounded-full transition-all ${busy ? "bg-brand" : "bg-green-600"}`}
              style={{ width: `${busy && pct < 10 ? 10 : pct}%` }}
            />
          </div>

          {job && (
            <p className="mt-2 text-[12px] text-muted">
              stored {job.files_stored ?? 0}/{job.files_found} files · {job.chunks_total} chunks
            </p>
          )}

          {/* Finished but nothing stored */}
          {job?.finished_at && (job.files_stored ?? 0) === 0 && !job.error && (
            <div className="mt-2 rounded-lg border border-amber-900 bg-amber-950/50 px-3.5 py-2.5 text-[13px] text-amber-300">
              ⚠️ No documents were added — no readable text could be extracted. If this is a
              scanned/image PDF, OCR may have failed or the page is blank.
            </div>
          )}

          {/* Per-file skips */}
          {job?.skipped?.length ? (
            <div className="mt-2 rounded-lg border border-amber-900 bg-amber-950/40 px-3.5 py-2.5 text-[13px] text-amber-300">
              <div className="mb-1 font-medium">Skipped {job.skipped.length} file(s):</div>
              <ul className="list-inside list-disc">
                {job.skipped.map((s) => (
                  <li key={s.file}>{s.file} — {s.reason}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {job?.error && (
            <div className="mt-2 rounded-lg border border-red-900 bg-red-950/60 px-3.5 py-2.5 text-[13px] text-red-300">
              {job.error}
            </div>
          )}

          {/* Live streaming log */}
          {job?.log?.length ? (
            <pre
              ref={logRef}
              className="mt-3 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-[#0b1220] p-3 font-mono text-xs text-muted"
            >
              {job.log.join("\n")}
            </pre>
          ) : null}

          {job?.finished_at && (job.files_stored ?? 0) > 0 && (
            <div className="mt-2 rounded-lg border border-green-900 bg-green-950/40 px-3.5 py-2.5 text-[13px] text-green-300">
              ✅ Added {job.files_stored} file(s) · {job.chunks_total} chunks. See the Knowledge Base tab.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
