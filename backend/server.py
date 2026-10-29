"""Entry point: `python server.py` runs the API with host, port and reload taken from .env."""

from pathlib import Path

import uvicorn

from src.config import settings

BACKEND_DIR = Path(__file__).resolve().parent


def main() -> None:
    uvicorn.run(
        "app:app",
        app_dir=str(BACKEND_DIR),
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD,
        reload_dirs=[str(BACKEND_DIR)] if settings.SERVER_RELOAD else None,
    )


if __name__ == "__main__":
    main()
