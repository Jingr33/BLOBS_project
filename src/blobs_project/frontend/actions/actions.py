from typing import Final

from .action_id import ActionId
from .action_place import ActionPlace
from .header_action import HeaderAction

HEADER_ACTIONS: Final[dict[ActionId, HeaderAction]] = {
    ActionId.FORCE_RESET: HeaderAction((ActionPlace.TOOLBAR,)),
    ActionId.IMPORT_CSV: HeaderAction((ActionPlace.REGULATION,)),
    ActionId.EXPORT_CSV: HeaderAction((ActionPlace.REGULATION,)),
}


def visible_actions(place: ActionPlace) -> dict[ActionId, HeaderAction]:
    return {
        action_id: action
        for action_id, action in HEADER_ACTIONS.items()
        if action.enabled and place in action.places
    }
