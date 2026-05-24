from typing import Final

_NORMALIZER_TABLE: Final = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
    }
)


def str_normalizer(day: str) -> str:
    return day.lower().translate(_NORMALIZER_TABLE)
