from typing import Annotated

from fastapi import APIRouter, Depends, Form

from api.endpoints import speak
from api.schemas import RecordingResponse, SpeakForm
from src.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/speak", tags=["speak"])


@router.post("", response_model=RecordingResponse, status_code=201)
async def save_speech(
    form: Annotated[SpeakForm, Form()],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> RecordingResponse:
    return await speak.save_speech(form, user)
