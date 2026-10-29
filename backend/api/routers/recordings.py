from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from api.endpoints import recordings
from api.schemas import RecordingPage
from src.auth import CurrentUser, get_current_user
from src.config import settings

router = APIRouter(prefix="/recordings", tags=["recordings"])

User = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("", response_model=RecordingPage)
async def list_recordings(
    user: User,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.RECORDINGS_MAX_PAGE_SIZE)] = settings.RECORDINGS_MAX_PAGE_SIZE,
) -> RecordingPage:
    return await recordings.list_recordings(user, skip, limit)


@router.get("/{recording_id}/audio", response_class=StreamingResponse)
async def get_recording_audio(recording_id: str, user: User) -> StreamingResponse:
    return await recordings.get_recording_audio(user, recording_id)


@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(recording_id: str, user: User) -> None:
    await recordings.delete_recording(user, recording_id)
