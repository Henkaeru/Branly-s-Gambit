# @ AI difficulty configuration
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AIConfig:
    DIFFICULTY_LEVELS: dict = field(default_factory=lambda: {
        "Easy": {"use_best_move_chance": 0.5, "heal_threshold": 0.2},
        "Normal": {"use_best_move_chance": 0.7, "heal_threshold": 0.3},
        "Hard": {"use_best_move_chance": 0.9, "heal_threshold": 0.5},
    })
