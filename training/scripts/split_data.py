"""Splits every prepared manifest into train / validation / test (70 / 15 / 15 by audio duration).

Splitting is speaker-independent: all clips of a speaker go to exactly one split, so the test set
only contains voices the model never trained on. Splits are made separately for each source, so
every source is represented in every split. Audio is hard-linked (no extra disk space).

Usage (from training/):  python scripts/split_data.py
Output: data/splits/{train,validation,test}/manifest.csv (+ audio/), data/splits/summary.json
"""

import json
import os
import random
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "data" / "prepared"
SPLITS = ROOT / "data" / "splits"
RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
SEED = 13
# Emilia speaker labels are per episode (<episode>_SPEAKER_00), so whole episodes are kept together.
# A podcast host appearing in several episodes can still span splits; the metadata has no channel id.
GROUP_KEY = {"emilia_malaysian_podcast": lambda speaker: speaker.split("_", 1)[0]}


def assign_groups(frame: pd.DataFrame) -> pd.Series:
    """Greedy: shuffled speaker groups fill the split that is furthest below its target duration."""
    groups = frame.speaker_id.map(GROUP_KEY.get(frame.source.iloc[0], lambda speaker: speaker))
    seconds = frame.groupby(groups).duration.sum().to_dict()
    speakers = sorted(seconds)
    random.Random(SEED).shuffle(speakers)
    total = sum(seconds.values())
    filled = dict.fromkeys(RATIOS, 0.0)
    assignment = {}
    for speaker in speakers:
        split = max(RATIOS, key=lambda name: RATIOS[name] * total - filled[name])
        assignment[speaker] = split
        filled[split] += seconds[speaker]
    return groups.map(assignment)


def link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def main() -> None:
    manifests = sorted(PREPARED.glob("*/manifest.csv"))
    if not manifests:
        raise SystemExit("No prepared manifests found. Run scripts/prepare_data.py first.")
    if SPLITS.exists():
        shutil.rmtree(SPLITS)

    parts = []
    for manifest in manifests:
        frame = pd.read_csv(manifest)
        frame["split"] = assign_groups(frame)
        parts.append(frame)
    data = pd.concat(parts, ignore_index=True)

    for split, frame in data.groupby("split"):
        frame = frame.copy()
        new_paths = []
        for path in frame.audio_path:
            destination = SPLITS / split / "audio" / Path(path).parent.parent.name / Path(path).name
            link(ROOT / path, destination)
            new_paths.append(destination.relative_to(ROOT).as_posix())
        frame["audio_path"] = new_paths
        frame.drop(columns="split").to_csv(SPLITS / split / "manifest.csv", index=False, encoding="utf-8")

    # Every speaker must appear in exactly one split.
    overlap = data.groupby(["source", "speaker_id"]).split.nunique().max()
    assert overlap == 1, "a speaker appears in more than one split"

    summary = {}
    for (split, pair, source), frame in data.groupby(["split", "language_pair", "source"]):
        summary.setdefault(split, {}).setdefault(pair, {})[source] = {
            "clips": len(frame),
            "hours": round(frame.duration.sum() / 3600, 2),
            "speakers": frame.speaker_id.nunique(),
            "code_mixed_clips": int(frame.is_code_mixed.fillna(False).astype(bool).sum()),
        }
    (SPLITS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
