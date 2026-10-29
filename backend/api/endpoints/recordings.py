from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from api.schemas import RecordingPage, RecordingResponse, RecordingSettings, RecordingSource, SpeakForm, UploadForm
from src.auth import CurrentUser
from src.config import settings
from src.services import audio_service, recording_service
from src.services.recording_service import RecordingNotFoundError

NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found.")
DEFAULT_CONTENT_TYPE = "application/octet-stream"


async def save_recording(source: RecordingSource, form: SpeakForm | UploadForm, user: CurrentUser) -> RecordingResponse:
    """Stores the form's audio file in GridFS together with its recording settings."""
    file = form.file
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Choose an audio file.")

    try:
        path = await audio_service.save_to_temp_file(file)
    except audio_service.AudioTooLargeError as error:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Audio files must be smaller than {settings.MAX_UPLOAD_MB} MB.",
        ) from error
    except audio_service.InvalidAudioError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    try:
        duration = await audio_service.probe_duration(path)
        document = await recording_service.create_recording(
            user_id=user.id,
            source=source.value,
            file_name=Path(file.filename or f"{source.value}-recording").name,
            content_type=file.content_type or DEFAULT_CONTENT_TYPE,
            audio_path=path,
            duration=duration,
            settings=form.model_dump(mode="json", include=set(RecordingSettings.model_fields)),
        )
    except audio_service.InvalidAudioError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    finally:
        path.unlink(missing_ok=True)
    return RecordingResponse.from_document(document)


async def list_recordings(user: CurrentUser, skip: int, limit: int) -> RecordingPage:
    items, total, analysed = await recording_service.list_recordings(user.id, skip, limit)
    return RecordingPage(items=[RecordingResponse.from_document(item) for item in items], total=total, analysed=analysed)


async def get_recording_audio(user: CurrentUser, recording_id: str) -> StreamingResponse:
    try:
        document = await recording_service.get_recording(user.id, recording_id)
        chunks = await recording_service.stream_audio(document)
    except RecordingNotFoundError as error:
        raise NOT_FOUND from error
    return StreamingResponse(chunks, media_type=document.get("content_type", DEFAULT_CONTENT_TYPE))


async def delete_recording(user: CurrentUser, recording_id: str) -> None:
    try:
        await recording_service.delete_recording(user.id, recording_id)
    except RecordingNotFoundError as error:
        raise NOT_FOUND from error
