from enum import Enum

from pydantic import BaseModel


class Language(str, Enum):
    # Values are stored on saved recordings and used by the dialect/translation services; never shown in the UI.
    MALAY_ENGLISH = "manglish"
    TAMIL_ENGLISH = "tanglish"


LANGUAGE_LABELS: dict[Language, str] = {
    Language.MALAY_ENGLISH: "Malay + English",
    Language.TAMIL_ENGLISH: "Tamil + English",
}


class LanguageOption(BaseModel):
    id: Language
    label: str
