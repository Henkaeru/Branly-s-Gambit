from __future__ import annotations
import copy
from pydantic import Field, RootModel, model_validator
from typing import Dict, Optional
from core.dsl.random_dsl import RINT, RNUM, RSTR, RVAL, check
import warnings
from core.dsl.resolvable import ResolvableModel
from core.registry import registry

TYPE = ("dev", "opti", "syst", "data", "proj", "team", "none")
STATUS = ("javaBien", "poison")
DEFAULT_STARTING_SHIELD = 0
DEFAULT_STARTING_CHARGE = 0
MAX_BUFFS = 4
MAX_HP = 999
MAX_ATTACK = 999
MAX_DEFENSE = 999
MAX_SHIELD = 999
MAX_CHARGE = 999
MAX_CHARGE_BONUS = 10.0

# ------------------------------
# Fighter Stats
# ------------------------------
class FighterStats(ResolvableModel):
    hp: RINT = 300
    attack: RINT = 100
    defense: RINT = 100
    shield: RINT = None  # if None, defaults to hp at start
    charge: RINT = 999
    charge_bonus: RNUM = 0.0

    @model_validator(mode="after")
    def check_stats(self):
        if self.shield is None:
            self.shield = self.hp
        check("0 <= hp <= max_hp", hp=self.hp, max_hp=MAX_HP)
        check("0 <= attack <= max_attack", attack=self.attack, max_attack=MAX_ATTACK)
        check("0 <= defense <= max_defense", defense=self.defense, max_defense=MAX_DEFENSE)
        check("0 <= shield <= max_shield", shield=self.shield, max_shield=MAX_SHIELD)
        check("0 <= charge <= max_charge", charge=self.charge, max_charge=MAX_CHARGE)
        check("0.0 <= charge_bonus <= max_charge_bonus", charge_bonus=self.charge_bonus, max_charge_bonus=MAX_CHARGE_BONUS)
        check("shield <= hp", shield=self.shield, hp=self.hp)
        return self


Stat = tuple(FighterStats().model_dump().keys())

# ------------------------------
# Buff Schema
# ------------------------------
class Buff(ResolvableModel):
    stat: str
    amount: RNUM = 0.10 # optional: flat/percentage increase/decrease
    duration: int = 1   # optional: how long it lasts, -1 for infinite

    @model_validator(mode="after")
    def check_buff(self):
        check("amount >= 0", amount=self.amount)
        check("duration >= -1", duration=self.duration)
        try:
            check("stat in stats", 
                    stat=self.stat, stats=Stat)
        except ValueError:
            raise ValueError("Buff 'stat' must be a valid stat")
        return self

# ------------------------------
# Status Schema
# ------------------------------
class Status(ResolvableModel):
    id: str
    stacks: int = 1    # optional: number of stacks for stackable statuses
    duration: int = 1  # optional: how long it lasts, -1 for infinite

    @model_validator(mode="after")
    def check_status(self):
        check("stacks >= 0", stacks=self.stacks)
        check("duration >= -1", duration=self.duration)
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
class Fighter(ResolvableModel):
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
    
    starting_stats: Optional[FighterStats] = None # optional starting stats
    starting_buffs: list[Buff] = Field(default_factory=list) # optional starting buffs
    starting_status: list[Status] = Field(default_factory=list) # optional starting status effects

    @model_validator(mode="after")
    def check_fighter(self):
        try:
            check("1 <= len(id) <= 63", id=self.id)
        except ValueError:
            raise ValueError(f"Invalid fighter id: {self.id}")
        try:    
            check("len(name) <= 127", name=self.name)
        except ValueError:
            raise ValueError(f"Invalid fighter name: {self.name}")
        try:
            check("len(description) <= 511", description=self.description)
        except ValueError:
            raise ValueError(f"Invalid fighter description: {self.description}")
        try:
            check("type in types", 
                  type=self.type, types=TYPE)
        except ValueError:
            raise ValueError(f"Invalid fighter type: {self.type}")
        move_set = registry.get("moves").set
        for m in self.moves:
            if m not in move_set:
                raise ValueError(f"Fighter '{self.id}' references unknown move '{m}'")
        if len(self.moves) > 4:
            raise ValueError(f"Fighter '{self.id}' has more than 4 moves.")
        # --- Build starting_stats by merging defaults + overrides ---
        base_stats = copy.deepcopy(self.stats)

        if self.starting_stats is not None:
            for field_name in self.starting_stats.model_fields_set:
                value = getattr(self.starting_stats, field_name)
                setattr(base_stats, field_name, value)

        self.starting_stats = base_stats

        # Apply default starting overrides (unless explicitly set)
        explicit = self.starting_stats.model_fields_set if self.starting_stats else set()

        if "shield" not in explicit:
            self.starting_stats.shield = DEFAULT_STARTING_SHIELD

        if "charge" not in explicit:
            self.starting_stats.charge = DEFAULT_STARTING_CHARGE
        for field_name in self.stats.model_fields:
            max_value = getattr(self.stats, field_name)
            start_value = getattr(self.starting_stats, field_name)
            check("start_value <= max_value", start_value=start_value, max_value=max_value)
        if len(self.starting_buffs) > MAX_BUFFS:
            raise ValueError(f"Fighter '{self.id}' has more than {MAX_BUFFS} starting buffs.")
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
