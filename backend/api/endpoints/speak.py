from api.schemas import RecordingResponse, RecordingSource, SpeakForm
from src.auth import CurrentUser

from .recordings import save_recording


async def save_speech(form: SpeakForm, user: CurrentUser) -> RecordingResponse:
    return await save_recording(RecordingSource.SPEAK, form, user)
