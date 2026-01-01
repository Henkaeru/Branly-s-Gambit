from __future__ import annotations
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine

from .action import ActionHandler


class RandomHandler(ActionHandler):
    def execute(
        self,
        engine: MoveEngine,
        action: ActionBase,
        user: FighterVolatile | None = None,
        target: FighterVolatile | None = None,
        battle_ctx: BattleContext | None = None,
        move_ctx: MoveContext | None = None,
        move: Move | None = None,
    ):
        if action is None:
            return False

        weights = [c.weight() if callable(c.weight) else c.weight for c in action.choices]
        if sum(weights) == 0:
            return False # no valid choices

        choice_action = random.choices(action.choices, weights=weights, k=1)[0].action
        return engine._execute_action(choice_action, user, target, battle_ctx, move_ctx, move)