from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator

from .languages import Language
from .modes import Mode
from .model_validators import known_recognition_model, known_translation_model


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class RecordingDefaults(BaseModel):
    """Pre-selected chat dropdown values; None means the first option."""

    language: Language | None = None
    mode: Mode | None = None
    recognition_model: str | None = None
    translation_model: str | None = None

    _check_recognition_model = field_validator("recognition_model")(known_recognition_model)
    _check_translation_model = field_validator("translation_model")(known_translation_model)


class PreferencesUpdate(BaseModel):
    theme: Theme
    defaults: RecordingDefaults


class ApiKeyStatus(BaseModel):
    configured: bool
    source: Literal["user", "server"] | None
    hint: str | None


class SettingsResponse(BaseModel):
    theme: Theme
    defaults: RecordingDefaults
    gemini_api_key: ApiKeyStatus


class ApiKeyUpdate(BaseModel):
    api_key: SecretStr = Field(min_length=1)
