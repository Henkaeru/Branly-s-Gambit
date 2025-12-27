from __future__ import annotations
from pydantic import BaseModel, Field, RootModel, model_validator
from typing import Dict, Optional
import warnings
import systems.moves
from core.registry import registry
from core.dsl.random_dsl import RINT, RNUM, RSTR, RVAL, check

# ------------------------------
# Fighter Stats / Context
# ------------------------------
class FighterContext(BaseModel):
    hp: RINT = 100
    attack: RINT = 10
    defense: RINT = 10
    charge_bonus: RNUM = 0.0

    @model_validator(mode="after")
    def check_stats(self):
        for value in self.model_dump().values():
            check("x >= 0", x=value)
        return self

# ------------------------------
# Fighter Schema
# ------------------------------
class Fighter(BaseModel):
    id: str
    name: RSTR = "Unnamed Fighter"
    description: RSTR = "No description."

    # the sprite part is just a placeholder
    sprite: RSTR = "/a_default_spite"
    selection_sprite: RSTR = "/a_default_sprite_but_selction"
    animations: dict = Field(default_factory=dict)  # placeholder for animations

    stats: FighterContext = Field(default_factory=FighterContext)
    moves: list[str] = Field(default_factory=list)

    enabled: bool = True

    @model_validator(mode="after")
    def check_fighter(self):
        move_set = registry.get("moves").move_set
        for m in self.moves:
            if m not in move_set:
                raise ValueError(f"Fighter '{self.id}' references unknown move '{m}'")
        if len(self.moves) > 4:
            warnings.warn(f"Fighter '{self.id}' has more than 4 moves.", stacklevel=2)
        return self

# ------------------------------
# Fighter Root Model
# ------------------------------
class FighterSet(RootModel[list[Fighter]]):
    """
    Root model for a list of Fighter instances.
    Behaves like a dict keyed by fighter.id.
    """
    def model_post_init(self, __context=None):
        self._by_id: Dict[str, Fighter] = {}
        seen_ids = set()

        for fighter in self.root:
            if fighter.enabled:
                if fighter.id in seen_ids:
                    warnings.warn(f"Duplicate fighter id detected: '{fighter.id}'. Using last occurrence.", stacklevel=2)
                seen_ids.add(fighter.id)
                self._by_id[fighter.id] = fighter

        if not self._by_id:
            warnings.warn("FighterSet is empty!", stacklevel=2)

    def __getitem__(self, fighter_id: str) -> Fighter:
        if fighter_id not in self._by_id:
            raise ValueError(f"Fighter with id '{fighter_id}' does not exist in this FighterSet.")
        return self._by_id[fighter_id]

    def __iter__(self):
        return iter(self._by_id.items())

    def __len__(self):
        return len(self._by_id)

    def __repr__(self):
        return repr(self._by_id)

    @property
    def fighters(self):
        return list(self._by_id.values())
