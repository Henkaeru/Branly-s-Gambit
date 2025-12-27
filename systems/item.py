# @ Item configuration
from dataclasses import dataclass, field

@dataclass(frozen=True)
class ItemConfig:
    ITEMS: dict = field(default_factory=lambda: {
        "Coffee": {"effect": "restore_hp", "value": 30, "description": "Restores 30 HP."},
        "Notebook": {"effect": "boost_attack", "value": 10, "description": "Increases attack for 3 turns."},
        "Calculator": {"effect": "boost_special", "value": 15, "description": "Increases special attack."},
    })
