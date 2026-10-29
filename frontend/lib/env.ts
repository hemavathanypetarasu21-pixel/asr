import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_APP_NAME: z.string().min(1),
  NEXT_PUBLIC_API_URL: z.url(),
  NEXT_PUBLIC_API_TIMEOUT_MS: z.coerce.number().int().positive(),
  NEXT_PUBLIC_MAX_AUDIO_UPLOAD_MB: z.coerce.number().positive(),
  NEXT_PUBLIC_SUPABASE_URL: z.url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
});

// NEXT_PUBLIC_* values are inlined at build time, so each must be referenced explicitly.
const parsed = envSchema.safeParse({
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_API_TIMEOUT_MS: process.env.NEXT_PUBLIC_API_TIMEOUT_MS,
  NEXT_PUBLIC_MAX_AUDIO_UPLOAD_MB: process.env.NEXT_PUBLIC_MAX_AUDIO_UPLOAD_MB,
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
});

if (!parsed.success) {
  const fields = parsed.error.issues.map((issue) => issue.path.join(".")).join(", ");
  throw new Error(`Invalid or missing environment variables: ${fields}. See .env.example.`);
}

export const env = {
  appName: parsed.data.NEXT_PUBLIC_APP_NAME,
  apiUrl: parsed.data.NEXT_PUBLIC_API_URL.replace(/\/$/, ""),
  apiTimeoutMs: parsed.data.NEXT_PUBLIC_API_TIMEOUT_MS,
  maxAudioUploadBytes: parsed.data.NEXT_PUBLIC_MAX_AUDIO_UPLOAD_MB * 1024 * 1024,
  maxAudioUploadMb: parsed.data.NEXT_PUBLIC_MAX_AUDIO_UPLOAD_MB,
  supabaseUrl: parsed.data.NEXT_PUBLIC_SUPABASE_URL,
  supabaseAnonKey: parsed.data.NEXT_PUBLIC_SUPABASE_ANON_KEY,
} as const;
