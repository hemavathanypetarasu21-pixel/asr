from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator

from .analyse import AnalysisResponse
from .languages import Language
from .model_validators import known_recognition_model, known_translation_model
from .modes import Mode


class RecordingSource(str, Enum):
    SPEAK = "speak"
    UPLOAD = "upload"


class RecordingFields(BaseModel):
    """Choices from the chat page, stored with every recording."""

    language: Language
    mode: Mode
    recognition_model: str
    translation_model: str


class RecordingSettings(RecordingFields):
    """Incoming choices: model ids must be currently configured."""

    _check_recognition_model = field_validator("recognition_model")(known_recognition_model)
    _check_translation_model = field_validator("translation_model")(known_translation_model)


class RecordingResponse(RecordingFields):
    """Stored recordings may reference models that have since been removed from the config."""

    id: str
    source: RecordingSource
    file_name: str
    duration: float | None
    created_at: datetime
    analysis: AnalysisResponse | None

    @classmethod
    def from_document(cls, document: dict) -> "RecordingResponse":
        return cls.model_validate({**document, "id": str(document["_id"])})


class RecordingPage(BaseModel):
    items: list[RecordingResponse]
    total: int
    analysed: int
