import pytest

from blobs_project.translations import (
    available_languages,
    current_language,
    set_language,
    tr,
)


def test_default_language_is_english() -> None:
    assert current_language() == "en"
    assert "en" in available_languages()


def test_translation_returns_string_for_known_key() -> None:
    assert tr("header.title") == "Process monitoring"
    assert tr("regulation.start_regulation") == "Start regulation"
    assert tr("regulation.stop_automatic") == "Stop automatic regulation"


def test_translation_formats_placeholders() -> None:
    assert (
        tr("regulation.profile_loaded", rows=3, step=5.0, total=15.0)
        == "Profile: 3 × 5 min = 15 min"
    )


def test_translation_falls_back_to_key_for_unknown_key() -> None:
    assert tr("missing.key") == "missing.key"


def test_unknown_language_is_rejected() -> None:
    with pytest.raises(ValueError):
        set_language("not-a-language")
