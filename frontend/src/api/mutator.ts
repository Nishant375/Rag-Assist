import axios, { type AxiosRequestConfig, type AxiosError } from "axios";

// Base URL: in dev, "/api" is proxied to the backend by Vite; in prod set
// VITE_API_URL to the deployed API origin.
const baseURL = import.meta.env.VITE_API_URL || "/api";

export const axiosInstance = axios.create({ baseURL });

// Attach the bearer token (if any) to every request.
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
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
      localStorage.removeItem("token");
      localStorage.removeItem("email");
      if (!location.pathname.startsWith("/login")) {
        location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

// Orval calls this for every operation.
export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return axiosInstance({ ...config }).then((r) => r.data);
};

export default customInstance;
