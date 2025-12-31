from __future__ import annotations
import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from systems.battle.schema import FighterVolatile
    
from pydantic import Field, RootModel, model_validator
from typing import Annotated, Dict, Literal, Optional, Union
from core.dsl.random_dsl import NUM, RINT, RNUM, RSTR, RVAL, check
import re
import warnings

from core.dsl.resolvable import ResolvableModel
from ..fighters.schema import FighterStats

Stat = tuple(FighterStats().model_dump().keys())
Target = ("self", "opponent")

COLOR = (
    "black", "dark_blue", "dark_green", "dark_aqua", "dark_red", "dark_purple",
    "gold", "gray", "dark_gray", "blue", "green", "aqua", "red", "light_purple", "yellow", "white"
)

STYLE = ("bold", "italic", "underlined", "strikethrough", "obfuscated")

STATUS = ("javaBien", "poison")

CONDITION = ("hp_below", "hp_above", "has_status", "lacks_status")

TYPE = ("dev", "opti", "syst", "data", "proj", "team", "none")

CATEGORY = ("damage", "support", "special", "none")

CHARGE_BONUS = 0.5  # % of base power at full charge
STAB_BONUS = 1.25    # STAB multiplier
    
# ------------------------------
# Full Move Context with defaults
# ------------------------------
class MoveContext(ResolvableModel):
    amount: RNUM = 0
    chance: RNUM = 1.0

    calc_target: RSTR = "self"
    calc_field: RSTR = "hp"

    mult: RNUM = 1.0
    flat: RINT = 0

    duration: RINT = -1

    @property
    def is_percentage(self) -> bool:
        """Whether `amount` is meant to be a percentage."""
        return isinstance(self.amount, float)
    
    def get_calc_target(self, user: FighterVolatile, target: FighterVolatile) -> FighterVolatile:
        """Get the target fighter based on calc_target."""
        if self.calc_target == "self":
            return user
        elif self.calc_target == "opponent":
            return target
        else:
            raise ValueError(f"Invalid calc_target '{self.calc_target}'")

    def get_calc_target_field_value(self, user: FighterVolatile, target: FighterVolatile) -> NUM:
        """The value of the field we are scaling against (hp, attack, etc.)."""
        return getattr(self.get_calc_target(user, target).current_fighter.stats, self.calc_field)

    def get_base_amount(self, user: FighterVolatile, target: FighterVolatile) -> NUM:
        """The base amount before any calculation."""
        if self.is_percentage:
            return self.amount * self.get_calc_target_field_value(user, target)
        return self.amount

    @model_validator(mode="after")
    def check_context(self):
        check("amount >= 0", amount=self.amount)
        check("0 <= chance <= 1", chance=self.chance)
        check("mult >= 0", mult=self.mult)
        check("duration >= -1", duration=self.duration)
        try:
            check("calc_target in target", 
                  calc_target=self.calc_target, target=Target)
        except ValueError:
            raise ValueError("MoveContext 'calc_target' must be 'self' or 'opponent'.")
        try:
            check("calc_field in stat", 
                  calc_field=self.calc_field, stat=Stat)
        except ValueError:
            raise ValueError("MoveContext 'calc_field' must be a valid stat.")
        try:
            check("amount + flat >= 0", 
                  amount=self.amount, flat=self.flat)
        except ValueError:
            raise ValueError("MoveContext 'amount' and 'flat' cannot sum to negative.")
        return self

# ------------------------------
# ActionBase
# ------------------------------
class ActionBase(ResolvableModel):
    id: str

    model_config = {
        "extra": "allow"
    }

    @property
    def params(self) -> dict:
        return {k: v for k, v in self.model_dump(exclude_none=True).items() if k != "id"}

# ------------------------------
# Leaf Actions
# ------------------------------
class DamageAction(ResolvableModel):
    id: Literal["damage"]
    crit_chance: RNUM = 0.0
    crit_damage: RNUM = 1.0
    piercing: RNUM = 0.0

    @model_validator(mode="after")
    def check_damage(self):
        check("0 <= crit_chance <= 1", crit_chance=self.crit_chance)
        check("crit_damage >= 0", crit_damage=self.crit_damage)
        check("0 <= piercing <= 1", piercing=self.piercing)
        return self
    
    @property
    def is_critical(self) -> bool:
        """Determine if the hit is a critical hit based on crit_chance."""
        return random.random() < self.crit_chance
    
