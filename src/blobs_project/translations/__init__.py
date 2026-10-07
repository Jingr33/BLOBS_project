from __future__ import annotations

from typing import Final

from . import en

DEFAULT_LANGUAGE: Final = "en"

_TRANSLATIONS: dict[str, dict[str, str]] = {"en": en.STRINGS}
_current_language: str = DEFAULT_LANGUAGE


def available_languages() -> tuple[str, ...]:
    return tuple(sorted(_TRANSLATIONS))


def current_language() -> str:
    return _current_language


def set_language(language: str) -> None:
    global _current_language
    if language not in _TRANSLATIONS:
        raise ValueError(f"Unsupported language {language!r}")
    _current_language = language


def register_language(language: str, strings: dict[str, str]) -> None:
    _TRANSLATIONS[language] = strings


def tr(key: str, **values: object) -> str:
    template = _TRANSLATIONS.get(_current_language, {}).get(key)
    if template is None:
        template = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if not values:
        return template
    try:
        return template.format(**values)
    except (KeyError, IndexError):
        return template
