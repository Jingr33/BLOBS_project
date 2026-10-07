from dataclasses import dataclass

from .action_place import ActionPlace


@dataclass(frozen=True)
class HeaderAction:
    place: ActionPlace
    enabled: bool = True