class BuffAction(ResolvableModel):
    id: Literal["buff"]
    stats: list[RSTR] | RSTR = "attack"

    @model_validator(mode="after")
    def check_buff(self):
        stats = [self.stats] if not isinstance(self.stats, list) else self.stats
        for stat in stats:
            try:
                check("stat in stats", 
                      stat=stat, stats=Stat)
            except ValueError:
                raise ValueError("Buff 'stat' must be a valid stat or list of stats.")
        return self

class ShieldAction(ActionBase):
    id: Literal["shield"]

class HealAction(ActionBase):
    id: Literal["heal"]

class ModifyAction(ResolvableModel):
    id: Literal["modify"]
    field: RSTR
    value: RVAL

    @model_validator(mode="after")
    def check_modify(self):
        pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
        try:
            check(
                "re.fullmatch(pattern, field) is not None",
                field=self.field,
                pattern=pattern,
                re=re,  # pass re module explicitly
            )
        except ValueError:
            raise ValueError("field must be a dot-path of identifiers (e.g. 'foo.bar_baz')")
        return self

class TextAction(ResolvableModel):
    id: Literal["text"]
    text: RSTR = "No text."
    style: RSTR = "{}"

@model_validator(mode="after")
def check_text(self):
    check("len(text) < 511", text=self.text)

    try:
        check("style.startswith('{') and style.endswith('}')", style=self.style)
    except ValueError:
        raise ValueError(
            "TextAction 'style' must be a dict-like string "
            "(e.g. '{\"color\":\"red\",\"bold\":true}')"
        )

    try:
        check("json.loads(style.replace(\"'\", '\"')).get('color') in color", 
              style=self.style, color=COLOR)
    except ValueError:
        raise ValueError(
            "TextAction 'style' contains invalid color flags."
        )

    try:
        check(
            "all(k in style and isinstance(v, bool) "
            "for k,v in json.loads(style.replace(\"'\", '\"')).items() if k != 'color')", 
            style=self.style, style=STYLE)
    except ValueError:
        raise ValueError(
            "TextAction 'style' contains invalid style flags."
        )

    return self
    
# ------------------------------
# Status / Condition
# ------------------------------

class Status(ResolvableModel):
    id: str

    @model_validator(mode="after")
    def check_status(self):
        try:
            check("status in statuses", 
                  status=self.id, statuses=STATUS)
        except ValueError:
            raise ValueError(f"Invalid status id: {self.id}")
        return self

class Condition(ResolvableModel):
    id: str
    value: RVAL

    @model_validator(mode="after")
    def check_condition(self):
        try:
            check("condition in conditions", 
                  condition=self.id, conditions=CONDITION)
        except ValueError:
            raise ValueError(f"Invalid condition id: {self.id}")
        return self

class StatusAction(ActionBase):
    id: Literal["status"]
    operation: RSTR = "add"
    status: list[Status]

    @model_validator(mode="after")
    def check_status_action(self):
        try:
            check("operation in ('add', 'remove')", operation=self.operation)
        except ValueError:
            raise ValueError("StatusAction 'operation' must be 'add' or 'remove'.")
        if not self.status:
            raise ValueError("StatusAction must have at least one status.")
        return self

class ConditionAction(ActionBase):
    id: Literal["condition"]
    conditions: list[Condition]
    actions: list[Action]

    @model_validator(mode="after")
    def check_condition(self):
        if not self.conditions:
            raise ValueError("ConditionAction must have at least one condition.")
        if not self.actions:
            raise ValueError("ConditionAction must have at least one action.")
        return self

# ------------------------------
# Recursive Actions
# ------------------------------

class RandomChoice(ResolvableModel):
    action: Action
    weight: RINT = 1

    @model_validator(mode="after")
    def check_choice(self):
        check("x >= 0", x=self.weight)
        return self

class RandomAction(ActionBase):
    id: Literal["random"]
    choices: list[RandomChoice]

    @model_validator(mode="after")
    def check_random(self):
        if not self.choices:
            raise ValueError("RandomAction must have at least one choice")
        
        # Validate that each choice's action is a valid Action
        # Need it 'cause pydantic doesn't parse nested discriminated unions automatically here
        for c in self.choices:
            if not isinstance(c.action, Action.__origin__): 
                raise TypeError(f"Choice action not valid: {c.action}")
        return self


