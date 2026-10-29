# ASR Frontend

Next.js 16 (App Router) frontend for Manglish / Tanglish speech-to-text.

## Setup

```bash
pnpm install
cp .env.example .env.local   # fill in values
pnpm dev
```

All configuration is read from environment variables and validated in `lib/env.ts`; the app fails fast if any are missing.

## Structure

```
app/                 routes (landing, auth, dashboard chat + insights)
components/          UI grouped by feature
lib/api/             axios client, endpoints, API types
lib/supabase/        browser + server Supabase clients
lib/audio/           microphone recorder hook
proxy.ts             session refresh + /dashboard protection
```

## Auth

Supabase email/password. `proxy.ts` redirects signed-out users from `/dashboard/*` to `/auth/login`.
Every API request sends `Authorization: Bearer <supabase access token>`; the backend must verify it.

## Backend API contract

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/languages` | — | `Option[]` |
| GET | `/modes` | — | `Option[]` |
| GET | `/models` | — | `{ recognition: Option[], translation: Option[] }` |
| POST | `/speak` | multipart `file`, `language`, `mode`, `recognition_model`, `translation_model` | `Recording` |
| POST | `/upload` | same as `/speak` | `Recording` |
| GET | `/recordings?skip=&limit=` | — | `{ items: Recording[], total, analysed }` |
| GET | `/recordings/{id}/audio` | — | audio bytes |
| DELETE | `/recordings/{id}` | — | 204 |
| POST | `/recordings/{id}/analyse` | — | `Recording` (with `analysis`) |

Shapes are defined in `lib/api/types.ts`. Errors return FastAPI's `{ "detail": "message" }`.
