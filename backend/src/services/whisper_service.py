"""Whisper model loading, audio decoding, transcription and language probabilities."""

import subprocess
import threading
from pathlib import Path

import numpy as np
import torch
import whisper

from src.config import settings

SAMPLE_RATE = whisper.audio.SAMPLE_RATE
WINDOW_SAMPLES = whisper.audio.N_SAMPLES  # 30 seconds, Whisper's input window

_models: dict[str, whisper.Whisper] = {}
_load_lock = threading.Lock()
# One inference at a time: Whisper models are not thread-safe and CPU inference saturates cores.
_inference_lock = threading.Lock()


class ModelUnavailableError(Exception):
    pass


class AudioDecodeError(Exception):
    pass


def get_model(model_id: str) -> whisper.Whisper:
    with _load_lock:
        if model_id not in _models:
            try:
                _models[model_id] = whisper.load_model(model_id)
            except Exception as error:
                raise ModelUnavailableError(f"Whisper model '{model_id}' could not be loaded.") from error
        return _models[model_id]


def decode_audio(path: Path) -> np.ndarray:
    """Decodes any ffmpeg-readable file to 16 kHz mono float32, as Whisper expects."""
    result = subprocess.run(
        [settings.FFMPEG_BINARY, "-nostdin", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
        capture_output=True,
    )
    if result.returncode != 0 and not result.stdout:
        raise AudioDecodeError("The recording could not be decoded.")
    return np.frombuffer(result.stdout, np.int16).astype(np.float32) / 32768.0


def transcribe(model: whisper.Whisper, audio: np.ndarray, initial_prompt: str) -> str:
    with _inference_lock:
        result = model.transcribe(
            audio,
            task="transcribe",
            initial_prompt=initial_prompt,
            fp16=model.device.type == "cuda",
        )
    return result["text"].strip()


def translate_to_english(model: whisper.Whisper, audio: np.ndarray) -> str:
    """Whisper's built-in speech-to-English translation; runs locally, so it needs no API key."""
    with _inference_lock:
        result = model.transcribe(audio, task="translate", fp16=model.device.type == "cuda")
    return result["text"].strip()


def language_probabilities(model: whisper.Whisper, audio: np.ndarray, max_windows: int) -> dict[str, float]:
    """Averages Whisper's language probabilities over up to `max_windows` evenly spaced 30 s windows."""
    window_count = max(1, min(max_windows, -(-len(audio) // WINDOW_SAMPLES)))
    starts = np.linspace(0, max(0, len(audio) - WINDOW_SAMPLES), window_count).astype(int)
    totals: dict[str, float] = {}
    with _inference_lock, torch.no_grad():
        for start in starts:
            window = whisper.pad_or_trim(audio[start : start + WINDOW_SAMPLES])
            mel = whisper.log_mel_spectrogram(window, n_mels=model.dims.n_mels).to(model.device)
            _, probabilities = model.detect_language(mel)
            for language, probability in probabilities.items():
                totals[language] = totals.get(language, 0.0) + float(probability)
    return {language: total / window_count for language, total in totals.items()}
