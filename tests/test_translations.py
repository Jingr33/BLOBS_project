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
    assert tr("regulation.stop_self_driven") == "Stop self-driven regulation"


def test_translation_formats_placeholders() -> None:
    assert tr("status.action_selected", label="Restart") == "Restart selected"
    assert (
        tr("status.profile_loaded", rows=120, duration=120.0)
        == "Profile loaded (120 rows / 120 s)"
    )


def test_translation_falls_back_to_key_for_unknown_key() -> None:
    assert tr("missing.key") == "missing.key"


def test_unknown_language_is_rejected() -> None:
    with pytest.raises(ValueError):
        set_language("not-a-language")
