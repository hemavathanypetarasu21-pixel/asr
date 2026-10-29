from enum import Enum

from pydantic import BaseModel


class Language(str, Enum):
    MANGLISH = "manglish"
    TANGLISH = "tanglish"


LANGUAGE_LABELS: dict[Language, str] = {
    Language.MANGLISH: "Manglish (Malay + English)",
    Language.TANGLISH: "Tanglish (Tamil + English)",
}


class LanguageOption(BaseModel):
    id: Language
    label: str
