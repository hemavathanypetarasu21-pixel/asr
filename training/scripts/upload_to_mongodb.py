"""Uploads prepared dataset clips into the app's MongoDB, separate from user recordings.

Each clip becomes one document in the `dataset_clips` collection, with its WAV audio in the
`dataset_audio` GridFS bucket. User recordings (`recordings` / `audio`) are not touched.
Uploads are idempotent: a clip already in the database (same source + original id) is skipped,
so the script can be re-run to add more clips.

Usage (from training/):
    python scripts/upload_to_mongodb.py --per-language 50     # random sample per language pair
    python scripts/upload_to_mongodb.py --split test          # every clip of one split
    python scripts/upload_to_mongodb.py --all                 # everything prepared

MongoDB connection settings are read from backend/.env (MONGODB_URI, MONGODB_DB_NAME).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from gridfs import GridFSBucket
from pymongo import ASCENDING, MongoClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
from src.config import settings  # noqa: E402
from src.db.mongo import DATASET_AUDIO_BUCKET, DATASET_COLLECTION  # noqa: E402
# Dataset language pair -> the app's language id (api.schemas.Language values).
APP_LANGUAGE = {"malay_english": "manglish", "tamil_english": "tanglish"}


def load_clips() -> pd.DataFrame:
    frames = []
    for split in ("train", "validation", "test"):
        manifest = ROOT / "data" / "splits" / split / "manifest.csv"
        if manifest.exists():
            frames.append(pd.read_csv(manifest).assign(split=split))
    if not frames:
        raise SystemExit("No split manifests found. Run scripts/prepare_data.py and scripts/split_data.py first.")
    return pd.concat(frames, ignore_index=True)


def source_urls() -> dict[str, str]:
    registry = json.loads((ROOT / "datasets.json").read_text(encoding="utf-8"))
    return {entry["id"]: entry["url"] for entry in registry["used"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--per-language", type=int, help="random clips per language pair")
    choice.add_argument("--split", choices=["train", "validation", "test"])
    choice.add_argument("--all", action="store_true")
    args = parser.parse_args()

    clips = load_clips()
    if args.per_language:
        clips = clips.groupby("language_pair", group_keys=False).apply(
            lambda frame: frame.sample(min(args.per_language, len(frame)), random_state=13))
    elif args.split:
        clips = clips[clips.split == args.split]

    database = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)[settings.MONGODB_DB_NAME]
    collection = database[DATASET_COLLECTION]
    bucket = GridFSBucket(database, bucket_name=DATASET_AUDIO_BUCKET)
    collection.create_index([("source", ASCENDING), ("original_id", ASCENDING)], unique=True)
    collection.create_index([("language", ASCENDING), ("split", ASCENDING)])

    urls = source_urls()
    added = skipped = missing = 0
    for clip in clips.itertuples():
        if collection.find_one({"source": clip.source, "original_id": clip.original_id}, {"_id": 1}):
            skipped += 1
            continue
        audio_path = ROOT / clip.audio_path
        if not audio_path.exists():
            missing += 1
            continue
        with audio_path.open("rb") as audio:
            audio_file_id = bucket.upload_from_stream(
                audio_path.name, audio, metadata={"content_type": "audio/wav", "source": clip.source})
        collection.insert_one({
            "file_name": audio_path.name,
            "audio_file_id": audio_file_id,
            "content_type": "audio/wav",
            "duration": float(clip.duration),
            "language": APP_LANGUAGE[clip.language_pair],
            "language_pair": clip.language_pair,
            "transcript": clip.transcript,            # original text exactly as published
            "training_text": clip.training_text,      # Tamil romanised; Malay-English unchanged
            "transcript_normalised": clip.transcript_normalised,
            "is_code_mixed": None if pd.isna(clip.is_code_mixed) else bool(clip.is_code_mixed),
            "speaker_id": clip.speaker_id,
            "split": clip.split,
            "source": clip.source,
            "source_url": urls.get(clip.source),
            "licence": clip.licence,
            "original_id": clip.original_id,
            "imported_at": datetime.now(timezone.utc),
        })
        added += 1

    total = collection.count_documents({})
    print(f"added {added}, already present {skipped}, audio missing {missing}; {DATASET_COLLECTION} now holds {total} clips")
    for row in collection.aggregate([{"$group": {"_id": {"language": "$language", "split": "$split"}, "clips": {"$sum": 1},
                                                 "hours": {"$sum": {"$divide": ["$duration", 3600]}}}},
                                     {"$sort": {"_id.language": 1, "_id.split": 1}}]):
        print(f"  {row['_id']['language']:9} {row['_id']['split']:10} {row['clips']:5} clips {row['hours']:.2f} h")


if __name__ == "__main__":
    main()
