import axios, { type AxiosRequestConfig, type AxiosError } from "axios";

// Base URL: in dev, "/api" is proxied to the backend by Vite; in prod set
// VITE_API_URL to the deployed API origin.
const baseURL = import.meta.env.VITE_API_URL || "/api";

export const axiosInstance = axios.create({ baseURL });

// Read the token from the persisted Zustand auth store ({ state: { token } }).
// Reading storage directly avoids a circular import with the store module.
function getToken(): string | null {
  try {
    const raw = localStorage.getItem("auth");
    return raw ? (JSON.parse(raw)?.state?.token ?? null) : null;
  } catch {
    return null;
  }
}

// Attach the bearer token (if any) to every request.
axiosInstance.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, drop the stale token so the app falls back to the login screen.
axiosInstance.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear the persisted Zustand auth store and bounce to login.
      // (Direct storage write avoids a circular import with the store.)
      localStorage.removeItem("auth");
      if (!location.pathname.startsWith("/login")) {
        location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

// Orval calls this for every operation.
export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  // For file uploads Orval hard-codes `Content-Type: multipart/form-data`, which
  // omits the boundary and makes the server reject the body ("Missing boundary").
  // Drop it so the browser sets multipart/form-data with the correct boundary.
  if (config.data instanceof FormData && config.headers) {
    delete (config.headers as Record<string, unknown>)["Content-Type"];
  }
  return axiosInstance({ ...config }).then((r) => r.data);
};

export default customInstance;
