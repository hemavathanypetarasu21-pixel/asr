from fastapi import UploadFile

from .recordings import RecordingSettings


class SpeakForm(RecordingSettings):
    """Multipart form for a microphone recording."""

    file: UploadFile
