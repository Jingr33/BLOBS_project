from blobs_project.frontend.actions import (
    HEADER_ACTIONS,
    ActionId,
    ActionPlace,
    HeaderAction,
    visible_actions,
)


def test_only_force_reset_is_visible_in_the_toolbar() -> None:
    toolbar = visible_actions(ActionPlace.TOOLBAR)

    assert ActionId.EXPORT_REPORT in HEADER_ACTIONS
    assert ActionId.EXPORT_REPORT not in toolbar
    assert set(toolbar) == {ActionId.FORCE_RESET}


def test_removed_header_actions_are_gone() -> None:
    values = {action_id.value for action_id in ActionId}

    assert values == {"force_reset", "export_report"}
    assert all(
        action.place is ActionPlace.TOOLBAR for action in HEADER_ACTIONS.values()
    )


def test_disabled_action_can_be_switched_on() -> None:
    original = HEADER_ACTIONS[ActionId.EXPORT_REPORT]
    try:
        HEADER_ACTIONS[ActionId.EXPORT_REPORT] = HeaderAction(
            ActionPlace.TOOLBAR, enabled=True
        )

        assert ActionId.EXPORT_REPORT in visible_actions(ActionPlace.TOOLBAR)
    finally:
        HEADER_ACTIONS[ActionId.EXPORT_REPORT] = original

    assert ActionId.EXPORT_REPORT not in visible_actions(ActionPlace.TOOLBAR)


def test_action_ids_are_unique_identifiers() -> None:
    values = [action_id.value for action_id in ActionId]

    assert len(values) == len(set(values))
    assert set(HEADER_ACTIONS) == set(ActionId)
