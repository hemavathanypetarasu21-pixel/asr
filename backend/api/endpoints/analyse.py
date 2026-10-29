from fastapi import HTTPException, status

from api.schemas import AnalyseRequest, RecordingResponse
from src.auth import CurrentUser
from src.services import analysis_service
from src.services.recording_service import RecordingNotFoundError
from src.services.whisper_service import AudioDecodeError, ModelUnavailableError

from .recordings import NOT_FOUND


async def analyse_recording(user: CurrentUser, recording_id: str, request: AnalyseRequest) -> RecordingResponse:
    try:
        document = await analysis_service.analyse(
            user.id, recording_id, request.recognition_model, request.translation_model
        )
    except RecordingNotFoundError as error:
        raise NOT_FOUND from error
    except ModelUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except AudioDecodeError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    return RecordingResponse.from_document(document)
