from typing import Annotated

from fastapi import APIRouter, Depends

from api.endpoints import settings
from api.schemas import ApiKeyUpdate, PreferencesUpdate, SettingsResponse
from src.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

User = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("", response_model=SettingsResponse)
async def get_settings(user: User) -> SettingsResponse:
    return await settings.get_settings(user)


@router.put("/preferences", response_model=SettingsResponse)
async def update_preferences(update: PreferencesUpdate, user: User) -> SettingsResponse:
    return await settings.update_preferences(user, update)


@router.put("/api-keys/gemini", response_model=SettingsResponse)
async def save_gemini_api_key(update: ApiKeyUpdate, user: User) -> SettingsResponse:
    return await settings.save_gemini_api_key(user, update)


@router.delete("/api-keys/gemini", response_model=SettingsResponse)
async def delete_gemini_api_key(user: User) -> SettingsResponse:
    return await settings.delete_gemini_api_key(user)
