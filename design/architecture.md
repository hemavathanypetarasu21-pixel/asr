context
We are working on a speech recognition application. The app records Manglish (Malay-English) and Tanglish (Tamil-English) speech, detects the dialect, and translates it to English.

user flow
    1. user logs in (Supabase email/password)
    2. chat page: user chooses language, mode and models, then speaks or uploads audio
    3. when speaking stops (or the upload finishes) the audio is saved to MongoDB - no processing yet
    4. insights page: every recording is listed as an accordion item
    5. user clicks "Analyse" on a recording -> transcribe, detect the dialect, translate to English
    6. the analysis result is saved on the recording and shown inside the accordion

data for future ML
    language (user-declared dialect) and mode (speaker nativeness) are stored with every recording.
    now:   language is a hint for transcription and is compared with the detected dialect.
    later: recordings + language + mode + detected dialect become the dataset for our own
           dialect models that take speaker nativeness into account.

frontend
A. Landing page
    1. nav bar
    2. hero section (highlighting Manglish & Tanglish support)
    3. features section
    4. footer

B. Auth
    1. login
    2. signup
    (Supabase email/password; /dashboard/* requires login)

C. Dashboard
    1. left sidebar
        a. upper div: logo + brand
        b. lower div (menu list):
            1. chat
            2. insights
        c. bottom: user avatar (initials) + name/email -> menu: settings, log out

    2. chat page
        a. dropdowns
            1. languages: Tanglish / Manglish
            2. modes: native speaker / non-native speaker
            3. dialect recognition model: Whisper tiny / medium
            4. translation model (Gemini, to English):
                gemini-2.5-flash-lite, gemini-2.5-flash, gemini-2.5-pro,
                gemini-3-flash-preview, gemini-3-pro-preview
            (both model lists come from backend env config, so they can change without code changes)
        b. buttons
            1. speak: start/stop microphone recording; saved to MongoDB on stop
            2. upload: sends an audio file; saved to MongoDB
            (record and speak are merged into "speak"; "send" is dropped - the app is speech only)
        c. list of recordings saved in this session (link to insights)

    3. insights page
        a. list of saved recordings (accordion, newest first)
        b. accordion header: file name / date, language, mode, analysis status
        c. accordion body:
            1. audio player
            2. analyse button
            3. analysis result: transcript, detected dialect, confidence,
               declared vs detected dialect match, English translation, models used
            4. delete

    4. settings page (from the avatar menu)
        a. profile: display name (Supabase user metadata), avatar initials
        b. appearance: theme light / dark / system (saved in MongoDB, cached locally)
        c. recording defaults: pre-selected chat dropdown values
        d. api keys: Gemini key, verified then stored encrypted in MongoDB (falls back to server key)
        e. security: change password, sign out of all devices

backend
    1. api (D:\asr\backend\api) - one file per UI control, in each of the 3 folders
        a. routers    - FastAPI APIRouter, paths only
        b. endpoints  - request handlers called by the routers
        c. schemas    - pydantic request/response models
        files:
            1. speak      - POST recorded mic audio, save recording
            2. upload     - POST audio file, save recording
            3. languages  - GET language options (tanglish, manglish)
            4. modes      - GET mode options (native, non_native)
            5. models     - GET dialect recognition + translation model options (from env config)
            6. recordings - GET list / GET audio / DELETE (feeds the insights page)
            7. analyse    - POST analyse a recording (transcription + dialect detection + translation)
            8. settings   - GET/PUT user preferences, PUT/DELETE encrypted Gemini API key

    2. src (D:\asr\backend\src) - logic
        a. config     - settings from environment variables
        b. db         - MongoDB connection (recordings collection, audio in GridFS)
        c. auth       - Supabase JWT verification (JWKS)
        d. services
            1. audio service        - decode / convert audio (ffmpeg)
            2. transcription service - Whisper transcription (chosen recognition model)
            3. dialect service      - Whisper language detection -> Manglish / Tanglish + confidence
            4. translation service  - translate transcript to English with the chosen Gemini model
            5. recording service    - save / list / delete recordings in MongoDB
            6. user settings service - preferences + encrypted API keys (crypto service, Fernet)

api endpoints
    POST   /speak                      save mic recording (+ language, mode, models)
    POST   /upload                     save uploaded file (+ language, mode, models)
    GET    /languages                  dropdown options
    GET    /modes                      dropdown options
    GET    /models                     dropdown options (recognition, translation)
    GET    /recordings?skip=&limit=    insights list
    GET    /recordings/{id}/audio      audio playback
    DELETE /recordings/{id}
    POST   /recordings/{id}/analyse    detect dialect + translate to English
    GET    /settings                   theme, recording defaults, API key status
    PUT    /settings/preferences       save theme + recording defaults
    PUT    /settings/api-keys/gemini   verify + save encrypted Gemini key
    DELETE /settings/api-keys/gemini
    every request carries the Supabase access token (Authorization: Bearer)

mongodb
    recordings collection
        user_id, source (speak / upload), file_name, audio_file_id (GridFS), duration,
        language, mode, recognition_model, translation_model, created_at,
        analysis: { transcript, detected_dialect, confidence, translation,
                    recognition_model, translation_model, analysed_at }
    user_settings collection (one per user)
        user_id, theme, defaults { language, mode, recognition_model, translation_model },
        gemini_api_key (Fernet-encrypted), gemini_api_key_hint (last 4), updated_at

## technology stack
backend:
    1. python
    2. fastapi
    3. uvicorn
    4. openai-whisper (transcription, dialect detection)
    5. google-genai sdk (Gemini translation)
    6. pymongo (async) + gridfs
    7. pyjwt (Supabase JWT verification)
    8. python-dotenv / pydantic-settings
    9. pydantic
    10. python-multipart
    11. httpx
    12. ffmpeg (audio decoding)

frontend:
framework:
    next.js (app router, built-in routing)

libraries:
    1. react
    2. tailwindcss
    3. axios
    4. react-hook-form
    5. zod
    6. @supabase/ssr + @supabase/supabase-js
    7. MediaRecorder API (speak)
