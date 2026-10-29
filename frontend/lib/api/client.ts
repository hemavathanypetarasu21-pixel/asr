import axios, { isAxiosError } from "axios";
import { env } from "@/lib/env";
import { createClient } from "@/lib/supabase/client";

export const apiClient = axios.create({
  baseURL: env.apiUrl,
  timeout: env.apiTimeoutMs,
});

// Forward the Supabase access token so the backend can identify the user.
apiClient.interceptors.request.use(async (config) => {
  const { data } = await createClient().auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.code === "ECONNABORTED") return "The request timed out. Try a shorter clip.";
    if (!error.response) return "The speech recognition API is unreachable.";
  }
  return fallback;
}
