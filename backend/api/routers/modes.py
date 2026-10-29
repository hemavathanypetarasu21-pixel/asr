from fastapi import APIRouter

from api.endpoints import modes
from api.schemas import ModeOption

router = APIRouter(prefix="/modes", tags=["modes"])


@router.get("", response_model=list[ModeOption])
async def list_modes() -> list[ModeOption]:
    return await modes.list_modes()
