from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext
    from ..engine import MoveEngine
    
from .action import ActionHandler


class RepeatHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None):
        count = action.count() if callable(action.count) else action.count

        battle_ctx.log.append(f"{user.current_fighter.name} will repeat actions {int(count)} times on {target.current_fighter.name}")
        for _ in range(int(count)):
            battle_ctx.log.append(f"Repeating action {action.actions} for {user.current_fighter.name} on {target.current_fighter.name}")
            for sub_action in action.actions:
                engine._execute_action(sub_action, user, target, battle_ctx, move_ctx)