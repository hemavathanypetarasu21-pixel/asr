from .analyse import router as analyse_router
from .languages import router as languages_router
from .models import router as models_router
from .modes import router as modes_router
from .recordings import router as recordings_router
from .settings import router as settings_router
from .speak import router as speak_router
from .upload import router as upload_router

routers = [
    speak_router,
    upload_router,
    languages_router,
    modes_router,
    models_router,
    recordings_router,
    analyse_router,
    settings_router,
]

__all__ = ["routers"]
