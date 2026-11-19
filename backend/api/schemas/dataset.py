from enum import Enum

from pydantic import BaseModel

from .languages import Language


class DatasetSplit(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class DatasetClipResponse(BaseModel):
    id: str
    file_name: str
    duration: float
    language: Language
    # Original transcript as published; for Tamil this is Tamil script.
    transcript: str
    # Romanised Tamil (Tanglish style); identical to `transcript` for Malay-English.
    training_text: str
    is_code_mixed: bool | None
    speaker_id: str
    split: DatasetSplit
    source: str
    source_url: str | None
    licence: str

    @classmethod
    def from_document(cls, document: dict) -> "DatasetClipResponse":
        return cls.model_validate({**document, "id": str(document["_id"])})


class DatasetGroup(BaseModel):
    language: Language
    split: DatasetSplit
    clips: int
    hours: float


class DatasetPage(BaseModel):
    items: list[DatasetClipResponse]
    # Clips matching the filters.
    total: int
    # Whole dataset, by language and split.
    summary: list[DatasetGroup]
