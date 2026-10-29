from typing import Annotated

from fastapi import APIRouter, Depends

from api.endpoints import analyse
from api.schemas import AnalyseRequest, RecordingResponse
from src.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/recordings", tags=["analyse"])


@router.post("/{recording_id}/analyse", response_model=RecordingResponse)
async def analyse_recording(
    recording_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    request: AnalyseRequest | None = None,
) -> RecordingResponse:
    return await analyse.analyse_recording(user, recording_id, request or AnalyseRequest())
