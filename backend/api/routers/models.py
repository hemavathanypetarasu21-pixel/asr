from typing import Annotated

from fastapi import APIRouter, Depends

from api.endpoints import models
from api.schemas import ModelsResponse
from src.auth import CurrentUser, get_optional_user

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelsResponse)
async def list_models(user: Annotated[CurrentUser | None, Depends(get_optional_user)]) -> ModelsResponse:
    return await models.list_models(user)
