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

  const upload = useUploadIngestUploadPost();
  const store = useStoreIngestStoreUploadIdPost();

  const statusQuery = useStatusIngestStatusJobIdGet(jobId ?? "", {
    query: {
      enabled: !!jobId,
      refetchInterval: (q) => {
        const j = q.state.data as JobStatus | undefined;
        return j?.finished_at ? false : 1500;
      },
    },
  });
  const job = statusQuery.data as JobStatus | undefined;
  const busy = upload.isPending || store.isPending || (!!jobId && !job?.finished_at);
  const rawErr = upload.error ?? store.error;
  const errorMsg = rawErr ? getErrorMessage(rawErr, "Upload failed") : "";

  // Refresh the KB list only once ingestion actually FINISHES (not when it starts),
  // so newly-stored documents show up without a manual refresh.
  const refreshedRef = useRef<string | null>(null);
  useEffect(() => {
    if (job?.finished_at && refreshedRef.current !== jobId) {
      refreshedRef.current = jobId;
      void qc.invalidateQueries({ queryKey: getListDocumentsDocumentsGetQueryKey() });
    }
  }, [job?.finished_at, jobId, qc]);

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
    if (staged.length === 0) return;
    setJobId(null);
    // BodyUploadIngestUploadPost types `files` as string[], but the generated
    // client appends them to FormData — File objects are correct at runtime.
    const body = { files: staged } as unknown as BodyUploadIngestUploadPost;
    const up = (await upload.mutateAsync({ data: body })) as { upload_id: string };
    const started = (await store.mutateAsync({ uploadId: up.upload_id })) as IngestStarted;
    setStaged([]);
    refreshedRef.current = null;
    setJobId(started.job_id);
  }

  const pct = job?.files_found ? Math.round((job.files_done / job.files_found) * 100) : 0;

  return (
    <div className="min-h-0 flex-1 overflow-y-auto py-5">
      <h3 className="mb-1 text-[15px] font-semibold text-gray-50">Upload documents</h3>
      <p className="mb-4 text-[13px] text-muted">
        PDF, DOCX, PPTX, TXT, or MD. They'll be embedded and added to your knowledge base.
        Scanned PDFs and images inside documents are read via OCR.
      </p>

      <div
        className={`cursor-pointer rounded-2xl border-2 border-dashed bg-panel px-6 py-10 text-center transition ${
          drag ? "border-brand" : "border-border"
        }`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
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

      {staged.map((f, i) => (
        <div key={i} className="card mt-2 flex items-center justify-between px-3.5 py-2.5">
          <span className="text-[13px] text-gray-200">📄 {f.name}</span>
          <span className="flex items-center gap-2 text-[11px] text-faint">
            {fmtSize(f.size)}
            <button
              className="rounded px-2 py-1 text-muted hover:bg-red-950 hover:text-red-300"
              onClick={() => setStaged((s) => s.filter((_, j) => j !== i))}
              aria-label="Remove"
            >
              ✕
            </button>
          </span>
        </div>
      ))}

      {staged.length > 0 && (
        <Button variant="primary" className="mt-4" onClick={ingest} loading={busy}>
          Ingest {staged.length} file(s)
        </Button>
      )}

      {job && (
        <>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-panel">
            <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-2 text-[13px] text-muted">
            {job.status} · stored {job.files_stored ?? 0}/{job.files_found} files · {job.chunks_total} chunks
            {job.current_file ? ` · ${job.current_file}` : ""}
          </p>

          {/* Done, but stored nothing → make the silent skip loud. */}
          {job.finished_at && (job.files_stored ?? 0) === 0 && !job.error && (
            <div className="mt-2 rounded-lg border border-amber-900 bg-amber-950/50 px-3.5 py-2.5 text-[13px] text-amber-300">
              ⚠️ No documents were added — no readable text could be extracted. If this is a
              scanned/image PDF, OCR may have failed or the page is blank.
            </div>
          )}

          {/* Per-file skips. */}
          {job.skipped?.length > 0 && (
            <div className="mt-2 rounded-lg border border-amber-900 bg-amber-950/40 px-3.5 py-2.5 text-[13px] text-amber-300">
              <div className="mb-1 font-medium">Skipped {job.skipped.length} file(s):</div>
              <ul className="list-inside list-disc">
                {job.skipped.map((s) => (
                  <li key={s.file}>
                    {s.file} — {s.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {job.error && (
            <div className="mt-2 rounded-lg border border-red-900 bg-red-950/60 px-3.5 py-2.5 text-[13px] text-red-300">
              {job.error}
            </div>
          )}
          {job.log?.length > 0 && (
            <pre className="mt-3.5 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-[#0b1220] p-3 font-mono text-xs text-muted">
              {job.log.join("\n")}
            </pre>
          )}
        </>
      )}
    </div>
  );
}
