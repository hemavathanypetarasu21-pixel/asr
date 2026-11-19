from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from .analyse import AnalysisResponse
from .languages import Language
from .model_validators import known_recognition_model, known_translation_model


class RecordingSource(str, Enum):
    SPEAK = "speak"
    UPLOAD = "upload"


class RecordingFields(BaseModel):
    """Choices from the chat page, stored with every recording."""

    language: Language
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
    # The user's corrected transcript; the model's output stays in `analysis.transcript`.
    corrected_transcript: str | None = None
    corrected_at: datetime | None = None

    @classmethod
    def from_document(cls, document: dict) -> "RecordingResponse":
        return cls.model_validate({**document, "id": str(document["_id"])})


class TranscriptUpdate(BaseModel):
    transcript: str = Field(min_length=1, max_length=20_000)

    @field_validator("transcript")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("The transcript cannot be empty.")
        return value


class RecordingPage(BaseModel):
    items: list[RecordingResponse]
    total: int
    analysed: int
