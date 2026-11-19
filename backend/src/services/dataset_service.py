"""Read access to the imported speech dataset clips (shared by all users, read-only in the app)."""

from collections.abc import AsyncIterator

from bson import ObjectId
from bson.errors import InvalidId
from gridfs.errors import NoFile

from src.db import get_dataset_audio_bucket, get_dataset_clips


class DatasetClipNotFoundError(Exception):
    pass


async def list_clips(filters: dict, skip: int, limit: int) -> tuple[list[dict], int]:
    collection = get_dataset_clips()
    items = await collection.find(filters).sort("_id", 1).skip(skip).limit(limit).to_list(length=limit)
    return items, await collection.count_documents(filters)


async def summary() -> list[dict]:
    """Clip count and hours per language and split, over the whole dataset."""
    pipeline = [
        {"$group": {"_id": {"language": "$language", "split": "$split"}, "clips": {"$sum": 1}, "seconds": {"$sum": "$duration"}}},
        {"$sort": {"_id.language": 1, "_id.split": 1}},
    ]
    rows = await (await get_dataset_clips().aggregate(pipeline)).to_list(length=None)
    return [{**row["_id"], "clips": row["clips"], "hours": row["seconds"] / 3600} for row in rows]


async def stream_audio(clip_id: str) -> tuple[AsyncIterator[bytes], str]:
    try:
        document = await get_dataset_clips().find_one({"_id": ObjectId(clip_id)})
    except InvalidId as error:
        raise DatasetClipNotFoundError from error
    if document is None:
        raise DatasetClipNotFoundError
    try:
        stream = await get_dataset_audio_bucket().open_download_stream(document["audio_file_id"])
    except NoFile as error:
        raise DatasetClipNotFoundError from error

    async def chunks() -> AsyncIterator[bytes]:
        try:
            while chunk := await stream.readchunk():
                yield chunk
        finally:
            await stream.close()

    return chunks(), document.get("content_type", "audio/wav")
