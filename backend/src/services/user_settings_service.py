"""Per-user preferences and encrypted API keys (user_settings collection, one document per user)."""

from datetime import datetime, timezone

from pymongo import ReturnDocument

from src.db import get_user_settings
from src.services import crypto_service

_KEY_HINT_LENGTH = 4


async def get_settings(user_id: str) -> dict:
    return await get_user_settings().find_one({"user_id": user_id}) or {"user_id": user_id}


async def update_preferences(user_id: str, preferences: dict) -> dict:
    return await get_user_settings().find_one_and_update(
        {"user_id": user_id},
        {"$set": {**preferences, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


async def set_gemini_api_key(user_id: str, api_key: str) -> dict:
    return await get_user_settings().find_one_and_update(
        {"user_id": user_id},
        {
            "$set": {
                "gemini_api_key": crypto_service.encrypt(api_key),
                "gemini_api_key_hint": api_key[-_KEY_HINT_LENGTH:],
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


async def delete_gemini_api_key(user_id: str) -> dict:
    return await get_user_settings().find_one_and_update(
        {"user_id": user_id},
        {"$unset": {"gemini_api_key": "", "gemini_api_key_hint": ""}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


async def get_gemini_api_key(user_id: str) -> str | None:
    document = await get_user_settings().find_one({"user_id": user_id}, {"gemini_api_key": 1})
    token = (document or {}).get("gemini_api_key")
    return crypto_service.decrypt(token) if token else None
