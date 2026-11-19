"""Converts downloaded corpora into one manifest of 16 kHz mono WAV clips with matching transcripts.

Usage (from training/):
    python scripts/prepare_data.py emilia --max-hours 30
    python scripts/prepare_data.py slr65 --max-hours 15
    python scripts/prepare_data.py slr127 --max-hours 20

Each run writes data/prepared/<source>/manifest.csv with the columns
    audio_path, transcript, training_text, transcript_normalised, language_pair, source,
    speaker_id, duration, licence, is_code_mixed, original_id
`transcript` is the original text exactly as published. `training_text` is what the model learns
(Tamil romanised Tanglish-style; Malay unchanged). `transcript_normalised` is lower-cased without
punctuation, for scoring. Clips that fail to decode, are shorter than 1 s or longer than 30 s
(Whisper's window), or are exact audio duplicates are dropped and counted in the summary.
"""

import argparse
import csv
import hashlib
import io
import re
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
from src.services.tamil_romanisation import romanise  # noqa: E402

RAW = ROOT / "data" / "raw"
PREPARED = ROOT / "data" / "prepared"
SAMPLE_RATE = 16_000
MIN_SECONDS, MAX_SECONDS = 1.0, 30.0
FFMPEG = "ffmpeg"

LICENCES = {
    "emilia_malaysian_podcast": "CC BY-NC 4.0",
    "slr65_google_tamil": "CC BY-SA 4.0",
    "slr127_mile_tamil": "CC BY 2.0",
}


@dataclass
class Clip:
    audio_path: str
    transcript: str
    training_text: str
    transcript_normalised: str
    language_pair: str
    source: str
    speaker_id: str
    duration: float
    licence: str
    is_code_mixed: bool | None
    original_id: str


