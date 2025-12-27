# @ Battle system configuration
from dataclasses import dataclass

@dataclass(frozen=True)
class BattleConfig:
    MAX_PARTY_SIZE: int = 3
    CRIT_MULTIPLIER: float = 1.5
    BASE_ACCURACY: float = 0.95
    XP_CURVE: str = "medium_fast"
    STATUS_DURATION: int = 3
    TURN_ANIMATION_SPEED: float = 0.5
    RANDOM_SEED: int = 42
