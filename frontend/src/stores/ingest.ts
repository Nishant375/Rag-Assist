import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import {
  uploadIngestUploadPost,
  storeIngestStoreUploadIdPost,
} from "@/api/generated/ingest/ingest";
import type { BodyUploadIngestUploadPost, IngestStarted } from "@/api/generated/model";
import { getErrorMessage } from "@/lib/error";

interface IngestState {
  staged: File[];
  jobId: string | null;
  uploading: boolean;
  error: string;
  addFiles: (files: File[]) => void;
  removeFile: (index: number) => void;
  startIngest: () => Promise<void>;
  dismiss: () => void;
  reset: () => void;
}

export const useIngestStore = create<IngestState>()(
  persist(
    (set, get) => ({
      staged: [],
      jobId: null,
      uploading: false,
      error: "",
      addFiles: (files) => {
        if (files.length) set((s) => ({ staged: [...s.staged, ...files] }));
      },
      removeFile: (index) => set((s) => ({ staged: s.staged.filter((_, i) => i !== index) })),
      startIngest: async () => {
        const { staged, uploading } = get();
        if (staged.length === 0 || uploading) return;
        set({ uploading: true, error: "", jobId: null });
        try {
          const body = { files: staged } as unknown as BodyUploadIngestUploadPost;
          const up = (await uploadIngestUploadPost(body)) as { upload_id: string };
          const started = (await storeIngestStoreUploadIdPost(up.upload_id)) as IngestStarted;
          set({ jobId: started.job_id, staged: [], uploading: false });
        } catch (err) {
          set({ error: getErrorMessage(err, "Upload failed"), uploading: false });
        }
      },
      dismiss: () => set({ jobId: null, error: "" }),
      reset: () => set({ staged: [], jobId: null, uploading: false, error: "" }),
    }),
    {
      name: "ingest",
      storage: createJSONStorage(() => localStorage),
      // Persist only the job id — File objects aren't serializable.
      partialize: (s) => ({ jobId: s.jobId }),
    }
  )
);
