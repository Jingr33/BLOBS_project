from dataclasses import dataclass

from .action_place import ActionPlace


@dataclass(frozen=True)
class HeaderAction:
    places: tuple[ActionPlace, ...]
    enabled: bool = True
