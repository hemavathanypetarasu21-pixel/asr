"""Analyse a saved recording: Whisper transcription + dialect detection, then Gemini translation."""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from whisper import Whisper

from src.config import settings
from src.services import dialect_service, recording_service, translation_service, user_settings_service, whisper_service
from src.services.crypto_service import DecryptionError

# Example code-switched text primes Whisper to keep both languages as spoken (keyed by declared language).
TRANSCRIPTION_PROMPTS = {
    "manglish": "Eh, you dah makan ke? Jom kita pergi mamak after this meeting lah.",
    "tanglish": "Machan, naan office la irukken, I'll call you back. Enna panra?",
}


WHISPER_TRANSLATION_PREFIX = "whisper-"


async def _translate(
    user_id: str,
    transcript: str,
    dialect: str,
    gemini_model: str,
    whisper_model: Whisper,
    whisper_model_id: str,
    audio: np.ndarray,
) -> tuple[str, str, str | None]:
    """Returns (translation, model used, note). Gemini is preferred; if it cannot be used
    (no key, no credits, retired model) Whisper translates the audio locally instead."""
    try:
        api_key = translation_service.resolve_api_key(await user_settings_service.get_gemini_api_key(user_id))
        return await translation_service.translate_to_english(transcript, dialect, gemini_model, api_key), gemini_model, None
    except (translation_service.MissingApiKeyError, translation_service.TranslationError, DecryptionError) as error:
        translation = await asyncio.to_thread(whisper_service.translate_to_english, whisper_model, audio)
        return translation, f"{WHISPER_TRANSLATION_PREFIX}{whisper_model_id}", f"Translated with Whisper because Gemini was unavailable: {error}"


async def analyse(
    user_id: str,
    recording_id: str,
    recognition_model: str | None = None,
    translation_model: str | None = None,
) -> dict:
    """Runs the analysis, stores it on the recording, and returns the updated document.

    Model arguments override the ones saved with the recording (e.g. when a model is retired).
    """
    document = await recording_service.get_recording(user_id, recording_id)
    recognition_model = recognition_model or document["recognition_model"]
    translation_model = translation_model or document["translation_model"]

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audio"
        await recording_service.download_audio(document, path)
        audio = await asyncio.to_thread(whisper_service.decode_audio, path)

    model = await asyncio.to_thread(whisper_service.get_model, recognition_model)
    probabilities = await asyncio.to_thread(
        whisper_service.language_probabilities, model, audio, settings.DIALECT_DETECTION_MAX_WINDOWS
    )
    detected = dialect_service.classify(probabilities)
    transcript = await asyncio.to_thread(
        whisper_service.transcribe, model, audio, TRANSCRIPTION_PROMPTS[document["language"]]
    )
    translation, translation_model_used, translation_note = await _translate(
        user_id,
        transcript,
        detected.dialect or document["language"],
        translation_model,
        model,
        recognition_model,
        audio,
    )

    analysis = {
        "transcript": transcript,
        "detected_dialect": detected.dialect,
        "confidence": detected.confidence,
        "translation": translation,
        "translation_error": translation_note,
        "recognition_model": recognition_model,
        "translation_model": translation_model_used,
        "analysed_at": datetime.now(timezone.utc),
    }
    return await recording_service.save_analysis(user_id, recording_id, analysis)
