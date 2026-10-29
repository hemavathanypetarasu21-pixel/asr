# ASR Studio — v1

Speech recognition for Malaysian code-switched speech. Record or upload **Manglish** (Malay + English) or **Tanglish** (Tamil + English) audio, then analyse it to get a transcript, the detected dialect with a confidence score, and an English translation.

## v1 features

| Area | What it does |
|---|---|
| **Landing page** | Product overview, dialect examples, features, how it works |
| **Auth** | Supabase email/password sign-up and login; `/dashboard` requires a session |
| **Chat** | Speak (microphone) or upload audio; choose language, speaker mode (native / non-native), dialect recognition model and translation model. Recordings are saved to MongoDB. |
| **Insights** | Every recording in an accordion: playback, **Analyse** (transcript, detected dialect, confidence, declared-vs-detected match, English translation), model override, remove |
| **Settings** | Display name and avatar, theme (light / dark / system), recording defaults, Gemini API key (verified, stored encrypted), password change, sign out everywhere |

### How analysis works

1. **Dialect** — Whisper language probabilities over up to N 30-second windows; Malay (`ms`, `id`) → Manglish, Tamil (`ta`) → Tanglish.
2. **Transcript** — Whisper, primed with a code-switched prompt for the declared language.
3. **Translation** — Gemini translates the transcript to English. If Gemini is unavailable (no key, no credits, retired model), Whisper translates the audio locally instead and a note explains why.

The declared language and speaker mode are stored with every recording as a dataset for future dialect models that account for speaker nativeness.

## Architecture

```
frontend/   Next.js 16 (App Router), React 19, Tailwind 4, axios, react-hook-form + zod, Supabase SSR
backend/    FastAPI, MongoDB (PyMongo async + GridFS), Supabase JWT (JWKS), openai-whisper, google-genai
design/     architecture.md (source of truth for structure), agent-rules.md
```

Backend layout: `api/{routers,endpoints,schemas}` has one module per UI control (`speak`, `upload`, `languages`, `modes`, `models`, `recordings`, `analyse`, `settings`); logic lives in `src/{config,db,auth,services}`. See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for endpoints and the API contract.

## Requirements

- Node.js 24+ and pnpm
- Python 3.10+
- MongoDB (local or Atlas)
- ffmpeg and ffprobe on `PATH`
- A Supabase project (email/password auth enabled)
- Optional: a Gemini API key from [AI Studio](https://aistudio.google.com/apikey); without one, translation falls back to Whisper

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env        # fill in every value; generate ENCRYPTION_KEY as described in the file
python server.py            # host/port from SERVER_HOST / SERVER_PORT

# Frontend (new terminal)
cd frontend
pnpm install
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL to the backend URL, plus Supabase URL and key
pnpm dev                    # http://localhost:3000
```

All configuration comes from environment variables; both apps refuse to start if a required one is missing.

## Known limitations (v1)

- Whisper `medium` is slow on CPU; long clips may exceed `NEXT_PUBLIC_API_TIMEOUT_MS`.
- Whisper's fallback translation is rougher than Gemini's.
- Gemini model availability changes; the translation dropdown only shows models the user's key can list, but a listed model can still be retired for new users.
- Dialect thresholds (`DIALECT_DETECTION_*`) are starting values and need tuning on real recordings.

## Roadmap

- Train dialect models on the collected recordings, using declared language and speaker nativeness.
- Live (streaming) transcription while speaking.
