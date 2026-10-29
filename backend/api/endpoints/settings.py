from fastapi import HTTPException, status

from api.schemas import ApiKeyStatus, ApiKeyUpdate, PreferencesUpdate, RecordingDefaults, SettingsResponse, Theme
from src.auth import CurrentUser
from src.config import settings as app_settings
from src.services import translation_service, user_settings_service


def _current_defaults(saved: dict | None) -> RecordingDefaults:
    """Drops saved defaults that point at models no longer configured."""
    saved = dict(saved or {})
    configured = {
        "recognition_model": {model.id for model in app_settings.RECOGNITION_MODELS},
        "translation_model": {model.id for model in app_settings.TRANSLATION_MODELS},
    }
    for field, ids in configured.items():
        if saved.get(field) not in ids:
            saved[field] = None
    return RecordingDefaults.model_validate(saved)


def _to_response(document: dict) -> SettingsResponse:
    hint = document.get("gemini_api_key_hint")
    if document.get("gemini_api_key"):
        key_status = ApiKeyStatus(configured=True, source="user", hint=hint)
    elif app_settings.GEMINI_API_KEY:
        key_status = ApiKeyStatus(configured=True, source="server", hint=None)
    else:
        key_status = ApiKeyStatus(configured=False, source=None, hint=None)
    return SettingsResponse(
        theme=document.get("theme", Theme.SYSTEM),
        defaults=_current_defaults(document.get("defaults")),
        gemini_api_key=key_status,
    )


async def get_settings(user: CurrentUser) -> SettingsResponse:
    return _to_response(await user_settings_service.get_settings(user.id))


async def update_preferences(user: CurrentUser, update: PreferencesUpdate) -> SettingsResponse:
    document = await user_settings_service.update_preferences(user.id, update.model_dump(mode="json"))
    return _to_response(document)


async def save_gemini_api_key(user: CurrentUser, update: ApiKeyUpdate) -> SettingsResponse:
    api_key = update.api_key.get_secret_value().strip()
    try:
        await translation_service.verify_api_key(api_key)
    except translation_service.InvalidApiKeyError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Gemini rejected this API key: {error}") from error
    return _to_response(await user_settings_service.set_gemini_api_key(user.id, api_key))


async def delete_gemini_api_key(user: CurrentUser) -> SettingsResponse:
    return _to_response(await user_settings_service.delete_gemini_api_key(user.id))
