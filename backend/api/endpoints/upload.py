from api.schemas import RecordingResponse, RecordingSource, UploadForm
from src.auth import CurrentUser

from .recordings import save_recording


async def upload_audio(form: UploadForm, user: CurrentUser) -> RecordingResponse:
    return await save_recording(RecordingSource.UPLOAD, form, user)
