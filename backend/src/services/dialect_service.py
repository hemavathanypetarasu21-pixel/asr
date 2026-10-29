"""Maps Whisper's Malay / Tamil language probabilities to Manglish / Tanglish."""

from dataclasses import dataclass

from src.config import settings

# Dialect id (matches api.schemas.Language values) -> Whisper language codes that count towards it.
# Whisper often labels Malay speech as Indonesian, so both count for Manglish.
DIALECT_LANGUAGES = {"manglish": ("ms", "id"), "tanglish": ("ta",)}


@dataclass(frozen=True)
class DialectResult:
    dialect: str | None
    confidence: float | None


def classify(probabilities: dict[str, float]) -> DialectResult:
    """
    Code-switched speech is mostly scored as English plus one of Malay or Tamil, so the dialect is
    decided by the Malay-vs-Tamil share. Confidence is the winning language's share of that pair.
    """
    scores = {
        dialect: sum(probabilities.get(language, 0.0) for language in languages)
        for dialect, languages in DIALECT_LANGUAGES.items()
    }
    combined = sum(scores.values())
    if combined < settings.DIALECT_DETECTION_MIN_CONFIDENCE:
        return DialectResult(dialect=None, confidence=None)

    dialect, best = max(scores.items(), key=lambda item: item[1])
    share = best / combined
    margin = share - (combined - best) / combined
    if margin < settings.DIALECT_DETECTION_MIN_MARGIN:
        return DialectResult(dialect=None, confidence=share)
    return DialectResult(dialect=dialect, confidence=share)
