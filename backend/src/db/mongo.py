from gridfs import AsyncGridFSBucket
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from src.config import settings

RECORDINGS_COLLECTION = "recordings"
USER_SETTINGS_COLLECTION = "user_settings"
AUDIO_BUCKET = "audio"

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None


async def connect_database() -> None:
    global _client, _database
    _client = AsyncMongoClient(settings.MONGODB_URI)
    _database = _client[settings.MONGODB_DB_NAME]
    await _database.command("ping")
    await get_recordings().create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    await get_user_settings().create_index("user_id", unique=True)


async def close_database() -> None:
    if _client is not None:
        await _client.close()


def _db() -> AsyncDatabase:
    if _database is None:
        raise RuntimeError("Database is not connected.")
    return _database


def get_recordings() -> AsyncCollection:
    return _db()[RECORDINGS_COLLECTION]


def get_user_settings() -> AsyncCollection:
    return _db()[USER_SETTINGS_COLLECTION]


def get_audio_bucket() -> AsyncGridFSBucket:
    return AsyncGridFSBucket(_db(), bucket_name=AUDIO_BUCKET)
