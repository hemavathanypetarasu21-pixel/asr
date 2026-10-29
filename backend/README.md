# ASR Backend

FastAPI backend for recording Manglish / Tanglish speech, detecting the dialect, and translating it to English.

## Setup

Requires Python 3.10+, MongoDB, and ffmpeg/ffprobe on `PATH` (or set `FFMPEG_BINARY` / `FFPROBE_BINARY`).

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in values; every variable is required
python server.py       # host/port/reload from .env (SERVER_*)
```

## Structure

```
app.py               FastAPI app factory: CORS, routers, MongoDB lifespan
server.py            entry point: runs uvicorn with SERVER_* settings
api/routers/         APIRouter per UI control (paths only)
api/endpoints/       request handlers called by the routers
api/schemas/         pydantic request/response models
src/config/          settings from environment variables
src/db/              MongoDB (recordings collection, audio in GridFS)
src/auth/            Supabase JWT verification (JWKS)
src/services/        audio, recording, Whisper, dialect, translation and analysis logic
```

## Endpoints

All `/speak`, `/upload` and `/recordings*` routes require `Authorization: Bearer <Supabase access token>`.

| Method | Path | Notes |
|---|---|---|
| GET | `/languages` | Manglish / Tanglish |
| GET | `/modes` | native / non_native |
| GET | `/models` | `RECOGNITION_MODELS` / `TRANSLATION_MODELS` from env |
| POST | `/speak` | multipart: `file`, `language`, `mode`, `recognition_model`, `translation_model` |
| POST | `/upload` | same fields as `/speak` |
| GET | `/recordings?skip=&limit=` | `{ items, total, analysed }`, newest first |
| GET | `/recordings/{id}/audio` | audio stream |
| DELETE | `/recordings/{id}` | removes record and audio |
| POST | `/recordings/{id}/analyse` | transcribe + detect dialect (Whisper) + translate to English (Gemini) |
| GET | `/health` | liveness |

## Analysis

1. Audio is decoded to 16 kHz mono with ffmpeg.
2. Dialect: Whisper language probabilities are averaged over up to `DIALECT_DETECTION_MAX_WINDOWS` 30-second windows.
   Malay (`ms`, plus `id`, which Whisper often assigns to Malay) counts for Manglish; Tamil (`ta`) for Tanglish.
   Confidence is the winner's share of Malay + Tamil. No dialect is reported below `DIALECT_DETECTION_MIN_CONFIDENCE`
   or `DIALECT_DETECTION_MIN_MARGIN`.
3. Transcript: Whisper with a code-switched prompt for the declared language.
4. Translation: Gemini (`translation_model`) translates the transcript to English.

Whisper models download on first use (`tiny` ~72 MB, `medium` ~1.5 GB) and run one at a time.

Interactive docs: `http://<SERVER_HOST>:<SERVER_PORT>/docs`.
