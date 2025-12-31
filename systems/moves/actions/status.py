from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler


class StatusHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):

        status = [s.id for s in action.status]

        # should ensure we respect the doc status application rules
        # don't care about amount when removing
        for status in status:
            if action.operation == "add":
                battle_ctx.log_stack.append(f"Applying status '{status}' to {target.current_fighter.name} for {move_ctx.effective_amount} turns !")
            elif action.operation == "remove":
                battle_ctx.log_stack.append(f"Removing status from {target.current_fighter.name} !")