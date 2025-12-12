# @ Move definitions
from dataclasses import dataclass, field

@dataclass(frozen=True)
class MoveConfig:
    MOVES: dict = field(default_factory=lambda: {
        "Punch": {
            "type": "Physical",
            "power": 40,
            "accuracy": 1.0,
            "category": "Normal",
            "animation": "punch_anim.png",
            "status_effect": None,
        },
        "Fire Chalk": {
            "type": "Special",
            "power": 60,
            "accuracy": 0.9,
            "category": "Fire",
            "status_effect": "Burn",
        },
        "Lecture": {
            "type": "Special",
            "power": 20,
            "accuracy": 1.0,
            "category": "Psychic",
            "status_effect": "Confuse",
        },
        "Detention": {
            "type": "Status",
            "power": 0,
            "accuracy": 0.9,
            "category": "Control",
            "status_effect": "Stun",
        },
    })
