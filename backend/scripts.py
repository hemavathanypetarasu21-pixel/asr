"""Scaffolds api/{endpoints,schemas,routers} with one module per UI control. Existing files are never overwritten."""

from pathlib import Path

PATH = Path(__file__).resolve().parent / "api"
folders = ["endpoints", "schemas", "routers"]
files = [
    # chat
    "speak",  # button: record from the microphone, saved on stop
    "upload",  # button: upload an audio file
    "languages",  # dropdown menu: tanglish / manglish
    "modes",  # dropdown menu: native / non-native speaker
    "models",  # dropdown menus: dialect recognition models / translation models
    # insights
    "recordings",  # accordion list, audio playback, delete
    "analyse",  # button: detect dialect + translate to English
    # settings (avatar menu)
    "settings",  # theme, recording defaults, API keys
]


def scaffold() -> None:
    (PATH / "__init__.py").touch()
    for folder in folders:
        directory = PATH / folder
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").touch()
        for name in files:
            module = directory / f"{name}.py"
            if not module.exists():
                module.touch()
                print(f"created {module}")


if __name__ == "__main__":
    scaffold()
