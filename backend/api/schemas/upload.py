from fastapi import UploadFile

from .recordings import RecordingSettings


class UploadForm(RecordingSettings):
    """Multipart form for an uploaded audio file."""

    file: UploadFile
