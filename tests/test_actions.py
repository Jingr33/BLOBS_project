from blobs_project.frontend.actions import (
    HEADER_ACTIONS,
    ActionId,
    ActionPlace,
    HeaderAction,
    visible_actions,
)


def test_every_action_is_registered() -> None:
    assert set(HEADER_ACTIONS) == set(ActionId)


def test_header_offers_export_csv_before_other_actions() -> None:
    assert list(visible_actions(ActionPlace.HEADER)) == [
        ActionId.EXPORT_CSV,
        ActionId.DOWNLOAD_CSV_TEMPLATE,
        ActionId.TARE,
    ]


def test_regulation_place_offers_only_import_csv() -> None:
    assert list(visible_actions(ActionPlace.REGULATION)) == [ActionId.IMPORT_CSV]


def test_disabled_action_is_hidden_from_users() -> None:
    original = HEADER_ACTIONS[ActionId.IMPORT_CSV]
    try:
        HEADER_ACTIONS[ActionId.IMPORT_CSV] = HeaderAction(
            (ActionPlace.REGULATION,), enabled=False
        )

        assert ActionId.IMPORT_CSV not in visible_actions(ActionPlace.REGULATION)
    finally:
        HEADER_ACTIONS[ActionId.IMPORT_CSV] = original

    assert ActionId.IMPORT_CSV in visible_actions(ActionPlace.REGULATION)