def normalise(text: str) -> str:
    # \w does not cover Tamil vowel signs and virama, so the Tamil block is kept explicitly.
    text = re.sub(r"[^\w\s'஀-௿]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def malay_english_mix(text: str) -> bool:
    """Heuristic: at least one clearly-English and one clearly-Malay word (wordfreq zipf scores)."""
    english = malay = 0
    for word in normalise(text).split():
        en, ms = zipf_frequency(word, "en"), zipf_frequency(word, "ms")
        if en >= 3 and en - ms >= 1:
            english += 1
        elif ms >= 3 and ms - en >= 1:
            malay += 1
    return english > 0 and malay > 0


def to_wav(source: bytes | Path, destination: Path) -> tuple[float, str] | None:
    """Decodes with ffmpeg to 16 kHz mono 16-bit WAV. Returns (seconds, pcm sha1) or None if unreadable."""
    from_stdin = isinstance(source, bytes)
    command = [FFMPEG, "-nostdin" if not from_stdin else "-hide_banner", "-v", "error", "-i", "pipe:0" if from_stdin else str(source),
               "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"]
    result = subprocess.run(command, input=source if from_stdin else None, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return None
    pcm = np.frombuffer(result.stdout, np.int16)
    seconds = len(pcm) / SAMPLE_RATE
    if not MIN_SECONDS <= seconds <= MAX_SECONDS or np.abs(pcm).max() < 100:  # too short/long or silent
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    import soundfile as sf

    sf.write(destination, pcm, SAMPLE_RATE, subtype="PCM_16")
    return seconds, hashlib.sha1(result.stdout).hexdigest()


def finish(source: str, jobs: list[tuple], workers: int = 4) -> None:
    """jobs: (audio bytes or path, destination, Clip without duration). Converts, dedupes, writes the manifest."""
    out_dir = PREPARED / source
    seen: set[str] = set()
    clips: list[Clip] = []
    dropped = {"unreadable_or_out_of_range": 0, "duplicate_audio": 0}

    def convert(job):
        audio, destination, clip = job
        return to_wav(audio() if callable(audio) else audio, destination), destination, clip

    with ThreadPoolExecutor(workers) as pool:
        for index, (converted, destination, clip) in enumerate(pool.map(convert, jobs), 1):
            if converted is None:
                dropped["unreadable_or_out_of_range"] += 1
                continue
            seconds, digest = converted
            if digest in seen:
                dropped["duplicate_audio"] += 1
                destination.unlink(missing_ok=True)
                continue
            seen.add(digest)
            clip.duration = round(seconds, 3)
            clip.audio_path = destination.relative_to(ROOT).as_posix()
            clips.append(clip)
            if index % 500 == 0:
                print(f"  {index}/{len(jobs)} processed", flush=True)

    manifest = out_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Clip.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(clip) for clip in clips)
    hours = sum(clip.duration for clip in clips) / 3600
    print(f"{source}: kept {len(clips)} clips ({hours:.2f} h), dropped {dropped} -> {manifest}")


def take_hours(frame: pd.DataFrame, max_hours: float, seconds_column: str) -> pd.DataFrame:
    keep = frame[seconds_column].cumsum() <= max_hours * 3600
    return frame[keep]


def prepare_emilia(max_hours: float) -> None:
    source, folder = "emilia_malaysian_podcast", RAW / "emilia"
    meta = pd.read_parquet(folder / "data" / "malaysian_podcast-00000-of-00001.parquet")
    archives = {}
    for path in sorted(folder.glob("malaysian-podcast_processed-*.zip")):
        archive = zipfile.ZipFile(path)
        for name in archive.namelist():
            archives[name] = archive
    meta = meta[meta.audio_filename.isin(archives)].copy()
    print(f"{len(meta)} metadata rows have audio in the downloaded archives")
    meta = meta[meta.language == "ms"]
    meta["seconds"] = meta.end - meta.start
    meta = meta[(meta.seconds >= MIN_SECONDS) & (meta.seconds <= MAX_SECONDS)]
    meta["is_code_mixed"] = meta.text.map(malay_english_mix)
    # Code-mixed segments first, then the rest, up to the hour cap.
    meta = meta.sort_values(["is_code_mixed", "audio_filename"], ascending=[False, True])
    meta = take_hours(meta, max_hours, "seconds")
    print(f"selected {len(meta)} segments, {meta.is_code_mixed.mean():.0%} code-mixed by heuristic")

    jobs = []
    for row in meta.itertuples():
        episode = row.folder.split("/", 1)[-1]
        episode_id = hashlib.sha1(episode.encode()).hexdigest()[:10]
        text = row.text.strip()
        jobs.append((
            (lambda name=row.audio_filename: archives[name].read(name)),
            PREPARED / source / "audio" / f"{episode_id}_{Path(row.audio_filename).stem.rsplit('_', 1)[-1]}.wav",
            Clip("", text, text, normalise(text), "malay_english", source, f"{episode_id}_{row.speaker}", 0.0,
                 LICENCES[source], bool(row.is_code_mixed), row.audio_filename),
        ))
    finish(source, jobs, workers=2)  # zipfile reads are not thread-safe beyond a few workers


def tamil_clip(source: str, file_id: str, speaker: str, text: str) -> Clip:
    text = text.strip()
    romanised = romanise(text)
    return Clip("", text, romanised, normalise(romanised), "tamil_english", source, speaker, 0.0, LICENCES[source], False, file_id)


def prepare_slr65(max_hours: float) -> None:
    source, folder = "slr65_google_tamil", RAW / "slr65"
    archives = {}
    for path in folder.glob("ta_in_*.zip"):
        archive = zipfile.ZipFile(path)
        for name in archive.namelist():
            if name.endswith(".wav"):
                archives[Path(name).stem] = (archive, name)
    rows = []
    for index_file in folder.glob("line_index_*.tsv"):
        for line in index_file.read_text(encoding="utf-8").splitlines():
            file_id, _, text = line.partition("\t")
            if file_id in archives and text:
                rows.append((file_id, text))
    rows.sort()
    # Sentences average roughly 5 s, so the hour cap is approximate for this corpus.
    rows = rows[: int(max_hours * 3600 / 5)]
    jobs = []
    for file_id, text in rows:
        archive, name = archives[file_id]
        speaker = "_".join(file_id.split("_")[:2])  # e.g. taf_00008
        jobs.append(((lambda a=archive, n=name: a.read(n)), PREPARED / source / "audio" / f"{file_id}.wav",
                     tamil_clip(source, file_id, speaker, text)))
    finish(source, jobs, workers=2)


def prepare_slr127(max_hours: float) -> None:
    source, folder = "slr127_mile_tamil", RAW / "slr127" / "extracted"
    wavs = {path.stem: path for path in folder.rglob("*.wav")}
    texts = {path.stem: path for path in folder.rglob("*.txt")}
    ids = sorted(set(wavs) & set(texts))
    print(f"{len(ids)} audio files with a matching transcript ({len(wavs)} wav, {len(texts)} txt)")
    ids = ids[: int(max_hours * 3600 / 6)]
    jobs = []
    for file_id in ids:
        text = texts[file_id].read_text(encoding="utf-8").strip()
        speaker = re.split(r"[_-]", file_id)[0]
        jobs.append((wavs[file_id], PREPARED / source / "audio" / f"{file_id}.wav", tamil_clip(source, file_id, speaker, text)))
    finish(source, jobs)


def retext(_max_hours: float) -> None:
    """Recomputes romanised training text for every Tamil manifest (after the romaniser changes)."""
    for manifest in PREPARED.glob("*/manifest.csv"):
        frame = pd.read_csv(manifest)
        tamil = frame.language_pair == "tamil_english"
        if not tamil.any():
            continue
        frame.loc[tamil, "training_text"] = frame.loc[tamil, "transcript"].map(lambda text: romanise(str(text).strip()))
        frame.loc[tamil, "transcript_normalised"] = frame.loc[tamil, "training_text"].map(normalise)
        frame.to_csv(manifest, index=False, encoding="utf-8")
        print(f"updated {tamil.sum()} Tamil rows in {manifest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", choices=["emilia", "slr65", "slr127", "retext"])
    parser.add_argument("--max-hours", type=float, default=25.0)
    args = parser.parse_args()
    {"emilia": prepare_emilia, "slr65": prepare_slr65, "slr127": prepare_slr127, "retext": retext}[args.source](args.max_hours)
