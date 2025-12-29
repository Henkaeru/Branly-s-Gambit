from __future__ import annotations
from .actions.damage import DamageHandler
from .actions.buff import BuffHandler
from .actions.shield import ShieldHandler
from .actions.heal import HealHandler
from .actions.modify import ModifyHandler
from .actions.text import TextHandler
from .actions.status import StatusHandler
from .actions.condition import ConditionHandler
from .actions.random import RandomHandler
from .actions.repeat import RepeatHandler

ACTION_HANDLERS = {
    "damage": DamageHandler(),
    "buff": BuffHandler(),
    "shield": ShieldHandler(),
    "heal": HealHandler(),
    "modify": ModifyHandler(),
    "text": TextHandler(),
    "status": StatusHandler(),
    "condition": ConditionHandler(),
    "random": RandomHandler(),
    "repeat": RepeatHandler(),
}
