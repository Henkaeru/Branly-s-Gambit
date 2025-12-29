from __future__ import annotations
from pydantic import BaseModel, Field, RootModel, model_validator
from typing import Dict, Optional
from core.dsl.random_dsl import RINT, RNUM, RSTR, RVAL, check
import warnings
from core.registry import registry

TYPE = ("dev", "opti", "syst", "data", "proj", "team", "none")
STATUS = ("javaBien", "poison")

# ------------------------------
# Fighter Stats
# ------------------------------
class FighterStats(BaseModel):
    hp: RINT = 100
    attack: RINT = 10
    defense: RINT = 10
    shield: RINT = 0
    charge: RNUM = 0.0
    charge_bonus: RNUM = 0.0

    @model_validator(mode="after")
    def check_stats(self):
        check("0 <= x <= 999", x=self.hp)
        check("0 <= x <= 999", x=self.attack)
        check("0 <= x <= 999", x=self.defense)
        check("0 <= x <= 999", x=self.shield)
        check("0.0 <= x <= 999", x=self.charge)
        check("0.0 <= x <= 10.0", x=self.charge_bonus)
        return self


Stat = tuple(FighterStats().model_dump().keys())

# ------------------------------
# Buff Schema
# ------------------------------
class Buff(BaseModel):
    stat: str
    amount: RNUM = 0.10 # optional: flat/percentage increase/decrease
    duration: int = 1   # optional: how long it lasts, -1 for infinite

    @model_validator(mode="after")
    def check_buff(self):
        check("x >= 0", x=self.amount)
        check("x >= -1", x=self.duration)
        try:
            check("x in stat", 
                    x=self.stat, stat=Stat)
        except ValueError:
            raise ValueError("Buff 'stat' must be a valid stat")
        return self

# ------------------------------
# Status Schema
# ------------------------------
class Status(BaseModel):
    id: str
    stacks: int = 1    # optional: number of stacks for stackable statuses
    duration: int = 1  # optional: how long it lasts, -1 for infinite

    @model_validator(mode="after")
    def check_status(self):
        check("x >= 0", x=self.stacks)
        check("x >= -1", x=self.duration)
        if self.id not in STATUS:
            raise ValueError(f"Invalid status id: {self.id}")
        return self

# To avoid circular imports while still loading the moves system.
# You could argue that the issue stems from putting buff and status
# definitions here instead of in their own module, but this is simpler
# and make more sense as buffs and statuses are tightly coupled with fighters
from ..import moves

# ------------------------------
# Fighter Schema
# ------------------------------
class Fighter(BaseModel):
    id: str
    name: RSTR = "Unnamed Fighter"
    description: RSTR = "No description."

    enabled: bool = True # whether this fighter is enabled in the game

    type: RSTR = "none" 
    category: RSTR = "wildcard" # see docs for categories

    # the sprite part is just a placeholder
    fighter_sprite: RSTR = "/fighters/battle_sprite/default.png"
    fighter_selection_sprite: RSTR = "/fighters/selection_sprite/default.png"
    animations: dict = Field(default_factory=dict)  # placeholder for animations

    stats: FighterStats = Field(default_factory=FighterStats) # base stats
    moves: list[str] = Field(default_factory=list) # list of move IDs (max 4)
    
    starting_stats: Optional[FighterStats] = Field(default_factory=FighterStats) # optional starting stats
    starting_buffs: list[Buff] = Field(default_factory=list) # optional starting buffs
    starting_status: list[Status] = Field(default_factory=list) # optional starting status effects

    @model_validator(mode="after")
    def check_fighter(self):
        try:
            check("1 <= len(x) <= 63", x=self.id)
        except ValueError:
            raise ValueError(f"Invalid fighter id: {self.id}")
        try:
            check("len(x) <= 127", x=self.name)
        except ValueError:
            raise ValueError(f"Invalid fighter name: {self.name}")
        try:
            check("len(x) <= 511", x=self.description)
        except ValueError:
            raise ValueError(f"Invalid fighter description: {self.description}")
        try:
            check("x in type", 
                  x=self.type, type=TYPE)
        except ValueError:
            raise ValueError(f"Invalid fighter type: {self.type}")
        move_set = registry.get("moves").set
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
    
    def keys(self):
        return self._by_id.keys()

    def values(self):
        return self._by_id.values()

    def items(self):
        return self._by_id.items()
    
    def get(self, fighter_id: str, default=None) -> Fighter | None:
        return self._by_id.get(fighter_id, default)

    def __contains__(self, key):
        return key in self._by_id
