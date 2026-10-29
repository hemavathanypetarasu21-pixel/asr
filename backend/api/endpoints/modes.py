from api.schemas import MODE_LABELS, ModeOption


async def list_modes() -> list[ModeOption]:
    return [ModeOption(id=mode, label=label) for mode, label in MODE_LABELS.items()]
