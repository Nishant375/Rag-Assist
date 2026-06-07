import { AxiosError } from "axios";

// Extract a human-readable message from an API error. FastAPI puts the useful
// text in response.data.detail; fall back to the axios/Error message.
export function getErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (err instanceof AxiosError) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
