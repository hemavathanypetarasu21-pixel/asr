"""Packs the train and validation splits into one zip for Google Colab / Kaggle.

Audio is re-encoded to FLAC (lossless, about half the size of WAV) to make the upload smaller.
Usage (from training/):  python scripts/package_for_colab.py
Output: outputs/lingosync_data.zip  -> upload to Google Drive at MyDrive/lingosync/
"""

import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
STAGING = ROOT / "outputs" / "colab_staging"
ZIP_PATH = ROOT / "outputs" / "lingosync_data.zip"


def to_flac(wav: Path, flac: Path) -> None:
    if flac.exists():
        return
    flac.parent.mkdir(parents=True, exist_ok=True)
    audio, rate = sf.read(wav, dtype="int16")
    sf.write(flac, audio, rate, format="FLAC")


def main() -> None:
    files: list[Path] = []
    for split in ("train", "validation"):
        manifest = pd.read_csv(SPLITS / split / "manifest.csv")
        flac_paths = [Path(path).with_suffix(".flac").as_posix() for path in manifest.audio_path]
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(lambda pair: to_flac(ROOT / pair[0], STAGING / pair[1]), zip(manifest.audio_path, flac_paths)))
        manifest["audio_path"] = flac_paths
        manifest_path = STAGING / "data" / "splits" / split / "manifest.csv"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(manifest_path, index=False, encoding="utf-8")
        files += [manifest_path] + [STAGING / path for path in flac_paths]
        print(f"{split}: {len(manifest)} clips")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_STORED) as archive:  # FLAC is already compressed
        for path in files:
            archive.write(path, path.relative_to(STAGING).as_posix())
    print(f"wrote {ZIP_PATH} ({ZIP_PATH.stat().st_size / 1e9:.2f} GB)")


if __name__ == "__main__":
    main()