class RepeatAction(ActionBase):
    id: Literal["repeat"]
    actions: list[Action]
    count: RINT = 1

    @model_validator(mode="after")
    def check_repeat(self):
        check("count >= 0", count=self.count)
        if not self.actions:
            raise ValueError("RepeatAction must have at least one action")
        return self

# ------------------------------
# Action union
# ------------------------------

Action = Annotated[
    Union[
        DamageAction,
        BuffAction,
        ShieldAction,
        HealAction,
        ModifyAction,
        TextAction,
        StatusAction,
        ConditionAction,
        RandomAction,
        RepeatAction,
    ],
    Field(discriminator="id")
]

# ------------------------------
# Move
# ------------------------------

class Move(MoveContext):
    id: str
    name: RSTR = "unknown move"
    description: RSTR = "no description provided."

    enabled: bool = True

    type: RSTR = "none"
    category: RSTR = "none"

    charge_usage: RNUM = 0.0

    sound: Optional[RSTR] = None

    actions: list[Action] = Field(default_factory=list)

    def is_stab(self, user: FighterVolatile) -> bool:
        """Whether the move gets STAB for the user."""
        return self.type == user.current_fighter.type

    def type_effectiveness(self, user: FighterVolatile, target: FighterVolatile) -> float:
        """Calculate type effectiveness multiplier."""
        # Placeholder for type effectiveness calculation TODO take this into account
        return 1.0

    def get_effective_amount(self, user: FighterVolatile, target: FighterVolatile) -> NUM:
        """The actual amount to apply after considering bonuses."""
        base_amount = self.get_base_amount(user, target)
        added_charge_amount = base_amount * CHARGE_BONUS * (user.current_fighter.stats.charge / user.base_fighter.stats.charge)
        stab = STAB_BONUS if self.is_stab(user) else 1.0
        type_effectiveness = self.type_effectiveness(user, target)
        return ((base_amount + added_charge_amount) * self.mult + self.flat) * stab * type_effectiveness

    @model_validator(mode="after")
    def check_move(self):
        try:
            check("1 <= len(id) <= 63", id=self.id)
        except ValueError:
            raise ValueError(f"Invalid move id: {self.id}")
        try:
            check("len(name) <= 127", name=self.name)
        except ValueError:
            raise ValueError(f"Invalid move name: {self.name}")
        try:
            check("len(description) <= 511", description=self.description)
        except ValueError:
            raise ValueError(f"Invalid move description: {self.description}")
        try:
            check("type in types", 
                  type=self.type, types=TYPE)
        except ValueError:
            raise ValueError(f"Invalid move type: {self.type}")
        try:
            check("category in categories", 
                  category=self.category, categories=CATEGORY)
        except ValueError:
            raise ValueError(f"Invalid move category: {self.category}")
        try:
            check("0.0 <= charge_usage <= 999.0", charge_usage=self.charge_usage)
        except ValueError:
            raise ValueError(f"Invalid move charge usage: {self.charge_usage}")
        return self

class MoveSet(RootModel[list[Move]]):
    """
    Root model for a list of Move instances.
    Behaves like a dict keyed by move.id.
    """

    def model_post_init(self, __context=None):
        self._by_id: Dict[str, Move] = {}
        seen_ids = set()

        for move in self.root:
            if move.enabled:
                if move.id in seen_ids:
                    warnings.warn(f"Duplicate move id detected: '{move.id}'. Using last occurrence.", stacklevel=2)
                seen_ids.add(move.id)
                self._by_id[move.id] = move

        if not self._by_id:
            warnings.warn("MoveSet is empty!", stacklevel=2)

    def __getitem__(self, move_id: str) -> Move:
        if move_id not in self._by_id:
            raise ValueError(f"Move with id '{move_id}' does not exist in this MoveSet.")
        return self._by_id[move_id]
        
    def __delitem__(self, move_id: str):
        raise RuntimeError("Moves cannot be deleted from a MoveSet at runtime.")

    def __iter__(self):
        return iter(self._by_id.items())

    def __len__(self):
        return len(self._by_id)

    def __repr__(self):
        return repr(self._by_id)

    def __str__(self):
        return str(self._by_id)
    
    def keys(self):
        return self._by_id.keys()

    def values(self):
        return self._by_id.values()

    def items(self):
        return self._by_id.items()

    def get(self, move_id: str, default=None) -> Move | None:
        return self._by_id.get(move_id, default)

    def __contains__(self, key):
        return key in self._by_id


ConditionAction.model_rebuild()
RandomAction.model_rebuild()
RepeatAction.model_rebuild()
