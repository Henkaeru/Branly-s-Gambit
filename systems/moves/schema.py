from __future__ import annotations
from pydantic import BaseModel, Field, RootModel, model_validator
from typing import Annotated, Dict, Literal, Optional, Union
from core.dsl.random_dsl import RINT, RNUM, RSTR, RVAL, check
import re
import warnings
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
    
# ------------------------------
# Full Move Context with defaults
# ------------------------------
class MoveContext(BaseModel):
    amount: RNUM = 0
    chance: RNUM = 1.0

    calc_target: RSTR = "self"
    calc_field: RSTR = "hp"

    mult: RNUM = 1.0
    flat: RNUM = 0

    duration: RINT = -1

    @model_validator(mode="after")
    def check_context(self):
        check("x >= 0", x=self.amount)
        check("0 <= x <= 1", x=self.chance)
        check("x >= 0", x=self.mult)
        check("x >= -1", x=self.duration)
        try:
            check("x in target", 
                  x=self.calc_target, target=Target)
        except ValueError:
            raise ValueError("MoveContext 'calc_target' must be 'self' or 'opponent'.")
        try:
            check("x in stat", 
                  x=self.calc_field, stat=Stat)
        except ValueError:
            raise ValueError("MoveContext 'calc_field' must be a valid stat.")
        try:
            check("x + y >= 0", 
                  x=self.amount, y=self.flat)
        except ValueError:
            raise ValueError("MoveContext 'amount' and 'flat' cannot sum to negative.")
        return self

# ------------------------------
# ActionBase
# ------------------------------
class ActionBase(BaseModel):
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
class DamageAction(ActionBase):
    id: Literal["damage"]
    crit_chance: RNUM = 0.0
    crit_damage: RNUM = 0
    piercing: RNUM = 0.0

    @model_validator(mode="after")
    def check_damage(self):
        check("0 <= x <= 1", x=self.crit_chance)
        check("x >= 0", x=self.crit_damage)
        check("0 <= x <= 1", x=self.piercing)
        return self

class BuffAction(ActionBase):
    id: Literal["buff"]
    stat: list[RSTR] | RSTR = "attack"

    @model_validator(mode="after")
    def check_buff(self):
        stats = [self.stat] if not isinstance(self.stat, list) else self.stat
        for s in stats:
            try:
                check("x in stat", 
                      x=s, stat=Stat)
            except ValueError:
                raise ValueError("Buff 'stat' must be a valid stat or list of stats.")
        return self

class ShieldAction(ActionBase):
    id: Literal["shield"]

class HealAction(ActionBase):
    id: Literal["heal"]

class ModifyAction(ActionBase):
    id: Literal["modify"]
    field: RSTR
    value: RVAL

    @model_validator(mode="after")
    def check_modify(self):
        pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
        try:
            check(
                "re.fullmatch(pattern, x) is not None",
                x=self.field,
                pattern=pattern,
                re=re,  # pass re module explicitly
            )
        except ValueError:
            raise ValueError("field must be a dot-path of identifiers (e.g. 'foo.bar_baz')")
        return self

class TextAction(ActionBase):
    id: Literal["text"]
    text: RSTR = "No text."
    style: RSTR = "{}"

@model_validator(mode="after")
def check_text(self):
    check("len(x) < 511", x=self.text)

    try:
        check("x.startswith('{') and x.endswith('}')", x=self.style)
    except ValueError:
        raise ValueError(
            "TextAction 'style' must be a dict-like string "
            "(e.g. '{\"color\":\"red\",\"bold\":true}')"
        )

    try:
        check("json.loads(x.replace(\"'\", '\"')).get('color') in color", 
              x=self.style, color=COLOR)
    except ValueError:
        raise ValueError(
            "TextAction 'style' contains invalid color flags."
        )

    try:
        check(
            "all(k in style and isinstance(v, bool) "
            "for k,v in json.loads(x.replace(\"'\", '\"')).items() if k != 'color')", 
            x=self.style, style=STYLE)
    except ValueError:
        raise ValueError(
            "TextAction 'style' contains invalid style flags."
        )

    return self
    
# ------------------------------
# Status / Condition
# ------------------------------

class Status(BaseModel):
    id: str

    @model_validator(mode="after")
    def check_status(self):
        try:
            check("x in status", 
                  x=self.id, status=STATUS)
        except ValueError:
            raise ValueError(f"Invalid status id: {self.id}")
        return self

class Condition(BaseModel):
    id: str
    value: RVAL

    @model_validator(mode="after")
    def check_condition(self):
        try:
            check("x in condition", 
                  x=self.id, condition=CONDITION)
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
            check("x in ('add', 'remove')", x=self.operation)
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

class RandomChoice(BaseModel):
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
        check("x >= 0", x=self.count)
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

    @model_validator(mode="after")
    def check_move(self):
        try:
            check("1 <= len(x) <= 63", x=self.id)
        except ValueError:
            raise ValueError(f"Invalid move id: {self.id}")
        try:
            check("len(x) <= 127", x=self.name)
        except ValueError:
            raise ValueError(f"Invalid move name: {self.name}")
        try:
            check("len(x) <= 511", x=self.description)
        except ValueError:
            raise ValueError(f"Invalid move description: {self.description}")
        try:
            check("x in type", 
                  x=self.type, type=TYPE)
        except ValueError:
            raise ValueError(f"Invalid move type: {self.type}")
        try:
            check("x in category", 
                  x=self.category, category=CATEGORY)
        except ValueError:
            raise ValueError(f"Invalid move category: {self.category}")
        try:
            check("0.0 <= x <= 999.0", x=self.charge_usage)
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
