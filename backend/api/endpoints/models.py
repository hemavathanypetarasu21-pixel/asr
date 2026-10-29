import logging

from api.schemas import ModelsResponse
from src.auth import CurrentUser
from src.config import settings
from src.services import translation_service, user_settings_service
from src.services.crypto_service import DecryptionError

logger = logging.getLogger(__name__)


async def list_models(user: CurrentUser | None) -> ModelsResponse:
    """Translation models are narrowed to those the caller's Gemini key can use, when that can be checked."""
    translation = settings.TRANSLATION_MODELS
    try:
        user_key = await user_settings_service.get_gemini_api_key(user.id) if user else None
        api_key = translation_service.resolve_api_key(user_key)
        available = await translation_service.available_models(api_key)
        translation = [model for model in translation if model.id in available] or translation
    except (translation_service.MissingApiKeyError, DecryptionError):
        pass  # No usable key yet: show the configured list.
    except Exception:
        # Filtering is best-effort: the dropdown must load even if Gemini cannot be reached.
        logger.exception("Could not list Gemini models; showing the configured list.")
    return ModelsResponse(recognition=settings.RECOGNITION_MODELS, translation=translation)
