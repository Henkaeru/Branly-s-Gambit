# @ Type matchups
from dataclasses import dataclass, field

@dataclass(frozen=True)
class TypeConfig:
    TYPE_CHART: dict = field(default_factory=lambda: {
        "Fire": {"strong_against": ["Grass"], "weak_against": ["Water"]},
        "Water": {"strong_against": ["Fire"], "weak_against": ["Electric"]},
        "Electric": {"strong_against": ["Water"], "weak_against": ["Ground"]},
        "Knowledge": {"strong_against": ["Ignorance"], "weak_against": ["Overload"]},
        "Normal": {"strong_against": [], "weak_against": []},
    })
