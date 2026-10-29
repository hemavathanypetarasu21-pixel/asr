from datetime import datetime

from pydantic import BaseModel, field_validator

from .languages import Language
from .model_validators import known_recognition_model, known_translation_model


class AnalyseRequest(BaseModel):
    """Optional model overrides; omitted fields use the models saved with the recording."""

    recognition_model: str | None = None
    translation_model: str | None = None

    _check_recognition_model = field_validator("recognition_model")(known_recognition_model)
    _check_translation_model = field_validator("translation_model")(known_translation_model)


class AnalysisResponse(BaseModel):
    transcript: str
    detected_dialect: Language | None
    confidence: float | None
    translation: str | None
    # Set when Gemini could not translate and Whisper's local translation was used instead.
    translation_error: str | None = None
    recognition_model: str
    translation_model: str
    analysed_at: datetime
