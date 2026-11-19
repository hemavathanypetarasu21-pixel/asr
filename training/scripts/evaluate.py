"""Measures WER / CER of a Whisper model on a test manifest, separately for each language pair.

The original model is run exactly as the app runs it (openai-whisper, same code-switched prompt per
language, CPU). A fine-tuned Hugging Face model directory can be evaluated with --hf-model.
Tamil output is romanised with the app's romaniser before scoring, since the targets are romanised.

Usage (from training/):
    python scripts/evaluate.py --model tiny --limit 200
    python scripts/evaluate.py --hf-model outputs/whisper-small-lingosync --limit 200

Writes outputs/eval/<name>/predictions.csv and results.json. Metrics:
    WER  word error rate (lower is better)       CER  character error rate
    accuracy = max(0, 1 - WER)
    loose_wer  WER after collapsing doubled letters and 'h' spelling variants (dh/th/zh), because
               romanised Tamil has no single correct spelling (e.g. innikku / inniku).
Filler sounds (uh, um, erm, hmm) are removed from references and hypotheses before scoring.

Re-score saved predictions without re-running the model:
    python scripts/evaluate.py --rescore outputs/eval/tiny-auto
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import jiwer
import pandas as pd
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
from src.services.tamil_romanisation import romanise  # noqa: E402

# The prompts the app gives Whisper (backend/src/services/analysis_service.py), keyed by language pair.
APP_PROMPTS = {
    "malay_english": "Eh, you dah makan ke? Jom kita pergi mamak after this meeting lah.",
    "tamil_english": "Machan, naan office la irukken, I'll call you back. Enna panra?",
}
WHISPER_LANGUAGE = {"malay_english": "ms", "tamil_english": "ta"}


# Hesitation sounds Whisper normally omits; removed from both sides before scoring.
# Meaningful particles (lah, ah, eh, ke, da) are kept.
FILLERS = re.compile(r"\b(?:uh+|um+|umm+|erm+|hmm+|mm+)\b")


def normalise(text: str) -> str:
    # \w does not cover Tamil vowel signs and virama, so the Tamil block is kept explicitly.
    text = re.sub(r"[^\w\s'஀-௿]", " ", str(text).lower())
    return re.sub(r"\s+", " ", FILLERS.sub(" ", text)).strip()


def loosen(text: str) -> str:
    text = re.sub(r"([a-z])\1+", r"\1", text)  # innikku -> iniku
    return re.sub(r"([tdzsk])h", r"\1", text)  # thamizh -> tamiz


class OpenAIWhisper:
    def __init__(self, model_id: str, force_language: bool):
        import whisper

        self.model = whisper.load_model(model_id)
        self.force_language = force_language

    def __call__(self, audio, language_pair: str) -> str:
        language = WHISPER_LANGUAGE[language_pair] if self.force_language else None
        result = self.model.transcribe(audio, task="transcribe", language=language, initial_prompt=APP_PROMPTS[language_pair],
                                       fp16=self.model.device.type == "cuda")
        return result["text"].strip()


class HuggingFaceWhisper:
    def __init__(self, path: str):
        import torch
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self.torch = torch
        self.processor = WhisperProcessor.from_pretrained(path)
        self.model = WhisperForConditionalGeneration.from_pretrained(path).eval()

    def __call__(self, audio, language_pair: str) -> str:
        features = self.processor(audio, sampling_rate=16_000, return_tensors="pt").input_features
        with self.torch.no_grad():
            ids = self.model.generate(features, language=WHISPER_LANGUAGE[language_pair], task="transcribe", max_new_tokens=225)
        return self.processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


def score(frame: pd.DataFrame) -> dict:
    references, hypotheses = list(frame.reference.map(normalise)), list(frame.hypothesis.map(normalise))
    wer = jiwer.wer(references, hypotheses)
    return {
        "clips": len(frame),
        "hours": round(frame.duration.sum() / 3600, 3),
        "wer": round(wer, 4),
        "cer": round(jiwer.cer(references, hypotheses), 4),
        "accuracy": round(max(0.0, 1 - wer), 4),
        "loose_wer": round(jiwer.wer([loosen(r) for r in references], [loosen(h) for h in hypotheses]), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", default="data/splits/test/manifest.csv")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model", help="openai-whisper model id, e.g. tiny, base, small, medium")
    group.add_argument("--hf-model", help="path to a fine-tuned Hugging Face Whisper model")
    group.add_argument("--rescore", help="folder with a predictions.csv to score again")
    parser.add_argument("--force-language", action="store_true",
                        help="openai-whisper only: force the language token from the declared language instead of auto-detecting")
    parser.add_argument("--limit", type=int, default=0, help="max clips per language pair (0 = all)")
    parser.add_argument("--name", help="output folder name (defaults to the model name)")
    args = parser.parse_args()

    if args.rescore:
        folder = ROOT / args.rescore
        results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        write_results(folder, pd.read_csv(folder / "predictions.csv"), results["model"], results["manifest"], results["language"])
        return

    test = pd.read_csv(ROOT / args.manifest)
    if args.limit:
        # Spread the sample over sources and speakers instead of taking the first rows.
        test = test.groupby("language_pair", group_keys=False).apply(
            lambda frame: frame.sample(min(args.limit, len(frame)), random_state=13))
    name = args.name or (args.model or Path(args.hf_model).name)
    out = ROOT / "outputs" / "eval" / name
    out.mkdir(parents=True, exist_ok=True)

    transcribe = OpenAIWhisper(args.model, args.force_language) if args.model else HuggingFaceWhisper(args.hf_model)
    rows, started = [], time.time()
    for index, clip in enumerate(test.itertuples(), 1):
        audio, _ = sf.read(ROOT / clip.audio_path, dtype="float32")
        raw = transcribe(audio, clip.language_pair)
        rows.append({
            "audio_path": clip.audio_path, "language_pair": clip.language_pair, "source": clip.source,
            "duration": clip.duration, "raw_output": raw,
            "reference": normalise(clip.training_text), "hypothesis": normalise(romanise(raw)),
        })
        if index % 25 == 0:
            print(f"  {index}/{len(test)} clips, {time.time() - started:.0f} s", flush=True)

    predictions = pd.DataFrame(rows)
    predictions.to_csv(out / "predictions.csv", index=False, encoding="utf-8")
    language = "forced" if args.force_language or args.hf_model else "auto-detected (as in the app)"
    write_results(out, predictions, name, args.manifest, language)


def write_results(out: Path, predictions: pd.DataFrame, name: str, manifest: str, language: str) -> None:
    predictions = predictions.fillna({"hypothesis": "", "reference": ""})
    results = {
        "model": name,
        "manifest": manifest,
        "language": language,
        "overall": score(predictions),
        "by_language_pair": {pair: score(frame) for pair, frame in predictions.groupby("language_pair")},
        "by_source": {source: score(frame) for source, frame in predictions.groupby("source")},
    }
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
