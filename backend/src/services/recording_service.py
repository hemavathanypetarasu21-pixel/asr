from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from gridfs.errors import NoFile
from pymongo import ReturnDocument

from src.db import get_audio_bucket, get_recordings


class RecordingNotFoundError(Exception):
    pass


def _object_id(recording_id: str) -> ObjectId:
    try:
        return ObjectId(recording_id)
    except InvalidId as error:
        raise RecordingNotFoundError from error


async def create_recording(
    *,
    user_id: str,
    source: str,
    file_name: str,
    content_type: str,
    audio_path: Path,
    duration: float | None,
    settings: dict,
) -> dict:
    with audio_path.open("rb") as audio:
        audio_file_id = await get_audio_bucket().upload_from_stream(
            file_name,
            audio,
            metadata={"user_id": user_id, "content_type": content_type},
        )
    document = {
        "user_id": user_id,
        "source": source,
        "file_name": file_name,
        "audio_file_id": audio_file_id,
        "content_type": content_type,
        "duration": duration,
        **settings,
        "created_at": datetime.now(timezone.utc),
        "analysis": None,
    }
    result = await get_recordings().insert_one(document)
    return {**document, "_id": result.inserted_id}


async def list_recordings(user_id: str, skip: int, limit: int) -> tuple[list[dict], int, int]:
    collection = get_recordings()
    cursor = collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await collection.count_documents({"user_id": user_id})
    analysed = await collection.count_documents({"user_id": user_id, "analysis": {"$ne": None}})
    return items, total, analysed


async def get_recording(user_id: str, recording_id: str) -> dict:
    document = await get_recordings().find_one({"_id": _object_id(recording_id), "user_id": user_id})
    if document is None:
        raise RecordingNotFoundError
    return document


async def stream_audio(document: dict) -> AsyncIterator[bytes]:
    try:
        stream = await get_audio_bucket().open_download_stream(document["audio_file_id"])
    except NoFile as error:
        raise RecordingNotFoundError from error

    async def chunks() -> AsyncIterator[bytes]:
        try:
            while chunk := await stream.readchunk():
                yield chunk
        finally:
            await stream.close()

    return chunks()


async def download_audio(document: dict, path: Path) -> None:
    try:
        with path.open("wb") as destination:
            await get_audio_bucket().download_to_stream(document["audio_file_id"], destination)
    except NoFile as error:
        raise RecordingNotFoundError from error


async def save_analysis(user_id: str, recording_id: str, analysis: dict) -> dict:
    document = await get_recordings().find_one_and_update(
        {"_id": _object_id(recording_id), "user_id": user_id},
        {"$set": {"analysis": analysis}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise RecordingNotFoundError
    return document


async def delete_recording(user_id: str, recording_id: str) -> None:
    document = await get_recording(user_id, recording_id)
    try:
        await get_audio_bucket().delete(document["audio_file_id"])
    except NoFile:
        pass
    await get_recordings().delete_one({"_id": document["_id"]})
