from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from api.endpoints import dataset
from api.schemas import DatasetPage, DatasetSplit, Language
from src.auth import get_current_user
from src.config import settings

# Signed-in users only; the dataset itself is shared and read-only.
router = APIRouter(prefix="/dataset", tags=["dataset"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=DatasetPage)
async def list_dataset_clips(
    language: Language | None = None,
    split: DatasetSplit | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.RECORDINGS_MAX_PAGE_SIZE)] = settings.RECORDINGS_MAX_PAGE_SIZE,
) -> DatasetPage:
    return await dataset.list_clips(language, split, skip, limit)


@router.get("/{clip_id}/audio", response_class=StreamingResponse)
async def get_dataset_clip_audio(clip_id: str) -> StreamingResponse:
    return await dataset.get_clip_audio(clip_id)
