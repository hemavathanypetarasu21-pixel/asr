from fastapi import APIRouter

from api.endpoints import languages
from api.schemas import LanguageOption

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=list[LanguageOption])
async def list_languages() -> list[LanguageOption]:
    return await languages.list_languages()
