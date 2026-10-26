from blobs_project.frontend.actions import (
    HEADER_ACTIONS,
    ActionId,
    ActionPlace,
    HeaderAction,
    visible_actions,
)


def test_every_action_is_registered() -> None:
    assert set(HEADER_ACTIONS) == set(ActionId)


def test_header_offers_only_the_sensor_tare() -> None:
    assert list(visible_actions(ActionPlace.HEADER)) == [ActionId.TARE]


def test_settings_offer_csv_management() -> None:
    assert list(visible_actions(ActionPlace.SETTINGS)) == [
        ActionId.EXPORT_CSV,
        ActionId.IMPORT_CSV,
        ActionId.DOWNLOAD_CSV_TEMPLATE,
    ]


def test_disabled_action_is_hidden_from_users() -> None:
    original = HEADER_ACTIONS[ActionId.EXPORT_CSV]
    try:
        HEADER_ACTIONS[ActionId.EXPORT_CSV] = HeaderAction(
            (ActionPlace.SETTINGS,), enabled=False
        )

        assert ActionId.EXPORT_CSV not in visible_actions(ActionPlace.SETTINGS)
    finally:
        HEADER_ACTIONS[ActionId.EXPORT_CSV] = original

    assert ActionId.EXPORT_CSV in visible_actions(ActionPlace.SETTINGS)
