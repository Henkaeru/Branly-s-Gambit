from __future__ import annotations
from ast import literal_eval
from pathlib import Path
import re
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Dict, Literal, Optional, TypeAlias, Union, Any, get_type_hints
from config.moves.random_number import NUM, RINT, RNUM, RSTR, RVAL

Stat = ["attack", "defense", "hp", "charge_bonus"]
Target = ["self", "opponent"]

COLOR = (
    "black", "dark_blue", "dark_green", "dark_aqua", "dark_red", "dark_purple",
    "gold", "gray", "dark_gray", "blue", "green", "aqua", "red", "light_purple", "yellow", "white"
)

STYLE = ("bold", "italic", "underlined", "strikethrough", "obfuscated")

STATUS = ("javaBien", "poison")

CONDITION = ("hp_below", "hp_above", "has_status", "lacks_status")
    
# ------------------------------
# Full Context with defaults
# ------------------------------

class Context(BaseModel):
    amount: RNUM = Field(0, ge=0)
    chance: RNUM = Field(1.0, ge=0.0, le=1.0)

    target: RSTR = "opponent"
    calc_target: RSTR = "self"
    calc_field: RSTR = "hp"

    mult: RNUM = Field(1.0, ge=0.0)
    flat: RNUM = 0

    duration: RINT = Field(-1, ge=-1)

    @model_validator(mode="after")
    def check_context(self):
        if self.target not in Target:
            raise ValueError("Context 'target' must be 'self' or 'opponent'.")
        if self.calc_target not in Target:
            raise ValueError("Context 'calc_target' must be 'self' or 'opponent'.")
        if self.calc_field not in Stat:
            raise ValueError("Context 'calc_field' must be a valid stat.")
        if self.amount + self.flat < 0:
            raise ValueError("Context 'flat' cannot make 'amount' negative.")
        return self

# ------------------------------
# ActionBase
# ------------------------------

class ActionBase(BaseModel):
    id: str

    @property
    def params(self) -> dict:
        """
        Action-specific parameters only (no context, no None)
        """
        return {
            k: v
            for k, v in self.model_dump(exclude_none=True).items()
            if k != "id"
        }

# ------------------------------
# Leaf Actions
# ------------------------------

class DamageAction(ActionBase):
    id: Literal["damage"]
    crit_chance: RNUM = Field(0.0, ge=0.0, le=1.0)
    crit_damage: RNUM = Field(0, ge=0)
    piercing: RNUM = Field(0.0, ge=0.0, le=1.0)

class BuffAction(ActionBase):
    id: Literal["buff"]
    stat: list[RSTR] | RSTR = "attack"

    @model_validator(mode="after")
    def check_buff(self):
        stats = [self.stat] if isinstance(self.stat, str) else self.stat
        for s in stats:
            if s not in Stat:
                raise ValueError("Buff 'stat' must be a valid stat or list of stats.")
        
        return self

class ShieldAction(ActionBase):
    id: Literal["shield"]

class HealAction(ActionBase):
    id: Literal["heal"]

class ModifyAction(ActionBase):
    id: Literal["modify"]
    field: RSTR = ""
    value: RVAL = None

    @model_validator(mode="after")
    def check_modify(self):
        pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
        if not pattern.match(self.field):
            raise ValueError("field must be a dot-path of identifiers (e.g. 'foo.bar_baz')")
        return self

class TextAction(ActionBase):
    id: Literal["text"]
    text: RSTR = Field(..., max_length=511)
    style: RSTR = "{}"

    @model_validator(mode="after")
    def check_text(self):
        # parse style string into a dict
        try:
            style_dict = literal_eval(self.style)
        except Exception:
            raise ValueError(f"Invalid style string: {self.style}")

        if not isinstance(style_dict, dict):
            raise ValueError(f"Style must be a dict-like string, got {type(style_dict).__name__}")

        # validate color
        color = style_dict.get("color")
        if color and color not in COLOR:
            raise ValueError(f"Invalid color: {color}")

        # validate style flags
        for key, val in style_dict.items():
            if key != "color" and (key not in STYLE or not isinstance(val, bool)):
                raise ValueError(f"Invalid style key/value: {key}={val}")

        # store parsed dict internally
        self.style = style_dict
        return self
    
# ------------------------------
# Status / Condition
# ------------------------------

class Status(BaseModel):
    id: str

    @model_validator(mode="after")
    def check_status(self):
        if self.id not in STATUS:
            raise ValueError(f"Invalid status id: {self.id}")
        return self

class Condition(BaseModel):
    id: str
    value: RVAL = None

    @model_validator(mode="after")
    def check_condition(self):
        if self.id not in CONDITION:
            raise ValueError(f"Invalid condition id: {self.id}")
        return self

class StatusAction(ActionBase):
    id: Literal["status"]
    operation: RSTR = "add"
    status: list[Status]

    @model_validator(mode="after")
    def check_status_action(self):
        if self.operation not in ("add", "remove"):
            raise ValueError("StatusAction 'operation' must be 'add' or 'remove'.")
        return self

class ConditionAction(ActionBase):
    id: Literal["condition"]
    conditions: list[Condition]
    actions: list[Action]

# ------------------------------
# Recursive Actions
# ------------------------------

class RandomChoice(BaseModel):
    action: Action
    weight: RINT = Field(1, ge=0)

class RandomAction(ActionBase):
    id: Literal["random"]
    choices: list[RandomChoice]

class RepeatAction(ActionBase):
    id: Literal["repeat"]
    actions: list[Action]
    count: RINT = Field(1, ge=0)


# ------------------------------
# Action union
# ------------------------------

Action = Annotated[
    Union[
        DamageAction,
        HealAction,
        ShieldAction,
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

class Move(Context):
    id: str = Field(..., min_length=3, max_length=63)
    name: RSTR = Field("unknown", min_length=1, max_length=127)
    description: RSTR = Field("No description provided.", max_length=511)

    enabled: bool = True

    type: RSTR = "none"
    category: RSTR = "none"

    charge_usage: RNUM = Field(0.0, ge=0.0, le=1.0)

    sound: Optional[RSTR] = None

    actions: list[Action] = []

    @model_validator(mode="after")
    def check_move(self):
        if self.type not in ("dev", "opti", "syst", "data", "proj", "team", "none"):
            raise ValueError(f"Invalid move type: {self.type}")
        if self.category not in ("damage", "support", "special", "none"):
            raise ValueError(f"Invalid move category: {self.category}")
        if self.sound:
            path = Path("assets/sounds/moves") / self.sound
            if not path.is_file():
                raise ValueError(f"Sound file does not exist: {path}")
        return self

