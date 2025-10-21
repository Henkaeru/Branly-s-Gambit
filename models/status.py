from dataclasses import dataclass
from typing import Optional

@dataclass
class Status:
    name: str
    turns_left: Optional[int]
    magnitude: int = 0
