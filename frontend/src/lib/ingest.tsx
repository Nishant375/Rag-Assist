import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
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

const JOB_KEY = "ingest:jobId";

interface IngestState {
  staged: File[];
  addFiles: (files: File[]) => void;
  removeFile: (index: number) => void;
  job: JobStatus | undefined;
  busy: boolean;
  running: boolean;
  errorMsg: string;
  startIngest: () => Promise<void>;
  dismiss: () => void;
}

const IngestContext = createContext<IngestState | null>(null);

// Lives above the router so an in-flight (or finished) ingestion survives tab
// switches; jobId is persisted to localStorage so it also survives a refresh —
// on reload we resume polling /ingest/status/{jobId} and show the live state.
export function IngestProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [staged, setStaged] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(() => localStorage.getItem(JOB_KEY));

  const upload = useUploadIngestUploadPost();
  const store = useStoreIngestStoreUploadIdPost();

  const statusQuery = useStatusIngestStatusJobIdGet(jobId ?? "", {
    query: {
      enabled: !!jobId,
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

  // Persist the active job id so a refresh can resume showing it.
  useEffect(() => {
    if (jobId) localStorage.setItem(JOB_KEY, jobId);
    else localStorage.removeItem(JOB_KEY);
  }, [jobId]);

  // Refresh the KB list once ingestion finishes.
  useEffect(() => {
    if (job?.finished_at) {
      void qc.invalidateQueries({ queryKey: getListDocumentsDocumentsGetQueryKey() });
    }
  }, [job?.finished_at, qc]);

  const addFiles = useCallback((files: File[]) => {
    if (files.length) setStaged((s) => [...s, ...files]);
  }, []);

  const removeFile = useCallback((index: number) => {
    setStaged((s) => s.filter((_, i) => i !== index));
  }, []);

  const startIngest = useCallback(async () => {
    if (staged.length === 0 || busy) return;
    setJobId(null);
    const body = { files: staged } as unknown as BodyUploadIngestUploadPost;
    const up = (await upload.mutateAsync({ data: body })) as { upload_id: string };
    const started = (await store.mutateAsync({ uploadId: up.upload_id })) as IngestStarted;
    setStaged([]);
    setJobId(started.job_id);
  }, [staged, busy, upload, store]);

  const dismiss = useCallback(() => {
    setJobId(null);
    upload.reset();
    store.reset();
  }, [upload, store]);

  return (
    <IngestContext.Provider
      value={{ staged, addFiles, removeFile, job, busy, running, errorMsg, startIngest, dismiss }}
    >
      {children}
    </IngestContext.Provider>
  );
}

export function useIngest(): IngestState {
  const ctx = useContext(IngestContext);
  if (!ctx) throw new Error("useIngest must be used within IngestProvider");
  return ctx;
}
