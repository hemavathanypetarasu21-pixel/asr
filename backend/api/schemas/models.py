from pydantic import BaseModel

from src.config import ModelOption


class ModelsResponse(BaseModel):
    recognition: list[ModelOption]
    translation: list[ModelOption]
