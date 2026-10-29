from api.schemas import LANGUAGE_LABELS, LanguageOption


async def list_languages() -> list[LanguageOption]:
    return [LanguageOption(id=language, label=label) for language, label in LANGUAGE_LABELS.items()]
