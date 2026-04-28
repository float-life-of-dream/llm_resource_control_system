import axios, { AxiosError, AxiosHeaders, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const ACCESS_TOKEN_KEY = "ai-monitor.access-token";
const REFRESH_TOKEN_KEY = "ai-monitor.refresh-token";

let refreshPromise: Promise<string | null> | null = null;

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export const http = axios.create({
  baseURL,
  timeout: 8000,
});

function toApiError(error: AxiosError) {
  const payload = error.response?.data as { message?: string; description?: string } | undefined;
  return new Error(payload?.message || payload?.description || error.message);
}

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers ?? new AxiosHeaders();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (error.response?.status !== 401 || originalRequest?._retry || !originalRequest) {
      return Promise.reject(toApiError(error));
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      return Promise.reject(toApiError(error));
    }

    originalRequest._retry = true;
    if (!refreshPromise) {
      refreshPromise = axios
        .post(`${baseURL}/auth/refresh`, { refreshToken })
        .then((response: AxiosResponse<{ accessToken: string; refreshToken: string }>) => {
          setTokens(response.data.accessToken, response.data.refreshToken);
          return response.data.accessToken as string;
        })
        .catch(() => {
          clearTokens();
          return null;
        })
        .finally(() => {
          refreshPromise = null;
        });
    }

    const accessToken = await refreshPromise;
    if (!accessToken) {
      return Promise.reject(toApiError(error));
    }

    originalRequest.headers = originalRequest.headers ?? new AxiosHeaders();
    originalRequest.headers.Authorization = `Bearer ${accessToken}`;
    return http(originalRequest);
  },
);
