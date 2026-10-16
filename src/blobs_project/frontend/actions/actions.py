from typing import Final

from .action_id import ActionId
from .action_place import ActionPlace
from .header_action import HeaderAction

HEADER_ACTIONS: Final[dict[ActionId, HeaderAction]] = {
    ActionId.EXPORT_CSV: HeaderAction((ActionPlace.HEADER,)),
    ActionId.FORCE_RESET: HeaderAction((ActionPlace.HEADER,)),
    ActionId.IMPORT_CSV: HeaderAction((ActionPlace.REGULATION,)),
    ActionId.DOWNLOAD_CSV_TEMPLATE: HeaderAction((ActionPlace.HEADER,)),
    ActionId.TARE: HeaderAction((ActionPlace.HEADER,)),
}


def visible_actions(place: ActionPlace) -> dict[ActionId, HeaderAction]:
    return {
        action_id: action
        for action_id, action in HEADER_ACTIONS.items()
        if action.enabled and place in action.places
    }
