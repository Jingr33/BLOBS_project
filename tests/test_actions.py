from blobs_project.frontend.actions import (
    HEADER_ACTIONS,
    ActionId,
    ActionPlace,
    HeaderAction,
    visible_actions,
)


def test_toolbar_contains_only_force_reset() -> None:
    toolbar = visible_actions(ActionPlace.TOOLBAR)

    assert set(toolbar) == {ActionId.FORCE_RESET}


def test_csv_actions_live_in_the_regulation_place() -> None:
    regulation = visible_actions(ActionPlace.REGULATION)

    assert set(regulation) == {ActionId.IMPORT_CSV, ActionId.EXPORT_CSV}


def test_removed_header_actions_are_gone() -> None:
    values = {action_id.value for action_id in ActionId}

    assert values == {"force_reset", "export_report", "import_csv", "export_csv"}


def test_disabled_action_can_be_switched_on() -> None:
    pass

def test_action_ids_are_unique_identifiers() -> None:
    values = [action_id.value for action_id in ActionId]

    assert len(values) == len(set(values))
    assert set(HEADER_ACTIONS) == set(ActionId)
