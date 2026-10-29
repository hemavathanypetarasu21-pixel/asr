"""Field validators shared by schemas that reference configured model ids."""

from src.config import settings


def known_recognition_model(value: str | None) -> str | None:
    if value is not None and value not in {model.id for model in settings.RECOGNITION_MODELS}:
        raise ValueError("Unknown dialect recognition model.")
    return value


def known_translation_model(value: str | None) -> str | None:
    if value is not None and value not in {model.id for model in settings.TRANSLATION_MODELS}:
        raise ValueError("Unknown translation model.")
    return value
