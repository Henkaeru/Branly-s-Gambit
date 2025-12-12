from pydantic import BaseModel, Field, model_validator
from typing import Any, List, Optional, Union, Dict

class StatusModel(BaseModel):
    id: str
    params: Optional[Dict[str, Any]] = {}

class ActionModel(BaseModel):
    id: str
    params: Optional[Dict[str, Any]] = {}

class ConditionModel(BaseModel):
    id: str
    params: Dict[str, Any] = {}
    actions: List[ActionModel] = []

class MoveModel(BaseModel):
    id: str
    name: str = Field(default_factory=lambda: "unknown")
    enabled: bool = True
    type: str = "none"
    category: str = "none"
    charge_usage: float = 0.0
    amount: Union[int, float] = 0
    chance: float = 1.0
    target: str  = "opponent"
    calc_target: str = "self"
    calc_field: str = "hp"
    multiply: float = 1.0
    divide: float = 1.0
    add: float = 0.0
    subtract: float = 0.0
    duration: int = -1
    description: str = ""
    actions: List[ActionModel] = []

    @model_validator(mode="before")
    def validate_chance_range(cls, values):
        chance = values.get("chance", 1.0)
        if not 0.0 <= chance <= 1.0:
            raise ValueError(f"chance must be between 0.0 and 1.0, got {chance}")
        return values
