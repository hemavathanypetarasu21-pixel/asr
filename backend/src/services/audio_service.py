import asyncio
import subprocess
import tempfile
from pathlib import Path

from fastapi import UploadFile

from src.config import settings

_CHUNK_BYTES = 1024 * 1024
# Low sample rate is enough to count samples when the container has no duration header.
_PROBE_SAMPLE_RATE = 8000
_PROBE_BYTES_PER_SAMPLE = 2


class AudioTooLargeError(Exception):
    pass


class InvalidAudioError(Exception):
    pass


async def save_to_temp_file(upload: UploadFile) -> Path:
    """Copies an upload to a temp file, enforcing MAX_UPLOAD_MB. Caller deletes the file."""
    suffix = Path(upload.filename or "").suffix
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    path = Path(handle.name)
    size = 0
    try:
        with handle:
            while chunk := await upload.read(_CHUNK_BYTES):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise AudioTooLargeError
                handle.write(chunk)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    if size == 0:
        path.unlink(missing_ok=True)
        raise InvalidAudioError("The audio file is empty.")
    return path


def _probe_duration(path: Path) -> float:
    probe = subprocess.run(
        [settings.FFPROBE_BINARY, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise InvalidAudioError("This file is not a supported audio format.")
    try:
        return float(probe.stdout.strip())
    except ValueError:
        pass

    # Browser recordings (WebM/Opus) often lack a duration header: decode and count samples.
    decoded = subprocess.run(
        [settings.FFMPEG_BINARY, "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(_PROBE_SAMPLE_RATE), "-"],
        capture_output=True,
    )
    if decoded.returncode != 0 and not decoded.stdout:
        raise InvalidAudioError("This file is not a supported audio format.")
    return len(decoded.stdout) / (_PROBE_SAMPLE_RATE * _PROBE_BYTES_PER_SAMPLE)


async def probe_duration(path: Path) -> float:
    return await asyncio.to_thread(_probe_duration, path)

