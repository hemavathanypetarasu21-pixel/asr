from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from api.schemas import DatasetClipResponse, DatasetGroup, DatasetPage, DatasetSplit, Language
from src.services import dataset_service
from src.services.dataset_service import DatasetClipNotFoundError


async def list_clips(language: Language | None, split: DatasetSplit | None, skip: int, limit: int) -> DatasetPage:
    filters = {key: value.value for key, value in {"language": language, "split": split}.items() if value is not None}
    items, total = await dataset_service.list_clips(filters, skip, limit)
    return DatasetPage(
        items=[DatasetClipResponse.from_document(item) for item in items],
        total=total,
        summary=[DatasetGroup(**row) for row in await dataset_service.summary()],
    )


async def get_clip_audio(clip_id: str) -> StreamingResponse:
    try:
        chunks, content_type = await dataset_service.stream_audio(clip_id)
    except DatasetClipNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset clip not found.") from error
    return StreamingResponse(chunks, media_type=content_type)
