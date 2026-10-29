"""Translates code-switched transcripts to English with Gemini."""

import hashlib
import time

from google import genai
from google.genai import errors, types

from src.config import settings

DIALECT_DESCRIPTIONS = {
    "manglish": "Manglish (Malaysian English mixed with Malay)",
    "tanglish": "Tanglish (Tamil mixed with English, often romanised)",
}

SYSTEM_INSTRUCTION = (
    "You translate transcripts of spoken, code-switched Malaysian speech into natural English. "
    "Keep names, places and meaning intact, keep the speaker's tone, and do not add explanations. "
    "Return only the English translation."
)


# sha256(api key) -> (expires_at, model ids usable with generateContent)
_available_models_cache: dict[str, tuple[float, frozenset[str]]] = {}


class TranslationError(Exception):
    pass


class InvalidApiKeyError(Exception):
    pass


class MissingApiKeyError(Exception):
    pass


def resolve_api_key(user_api_key: str | None) -> str:
    """The user's saved key wins; the server key is the fallback."""
    api_key = user_api_key or settings.GEMINI_API_KEY
    if not api_key:
        raise MissingApiKeyError("Add your Gemini API key in Settings to translate recordings.")
    return api_key


async def verify_api_key(api_key: str) -> None:
    """Makes a cheap authenticated call so an invalid key is rejected when it is saved."""
    try:
        async with genai.Client(api_key=api_key).aio as client:
            await client.models.list(config=types.ListModelsConfig(page_size=1))
    except errors.APIError as error:
        raise InvalidApiKeyError(error.message or "Gemini rejected this API key.") from error


async def available_models(api_key: str) -> frozenset[str]:
    """Model ids this key can call generateContent on, cached per key."""
    cache_key = hashlib.sha256(api_key.encode()).hexdigest()
    cached = _available_models_cache.get(cache_key)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    # Keep the client open while paging: an unreferenced client is closed before the pager finishes.
    async with genai.Client(api_key=api_key).aio as client:
        models = frozenset(
            [
                (model.name or "").removeprefix("models/")
                async for model in await client.models.list()
                if "generateContent" in (model.supported_actions or [])
            ]
        )
    _available_models_cache[cache_key] = (time.monotonic() + settings.GEMINI_MODEL_CACHE_SECONDS, models)
    return models


async def translate_to_english(transcript: str, dialect: str, model: str, api_key: str) -> str:
    if not transcript.strip():
        return ""
    prompt = f"The transcript is {DIALECT_DESCRIPTIONS[dialect]}.\n\nTranscript:\n{transcript}"
    try:
        async with genai.Client(api_key=api_key).aio as client:
            response = await client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=settings.GEMINI_TEMPERATURE,
                ),
            )
    except errors.APIError as error:
        raise TranslationError(f"Translation with {model} failed: {error.message or error.status}") from error

    translation = (response.text or "").strip()
    if not translation:
        raise TranslationError(f"{model} returned no translation.")
    return translation
