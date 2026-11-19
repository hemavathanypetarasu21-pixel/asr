"""Romanises Tamil script the way Tanglish is usually typed (e.g. நான் வரேன் -> naan varen).

Tamil has no single romanisation standard, so these rules aim for the common informal spelling:
long vowels are doubled, stops are voiced between vowels (வகுப்பு -> vaguppu), and nasal + stop
clusters are voiced (வந்து -> vandhu). Non-Tamil characters (English words, digits, punctuation)
pass through unchanged, so code-mixed text keeps its English words.
"""

import re

VIRAMA = "்"

INDEPENDENT_VOWELS = {
    "அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo",
    "எ": "e", "ஏ": "e", "ஐ": "ai", "ஒ": "o", "ஓ": "o", "ஔ": "au",
}
VOWEL_SIGNS = {
    "ா": "aa", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo",
    "ெ": "e", "ே": "e", "ை": "ai", "ொ": "o", "ோ": "o", "ௌ": "au",
}
# consonant -> (word-initial or after a consonant, between vowels, doubled)
CONSONANTS = {
    "க": ("k", "g", "kk"), "ச": ("s", "s", "ch"), "ட": ("t", "d", "tt"), "த": ("th", "dh", "tth"),
    "ப": ("p", "b", "pp"), "ற": ("r", "r", "tr"),
    "ங": ("ng", "ng", "ng"), "ஞ": ("nj", "nj", "nj"), "ண": ("n", "n", "nn"), "ந": ("n", "n", "nn"),
    "ம": ("m", "m", "mm"), "ன": ("n", "n", "nn"), "ய": ("y", "y", "yy"), "ர": ("r", "r", "rr"),
    "ல": ("l", "l", "ll"), "வ": ("v", "v", "vv"), "ழ": ("zh", "zh", "zh"), "ள": ("l", "l", "ll"),
    "ஜ": ("j", "j", "jj"), "ஷ": ("sh", "sh", "sh"), "ஸ": ("s", "s", "ss"), "ஹ": ("h", "h", "h"),
    "ஶ": ("sh", "sh", "sh"),
}
# Nasal + stop clusters are voiced in speech.
NASAL_CLUSTERS = {
    ("ங", "க"): "ng", ("ஞ", "ச"): "nj", ("ண", "ட"): "nd", ("ந", "த"): "ndh",
    ("ம", "ப"): "mb", ("ன", "ற"): "ndr",
}
# Other clusters with a conventional spelling (காட்சி -> kaatchi).
CLUSTERS = {("ட", "ச"): "tch"}
SPECIAL = {"ஸ்ரீ": "sri", "க்ஷ": "ksh", "ஃ": "h"}

_TAMIL_RE = re.compile(r"[஀-௿]")


def contains_tamil(text: str) -> bool:
    return bool(_TAMIL_RE.search(text))


def _syllables(word: str) -> list[tuple[str, str | None, bool]]:
    """Splits a Tamil word into (consonant or independent vowel, vowel sign, has_virama) units."""
    units: list[tuple[str, str | None, bool]] = []
    for char in word:
        if char in VOWEL_SIGNS and units and units[-1][0] in CONSONANTS:
            base, _, _ = units[-1]
            units[-1] = (base, char, False)
        elif char == VIRAMA and units and units[-1][0] in CONSONANTS:
            base, _, _ = units[-1]
            units[-1] = (base, None, True)
        else:
            units.append((char, None, False))
    return units


def _romanise_word(word: str) -> str:
    for tamil, latin in SPECIAL.items():
        word = word.replace(tamil, f"\u0000{latin}\u0000")
    out: list[str] = []
    units = _syllables(word)
    skip_next_consonant = False
    for index, (base, sign, dead) in enumerate(units):
        previous = units[index - 1] if index > 0 else None
        following = units[index + 1] if index + 1 < len(units) else None

        if base in INDEPENDENT_VOWELS:
            out.append(INDEPENDENT_VOWELS[base])
            continue
        if base not in CONSONANTS:
            out.append(base)
            continue

        if skip_next_consonant:
            # Second half of a doubled consonant or nasal cluster, already written.
            skip_next_consonant = False
        elif dead and following and following[0] == base:
            out.append(CONSONANTS[base][2])
            skip_next_consonant = True
        elif dead and following and (base, following[0]) in NASAL_CLUSTERS:
            out.append(NASAL_CLUSTERS[(base, following[0])])
            skip_next_consonant = True
        elif dead and following and (base, following[0]) in CLUSTERS:
            out.append(CLUSTERS[(base, following[0])])
            skip_next_consonant = True
        else:
            initial, medial, _ = CONSONANTS[base]
            # Stops are voiced only between vowels, not before another consonant (எகிப்து -> egipthu).
            between_vowels = not dead and previous is not None and not previous[2] and previous[0] != "\u0000"
            out.append(medial if between_vowels else initial)

        if dead:
            continue
        out.append(VOWEL_SIGNS[sign] if sign else "a")
    latin = "".join(out).replace("\u0000", "")
    # A final long "aa" is normally typed short (அம்மா -> amma).
    return latin[:-1] if latin.endswith("aa") and len(latin) > 3 else latin


def romanise(text: str) -> str:
    """Romanises every Tamil word in `text`; other words are returned unchanged."""
    if not contains_tamil(text):
        return text
    return re.sub(r"[஀-௿]+", lambda match: _romanise_word(match.group(0)), text)
