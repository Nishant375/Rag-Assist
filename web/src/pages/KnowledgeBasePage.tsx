import { useQueryClient } from "@tanstack/react-query";
import {
  useListDocumentsDocumentsGet,
  useDeleteDocumentDocumentsSourceDelete,
  getListDocumentsDocumentsGetQueryKey,
} from "@/api/generated/documents/documents";
import type { KnowledgeBaseDoc } from "@/lib/types";
import { getErrorMessage } from "@/lib/error";
import { Button } from "@/components/ui/Button";

export function KnowledgeBasePage() {
  const qc = useQueryClient();
  const { data, isLoading, isError, error, refetch, isFetching } = useListDocumentsDocumentsGet();
  const del = useDeleteDocumentDocumentsSourceDelete();

  const docs = (Array.isArray(data) ? data : []) as KnowledgeBaseDoc[];
  const errMsg = isError ? getErrorMessage(error) : "";

  async function remove(source: string) {
    if (!confirm(`Delete "${source}" from the knowledge base?`)) return;
    await del.mutateAsync({ source });
    void qc.invalidateQueries({ queryKey: getListDocumentsDocumentsGetQueryKey() });
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto py-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-gray-50">Knowledge base</h3>
          <p className="mb-4 text-[13px] text-muted">Documents currently embedded and searchable.</p>
        </div>
        <Button onClick={() => refetch()} loading={isFetching}>
          ↻ Refresh
        </Button>
      </div>

      {errMsg && (
        <div className="rounded-lg border border-red-900 bg-red-950/60 px-3.5 py-2.5 text-[13px] text-red-300">
          {errMsg}
        </div>
      )}

      {!isLoading && docs.length === 0 && !errMsg && (
        <div className="px-5 py-14 text-center text-faint">
          <div className="mb-4 text-[44px]">🗂️</div>
          <h2 className="mb-2 text-xl font-semibold text-gray-50">No documents yet</h2>
          <p className="mx-auto max-w-[380px] text-sm text-muted">
            Upload files in the <b>Documents</b> tab to build your knowledge base.
          </p>
        </div>
      )}

      {docs.map((d) => (
        <div key={d.source} className="card mt-2 flex items-center justify-between px-3.5 py-2.5">
          <span className="text-[13px] text-gray-200">📄 {d.source}</span>
          <span className="flex items-center gap-2 text-[11px] text-faint">
            {d.chunks != null ? `${d.chunks} chunks` : ""}
            {d.store ? ` · ${d.store}` : ""}
            <button
              className="rounded px-2 py-1 text-muted hover:bg-red-950 hover:text-red-300"
              onClick={() => remove(d.source)}
              aria-label="Delete"
              disabled={del.isPending}
            >
              🗑
            </button>
          </span>
        </div>
      ))}
    </div>
  );
}
