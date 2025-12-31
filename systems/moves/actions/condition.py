from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler


class ConditionHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        for condition in action.conditions:
            battle_ctx.log_stack.append(f"Evaluating condition '{condition.id}' with value '{condition.value}'")
            # if not check_condition(condition.id, condition.value, ctx): return

            # Evaluate all conditions with AND logic
            # If any condition is False, the overall result is False
            # Evaluation are based on condition, values pairs

        for sub_action in action.actions:
            engine._execute_action(sub_action, user, target, battle_ctx, move_ctx)