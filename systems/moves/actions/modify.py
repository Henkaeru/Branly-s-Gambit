from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...battle.schema import BattleContext, FighterVolatile
    from ..schema import ActionBase, MoveContext, Move
    from ..engine import MoveEngine
    
from .action import ActionHandler


class ModifyHandler(ActionHandler):
    def execute(self, engine : MoveEngine, action : ActionBase, user: FighterVolatile | None = None, target: FighterVolatile | None = None,  battle_ctx : BattleContext | None = None, move_ctx: MoveContext | None = None, move: Move | None = None):
        field = action.field() if callable(action.field) else action.field
        value = action.value() if callable(action.value) else action.value

        # Complicated asf logic for modifying a field on a target
        # So not gonna implement it fully for now

        battle_ctx.log_stack.append(f"{target.current_fighter.name}'s {field} is modified to {value}")