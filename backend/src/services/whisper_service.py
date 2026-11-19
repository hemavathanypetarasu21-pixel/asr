"""Whisper model loading, audio decoding, transcription and language probabilities.

Two kinds of model are supported: openai-whisper checkpoints (tiny, medium, ...) and fine-tuned
Hugging Face Whisper folders listed in FINETUNED_MODEL_DIRS (e.g. the LoRA-tuned LingoSync model).
"""

import subprocess
import threading
from pathlib import Path

import numpy as np
import torch
import whisper

from src.config import settings

SAMPLE_RATE = whisper.audio.SAMPLE_RATE
WINDOW_SAMPLES = whisper.audio.N_SAMPLES  # 30 seconds, Whisper's input window

_models: dict[str, "whisper.Whisper | FineTunedWhisper"] = {}
_load_lock = threading.Lock()
# One inference at a time: Whisper models are not thread-safe and CPU inference saturates cores.
_inference_lock = threading.Lock()


class ModelUnavailableError(Exception):
    pass


class AudioDecodeError(Exception):
    pass


class FineTunedWhisper:
    """A Hugging Face Whisper model folder, run on 30-second windows with the language token forced."""

    def __init__(self, path: str):
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self.processor = WhisperProcessor.from_pretrained(path)
        self.model = WhisperForConditionalGeneration.from_pretrained(path).eval()
        tokenizer = self.processor.tokenizer
        self.start_token = tokenizer.convert_tokens_to_ids("<|startoftranscript|>")
        self.language_tokens = {code: tokenizer.convert_tokens_to_ids(f"<|{code}|>") for code in whisper.tokenizer.LANGUAGES}

    def features(self, window: np.ndarray) -> torch.Tensor:
        return self.processor.feature_extractor(window, sampling_rate=SAMPLE_RATE, return_tensors="pt").input_features

    def generate(self, audio: np.ndarray, task: str, language: str | None) -> str:
        texts = []
        for start in range(0, max(len(audio), 1), WINDOW_SAMPLES):
            with torch.no_grad():
                ids = self.model.generate(
                    self.features(audio[start : start + WINDOW_SAMPLES]), task=task, language=language, max_new_tokens=225
                )
            texts.append(self.processor.batch_decode(ids, skip_special_tokens=True)[0].strip())
        return " ".join(text for text in texts if text)

    def language_probabilities(self, window: np.ndarray) -> dict[str, float]:
        with torch.no_grad():
            logits = self.model(
                input_features=self.features(window), decoder_input_ids=torch.tensor([[self.start_token]])
            ).logits[0, -1]
        codes = list(self.language_tokens)
        probabilities = torch.softmax(logits[[self.language_tokens[code] for code in codes]], dim=-1)
        return dict(zip(codes, probabilities.tolist()))


def is_fine_tuned(model: "whisper.Whisper | FineTunedWhisper") -> bool:
    return isinstance(model, FineTunedWhisper)


def get_model(model_id: str) -> "whisper.Whisper | FineTunedWhisper":
    with _load_lock:
        if model_id not in _models:
            try:
                path = settings.FINETUNED_MODEL_DIRS.get(model_id)
                if path is not None and not Path(path).is_dir():
                    raise FileNotFoundError(path)
                _models[model_id] = FineTunedWhisper(path) if path is not None else whisper.load_model(model_id)
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


def transcribe(
    model: "whisper.Whisper | FineTunedWhisper", audio: np.ndarray, initial_prompt: str, language: str | None = None
) -> str:
    """`language` forces Whisper's language token (None = auto-detect). The prompt only applies to openai-whisper models."""
    with _inference_lock:
        if is_fine_tuned(model):
            return model.generate(audio, "transcribe", language)
        result = model.transcribe(
            audio,
            task="transcribe",
            language=language,
            initial_prompt=initial_prompt,
            fp16=model.device.type == "cuda",
        )
    return result["text"].strip()


def translate_to_english(model: "whisper.Whisper | FineTunedWhisper", audio: np.ndarray) -> str:
    """Whisper's built-in speech-to-English translation; runs locally, so it needs no API key."""
    with _inference_lock:
        if is_fine_tuned(model):
            return model.generate(audio, "translate", None)
        result = model.transcribe(audio, task="translate", fp16=model.device.type == "cuda")
    return result["text"].strip()


def language_probabilities(model: "whisper.Whisper | FineTunedWhisper", audio: np.ndarray, max_windows: int) -> dict[str, float]:
    """Averages Whisper's language probabilities over up to `max_windows` evenly spaced 30 s windows."""
    window_count = max(1, min(max_windows, -(-len(audio) // WINDOW_SAMPLES)))
    starts = np.linspace(0, max(0, len(audio) - WINDOW_SAMPLES), window_count).astype(int)
    totals: dict[str, float] = {}
    with _inference_lock, torch.no_grad():
        for start in starts:
            window = whisper.pad_or_trim(audio[start : start + WINDOW_SAMPLES])
            if is_fine_tuned(model):
                probabilities = model.language_probabilities(window)
            else:
                mel = whisper.log_mel_spectrogram(window, n_mels=model.dims.n_mels).to(model.device)
                _, probabilities = model.detect_language(mel)
            for language, probability in probabilities.items():
                totals[language] = totals.get(language, 0.0) + float(probability)
    return {language: total / window_count for language, total in totals.items()}
