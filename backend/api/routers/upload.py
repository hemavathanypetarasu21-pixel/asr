from typing import Annotated

from fastapi import APIRouter, Depends, Form

from api.endpoints import upload
from api.schemas import RecordingResponse, UploadForm
from src.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=RecordingResponse, status_code=201)
async def upload_audio(
    form: Annotated[UploadForm, Form()],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> RecordingResponse:
    return await upload.upload_audio(form, user)
