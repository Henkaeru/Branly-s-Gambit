# @ Fighter configuration
from dataclasses import dataclass, field

@dataclass(frozen=True)
class FighterConfig:
    DEFAULT_STATS: dict = field(default_factory=lambda: {
        "max_hp": 100,
        "attack": 50,
        "defense": 50,
        "speed": 50,
        "special": 50,
    })

    FIGHTERS: dict = field(default_factory=lambda: {
        "Prof": {
            "sprite": "assets/fighters/prof.png",
            "types": ["Knowledge", "Fire"],
            "moves": ["Lecture", "Fire Chalk", "Punch", "Detention"],
            "stats": {"attack": 60, "defense": 40, "special": 70},
        },
        "Student": {
            "sprite": "assets/fighters/student.png",
            "types": ["Normal"],
            "moves": ["Punch", "Kick"],
            "stats": {"speed": 70, "attack": 55},
        },
    })
