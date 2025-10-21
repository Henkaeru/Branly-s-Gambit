from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .status import Status

@dataclass
class Character:
    config_key: str
    name: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    charge_bonus: float
    moveset: List[str]
    charge_move: str
    charge: float = 0.0
    statuses: Dict[str, Status] = field(default_factory=dict)
    color: Tuple[int, int, int] = (100, 100, 255)

    def is_alive(self) -> bool:
        return self.hp > 0

    def add_status(self, name: str, turns: Optional[int], magnitude: int = 0):
        self.statuses[name] = Status(name, turns, magnitude)

    def remove_status(self, name: str):
        self.statuses.pop(name, None)

    def get_roll_modifier(self) -> int:
        mod = 0
        if "javaBien" in self.statuses: mod += 3
        if "jeudiSoir" in self.statuses: mod += 4
        if "retour2Cuite" in self.statuses: mod -= 2
        return mod

    def tick_statuses(self):
        expired = []
        for name, s in list(self.statuses.items()):
            if s.turns_left is not None:
                s.turns_left -= 1
                if s.turns_left <= 0:
                    if name == "jeudiSoir":
                        self.add_status("retour2Cuite", None)
                    expired.append(name)
        for n in expired:
            self.remove_status(n)
